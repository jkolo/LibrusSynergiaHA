"""The Librus APIX integration."""

import asyncio
import logging
import traceback
from datetime import date
from typing import Dict, Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv

from librus_apix.client import Client, new_client
from librus_apix.exceptions import TokenError

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


def _current_semester() -> int:
    """Zwroc numer biezacego semestru (1 lub 2) wg polskiego roku szkolnego.

    Semestr 1: wrzesien (9) - styczen (1)
    Semestr 2: luty (2) - czerwiec (6)
    Lipiec-sierpien to wakacje - zwracamy 2 (ostatni semestr roku).
    """
    m = date.today().month
    return 1 if m >= 9 else 2

PLATFORMS = ["sensor", "calendar"]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


class LibrusApiClient:
    """Class to interface with the Librus API."""

    def __init__(self, username: str, password: str):
        """Initialize the client."""
        self.username = username
        self.password = password
        self._client: Client = None
        self._token = None
        self._auth_lock = asyncio.Lock()

    def _reset_auth(self) -> None:
        """Reset authentication state to force re-authentication on next call."""
        self._client = None
        self._token = None

    async def async_authenticate(self):
        """Authenticate with Librus API."""
        async with self._auth_lock:
            try:
                loop = asyncio.get_running_loop()
                self._client = await loop.run_in_executor(None, new_client)
                self._token = await loop.run_in_executor(
                    None, self._client.get_token, self.username, self.password
                )
                _LOGGER.debug("Authentication successful for %s", self.username)
                return True
            except Exception as ex:
                _LOGGER.error("Authentication failed: %s\n%s", ex, traceback.format_exc())
                self._reset_auth()
                return False

    async def async_get_grades(self):
        """Get grades from Librus."""
        for attempt in range(2):
            try:
                if not self._client or not self._token:
                    if not await self.async_authenticate():
                        return None
                client = self._client

                from librus_apix.grades import get_grades

                loop = asyncio.get_running_loop()
                numeric_grades, average_grades, descriptive_grades = await loop.run_in_executor(
                    None, get_grades, client, "all"
                )

                current_sem = _current_semester()
                _LOGGER.debug("Filtrowanie ocen dla semestru %d", current_sem)

                # Process all grades
                all_grades = []

                # Process numeric grades (only current semester)
                for subject_grades in numeric_grades:
                    for subject, grades_list in subject_grades.items():
                        for grade in grades_list:
                            if grade.semester != current_sem:
                                continue
                            all_grades.append({
                                'subject': subject,
                                'grade': grade.grade,
                                'date': grade.date,
                                'category': grade.category,
                                'teacher': getattr(grade, 'teacher', ''),
                                'semester': grade.semester,
                                'type': 'numeric'
                            })

                # Process descriptive grades (only current semester, many are actually numeric)
                for subject_grades in descriptive_grades:
                    for subject, grades_list in subject_grades.items():
                        for desc_grade in grades_list:
                            if desc_grade.semester != current_sem:
                                continue
                            grade_val = desc_grade.grade.strip()
                            if grade_val and (grade_val.replace('+', '').replace('-', '').isdigit() or
                                            grade_val in ['1', '2', '3', '4', '5', '6', '1+', '1-', '2+', '2-',
                                                         '3+', '3-', '4+', '4-', '5+', '5-', '6+', '6-']):
                                all_grades.append({
                                    'subject': subject,
                                    'grade': desc_grade.grade,
                                    'date': desc_grade.date,
                                    'category': getattr(desc_grade, 'desc', '').split('\n')[0] if hasattr(desc_grade, 'desc') else '',
                                    'teacher': getattr(desc_grade, 'teacher', ''),
                                    'semester': desc_grade.semester,
                                    'type': 'descriptive'
                                })

                return all_grades

            except TokenError as ex:
                _LOGGER.warning(
                    "Token expired fetching grades (attempt %d/2), re-authenticating...",
                    attempt + 1,
                )
                self._reset_auth()
                if attempt == 1:
                    _LOGGER.error("Failed to get grades after re-authentication.")
                    return None
            except Exception as ex:
                _LOGGER.error(
                    "Failed to get grades (attempt %d/2): %s\n%s",
                    attempt + 1, ex, traceback.format_exc(),
                )
                self._reset_auth()
                if attempt == 1:
                    return None

    async def async_get_messages(self, count: int = 10):
        """Get latest messages from Librus (subject and sender only, no content fetch to avoid marking as read)."""
        for attempt in range(2):
            try:
                if not self._client or not self._token:
                    if not await self.async_authenticate():
                        return None
                client = self._client

                from librus_apix.messages import get_received

                loop = asyncio.get_running_loop()
                messages = await loop.run_in_executor(None, get_received, client, 0)
                messages = messages[:count] if messages else []

                result = [
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

                return result

            except TokenError as ex:
                _LOGGER.warning(
                    "Token expired fetching messages (attempt %d/2), re-authenticating...",
                    attempt + 1,
                )
                self._reset_auth()
                if attempt == 1:
                    _LOGGER.error("Failed to get messages after re-authentication.")
                    return None
            except Exception as ex:
                _LOGGER.error(
                    "Failed to get messages (attempt %d/2): %s\n%s",
                    attempt + 1, ex, traceback.format_exc(),
                )
                self._reset_auth()
                if attempt == 1:
                    return None

    async def async_get_student_information(self):
        """Get student information from Librus."""
        from librus_apix.student_information import get_student_information

        for attempt in range(2):
            try:
                if not self._client or not self._token:
                    if not await self.async_authenticate():
                        return None

                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(
                    None, get_student_information, self._client
                )

            except TokenError:
                _LOGGER.warning(
                    "Token expired fetching student info (attempt %d/2), re-authenticating...",
                    attempt + 1,
                )
                self._reset_auth()
                if attempt == 1:
                    _LOGGER.error("Failed to get student info after re-authentication.")
                    return None
            except Exception as ex:
                _LOGGER.error(
                    "Failed to get student information (attempt %d/2): %s\n%s",
                    attempt + 1, ex, traceback.format_exc(),
                )
                self._reset_auth()
                if attempt == 1:
                    return None

    async def async_get_schedule_events(
        self, months_ahead: int = 2, only_exams: bool = True
    ):
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
        from datetime import date as _date, timedelta

        for attempt in range(2):
            try:
                if not self._client or not self._token:
                    if not await self.async_authenticate():
                        return None
                client = self._client

                from librus_apix.schedule import get_schedule

                loop = asyncio.get_running_loop()
                today = _date.today()

                # Pobierz schedule dla biezacego + nastepnych miesiecy
                merged: Dict[int, list] = {}
                month_year_pairs = []
                for offset in range(months_ahead):
                    target = today.replace(day=1) + timedelta(days=32 * offset)
                    target = target.replace(day=1)
                    month_year_pairs.append((target.month, target.year))

                events_raw = []
                for month, year in month_year_pairs:
                    try:
                        result = await loop.run_in_executor(
                            None, get_schedule, client, str(month), str(year), False
                        )
                        # result: DefaultDict[int, List[Event]] — klucz = dzien miesiaca
                        for day_num, day_events in result.items():
                            for event in day_events:
                                events_raw.append((month, year, day_num, event))
                    except Exception as ex:
                        _LOGGER.debug(
                            "Schedule fetch failed for %d/%d: %s", month, year, ex
                        )
                        continue

                # Filtruj eventy ktore sa sprawdzianami/kartkowkami
                # Slowa kluczowe (positive) - musi byc co najmniej jedno
                exam_keywords = (
                    "sprawdzian",
                    "kartkow",  # kartkowka/kartkowki
                    "praca klasowa",
                    "praca kontrolna",
                    "test ",
                    "wypracowanie klasowe",
                )
                # Negatywne slowa - jesli wystapia, event jest wykluczony
                # (Librus pokazuje "Egzamin osmoklasisty - dzien wolny" jako event,
                #  ale to dzien wolny od zajec, nie sprawdzian dla naszych dzieci)
                exclude_keywords = (
                    "dzien wolny",
                    "dzień wolny",
                    "wolne od zaj",
                    "wolny od zaj",
                )
                # href zawierajacy "wolne" wskazuje na dzien wolny w terminarzu Librusa
                exclude_href_fragments = ("szczegoly_wolne", "wolne",)

                upcoming = []
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
                    # Klasyfikacja machine-readable do tagowania w calendar:
                    # sprawdzian / kartkowka / praca_klasowa / praca_kontrolna /
                    # wypracowanie_klasowe / test / dzien_wolny / inne
                    if is_day_off:
                        event_type = "dzien_wolny"
                    elif "sprawdzian" in haystack:
                        event_type = "sprawdzian"
                    elif "kartkow" in haystack:
                        event_type = "kartkowka"
                    elif "praca klasowa" in haystack:
                        event_type = "praca_klasowa"
                    elif "praca kontrolna" in haystack:
                        event_type = "praca_kontrolna"
                    elif "wypracowanie klasowe" in haystack:
                        event_type = "wypracowanie_klasowe"
                    elif "test " in haystack:
                        event_type = "test"
                    else:
                        event_type = "inne"
                    is_exam = event_type in (
                        "sprawdzian", "kartkowka", "praca_klasowa",
                        "praca_kontrolna", "wypracowanie_klasowe", "test",
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

                # Sortuj po dacie
                upcoming.sort(key=lambda e: (e["date"], e.get("hour") or ""))
                return upcoming

            except TokenError as ex:
                _LOGGER.warning(
                    "Token expired fetching schedule (attempt %d/2), re-authenticating...",
                    attempt + 1,
                )
                self._reset_auth()
                if attempt == 1:
                    _LOGGER.error("Failed to get schedule after re-authentication.")
                    return None
            except Exception as ex:
                _LOGGER.error(
                    "Failed to get schedule (attempt %d/2): %s\n%s",
                    attempt + 1, ex, traceback.format_exc(),
                )
                self._reset_auth()
                if attempt == 1:
                    return None

    async def async_get_timetable_events(self, weeks_ahead: int = 2):
        """Pobierz plan lekcji z Librusa (timetable).

        Args:
            weeks_ahead: Ile tygodni w przod pobrac (1 = tylko biezacy).

        Returns:
            Lista dictow z polami: subject, teacher, classroom, date (YYYY-MM-DD),
            time_from (HH:MM), time_to (HH:MM), weekday, lesson_number, info.
            None jesli blad.
        """
        from datetime import date as _date, datetime as _dt, timedelta

        for attempt in range(2):
            try:
                if not self._client or not self._token:
                    if not await self.async_authenticate():
                        return None
                client = self._client

                from librus_apix.timetable import get_timetable

                loop = asyncio.get_running_loop()
                today = _date.today()
                # Najblizszy poniedzialek (lub dzisiaj jesli to poniedzialek)
                monday = today - timedelta(days=today.weekday())

                lessons = []
                for week_offset in range(weeks_ahead):
                    target_monday = monday + timedelta(weeks=week_offset)
                    monday_dt = _dt.combine(target_monday, _dt.min.time())
                    try:
                        week = await loop.run_in_executor(
                            None, get_timetable, client, monday_dt
                        )
                    except Exception as ex:
                        _LOGGER.debug(
                            "Timetable fetch failed for %s: %s", target_monday, ex
                        )
                        continue
                    # week to List[List[Period]] - lista dni, kazdy dzien lista lekcji
                    for day_periods in week:
                        for period in day_periods:
                            try:
                                # Filtruj okienka (subject pusty)
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

                # Sortuj po dacie + godzinie
                lessons.sort(key=lambda l: (l["date"], l.get("time_from") or ""))
                return lessons

            except TokenError as ex:
                _LOGGER.warning(
                    "Token expired fetching timetable (attempt %d/2), re-authenticating...",
                    attempt + 1,
                )
                self._reset_auth()
                if attempt == 1:
                    _LOGGER.error("Failed to get timetable after re-authentication.")
                    return None
            except Exception as ex:
                _LOGGER.error(
                    "Failed to get timetable (attempt %d/2): %s\n%s",
                    attempt + 1, ex, traceback.format_exc(),
                )
                self._reset_auth()
                if attempt == 1:
                    return None


async def async_setup(hass: HomeAssistant, config: Dict[str, Any]) -> bool:
    """Set up the Librus APIX component."""
    hass.data.setdefault(DOMAIN, {})
    
    if DOMAIN in config:
        username = config[DOMAIN][CONF_USERNAME]
        password = config[DOMAIN][CONF_PASSWORD]
        
        client = LibrusApiClient(username, password)
        hass.data[DOMAIN]["client"] = client
        
        # Test authentication
        if not await client.async_authenticate():
            _LOGGER.error("Failed to authenticate")
            return False

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Librus APIX from a config entry."""
    from homeassistant.exceptions import ConfigEntryNotReady

    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    client = LibrusApiClient(username, password)

    # Test authentication; gdy Librus jest w maintenance lub niedostepny, rzuc
    # ConfigEntryNotReady - HA bedzie automatycznie retryowal setup z exponential
    # backoff zamiast porazki na stale (config_entry "setup_failed" wymaga manualnego
    # reload). Librus ma okresowe przerwy techniczne raz dziennie, wiec retry jest
    # kluczowy dla niezawodnosci.
    if not await client.async_authenticate():
        raise ConfigEntryNotReady(
            f"Nie udalo sie zalogowac do Librus dla {username} (mozliwy maintenance Librus). "
            "HA wykona retry automatycznie."
        )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client

    # Stworz coordinator wczesniej, zeby sensor i calendar uzyly tego samego.
    from .sensor import LibrusDataUpdateCoordinator
    coordinator = LibrusDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][f"{entry.entry_id}_coordinator"] = coordinator

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        hass.data[DOMAIN].pop(f"{entry.entry_id}_coordinator", None)
    
    return unload_ok