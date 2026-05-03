"""The Librus APIX integration."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date as _date, datetime as _dt, timedelta
from typing import Any, TypeVar

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from librus_apix import urls as librus_urls
from librus_apix.client import Client, new_client
from librus_apix.exceptions import TokenError
from librus_apix.grades import get_grades
from librus_apix.messages import get_received
from librus_apix.schedule import get_schedule
from librus_apix.student_information import get_student_information
from librus_apix.timetable import get_timetable

from .const import DOMAIN
from .coordinator import LibrusDataUpdateCoordinator
from .humanize import build_headers, pick_user_agent

T = TypeVar("T")

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "calendar"]


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
    ) -> None:
        """Initialize the client.

        Args:
            username: Librus login.
            password: Librus password.
            rng: Optional `random.Random` for deterministic User-Agent
                selection (testing) or per-entry stable choice (seed by
                entry_id at the call site).
        """
        self.username = username
        self.password = password
        self._client: Client | None = None
        self._token: Any | None = None
        self._auth_lock = asyncio.Lock()
        self._rng = rng or random.Random()
        # UA wybrany raz przy starcie integracji — przeglądarka też nie
        # zmienia UA mid-session. Stabilny do reloadu.
        self._user_agent = pick_user_agent(self._rng)
        self._headers = build_headers(self._user_agent)
        _LOGGER.debug(
            "Librus client created for %s with User-Agent=%s",
            username, self._user_agent,
        )

    def _apply_headers(self) -> None:
        """Patch the global librus_apix.urls.HEADERS dict with our headers.

        The library reads headers via `s.headers = urls.HEADERS` (reference
        to a module-level dict) in every HTTP method. By replacing the
        dict's contents (not rebinding the name) we propagate our browser-
        like headers through all library calls without modifying the lib.

        Idempotent — safe to call before every fetch. With multiple config
        entries the global dict can race; we accept this since both
        entries' headers are realistic (anti-bot won't notice the swap).
        """
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
                        all_grades.append({
                            "subject": subject,
                            "grade": grade.grade,
                            "date": grade.date,
                            "category": grade.category,
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
                            desc = getattr(desc_grade, "desc", "")
                            all_grades.append({
                                "subject": subject,
                                "grade": desc_grade.grade,
                                "date": desc_grade.date,
                                "category": desc.split("\n")[0] if desc else "",
                                "teacher": getattr(desc_grade, "teacher", ""),
                                "semester": desc_grade.semester,
                                "type": "descriptive",
                            })

            return all_grades

        return await self._with_retry("grades", _work)

    async def async_get_messages(self, count: int = 10) -> list[dict[str, Any]] | None:
        """Get latest messages from Librus.

        Only subject and sender are returned — message body is NOT fetched
        to avoid marking messages as read in Librus.
        """
        def _work(client: Client) -> list[dict[str, Any]]:
            messages = get_received(client, 0)
            messages = messages[:count] if messages else []
            return [
                {
                    "author": msg.author,
                    "title": msg.title,
                    "date": msg.date,
                    "href": msg.href,
                    "unread": msg.unread,
                    "has_attachment": msg.has_attachment,
                }
                for msg in messages
            ]

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


async def async_setup_entry(hass: HomeAssistant, entry: LibrusConfigEntry) -> bool:
    """Set up Librus APIX from a config entry."""
    # Seed RNG by entry_id so each child gets a stable but distinct UA
    # across HA restarts (deterministic per entry, different per entry).
    rng = random.Random(entry.entry_id)
    client = LibrusApiClient(
        entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], rng=rng
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
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = LibrusRuntimeData(client=client, coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: LibrusConfigEntry) -> bool:
    """Unload a config entry. runtime_data is cleaned up by HA automatically."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)