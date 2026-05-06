"""DataUpdateCoordinator for the Librus APIX integration."""

from __future__ import annotations

import asyncio
import logging
import random
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING, Any

import hashlib

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    DEFAULT_BASE_MINUTES,
    DEFAULT_HUMANIZE,
    DEFAULT_JITTER,
    DEFAULT_MESSAGE_NOTIFY,
    DEFAULT_OFF_SCHOOL_MULTIPLIER,
    DEFAULT_QUIET_END,
    DEFAULT_QUIET_HOURS_ENABLED,
    DEFAULT_QUIET_START,
    DOMAIN,
    EVENT_NOWA_WIADOMOSC,
    OPT_BASE_MINUTES,
    OPT_HUMANIZE,
    OPT_JITTER,
    OPT_MESSAGE_NOTIFY,
    OPT_OFF_SCHOOL_MULTIPLIER,
    OPT_QUIET_END,
    OPT_QUIET_HOURS_ENABLED,
    OPT_QUIET_START,
    SCAN_INTERVAL,
)
from .humanize import (
    is_school_day,
    jitter_pause_seconds,
    next_run_delay,
    random_endpoint_order,
)

if TYPE_CHECKING:
    from . import LibrusApiClient
    from ._data_store import LibrusDataStore
    from ._message_store import ReadMessagesStore

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

# Event entity keys (v3.0). Replace the legacy `hass.bus.fire` mechanism —
# the coordinator now buffers payloads and event entities consume them via
# `consume_pending_event(key)` in their listener.
EVENT_KEY_NEW_MESSAGE = "new_message"
EVENT_KEY_NEW_GRADE = "new_grade"
EVENT_KEY_NEW_EXAM = "new_exam"
EVENT_KEY_NEW_ANNOUNCEMENT = "new_announcement"
EVENT_KEY_NEW_ABSENCE = "new_absence"
EVENT_KEYS = (
    EVENT_KEY_NEW_MESSAGE,
    EVENT_KEY_NEW_GRADE,
    EVENT_KEY_NEW_EXAM,
    EVENT_KEY_NEW_ANNOUNCEMENT,
    EVENT_KEY_NEW_ABSENCE,
)


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


def _attendance_frequency(
    attendance: list[dict] | None, current_semester: int
) -> dict[str, float]:
    """Compute (sem1, sem2, total, current) attendance percentages.

    Frequency = present_count / (present_count + counted_absences) × 100.
    Counted absences: nieobecności (`nb`, `u`) i spóźnienia (`sp`). Wycieczki,
    konkursy, szkolenia, zwolnienia liczymy jako obecność (dziecko jest pod
    opieką szkoły).
    """
    if not attendance:
        return {"semester_1": 0.0, "semester_2": 0.0, "total": 0.0, "current": 0.0}

    counts = {1: {"present": 0, "missed": 0}, 2: {"present": 0, "missed": 0}}
    for entry in attendance:
        sem = entry.get("semester")
        if sem not in counts:
            continue
        if entry.get("is_present") or entry.get("excursion"):
            counts[sem]["present"] += 1
        elif entry.get("is_absence") or entry.get("is_late"):
            counts[sem]["missed"] += 1

    def _pct(c: dict[str, int]) -> float:
        total = c["present"] + c["missed"]
        return round(c["present"] / total * 100.0, 2) if total else 0.0

    sem1 = _pct(counts[1])
    sem2 = _pct(counts[2])
    total_present = counts[1]["present"] + counts[2]["present"]
    total_missed = counts[1]["missed"] + counts[2]["missed"]
    total = (
        round(total_present / (total_present + total_missed) * 100.0, 2)
        if (total_present + total_missed)
        else 0.0
    )
    current = sem1 if current_semester == 1 else sem2
    return {
        "semester_1": sem1,
        "semester_2": sem2,
        "total": total,
        "current": current,
    }


def _attendance_by_subject(
    attendance: list[dict] | None,
) -> dict[str, dict[str, int | float]]:
    """For each subject return present/missed counts and frequency %."""
    if not attendance:
        return {}
    by_subject: dict[str, dict[str, int]] = {}
    for entry in attendance:
        subject = entry.get("subject") or "(unknown)"
        bucket = by_subject.setdefault(subject, {"present": 0, "missed": 0})
        if entry.get("is_present") or entry.get("excursion"):
            bucket["present"] += 1
        elif entry.get("is_absence") or entry.get("is_late"):
            bucket["missed"] += 1
    out: dict[str, dict[str, int | float]] = {}
    for subject, c in by_subject.items():
        total = c["present"] + c["missed"]
        out[subject] = {
            "present": c["present"],
            "missed": c["missed"],
            "frequency": round(c["present"] / total * 100.0, 2) if total else 0.0,
        }
    return out


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
        self.data_store: LibrusDataStore | None = None
        self.read_messages_store: ReadMessagesStore | None = None
        self._step_timestamps: dict[str, datetime | None] = {k: None for k in (
            "student_info", "grades", "messages", "schedule",
            "timetable", "attendance", "announcements",
        )}
        self._last_full_refresh: datetime | None = None
        self._seen_message_hrefs: OrderedDict[str, None] = OrderedDict()
        self._seen_grade_ids: OrderedDict[tuple, None] = OrderedDict()
        self._seen_exam_ids: OrderedDict[tuple, None] = OrderedDict()
        self._seen_announcement_keys: OrderedDict[tuple, None] = OrderedDict()
        self._seen_absence_keys: OrderedDict[tuple, None] = OrderedDict()
        self._first_run: bool = True
        # Tracks consecutive ticks where every endpoint returned None — used
        # to escalate to a repair issue suggesting a librus-apix upgrade
        # (Librus likely changed HTML/CSS, breaking the parser).
        self._consecutive_total_failures: int = 0
        # Pending events buffer — coordinator stuffs latest unconsumed payload
        # per event key here; event entities pop it in their listener and
        # call `_trigger_event`. Replaces v2.x `hass.bus.fire` mechanism.
        self._pending_events: dict[str, dict[str, Any]] = {}
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

    def _seed_seen_sets_from_data(self, data: dict[str, Any]) -> None:
        """Seed seen-sets from coordinator data bez emitowania bus events.

        Wywoływana przy _first_run (przed bus events) i przy cache-first startup
        z __init__.py, by kolejny refresh poprawnie wykrył tylko nowe elementy.
        """
        for msg in data.get("messages", []) or []:
            href = msg.get("href", "")
            _add_lru(self._seen_message_hrefs, href)
        for grade in data.get("grades", []) or []:
            _add_lru(
                self._seen_grade_ids,
                (grade["subject"], grade["date"], grade["grade"]),
            )
        for exam in data.get("upcoming_exams", []) or []:
            _add_lru(
                self._seen_exam_ids,
                (exam["date"], exam["subject"], exam["title"]),
            )
        for ann in data.get("announcements", []) or []:
            _add_lru(
                self._seen_announcement_keys,
                (ann.get("date", ""), ann.get("title", "")),
            )
        for att in data.get("attendance", []) or []:
            if att.get("is_absence") or att.get("is_late"):
                _add_lru(
                    self._seen_absence_keys,
                    (
                        att.get("date", ""),
                        att.get("subject", ""),
                        att.get("period"),
                        att.get("symbol", ""),
                    ),
                )

    # ---------- Options helpers (PR 6) ----------

    def _opts(self) -> dict[str, Any]:
        """Return current entry.options dict (empty when no entry attached)."""
        if self.config_entry is None:
            return {}
        return dict(self.config_entry.options)

    def _opt_humanize(self) -> bool:
        return self._opts().get(OPT_HUMANIZE, DEFAULT_HUMANIZE)

    def _opt_quiet_hours(self) -> tuple[time, time] | None:
        opts = self._opts()
        if not opts.get(OPT_QUIET_HOURS_ENABLED, DEFAULT_QUIET_HOURS_ENABLED):
            return None
        try:
            start = time.fromisoformat(
                opts.get(OPT_QUIET_START, DEFAULT_QUIET_START)
            )
            end = time.fromisoformat(opts.get(OPT_QUIET_END, DEFAULT_QUIET_END))
        except ValueError:
            _LOGGER.warning(
                "Invalid quiet_hours config — falling back to defaults"
            )
            start = time.fromisoformat(DEFAULT_QUIET_START)
            end = time.fromisoformat(DEFAULT_QUIET_END)
        return (start, end)

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
        opts = self._opts()
        humanize = self._opt_humanize()
        if humanize:
            schedule = (self.data or {}).get("schedule") or []
            school_day_now = is_school_day(now.date(), schedule)
            quiet = self._opt_quiet_hours()
            multiplier = opts.get(
                OPT_OFF_SCHOOL_MULTIPLIER, DEFAULT_OFF_SCHOOL_MULTIPLIER
            )
            jitter = opts.get(OPT_JITTER, DEFAULT_JITTER)
        else:
            # Legacy mode — fixed cadence, no jitter, no quiet hours, no
            # off-school slowdown. Useful for debugging or when the user
            # explicitly wants predictable behaviour.
            school_day_now = True
            quiet = None
            multiplier = 1.0
            jitter = 0.0

        base = opts.get(OPT_BASE_MINUTES, DEFAULT_BASE_MINUTES)
        delay = next_run_delay(
            self._rng,
            base_minutes=float(base),
            jitter=jitter,
            quiet_hours=quiet,
            is_school_day_now=school_day_now,
            off_school_multiplier=multiplier,
            now=now,
        )
        _LOGGER.debug(
            "Next Librus refresh in %.1f s (humanize=%s, school_day=%s)",
            delay, humanize, school_day_now,
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
                "attendance": self.client.async_get_attendance,
                "announcements": self.client.async_get_announcements,
            }
            humanize = self._opt_humanize()
            order = (
                random_endpoint_order(self._rng, list(fetchers))
                if humanize
                else list(fetchers)
            )
            _LOGGER.debug(
                "Refresh fetch order (humanize=%s): %s", humanize, order
            )
            results: dict[str, Any] = {}
            for i, name in enumerate(order):
                results[name] = await fetchers[name]()
                if results[name] is not None:
                    self._step_timestamps[name] = dt_util.utcnow()
                # Skip jitter on first_run: HA cancels setup after ~60s,
                # and 7 fetchers × up to 15s pause would exceed that limit.
                if humanize and i < len(order) - 1 and not self._first_run:
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
            attendance = results["attendance"]
            announcements = results["announcements"]

            # Detect "every endpoint failed" (None) — indicates a likely
            # parser breakage in librus-apix. Threshold guards against a
            # single transient outage triggering a repair notification.
            all_none = all(
                v is None
                for v in (
                    student_info, grades, messages, schedule_all, timetable,
                    attendance, announcements,
                )
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
                    "attendance": (
                        attendance
                        if attendance is not None
                        else prev.get("attendance", [])
                    ),
                    "attendance_frequency": _attendance_frequency(
                        attendance
                        if attendance is not None
                        else prev.get("attendance", []),
                        current_semester,
                    ),
                    "attendance_by_subject": _attendance_by_subject(
                        attendance
                        if attendance is not None
                        else prev.get("attendance", [])
                    ),
                    "announcements": (
                        announcements
                        if announcements is not None
                        else prev.get("announcements", [])
                    ),
                    "current_semester": current_semester,
                }

            # Group grades by subject and tag fresh ones. Wszystkie nowe
            # pola (value/weight/description/title/counts) propagowane są
            # do per-subject sensorow (PR 3) i kalendarza ocen (PR 5).
            grades_by_subject: dict[str, list[dict]] = {}
            for grade in grades:
                subject = grade["subject"]
                if subject not in grades_by_subject:
                    grades_by_subject[subject] = []
                grades_by_subject[subject].append({
                    "grade": grade["grade"],
                    "value": grade.get("value"),
                    "counts": grade.get("counts"),
                    "weight": grade.get("weight"),
                    "date": grade["date"],
                    "category": grade["category"],
                    "description": grade.get("description", ""),
                    "title": grade.get("title", ""),
                    "teacher": grade["teacher"],
                    "semester": grade.get("semester"),
                    "type": grade.get("type", "numeric"),
                    "is_recent": _is_recent(grade["date"]),
                })

            annotated_messages = self._annotate_messages(messages)
            exams_list = upcoming_exams if upcoming_exams is not None else []

            attendance_list = attendance if attendance is not None else []
            announcements_list = announcements if announcements is not None else []

            result = {
                "student_info": student_info,
                "grades": grades,
                "grades_by_subject": grades_by_subject,
                "messages": annotated_messages,
                "upcoming_exams": exams_list,
                "schedule": schedule_all if schedule_all is not None else [],
                "timetable": timetable if timetable is not None else [],
                "attendance": attendance_list,
                "attendance_frequency": _attendance_frequency(
                    attendance_list, current_semester
                ),
                "attendance_by_subject": _attendance_by_subject(attendance_list),
                "announcements": announcements_list,
                "current_semester": current_semester,
            }

            # First refresh: seed seen-sets and fire bus events with initial=True
            # (IMAP-style — lets automations distinguish startup flood from
            # genuinely new messages). Do NOT enqueue to _pending_events.
            if self._first_run:
                self._first_run = False
                self._seed_seen_sets_from_data(result)
                for msg in annotated_messages:
                    if href := msg.get("href", ""):
                        self.hass.bus.async_fire(EVENT_NOWA_WIADOMOSC, {
                            "sender": msg.get("author", ""),
                            "title": msg.get("title", ""),
                            "date": msg.get("date", ""),
                            "href": href,
                            "has_attachment": msg.get("has_attachment", False),
                            "initial": True,
                        })
            else:
                self._enqueue_events(
                    annotated_messages, grades, exams_list,
                    announcements_list, attendance_list,
                )

            if self.read_messages_store is not None:
                active_hrefs = {m.get("href") for m in annotated_messages if m.get("href")}
                self.hass.async_create_task(
                    self.read_messages_store.async_purge_stale(active_hrefs)
                )

            # Successful refresh: clear the auth repair issue if present.
            self._clear_issue(ISSUE_AUTH_FAILED)
            self._last_full_refresh = dt_util.utcnow()
            if self.data_store is not None:
                self.hass.async_create_task(
                    self.data_store.async_save(result, self._last_full_refresh)
                )
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

    def consume_pending_event(self, key: str) -> dict[str, Any] | None:
        """Pop and return the latest payload for `key` (or None).

        Called by `LibrusEvent` entities in their listener — replaces the
        v2.x `hass.bus.fire` mechanism. Single-slot per key: if multiple
        events arrived in one refresh, only the most recent is delivered
        (event entity already shows full state.last_event with timestamp).
        """
        return self._pending_events.pop(key, None)

    def _enqueue_events(
        self,
        messages: list[dict],
        grades: list[dict],
        upcoming_exams: list[dict],
        announcements: list[dict],
        attendance: list[dict],
    ) -> None:
        """Buffer payloads for newly observed items so event entities emit them.

        Mark-and-skip via per-domain LRU `_seen_*` sets — same logic as
        legacy `_fire_events`, but writes to `_pending_events` instead of
        `hass.bus`. Event entities pop the payload in their listener.
        """
        for msg in messages:
            href = msg.get("href", "")
            if href and href not in self._seen_message_hrefs:
                _add_lru(self._seen_message_hrefs, href)
                _LOGGER.debug("New message: %s", msg.get("title"))
                payload: dict[str, Any] = {
                    "sender": msg.get("author", ""),
                    "title": msg.get("title", ""),
                    "date": msg.get("date", ""),
                    "href": href,
                    "has_attachment": msg.get("has_attachment", False),
                    "initial": False,
                }
                self._pending_events[EVENT_KEY_NEW_MESSAGE] = payload
                self.hass.bus.async_fire(EVENT_NOWA_WIADOMOSC, payload)
                if (
                    self.config_entry is not None
                    and self.config_entry.options.get(
                        OPT_MESSAGE_NOTIFY, DEFAULT_MESSAGE_NOTIFY
                    )
                ):
                    href_hash = hashlib.sha1(href.encode()).hexdigest()[:10]
                    notification_id = (
                        f"librus_apix_msg_{self.config_entry.entry_id}_{href_hash}"
                    )
                    persistent_notification.async_create(
                        self.hass,
                        message=f"**{msg.get('author', '')}**: {msg.get('title', '')}",
                        title="Librus: nowa wiadomość",
                        notification_id=notification_id,
                    )

        for grade in grades:
            grade_id = (grade["subject"], grade["date"], grade["grade"])
            if grade_id not in self._seen_grade_ids:
                _add_lru(self._seen_grade_ids, grade_id)
                _LOGGER.debug("New grade: %s %s", grade["subject"], grade["grade"])
                self._pending_events[EVENT_KEY_NEW_GRADE] = {
                    "subject": grade["subject"],
                    "grade": grade["grade"],
                    "value": grade.get("value"),
                    "weight": grade.get("weight"),
                    "date": grade["date"],
                    "category": grade["category"],
                    "description": grade.get("description", ""),
                    "teacher": grade["teacher"],
                }

        for exam in upcoming_exams:
            exam_id = (exam["date"], exam["subject"], exam["title"])
            if exam_id not in self._seen_exam_ids:
                _add_lru(self._seen_exam_ids, exam_id)
                _LOGGER.debug(
                    "New exam announcement: %s %s (%s)",
                    exam.get("subject"), exam.get("title"), exam.get("date"),
                )
                self._pending_events[EVENT_KEY_NEW_EXAM] = {
                    "title": exam.get("title", ""),
                    "subject": exam.get("subject", ""),
                    "category": exam.get("category", ""),
                    "date": exam.get("date", ""),
                    "time": exam.get("hour", ""),
                    "days_until": exam.get("days_until", 0),
                }

        for ann in announcements:
            ann_key = (ann.get("date", ""), ann.get("title", ""))
            if ann_key not in self._seen_announcement_keys:
                _add_lru(self._seen_announcement_keys, ann_key)
                _LOGGER.debug("New announcement: %s", ann.get("title"))
                self._pending_events[EVENT_KEY_NEW_ANNOUNCEMENT] = {
                    "title": ann.get("title", ""),
                    "author": ann.get("author", ""),
                    "date": ann.get("date", ""),
                    "description": ann.get("description", ""),
                }

        for att in attendance:
            if not (att.get("is_absence") or att.get("is_late")):
                continue
            abs_key = (
                att.get("date", ""),
                att.get("subject", ""),
                att.get("period"),
                att.get("symbol", ""),
            )
            if abs_key not in self._seen_absence_keys:
                _add_lru(self._seen_absence_keys, abs_key)
                _LOGGER.debug(
                    "New absence: %s %s (%s)",
                    att.get("date"), att.get("subject"), att.get("symbol"),
                )
                self._pending_events[EVENT_KEY_NEW_ABSENCE] = {
                    "date": att.get("date", ""),
                    "subject": att.get("subject", ""),
                    "type": att.get("type", ""),
                    "symbol": att.get("symbol", ""),
                    "period": att.get("period"),
                    "teacher": att.get("teacher", ""),
                    "is_unjustified": bool(att.get("is_unjustified", False)),
                    "is_late": bool(att.get("is_late", False)),
                }

    def _annotate_messages(self, messages: list[dict] | None) -> list[dict]:
        """Mark fresh messages and return the list (in-place tagged copy)."""
        result = []
        for msg in messages or []:
            href = msg.get("href", "")
            msg["is_recent"] = _is_recent(msg.get("date", ""))
            msg["notification_dismissed"] = (
                self.read_messages_store is not None
                and bool(href)
                and self.read_messages_store.is_read(href)
            )
            result.append(msg)
        return result
