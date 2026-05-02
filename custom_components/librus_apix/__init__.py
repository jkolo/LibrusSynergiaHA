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

PLATFORMS = ["sensor"]

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
        try:
            if not self._client or not self._token:
                if not await self.async_authenticate():
                    return None

            from librus_apix.student_information import get_student_information

            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, get_student_information, self._client)

        except Exception as ex:
            _LOGGER.error(
                "Failed to get student information: %s\n%s", ex, traceback.format_exc()
            )
            self._reset_auth()
            return None

    async def async_get_schedule_events(self, months_ahead: int = 2):
        """Pobierz zapowiedzi sprawdzianow/kartkowek z terminarza Librusa.

        Args:
            months_ahead: Ile miesiecy w przod pobrac (1 = tylko biezacy, 2 = + nastepny).

        Returns:
            Lista dictow z polami: title, subject, category, date (YYYY-MM-DD),
            hour, day, href, days_until. Filtrowane po slowach kluczowych
            wskazujacych na sprawdzian/kartkowke.
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

                    # Wyklucz dni wolne/zajecia odwolane
                    if any(ex in haystack for ex in exclude_keywords):
                        continue
                    if any(frag in href_lower for frag in exclude_href_fragments):
                        continue

                    if not any(kw in haystack for kw in exam_keywords):
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
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    
    client = LibrusApiClient(username, password)
    
    # Test authentication
    if not await client.async_authenticate():
        _LOGGER.error("Failed to authenticate")
        return False
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok