"""DataUpdateCoordinator for the Librus APIX integration."""

from __future__ import annotations

import logging
from collections import OrderedDict
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL

if TYPE_CHECKING:
    from . import LibrusApiClient

_LOGGER = logging.getLogger(__name__)

# Trim seen-id sets to this many entries (LRU). A long-running HA instance
# would otherwise let these grow unbounded over months/years.
_MAX_SEEN_ITEMS = 500

# Public event names (HA bus). v2.0.0 BREAKING: renamed from
# librus_apix_nowa_* to librus_apix_new_*.
EVENT_NEW_MESSAGE = f"{DOMAIN}_new_message"
EVENT_NEW_GRADE = f"{DOMAIN}_new_grade"
EVENT_NEW_EXAM = f"{DOMAIN}_new_exam"


def _is_recent(date_str: str) -> bool:
    """Return True if `date_str` parses to today or yesterday."""
    if not date_str:
        return False
    yesterday = date.today() - timedelta(days=1)
    for fmt in (
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            d = datetime.strptime(date_str.strip(), fmt).date()
            return d >= yesterday
        except ValueError:
            continue
    return False


def _add_lru(items: OrderedDict[Any, None], key: Any) -> None:
    """Add an item to an OrderedDict-as-LRU set, evicting oldest if over cap."""
    if key in items:
        items.move_to_end(key)
    else:
        items[key] = None
        if len(items) > _MAX_SEEN_ITEMS:
            items.popitem(last=False)


class LibrusDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator fetching student data from Librus."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: LibrusApiClient,
        config_entry: ConfigEntry | None = None,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self._seen_message_hrefs: OrderedDict[str, None] = OrderedDict()
        self._seen_grade_ids: OrderedDict[tuple, None] = OrderedDict()
        self._seen_exam_ids: OrderedDict[tuple, None] = OrderedDict()
        self._first_run: bool = True
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            always_update=False,
        )

    async def _async_setup(self) -> None:
        """One-time initialization: first login.

        Called by HA on the first refresh. If Librus is in maintenance,
        ConfigEntryNotReady triggers HA's exponential-backoff retry.
        """
        if not await self.client.async_authenticate():
            raise ConfigEntryNotReady(
                f"Failed to log in to Librus for {self.client.username} "
                "(possible Librus maintenance). HA will retry automatically."
            )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch fresh data from the Librus API."""
        from . import LibrusAuthError  # local import to avoid circular at module import

        current_semester = 1 if date.today().month >= 9 else 2

        try:
            student_info = await self.client.async_get_student_information()
            grades = await self.client.async_get_grades()
            messages = await self.client.async_get_messages(count=10)
            # Fetch the full schedule once: sensor.zapowiedzi uses only exam
            # events, calendar.terminarz uses everything.
            schedule_all = await self.client.async_get_schedule_events(
                months_ahead=2, only_exams=False
            )
            upcoming_exams = (
                [e for e in schedule_all if e.get("is_exam")]
                if schedule_all is not None
                else None
            )
            timetable = await self.client.async_get_timetable_events(weeks_ahead=4)

            if grades is None:
                # Fall back to cached grades if available; refresh other slots
                # if their fetches succeeded.
                prev = self.data or {}
                if not prev.get("grades"):
                    raise UpdateFailed("Failed to fetch grades and no cache available")
                _LOGGER.warning(
                    "Failed to fetch grades — using cached values"
                )
                return {
                    "student_info": student_info or prev.get("student_info"),
                    "grades": prev.get("grades", []),
                    "grades_by_subject": prev.get("grades_by_subject", {}),
                    "messages": (
                        self._annotate_messages(messages)
                        if messages is not None
                        else prev.get("messages", [])
                    ),
                    "upcoming_exams": (
                        upcoming_exams
                        if upcoming_exams is not None
                        else prev.get("upcoming_exams", [])
                    ),
                    "schedule": (
                        schedule_all
                        if schedule_all is not None
                        else prev.get("schedule", [])
                    ),
                    "timetable": (
                        timetable
                        if timetable is not None
                        else prev.get("timetable", [])
                    ),
                    "current_semester": current_semester,
                }

            # Group grades by subject and tag fresh ones.
            grades_by_subject: dict[str, list[dict]] = {}
            for grade in grades:
                subject = grade["subject"]
                if subject not in grades_by_subject:
                    grades_by_subject[subject] = []
                grades_by_subject[subject].append({
                    "grade": grade["grade"],
                    "date": grade["date"],
                    "category": grade["category"],
                    "teacher": grade["teacher"],
                    "semester": grade.get("semester"),
                    "is_recent": _is_recent(grade["date"]),
                })

            annotated_messages = self._annotate_messages(messages)
            exams_list = upcoming_exams if upcoming_exams is not None else []

            result = {
                "student_info": student_info,
                "grades": grades,
                "grades_by_subject": grades_by_subject,
                "messages": annotated_messages,
                "upcoming_exams": exams_list,
                "schedule": schedule_all if schedule_all is not None else [],
                "timetable": timetable if timetable is not None else [],
                "current_semester": current_semester,
            }

            # First refresh: only seed seen-sets, do not fire events to avoid
            # spurious notifications for everything that already exists.
            if self._first_run:
                self._first_run = False
                for msg in annotated_messages:
                    _add_lru(self._seen_message_hrefs, msg["href"])
                for grade in grades:
                    _add_lru(
                        self._seen_grade_ids,
                        (grade["subject"], grade["date"], grade["grade"]),
                    )
                for exam in exams_list:
                    _add_lru(
                        self._seen_exam_ids,
                        (exam["date"], exam["subject"], exam["title"]),
                    )
            else:
                self._fire_events(annotated_messages, grades, exams_list)

            return result

        except LibrusAuthError as err:
            # Password likely changed in Librus — start reauth flow.
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
            ) from err
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Librus API error: {err}") from err

    def _fire_events(
        self,
        messages: list[dict],
        grades: list[dict],
        upcoming_exams: list[dict] | None = None,
    ) -> None:
        """Emit HA bus events for newly observed messages/grades/exams.

        Event payload uses English keys (v2.0.0 BREAKING).
        """
        for msg in messages:
            href = msg.get("href", "")
            if href and href not in self._seen_message_hrefs:
                _add_lru(self._seen_message_hrefs, href)
                _LOGGER.debug("New message: %s", msg.get("title"))
                self.hass.bus.fire(
                    EVENT_NEW_MESSAGE,
                    {
                        "sender": msg.get("author", ""),
                        "title": msg.get("title", ""),
                        "date": msg.get("date", ""),
                        "has_attachment": msg.get("has_attachment", False),
                    },
                )

        for grade in grades:
            grade_id = (grade["subject"], grade["date"], grade["grade"])
            if grade_id not in self._seen_grade_ids:
                _add_lru(self._seen_grade_ids, grade_id)
                _LOGGER.debug("New grade: %s %s", grade["subject"], grade["grade"])
                self.hass.bus.fire(
                    EVENT_NEW_GRADE,
                    {
                        "subject": grade["subject"],
                        "grade": grade["grade"],
                        "date": grade["date"],
                        "category": grade["category"],
                        "teacher": grade["teacher"],
                    },
                )

        for exam in upcoming_exams or []:
            exam_id = (exam["date"], exam["subject"], exam["title"])
            if exam_id not in self._seen_exam_ids:
                _add_lru(self._seen_exam_ids, exam_id)
                _LOGGER.debug(
                    "New exam announcement: %s %s (%s)",
                    exam.get("subject"),
                    exam.get("title"),
                    exam.get("date"),
                )
                self.hass.bus.fire(
                    EVENT_NEW_EXAM,
                    {
                        "title": exam.get("title", ""),
                        "subject": exam.get("subject", ""),
                        "category": exam.get("category", ""),
                        "date": exam.get("date", ""),
                        "time": exam.get("hour", ""),
                        "days_until": exam.get("days_until", 0),
                    },
                )

    def _annotate_messages(self, messages: list[dict] | None) -> list[dict]:
        """Mark fresh messages and return the list (in-place tagged copy)."""
        result = []
        for msg in messages or []:
            msg["is_recent"] = _is_recent(msg.get("date", ""))
            result.append(msg)
        return result
