"""DataUpdateCoordinator for the Librus APIX integration."""

from __future__ import annotations

import asyncio
import logging
import random
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SCAN_INTERVAL
from .humanize import (
    is_school_day,
    jitter_pause_seconds,
    next_run_delay,
    random_endpoint_order,
)

if TYPE_CHECKING:
    from . import LibrusApiClient

_LOGGER = logging.getLogger(__name__)

# Trim seen-id sets to this many entries (LRU). A long-running HA instance
# would otherwise let these grow unbounded over months/years.
_MAX_SEEN_ITEMS = 500

# Defaults for the human-like scheduler. PR 6 makes them user-tunable
# via OptionsFlow; for now they're hard-coded constants.
_DEFAULT_BASE_MINUTES = 120.0
_DEFAULT_JITTER = 0.25
# Off-school multiplier — extends the base interval on weekends, holidays,
# breaks, and any other day Librus marks as a day off in the schedule.
# 6 × 120 min = 12 h; in practice a refresh per breakfast and per dinner.
_DEFAULT_OFF_SCHOOL_MULTIPLIER = 6.0
# Sentinel update_interval — DataUpdateCoordinator requires one but we drive
# refreshes ourselves via async_call_later. Picked far enough in the future
# that the built-in poll never fires before our scheduler does.
_SENTINEL_UPDATE_INTERVAL = timedelta(days=1)

# Number of consecutive refreshes returning None for *every* endpoint before
# we surface a repair issue. 5 ticks at 30 minute SCAN_INTERVAL ≈ 2.5 h —
# enough to filter transient outages without making the user wait too long.
_LIB_OUTDATED_THRESHOLD = 5

# Repair issue identifiers (Gold rule `repair-issues`). Stable across refreshes
# so HA can deduplicate and let the user dismiss them.
ISSUE_LIB_OUTDATED = "librus_lib_outdated"
ISSUE_AUTH_FAILED = "auth_failed"

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
        *,
        rng: random.Random | None = None,
    ) -> None:
        """Initialize the coordinator.

        Args:
            rng: Optional `random.Random` used for endpoint shuffling and
                inter-fetch pause durations. Tests inject `Random(42)`;
                production seeds by `entry_id` upstream so each child has
                a stable but distinct order pattern.
        """
        self.client = client
        self._seen_message_hrefs: OrderedDict[str, None] = OrderedDict()
        self._seen_grade_ids: OrderedDict[tuple, None] = OrderedDict()
        self._seen_exam_ids: OrderedDict[tuple, None] = OrderedDict()
        self._first_run: bool = True
        # Tracks consecutive ticks where every endpoint returned None — used
        # to escalate to a repair issue suggesting a librus-apix upgrade
        # (Librus likely changed HTML/CSS, breaking the parser).
        self._consecutive_total_failures: int = 0
        self._rng = rng or random.Random()
        # Custom scheduler state — see _schedule_next_refresh / async_shutdown.
        self._unsub_next: CALLBACK_TYPE | None = None
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=_SENTINEL_UPDATE_INTERVAL,
            always_update=False,
        )

    def _issue_id(self, kind: str) -> str:
        """Per-entry issue id so multiple entries don't collide."""
        entry_suffix = self.config_entry.entry_id if self.config_entry else "global"
        return f"{kind}_{entry_suffix}"

    def _create_issue_lib_outdated(self) -> None:
        """Surface a repair issue suggesting a librus-apix package upgrade."""
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self._issue_id(ISSUE_LIB_OUTDATED),
            is_fixable=False,
            is_persistent=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_LIB_OUTDATED,
            translation_placeholders={"username": self.client.username},
            learn_more_url="https://github.com/LukMaverick/LibrusSynergiaHA/issues",
        )

    def _create_issue_auth_failed(self) -> None:
        """Surface a repair issue mirroring the reauth flow for visibility."""
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self._issue_id(ISSUE_AUTH_FAILED),
            is_fixable=False,
            is_persistent=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key=ISSUE_AUTH_FAILED,
            translation_placeholders={"username": self.client.username},
        )

    def _clear_issue(self, kind: str) -> None:
        ir.async_delete_issue(self.hass, DOMAIN, self._issue_id(kind))

    @callback
    def schedule_next_refresh(self) -> None:
        """Schedule the next refresh through async_call_later.

        We bypass DataUpdateCoordinator's built-in periodic poll (sentinel
        update_interval=1 day) and drive refreshes ourselves so each tick
        can pick a randomised delay around `_DEFAULT_BASE_MINUTES`.
        """
        if self._unsub_next is not None:
            self._unsub_next()
            self._unsub_next = None

        now = dt_util.now()
        schedule = (self.data or {}).get("schedule") or []
        school_day_now = is_school_day(now.date(), schedule)
        delay = next_run_delay(
            self._rng,
            base_minutes=_DEFAULT_BASE_MINUTES,
            jitter=_DEFAULT_JITTER,
            quiet_hours=None,
            is_school_day_now=school_day_now,
            off_school_multiplier=_DEFAULT_OFF_SCHOOL_MULTIPLIER,
            now=now,
        )
        _LOGGER.debug(
            "Next Librus refresh scheduled in %.1f s (school_day=%s)",
            delay, school_day_now,
        )
        self._unsub_next = async_call_later(
            self.hass, delay, self._scheduled_refresh
        )

    async def _scheduled_refresh(self, _now) -> None:
        """Async callback fired by async_call_later — refresh + reschedule."""
        self._unsub_next = None
        await self.async_refresh()
        if not self.hass.is_stopping:
            self.schedule_next_refresh()

    async def async_shutdown(self) -> None:
        """Cancel any pending scheduled refresh on entry unload / HA stop."""
        if self._unsub_next is not None:
            self._unsub_next()
            self._unsub_next = None
        await super().async_shutdown()

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
            # Endpoint fetchers, addressed by name. Order is shuffled below
            # per-refresh so the traffic pattern doesn't betray a robot.
            fetchers: dict[str, Callable[[], Awaitable[Any]]] = {
                "student_info": self.client.async_get_student_information,
                "grades": self.client.async_get_grades,
                "messages": lambda: self.client.async_get_messages(count=10),
                # Fetch the full schedule once: sensor.zapowiedzi uses only
                # exam events, calendar.terminarz uses everything.
                "schedule": lambda: self.client.async_get_schedule_events(
                    months_ahead=2, only_exams=False
                ),
                "timetable": lambda: self.client.async_get_timetable_events(
                    weeks_ahead=4
                ),
            }
            order = random_endpoint_order(self._rng, list(fetchers))
            _LOGGER.debug("Refresh fetch order: %s", order)
            results: dict[str, Any] = {}
            for i, name in enumerate(order):
                results[name] = await fetchers[name]()
                if i < len(order) - 1:
                    pause = jitter_pause_seconds(self._rng)
                    _LOGGER.debug(
                        "Pause %.2fs before next fetch after %s", pause, name
                    )
                    await asyncio.sleep(pause)

            student_info = results["student_info"]
            grades = results["grades"]
            messages = results["messages"]
            schedule_all = results["schedule"]
            upcoming_exams = (
                [e for e in schedule_all if e.get("is_exam")]
                if schedule_all is not None
                else None
            )
            timetable = results["timetable"]

            # Detect "every endpoint failed" (None) — indicates a likely
            # parser breakage in librus-apix. Threshold guards against a
            # single transient outage triggering a repair notification.
            all_none = all(
                v is None
                for v in (student_info, grades, messages, schedule_all, timetable)
            )
            if all_none:
                self._consecutive_total_failures += 1
                if self._consecutive_total_failures >= _LIB_OUTDATED_THRESHOLD:
                    self._create_issue_lib_outdated()
            else:
                if self._consecutive_total_failures > 0:
                    self._clear_issue(ISSUE_LIB_OUTDATED)
                self._consecutive_total_failures = 0

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

            # Successful refresh: clear the auth repair issue if present.
            self._clear_issue(ISSUE_AUTH_FAILED)
            return result

        except LibrusAuthError as err:
            # Password likely changed in Librus — start reauth flow and
            # surface a repair issue so the user has a visible nudge in
            # Settings → Repairs even if they miss the reauth notification.
            self._create_issue_auth_failed()
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
