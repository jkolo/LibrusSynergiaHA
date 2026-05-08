"""The Librus APIX integration."""

from __future__ import annotations

import asyncio
import logging
import random
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date as _date, datetime as _dt, timedelta
from pathlib import Path
from typing import Any, TypeVar

import uuid

import voluptuous as vol
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util
from librus_apix import urls as librus_urls
from librus_apix.announcements import get_announcements
from librus_apix.attendance import get_attendance, get_attendance_frequency
from librus_apix.client import Client, new_client
from librus_apix.exceptions import TokenError
from librus_apix.grades import get_grades
from librus_apix.messages import get_max_page_number, get_received
from librus_apix.schedule import get_schedule
from librus_apix.student_information import get_student_information
from librus_apix.timetable import get_timetable

from ._data_store import LibrusDataStore
from ._message_store import ReadMessagesStore
from .const import (
    DEFAULT_BASE_MINUTES,
    DEFAULT_HUMANIZE,
    DOMAIN,
    OPT_BASE_MINUTES,
    OPT_HUMANIZE,
    SERVICE_CLEAR_DISMISSED_NOTIFICATIONS,
    SERVICE_DISMISS_MESSAGE_NOTIFICATION,
    SERVICE_DOWNLOAD_ATTACHMENT,
    SERVICE_FETCH_MESSAGE_CONTENT,
    SERVICE_LIST_MESSAGES,
    SERVICE_RESTORE_MESSAGE_NOTIFICATION,
)
from .coordinator import LibrusDataUpdateCoordinator
from .humanize import build_headers, pick_user_agent

T = TypeVar("T")

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "calendar", "event"]

_MESSAGES_CARD_PATH = "/librus_apix/librus-messages-card.js"
_GRADES_CARD_PATH = "/librus_apix/librus-grades-card.js"

# Odczyt manifestu przy załadowaniu modułu (poza event loop) — cache bust dla karty Lovelace.
try:
    import json as _json
    _CARD_VERSION: str = _json.loads(
        (Path(__file__).parent / "manifest.json").read_text()
    )["version"]
except Exception:  # noqa: BLE001
    _CARD_VERSION = ""


def _card_url(path: str) -> str:
    """Zwróć URL karty z ?v= z manifest.json — bust cache przy update."""
    return f"{path}?v={_CARD_VERSION}" if _CARD_VERSION else path


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Zarejestruj karty Lovelace jako statyczne zasoby HA."""
    www_dir = Path(__file__).parent / "www"
    if hass.http is None:
        return True
    static_paths: list[StaticPathConfig] = []
    messages_js = www_dir / "librus-messages-card.js"
    if messages_js.exists():
        static_paths.append(StaticPathConfig(_MESSAGES_CARD_PATH, str(messages_js), cache_headers=False))
        hass.async_create_task(_async_ensure_lovelace_resource(hass, _card_url(_MESSAGES_CARD_PATH)))
    grades_js = www_dir / "librus-grades-card.js"
    if grades_js.exists():
        static_paths.append(StaticPathConfig(_GRADES_CARD_PATH, str(grades_js), cache_headers=False))
        hass.async_create_task(_async_ensure_lovelace_resource(hass, _card_url(_GRADES_CARD_PATH)))
    if static_paths:
        await hass.http.async_register_static_paths(static_paths)
        _LOGGER.debug("Librus Lovelace cards registered: %s", [p.url_path for p in static_paths])
    return True


async def _async_ensure_lovelace_resource(hass: HomeAssistant, url: str) -> None:
    """Dodaj lub zaktualizuj wpis karty Lovelace.

    Dopasowuje po ścieżce (bez query string) — jeśli wpis istnieje z inną
    wersją (np. ?v=3.5.0), podmienia go na nowy URL żeby wymusić reload JS.
    """
    from homeassistant.helpers.storage import Store

    base_path = url.split("?")[0]

    store = Store(hass, 1, "lovelace_resources", minor_version=1)
    data = await store.async_load() or {"items": []}
    items: list[dict] = data.setdefault("items", [])

    existing = next(
        (item for item in items if item.get("url", "").split("?")[0] == base_path),
        None,
    )
    if existing:
        if existing.get("url") == url:
            return  # Ten sam URL+wersja — nic do roboty
        existing["url"] = url  # Zaktualizuj wersję (cache bust)
        _LOGGER.info("Updated Lovelace resource to %s", url)
    else:
        items.append({"id": uuid.uuid4().hex, "url": url, "type": "module"})
        _LOGGER.info("Registered Lovelace resource: %s (effective after browser reload)", url)

    await store.async_save(data)

    # Powiadom na żywo aktywną kolekcję zasobów (działa gdy lovelace już skonfigurowane)
    # hass.data["lovelace"] to LovelaceData (obiekt, nie dict) — używamy getattr
    _lovelace_data = hass.data.get("lovelace")
    lovelace_resources = getattr(_lovelace_data, "resources", None) if _lovelace_data is not None else None
    if lovelace_resources is not None:
        try:
            live_items = lovelace_resources.async_items()
            live_existing = next(
                (i for i in live_items if i.get("url", "").split("?")[0] == base_path),
                None,
            )
            if live_existing is None:
                await lovelace_resources.async_create_item({"res_type": "module", "url": url})
            elif live_existing.get("url") != url:
                await lovelace_resources.async_update_item(
                    live_existing["id"], {"res_type": "module", "url": url}
                )
            _LOGGER.debug("Lovelace resource live-updated: %s", url)
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("Could not update Lovelace resource live: %s", exc)


@dataclass
class LibrusRuntimeData:
    """Runtime data stored on the config entry.

    Replaces the legacy hass.data[DOMAIN][entry_id] storage. HA cleans this
    up automatically when the entry is unloaded, so async_unload_entry just
    needs to forward the platform unload.
    """

    client: LibrusApiClient
    coordinator: LibrusDataUpdateCoordinator


type LibrusConfigEntry = ConfigEntry[LibrusRuntimeData]


class LibrusAuthError(Exception):
    """Raised when authentication permanently fails (likely password changed).

    Distinguished from a transient maintenance failure: emitted only after
    we've re-authenticated unsuccessfully twice in a row for the same fetch.
    Coordinator catches this and converts it to ConfigEntryAuthFailed so HA
    starts the reauth flow.
    """


_DESCRIPTIVE_DESC_KEYS = (
    "Ocena", "Przedmiot", "Obszar oceniania", "Umiejętność",
    "Data", "Nauczyciel", "Dodał", "Komentarz",
)


def _parse_descriptive_desc(desc: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in desc.split("\n"):
        line = line.strip()
        for key in _DESCRIPTIVE_DESC_KEYS:
            if line.startswith(f"{key}:"):
                result[key] = line[len(key) + 1:].strip()
                break
    # Komentarz może być wieloliniowy — wyciągnij pełną zawartość z oryginalnego stringa.
    komm_idx = desc.find("\nKomentarz:")
    if komm_idx != -1:
        result["Komentarz"] = desc[komm_idx + len("\nKomentarz:"):].strip()
    return result


def _current_semester() -> int:
    """Return current Polish school-year semester (1 or 2).

    Semester 1: September (9) - January (1).
    Semester 2: February (2) - June (6).
    July/August are summer break - we return 2 (last semester of the year).
    """
    m = _date.today().month
    return 1 if m >= 9 else 2


class LibrusApiClient:
    """Class to interface with the Librus API."""

    def __init__(
        self,
        username: str,
        password: str,
        *,
        rng: random.Random | None = None,
        humanize: bool = True,
    ) -> None:
        """Initialize the client.

        Args:
            username: Librus login.
            password: Librus password.
            rng: Optional `random.Random` for deterministic User-Agent
                selection (testing) or per-entry stable choice (seed by
                entry_id at the call site).
            humanize: When False, skip the headers patch entirely so the
                library uses its built-in defaults. Used by the OptionsFlow
                "humanize=off" debug switch.
        """
        self.username = username
        self.password = password
        self._client: Client | None = None
        self._token: Any | None = None
        self._auth_lock = asyncio.Lock()
        self._rng = rng or random.Random()
        self._humanize = humanize
        # UA wybrany raz przy starcie integracji — przeglądarka też nie
        # zmienia UA mid-session. Stabilny do reloadu.
        self._user_agent = pick_user_agent(self._rng)
        self._headers = build_headers(self._user_agent)
        _LOGGER.debug(
            "Librus client created for %s with User-Agent=%s, humanize=%s",
            username, self._user_agent, humanize,
        )

    def _apply_headers(self) -> None:
        """Patch the global librus_apix.urls.HEADERS dict with our headers.

        The library reads headers via `s.headers = urls.HEADERS` (reference
        to a module-level dict) in every HTTP method. By replacing the
        dict's contents (not rebinding the name) we propagate our browser-
        like headers through all library calls without modifying the lib.

        No-op when `humanize=False` — the library keeps its built-in UA.
        Idempotent — safe to call before every fetch. With multiple config
        entries the global dict can race; we accept this since both
        entries' headers are realistic (anti-bot won't notice the swap).
        """
        if not self._humanize:
            return
        librus_urls.HEADERS.clear()
        librus_urls.HEADERS.update(self._headers)

    def _reset_auth(self) -> None:
        """Reset authentication state to force re-authentication on next call."""
        self._client = None
        self._token = None

    async def async_authenticate(self) -> bool:
        """Authenticate with Librus API."""
        async with self._auth_lock:
            try:
                # Patch headers before initial token fetch too — the very
                # first request to /OAuth/Authorization uses urls.HEADERS.
                self._apply_headers()
                loop = asyncio.get_running_loop()
                self._client = await loop.run_in_executor(None, new_client)
                self._token = await loop.run_in_executor(
                    None, self._client.get_token, self.username, self.password
                )
                _LOGGER.debug("Authentication successful for %s", self.username)
                return True
            except Exception:
                _LOGGER.exception("Authentication failed")
                self._reset_auth()
                return False

    async def _with_retry(
        self,
        label: str,
        work: Callable[[Client], T],
    ) -> T | None:
        """Run a sync librus-apix call with auth retry.

        `work` runs in the default executor. Behaviour:

        - On TokenError (or auth returning False): we re-authenticate and
          try once more. After the second TokenError we raise
          LibrusAuthError — the coordinator translates it into
          ConfigEntryAuthFailed so HA starts a reauth flow.
        - On any other exception we log and return None — that's treated
          as transient failure and the coordinator falls back to cache.
        """
        auth_failures = 0
        for attempt in range(2):
            try:
                if not self._client or not self._token:
                    if not await self.async_authenticate():
                        auth_failures += 1
                        if auth_failures >= 2:
                            raise LibrusAuthError(
                                f"Authentication failed twice fetching {label}"
                            )
                        continue
                # Apply browser-like headers before every request — the
                # library uses a global `urls.HEADERS` dict, so we patch
                # it idempotently per call.
                self._apply_headers()
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, work, self._client)
            except TokenError:
                _LOGGER.warning(
                    "Token expired fetching %s (attempt %d/2), re-authenticating...",
                    label, attempt + 1,
                )
                self._reset_auth()
                if attempt == 1:
                    _LOGGER.error(
                        "TokenError persisted after re-auth fetching %s — "
                        "treating as auth failure", label,
                    )
                    raise LibrusAuthError(
                        f"Token expired persistently fetching {label}"
                    )
            except LibrusAuthError:
                raise
            except Exception:
                _LOGGER.exception(
                    "Failed to get %s (attempt %d/2)", label, attempt + 1
                )
                self._reset_auth()
                if attempt == 1:
                    return None
        return None

    async def async_get_grades(self) -> list[dict[str, Any]] | None:
        """Get grades from Librus."""
        current_sem = _current_semester()
        _LOGGER.debug("Filtrowanie ocen dla semestru %d", current_sem)

        def _work(client: Client) -> list[dict[str, Any]]:
            numeric_grades, _avg, descriptive_grades = get_grades(client, "all")

            all_grades: list[dict[str, Any]] = []

            for subject_grades in numeric_grades:
                for subject, grades_list in subject_grades.items():
                    for grade in grades_list:
                        if grade.semester != current_sem:
                            continue
                        # `value` is a property — może rzucić ValueError dla
                        # zachowaniowych ocen typu "A+". Cache w try by nie
                        # wywalić całego fetcha.
                        try:
                            value = grade.value
                        except ValueError:
                            value = None
                        all_grades.append({
                            "subject": subject,
                            "grade": grade.grade,
                            "value": value,
                            "counts": grade.counts,
                            "weight": grade.weight,
                            "date": grade.date,
                            "category": grade.category,
                            "description": getattr(grade, "desc", ""),
                            "title": getattr(grade, "title", ""),
                            "teacher": getattr(grade, "teacher", ""),
                            "semester": grade.semester,
                            "type": "numeric",
                        })

            for subject_grades in descriptive_grades:
                for subject, grades_list in subject_grades.items():
                    for desc_grade in grades_list:
                        if desc_grade.semester != current_sem:
                            continue
                        grade_val = desc_grade.grade.strip()
                        # Akceptuj wartosc jesli po usunieciu +/- jest cyfra (1-6).
                        if grade_val and grade_val.replace("+", "").replace("-", "").isdigit():
                            desc = getattr(desc_grade, "desc", "") or ""
                            parsed = _parse_descriptive_desc(desc)
                            all_grades.append({
                                "subject": subject,
                                "grade": desc_grade.grade,
                                "value": None,
                                "counts": False,
                                "weight": 0,
                                "date": desc_grade.date,
                                "category": parsed.get("Umiejętność", ""),
                                "description": parsed.get("Komentarz", ""),
                                "title": parsed.get("Obszar oceniania", ""),
                                "teacher": parsed.get("Nauczyciel", ""),
                                "semester": desc_grade.semester,
                                "type": "descriptive",
                            })

            return all_grades

        return await self._with_retry("grades", _work)

    async def async_get_messages(
        self, known_hrefs: frozenset[str] | None = None
    ) -> list[dict[str, Any]] | None:
        """Get new inbox messages from Librus (delta fetch).

        Only headers are returned — body NOT fetched to avoid marking as read.
        Iterates pages 0..max_page; stops at the first page containing a message
        whose href is already in known_hrefs (previous sync). Returns only the
        messages that are newer than any known href.
        """
        def _work(client: Client) -> list[dict[str, Any]]:
            max_page = get_max_page_number(client)
            new_messages: list[dict[str, Any]] = []
            for page in range(max_page + 1):
                page_msgs = get_received(client, page)
                if not page_msgs:
                    break
                found_known = False
                for msg in page_msgs:
                    if known_hrefs and msg.href in known_hrefs:
                        found_known = True
                        break  # wiadomości po granicy są starsze — już w cache
                    new_messages.append({
                        "author": msg.author,
                        "title": msg.title,
                        "date": msg.date,
                        "href": msg.href,
                        "unread": msg.unread,
                        "has_attachment": msg.has_attachment,
                    })
                if found_known:
                    break
            return new_messages

        return await self._with_retry("messages", _work)

    async def async_get_student_information(self) -> Any | None:
        """Get student information from Librus."""
        return await self._with_retry("student information", get_student_information)

    async def async_get_schedule_events(
        self, months_ahead: int = 2, only_exams: bool = True
    ) -> list[dict[str, Any]] | None:
        """Pobierz wydarzenia z terminarza Librusa.

        Args:
            months_ahead: Ile miesiecy w przod pobrac (1 = tylko biezacy, 2 = + nastepny).
            only_exams: True = zwroc tylko sprawdziany/kartkowki (default, backwards compat).
                False = zwroc cały terminarz (sprawdziany, dni wolne, swieta, etc.) z polami
                `is_exam` i `is_day_off` na kazdym evencie.

        Returns:
            Lista dictow z polami: title, subject, category, date (YYYY-MM-DD),
            hour, day, href, days_until, is_exam, is_day_off.
        """
        today = _date.today()

        # Slowa kluczowe wykluczajace - jesli wystapia, event jest klasyfikowany
        # jako dzien_wolny (Librus pokazuje "Egzamin osmoklasisty - dzien wolny"
        # jako event, ale to dzien wolny od zajec, nie sprawdzian).
        exclude_keywords = (
            "dzien wolny",
            "dzień wolny",
            "wolne od zaj",
            "wolny od zaj",
        )
        # href zawierajacy "wolne" wskazuje na dzien wolny w terminarzu Librusa
        exclude_href_fragments = ("szczegoly_wolne", "wolne")

        # Pobierz schedule dla biezacego + nastepnych miesiecy
        month_year_pairs: list[tuple[int, int]] = []
        for offset in range(months_ahead):
            target = today.replace(day=1) + timedelta(days=32 * offset)
            target = target.replace(day=1)
            month_year_pairs.append((target.month, target.year))

        def _work(client: Client) -> list[dict[str, Any]]:
            events_raw: list[tuple[int, int, int, Any]] = []
            for idx, (month, year) in enumerate(month_year_pairs):
                if idx > 0:
                    # Human-like pause between consecutive month fetches
                    # — sync sleep is fine, we run inside run_in_executor.
                    time.sleep(self._rng.uniform(0.5, 3.0))
                try:
                    result = get_schedule(client, str(month), str(year), False)
                except TokenError:
                    raise  # bubble up to _with_retry for re-auth
                except Exception as ex:
                    _LOGGER.debug(
                        "Schedule fetch failed for %d/%d: %s", month, year, ex
                    )
                    continue
                # result: DefaultDict[int, List[Event]] — klucz = dzien miesiaca
                for day_num, day_events in result.items():
                    for event in day_events:
                        events_raw.append((month, year, day_num, event))

            upcoming: list[dict[str, Any]] = []
            for month, year, day_num, event in events_raw:
                try:
                    event_date = _date(year, month, day_num)
                except ValueError:
                    continue

                if event_date < today:
                    continue  # przeszle pomijamy

                title = (event.title or "").lower()
                subject = event.subject or ""
                # event.data to dict - moze zawierac szczegoly (Kategoria, Typ)
                data_dict = event.data if isinstance(event.data, dict) else {}
                category_str = str(data_dict.get("Kategoria", "")).lower()
                type_str = str(data_dict.get("Typ", "")).lower()
                haystack = f"{title} {category_str} {type_str}"
                href_lower = (event.href or "").lower()

                is_day_off = (
                    any(ex in haystack for ex in exclude_keywords)
                    or any(frag in href_lower for frag in exclude_href_fragments)
                )
                # Machine-readable classification for calendar tagging.
                # Values are English codes; calendar.py maps them to Polish
                # display tags (SPRAWDZIAN, KARTKOWKA, ...) in summaries.
                if is_day_off:
                    event_type = "day_off"
                elif "sprawdzian" in haystack:
                    event_type = "exam"
                elif "kartkow" in haystack:
                    event_type = "quiz"
                elif "praca klasowa" in haystack:
                    event_type = "class_test"
                elif "praca kontrolna" in haystack:
                    event_type = "assessment"
                elif "wypracowanie klasowe" in haystack:
                    event_type = "essay_test"
                elif "test " in haystack:
                    event_type = "test"
                else:
                    event_type = "other"
                is_exam = event_type in (
                    "exam", "quiz", "class_test", "assessment", "essay_test", "test",
                )

                if only_exams and not is_exam:
                    continue

                days_until = (event_date - today).days
                upcoming.append({
                    "title": event.title,
                    "subject": subject,
                    "category": data_dict.get("Kategoria") or data_dict.get("Typ") or "",
                    "date": event_date.isoformat(),
                    "hour": event.hour or "",
                    "day_label": event.day or "",
                    "lesson_number": event.number,
                    "href": event.href or "",
                    "days_until": days_until,
                    "is_exam": is_exam,
                    "is_day_off": is_day_off,
                    "event_type": event_type,
                })

            upcoming.sort(key=lambda e: (e["date"], e.get("hour") or ""))
            return upcoming

        return await self._with_retry("schedule", _work)

    async def async_get_timetable_events(
        self, weeks_ahead: int = 2
    ) -> list[dict[str, Any]] | None:
        """Pobierz plan lekcji z Librusa (timetable).

        Args:
            weeks_ahead: Ile tygodni w przod pobrac (1 = tylko biezacy).

        Returns:
            Lista dictow z polami: subject, teacher, classroom, date (YYYY-MM-DD),
            time_from (HH:MM), time_to (HH:MM), weekday, lesson_number, info.
            None jesli blad.
        """
        today = _date.today()
        # Najblizszy poniedzialek (lub dzisiaj jesli to poniedzialek)
        monday = today - timedelta(days=today.weekday())

        def _work(client: Client) -> list[dict[str, Any]]:
            lessons: list[dict[str, Any]] = []
            for week_offset in range(weeks_ahead):
                if week_offset > 0:
                    # Human-like pause between consecutive week fetches.
                    time.sleep(self._rng.uniform(0.5, 3.0))
                target_monday = monday + timedelta(weeks=week_offset)
                monday_dt = _dt.combine(target_monday, _dt.min.time())
                try:
                    week = get_timetable(client, monday_dt)
                except TokenError:
                    raise
                except Exception as ex:
                    _LOGGER.debug(
                        "Timetable fetch failed for %s: %s", target_monday, ex
                    )
                    continue
                # week to List[List[Period]] - lista dni, kazdy dzien lista lekcji
                for day_periods in week:
                    for period in day_periods:
                        try:
                            if not period.subject:
                                continue
                            lessons.append({
                                "subject": period.subject,
                                "teacher_and_classroom": period.teacher_and_classroom or "",
                                "date": period.date or "",
                                "time_from": period.date_from or "",
                                "time_to": period.date_to or "",
                                "weekday": period.weekday or "",
                                "lesson_number": period.number,
                                "info": dict(period.info) if period.info else {},
                            })
                        except AttributeError:
                            continue

            lessons.sort(key=lambda l: (l["date"], l.get("time_from") or ""))
            return lessons

        return await self._with_retry("timetable", _work)

    async def async_get_attendance(self) -> list[dict[str, Any]] | None:
        """Pobierz wszystkie wpisy frekwencji (cały rok szkolny).

        Każdy wpis ma symbol Librusa (`nb`/`sp`/`u`/`zw`/`ob`/`wy`/`k`/`sz`).
        Płaska lista po obu semestrach + flag-owe pola dla łatwego filtrowania
        w sensorach (is_absence/is_late/is_unjustified/is_excused).
        """

        def _work(client: Client) -> list[dict[str, Any]]:
            per_sem = get_attendance(client, "all")  # List[List[Attendance]]
            flat: list[dict[str, Any]] = []
            for sem_list in per_sem:
                for entry in sem_list:
                    sym = entry.symbol or ""
                    flat.append({
                        "symbol": sym,
                        "type": entry.type or "",
                        "date": entry.date or "",
                        "subject": entry.subject or "",
                        "teacher": entry.teacher or "",
                        "period": entry.period,
                        "topic": entry.topic or "",
                        "semester": entry.semester,
                        "excursion": bool(entry.excursion),
                        "is_present": sym == "ob",
                        "is_absence": sym in ("nb", "u"),
                        "is_unjustified": sym == "nb",
                        "is_excused": sym == "u",
                        "is_late": sym == "sp",
                        "is_release": sym == "zw",
                    })
            flat.sort(key=lambda e: e["date"])
            return flat

        return await self._with_retry("attendance", _work)

    async def async_get_attendance_frequency(
        self,
    ) -> tuple[float, float, float] | None:
        """Procent obecności jako (semestr_1, semestr_2, ogółem).

        Tuple of three floats; gdy biblioteka zwraca brak danych — None.
        """

        def _work(client: Client) -> tuple[float, float, float]:
            return get_attendance_frequency(client)

        return await self._with_retry("attendance_frequency", _work)

    async def async_get_announcements(self) -> list[dict[str, Any]] | None:
        """Pobierz ogłoszenia systemowe szkoły.

        Pola: `title`, `author`, `description`, `date`. Lista posortowana
        chronologicznie (najnowsze pierwsze).
        """

        def _work(client: Client) -> list[dict[str, Any]]:
            items = get_announcements(client)
            return [
                {
                    "title": a.title or "",
                    "author": a.author or "",
                    "description": a.description or "",
                    "date": a.date or "",
                }
                for a in items
            ]

        return await self._with_retry("announcements", _work)


    async def async_get_message_content(self, href: str) -> dict[str, str] | None:
        """Pobierz pełną treść wiadomości (inner HTML) po numerycznym ID href.

        UWAGA: GET na URL wiadomości SERVER-SIDE oznacza ją jako przeczytaną
        w Librusie. Drugi rodzic na osobnym koncie Librus nie jest dotknięty.
        Implementacja własna (nie przez message_content() z librus-apix) —
        biblioteka zwraca .text (plain text); potrzebujemy decode_contents() (HTML).
        """
        def _work(client: Client) -> dict[str, str]:
            from bs4 import BeautifulSoup
            from librus_apix.exceptions import ParseError
            from librus_apix.helpers import no_access_check
            from librus_apix.messages import unwrap_message_data
            import librus_apix.urls as _urls

            # Krok 1: Odwiedź listę wiadomości — symuluje nawigację użytkownika,
            # prymuje stan sesji Librusa przed fetchem konkretnej wiadomości.
            client.post(_urls.MESSAGE_URL, data={
                "numer_strony105": 0,
                "porcjowanie_pojemnik105": "105",
            })

            # Krok 2: Pobierz konkretną wiadomość (side-effect: SS mark-as-read).
            soup = no_access_check(
                BeautifulSoup(
                    client.get(_urls.MESSAGE_URL + "/" + href).text, "lxml"
                )
            )
            message_data = soup.select_one("table[class='stretch']")
            if message_data is None:
                raise ParseError("Error in parsing message data.")
            trs = message_data.select("tr")
            if len(trs) < 3:
                raise ParseError("Not enough rows in message_data")
            author_row, title_row, date_row = trs[:3]
            content = soup.find("div", attrs={"class": "container-message-content"})
            if content is None:
                raise ParseError("Error in parsing message content.")

            # Librus embeds attachment download URLs in onclick of <img> elements:
            # otworz_w_nowym_oknie("\/wiadomosci\/pobierz_zalacznik\/MSG_ID\/ATTACH_ID", ...)
            attachments: list[dict[str, str]] = []
            seen_urls: set[str] = set()

            for img in soup.select("img[onclick*='pobierz_zalacznik']"):
                onclick = img.get("onclick", "")
                m = re.search(r'"((?:\\/|/)[^"]+pobierz_zalacznik[^"]+)"', onclick)
                if not m:
                    continue
                url = m.group(1).replace("\\/", "/")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                # Filename is in the sibling <td> (same <tr>, first cell)
                tr = img.find_parent("tr")
                name = ""
                if tr:
                    tds = tr.find_all("td")
                    if tds:
                        name = tds[0].get_text(strip=True)
                attachments.append({"name": name, "url": url})

            return {
                "author": unwrap_message_data(author_row),
                "title": unwrap_message_data(title_row),
                "date": unwrap_message_data(date_row),
                "content": content.decode_contents(),
                "attachments": attachments,
            }

        try:
            return await self._with_retry("message_content", _work)
        except Exception as exc:
            _LOGGER.warning("Could not fetch message content for %s: %s", href, exc)
            return None


    async def async_download_attachment(self, attachment_url: str) -> dict[str, Any] | None:
        """Pobierz załącznik przez sesję Librusa i zwróć jako base64."""
        def _work(client: Client) -> dict[str, Any]:
            import base64
            import os
            import time as _time
            from urllib.parse import urlparse, parse_qs
            import librus_apix.urls as _urls

            full_url = (
                _urls.BASE_URL + attachment_url
                if attachment_url.startswith("/")
                else attachment_url
            )

            # Przygotuj sesję z odpowiednimi cookies — Client.get() nie obsługuje kwargs
            client.cookies.update(client.token.access_cookies())
            session = client._session
            session.headers = _urls.HEADERS
            session.cookies = client.cookies

            # allow_redirects=False — Librus zwraca 302 do CSTryToDownload
            response = session.get(full_url, proxies=client.proxy, allow_redirects=False)

            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location", "")

                if "CSTryToDownload" in location or "singleUseKey" in location:
                    parsed = urlparse(location)
                    key = parse_qs(parsed.query).get("singleUseKey", [None])[0]

                    # Krok 1: GET CSTryToDownload — inicjuje pobieranie po stronie serwera
                    r_try = session.get(location, proxies=client.proxy)

                    if not key:
                        m = re.search(r'singleUseKey\s*=\s*["\']([^"\']+)["\']', r_try.text)
                        key = m.group(1) if m else None

                    if key:
                        # Krok 2: Poll CSCheckKey do "ready" (max 10 prób, 0.5s przerwa)
                        check_url = "https://sandbox.librus.pl/index.php?action=CSCheckKey"
                        for _ in range(10):
                            r_check = session.post(check_url, data={"singleUseKey": key}, proxies=client.proxy)
                            try:
                                if r_check.json().get("status") == "ready":
                                    break
                            except Exception:
                                pass
                            _time.sleep(0.5)

                        # Krok 3: GET CSDownload
                        download_url = location.replace("CSTryToDownload", "CSDownload")
                        response = session.get(download_url, proxies=client.proxy)
                    else:
                        response = r_try

                elif "GetFile" in location:
                    response = session.get(location.rstrip("/") + "/get", proxies=client.proxy)
                else:
                    response = session.get(location, proxies=client.proxy)
            else:
                if response.status_code != 200:
                    response = session.get(full_url, proxies=client.proxy)

            content_type = (
                response.headers.get("Content-Type", "application/octet-stream")
                .split(";")[0]
                .strip()
            )
            cd = response.headers.get("Content-Disposition", "")
            filename = ""
            if "filename=" in cd:
                raw = cd.split("filename=")[-1].strip().strip("\"'")
                try:
                    filename = raw.encode("latin-1").decode("utf-8")
                except (UnicodeDecodeError, UnicodeEncodeError):
                    filename = raw
            if not filename:
                filename = os.path.basename(attachment_url.split("?")[0]) or "attachment"

            _LOGGER.debug("Pobrano załącznik %s (%s, %d B)", filename, content_type, len(response.content))

            return {
                "filename": filename,
                "content_type": content_type,
                "data": base64.b64encode(response.content).decode("utf-8"),
            }

        try:
            return await self._with_retry("attachment", _work)
        except Exception as exc:
            _LOGGER.warning("Could not download attachment %s: %s", attachment_url, exc)
            return None


async def _async_options_updated(hass: HomeAssistant, entry: LibrusConfigEntry) -> None:
    """Reload the entry whenever the user changes options."""
    await hass.config_entries.async_reload(entry.entry_id)


def _setup_services(hass: HomeAssistant) -> None:
    """Register mark-as-read services (no-op if already registered)."""
    if hass.services.has_service(DOMAIN, SERVICE_DISMISS_MESSAGE_NOTIFICATION):
        return

    _schema_with_href = vol.Schema({
        vol.Required("entry"): cv.string,
        vol.Required("message_href"): cv.string,
    })
    _schema_entry_only = vol.Schema({
        vol.Required("entry"): cv.string,
    })

    def _resolve_coordinator(entry_id: str) -> LibrusDataUpdateCoordinator:
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_entry",
                translation_placeholders={"entry_id": entry_id},
            )
        runtime = getattr(entry, "runtime_data", None)
        if runtime is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="entry_not_initialized",
            )
        return runtime.coordinator

    def _validate_href(coordinator: LibrusDataUpdateCoordinator, href: str) -> dict:
        msgs = (coordinator.data or {}).get("messages") or []
        msg = next((m for m in msgs if m.get("href") == href), None)
        if msg is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="message_not_found",
                translation_placeholders={"href": href},
            )
        return msg

    async def _dismiss_notification(call: ServiceCall) -> None:
        import hashlib
        from homeassistant.components import persistent_notification

        entry_id: str = call.data["entry"]
        href: str = call.data["message_href"]
        coordinator = _resolve_coordinator(entry_id)
        _validate_href(coordinator, href)
        await coordinator.read_messages_store.async_mark_read(href)
        for m in (coordinator.data or {}).get("messages", []):
            if m.get("href") == href:
                m["notification_dismissed"] = True
                break
        coordinator.async_set_updated_data(coordinator.data)
        href_hash = hashlib.sha1(href.encode()).hexdigest()[:10]
        notification_id = f"librus_apix_msg_{entry_id}_{href_hash}"
        persistent_notification.async_dismiss(hass, notification_id)

    async def _restore_notification(call: ServiceCall) -> None:
        entry_id: str = call.data["entry"]
        href: str = call.data["message_href"]
        coordinator = _resolve_coordinator(entry_id)
        _validate_href(coordinator, href)
        await coordinator.read_messages_store.async_mark_unread(href)
        for m in (coordinator.data or {}).get("messages", []):
            if m.get("href") == href:
                m["notification_dismissed"] = False
                break
        coordinator.async_set_updated_data(coordinator.data)

    async def _clear_dismissed(call: ServiceCall) -> None:
        entry_id: str = call.data["entry"]
        coordinator = _resolve_coordinator(entry_id)
        await coordinator.read_messages_store.async_clear()
        for m in (coordinator.data or {}).get("messages", []):
            m["notification_dismissed"] = False
        coordinator.async_set_updated_data(coordinator.data)

    async def _fetch_content(call: ServiceCall) -> dict:
        entry_id: str = call.data["entry"]
        href: str = call.data["message_href"]
        coordinator = _resolve_coordinator(entry_id)
        _validate_href(coordinator, href)
        content = await coordinator.client.async_get_message_content(href)
        if content is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="message_fetch_failed",
                translation_placeholders={"href": href},
            )
        await coordinator.read_messages_store.async_mark_read(href)
        for m in (coordinator.data or {}).get("messages", []):
            if m.get("href") == href:
                m["notification_dismissed"] = True
                break
        coordinator.async_set_updated_data(coordinator.data)
        # Ensure attachments key is always present (backwards-compat with older clients)
        content.setdefault("attachments", [])
        return content

    hass.services.async_register(
        DOMAIN, SERVICE_DISMISS_MESSAGE_NOTIFICATION, _dismiss_notification,
        schema=_schema_with_href,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RESTORE_MESSAGE_NOTIFICATION, _restore_notification,
        schema=_schema_with_href,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CLEAR_DISMISSED_NOTIFICATIONS, _clear_dismissed,
        schema=_schema_entry_only,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_FETCH_MESSAGE_CONTENT, _fetch_content,
        schema=_schema_with_href,
        supports_response=SupportsResponse.ONLY,
    )

    async def _list_messages(call: ServiceCall) -> dict:
        entry_id: str = call.data["entry"]
        offset: int = call.data["offset"]
        count: int = call.data["count"]
        coordinator = _resolve_coordinator(entry_id)
        # Read from coordinator cache — NO Librus API call.
        # coordinator.data["messages"] is already annotated by _annotate_messages.
        all_messages: list = (coordinator.data or {}).get("messages", [])
        page = all_messages[offset : offset + count]
        return {
            "messages": [
                {
                    "sender": m["author"],
                    "title": m["title"],
                    "date": m["date"],
                    "unread": m.get("unread", False),
                    "is_recent": m.get("is_recent", False),
                    "notification_dismissed": m.get("notification_dismissed", False),
                    "has_attachment": m.get("has_attachment", False),
                    "href": m.get("href", ""),
                }
                for m in page
            ],
            "has_more": len(all_messages) > offset + count,
            "total_count": len(all_messages),
        }

    hass.services.async_register(
        DOMAIN, SERVICE_LIST_MESSAGES, _list_messages,
        schema=vol.Schema({
            vol.Required("entry"): cv.string,
            vol.Optional("offset", default=0): vol.All(int, vol.Range(min=0)),
            vol.Optional("count", default=10): vol.All(int, vol.Range(min=1, max=100)),
        }),
        supports_response=SupportsResponse.ONLY,
    )

    async def _download_attachment(call: ServiceCall) -> dict:
        entry_id: str = call.data["entry"]
        attachment_url: str = call.data["attachment_url"]
        coordinator = _resolve_coordinator(entry_id)
        result = await coordinator.client.async_download_attachment(attachment_url)
        if result is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="attachment_download_failed",
                translation_placeholders={"url": attachment_url},
            )
        return result

    hass.services.async_register(
        DOMAIN, SERVICE_DOWNLOAD_ATTACHMENT, _download_attachment,
        schema=vol.Schema({
            vol.Required("entry"): cv.string,
            vol.Required("attachment_url"): cv.string,
        }),
        supports_response=SupportsResponse.ONLY,
    )


async def async_setup_entry(hass: HomeAssistant, entry: LibrusConfigEntry) -> bool:
    """Set up Librus APIX from a config entry."""
    # Seed RNG by entry_id so each child gets a stable but distinct UA
    # across HA restarts (deterministic per entry, different per entry).
    rng = random.Random(entry.entry_id)
    humanize = entry.options.get(OPT_HUMANIZE, DEFAULT_HUMANIZE)
    client = LibrusApiClient(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        rng=rng,
        humanize=humanize,
    )

    # Coordinator wykonuje pierwszy login w _async_setup() podczas
    # async_config_entry_first_refresh(). On failure rzuca ConfigEntryNotReady
    # (np. Librus maintenance) — HA retryuje setup z exponential backoff.
    # Osobny RNG dla koordynatora (kolejność/pauzy) — niezależny od UA-RNG
    # by każdy refresh dawał inną kolejność, niezależnie od UA wybranego raz.
    coord_rng = random.Random(f"{entry.entry_id}-coordinator")
    coordinator = LibrusDataUpdateCoordinator(
        hass, client, config_entry=entry, rng=coord_rng
    )

    read_store = ReadMessagesStore(hass, entry.entry_id)
    await read_store.async_load()
    coordinator.read_messages_store = read_store

    data_store = LibrusDataStore(hass, entry.entry_id)
    coordinator.data_store = data_store
    cached = await data_store.async_load()

    if cached is not None:
        coordinator.data, saved_at = cached
        coordinator._seed_seen_sets_from_data(coordinator.data)
        coordinator._first_run = False
        _LOGGER.debug(
            "Loaded coordinator data from cache (saved %s), skipping first_refresh",
            saved_at.isoformat(),
        )
        # Jeśli cache jest starszy niż jeden interwał — odśwież szybko po 60s,
        # by nie pokazywać nieaktualnych danych dłużej niż jeden cykl.
        base_min = entry.options.get(OPT_BASE_MINUTES, DEFAULT_BASE_MINUTES)
        cache_age = dt_util.utcnow() - saved_at
        if cache_age.total_seconds() > base_min * 60:
            _LOGGER.debug("Cache stale (age=%s), scheduling fast refresh in 60s", cache_age)
            coordinator._unsub_next = async_call_later(
                hass, 60, coordinator._scheduled_refresh
            )
        else:
            coordinator.schedule_next_refresh()
    else:
        await coordinator.async_config_entry_first_refresh()
        # Custom scheduler kicks off here so coordinator.data["schedule"] is
        # already populated from the first refresh — schedule_next_refresh
        # reads is_school_day(today, schedule) to slow down on holidays.
        coordinator.schedule_next_refresh()

    entry.runtime_data = LibrusRuntimeData(client=client, coordinator=coordinator)

    _setup_services(hass)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: LibrusConfigEntry) -> bool:
    """Unload a config entry. runtime_data is cleaned up by HA automatically."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)