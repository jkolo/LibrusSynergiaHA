"""Calendar platform dla Librus Synergia HA.

Cztery kalendarze per config_entry (per dziecko):
- calendar.librus_<dziecko>_terminarz - cały terminarz Librusa (sprawdziany, dni
  wolne, inne) z tagami [SPRAWDZIAN]/[KARTKOWKA]/[PRACA-KLASOWA]/[WOLNE]/[INFO]
  na poczatku summary do filtrowania.
- calendar.librus_<dziecko>_plan_lekcji - plan lekcji (timetable).
- calendar.librus_<dziecko>_obecnosci - nieobecnosci/spoznienia/zwolnienia
  z tagami [NIEOBECNOSC]/[SPOZNIENIE]/[USPRAWIEDLIWIONA]/[ZWOLNIENIE]/...
- calendar.librus_<dziecko>_oceny - oceny jako eventy w dniu wystawienia
  z tagami [OCENA 5]/[OCENA 4+]/[OCENA OPISOWA].
"""
from __future__ import annotations

import logging
from datetime import date as _date, datetime, time, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import LibrusBaseEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0  # All entities read from coordinator, no per-entity I/O.


# Map: internal event_type code (English) → (display tag, emoji).
# Tags shown in the calendar summary stay Polish for user-facing recognition;
# they're the visible identifier in dashboards and automations.
EVENT_TYPE_TAGS = {
    "exam": ("SPRAWDZIAN", "📝"),
    "quiz": ("KARTKOWKA", "✏️"),
    "class_test": ("PRACA-KLASOWA", "📋"),
    "assessment": ("PRACA-KONTROLNA", "📋"),
    "essay_test": ("WYPRACOWANIE", "📜"),
    "test": ("TEST", "🧪"),
    "day_off": ("WOLNE", "🏖️"),
    "other": ("INFO", "📌"),
}


# Map: Librus attendance symbol → (display tag, emoji).
# `ob` (present) is intentionally absent — it doesn't surface as a calendar
# event. Symbols match the librus-apix Attendance.symbol field.
ATTENDANCE_TAGS = {
    "nb": ("NIEOBECNOSC", "❌"),
    "u": ("USPRAWIEDLIWIONA", "✓"),
    "sp": ("SPOZNIENIE", "⏰"),
    "zw": ("ZWOLNIENIE", "🏥"),
    "wy": ("WYCIECZKA", "🎒"),
    "k": ("KONKURS", "🏆"),
    "sz": ("SZKOLENIE", "📚"),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up calendar entities from a config entry."""
    coordinator = config_entry.runtime_data.coordinator
    async_add_entities([
        LibrusScheduleCalendar(coordinator, config_entry),
        LibrusTimetableCalendar(coordinator, config_entry),
        LibrusAttendanceCalendar(coordinator, config_entry),
        LibrusGradesCalendar(coordinator, config_entry),
    ])


def _parse_hour_range(hour_str: str) -> tuple[time | None, time | None]:
    """Sparsuj 'HH:MM - HH:MM' (lub 'HH:MM') do tuple czasow."""
    if not hour_str:
        return None, None
    parts = [p.strip() for p in hour_str.split("-")]
    try:
        start = datetime.strptime(parts[0], "%H:%M").time()
    except (ValueError, IndexError):
        return None, None
    end = None
    if len(parts) > 1 and parts[1]:
        try:
            end = datetime.strptime(parts[1], "%H:%M").time()
        except ValueError:
            end = None
    return start, end


def _schedule_event_to_calendar_event(event_dict: dict) -> CalendarEvent | None:
    """Convert a Librus schedule event into a tagged HA CalendarEvent."""
    date_iso = event_dict.get("date")
    if not date_iso:
        return None
    try:
        event_date = _date.fromisoformat(date_iso)
    except ValueError:
        return None

    title = event_dict.get("title") or ""
    subject = event_dict.get("subject") or ""
    category = event_dict.get("category") or ""
    event_type = event_dict.get("event_type") or "other"

    tag, emoji = EVENT_TYPE_TAGS.get(event_type, EVENT_TYPE_TAGS["other"])

    # Summary: "📝 [SPRAWDZIAN] matematyka — Prace klasowe sprawdziany."
    body_parts = []
    if subject:
        body_parts.append(subject)
    if title and title.lower() not in (b.lower() for b in body_parts):
        body_parts.append(title)
    body = " — ".join(body_parts) if body_parts else (title or "(brak opisu)")
    summary = f"{emoji} [{tag}] {body}"

    # Description: dodatkowe szczegoly
    desc_parts = []
    if category:
        desc_parts.append(f"Kategoria: {category}")
    if event_dict.get("day_label"):
        desc_parts.append(f"Dzień: {event_dict['day_label']}")
    if event_dict.get("hour"):
        desc_parts.append(f"Godzina: {event_dict['hour']}")
    if event_dict.get("lesson_number") is not None:
        desc_parts.append(f"Lekcja nr: {event_dict['lesson_number']}")
    desc_parts.append(f"event_type: {event_type}")
    description = "\n".join(desc_parts)

    start_time, end_time = _parse_hour_range(event_dict.get("hour", ""))
    tz = dt_util.DEFAULT_TIME_ZONE

    if start_time:
        start_dt = datetime.combine(event_date, start_time, tzinfo=tz)
        end_dt = (
            datetime.combine(event_date, end_time, tzinfo=tz)
            if end_time
            else start_dt + timedelta(minutes=45)
        )
        return CalendarEvent(
            start=start_dt,
            end=end_dt,
            summary=summary,
            description=description,
        )
    return CalendarEvent(
        start=event_date,
        end=event_date + timedelta(days=1),
        summary=summary,
        description=description,
    )


def _lesson_to_calendar_event(period: dict) -> CalendarEvent | None:
    """Konwertuj period planu lekcji na HA CalendarEvent."""
    date_iso = period.get("date")
    time_from = period.get("time_from")
    time_to = period.get("time_to")
    if not date_iso or not time_from or not time_to:
        return None
    try:
        event_date = _date.fromisoformat(date_iso)
        start_t = datetime.strptime(time_from, "%H:%M").time()
        end_t = datetime.strptime(time_to, "%H:%M").time()
    except ValueError:
        return None

    tz = dt_util.DEFAULT_TIME_ZONE
    start_dt = datetime.combine(event_date, start_t, tzinfo=tz)
    end_dt = datetime.combine(event_date, end_t, tzinfo=tz)

    subject = period.get("subject") or "(lekcja)"
    teacher_classroom = period.get("teacher_and_classroom") or ""
    lesson_no = period.get("lesson_number")
    summary = f"{lesson_no}. {subject}" if lesson_no else subject

    desc_parts = []
    if teacher_classroom:
        desc_parts.append(teacher_classroom)
    info = period.get("info") or {}
    for k, v in info.items():
        desc_parts.append(f"{k}: {v}")
    description = "\n".join(desc_parts)

    return CalendarEvent(
        start=start_dt,
        end=end_dt,
        summary=summary,
        description=description,
        location=teacher_classroom or None,
    )


def _attendance_to_calendar_event(raw: dict) -> CalendarEvent | None:
    """Konwertuj wpis frekwencji na full-day CalendarEvent z tagiem.

    Zwraca None gdy wpis to obecność (`ob`) lub gdy symbol nieznany —
    obecność nie jest wydarzeniem, nieznany symbol nie ma sensownego mapowania.
    """
    symbol = raw.get("symbol") or ""
    if symbol == "ob" or raw.get("is_present"):
        return None
    if symbol not in ATTENDANCE_TAGS:
        return None
    date_iso = raw.get("date") or ""
    if not date_iso:
        return None
    try:
        event_date = _date.fromisoformat(date_iso)
    except ValueError:
        return None

    tag, emoji = ATTENDANCE_TAGS[symbol]
    subject = raw.get("subject") or "(brak przedmiotu)"
    summary = f"{emoji} [{tag}] {subject}"

    desc_parts: list[str] = []
    if raw.get("type"):
        desc_parts.append(f"Typ: {raw['type']}")
    period = raw.get("period")
    if period is not None and period != "":
        desc_parts.append(f"Lekcja: {period}")
    if raw.get("teacher"):
        desc_parts.append(f"Nauczyciel: {raw['teacher']}")
    if raw.get("topic"):
        desc_parts.append(f"Temat: {raw['topic']}")
    description = "\n".join(desc_parts)

    return CalendarEvent(
        start=event_date,
        end=event_date + timedelta(days=1),
        summary=summary,
        description=description,
    )


def _grade_to_calendar_event(raw: dict) -> CalendarEvent | None:
    """Konwertuj ocenę na full-day CalendarEvent z tagiem [OCENA <wartość>].

    Oceny opisowe (`type=descriptive`) → tag [OCENA OPISOWA].
    """
    date_iso = raw.get("date") or ""
    if not date_iso:
        return None
    try:
        event_date = _date.fromisoformat(date_iso)
    except ValueError:
        return None

    grade_text = (raw.get("grade") or "").strip()
    grade_type = raw.get("type") or "numeric"

    if grade_type == "descriptive":
        tag = "OCENA OPISOWA"
    else:
        tag = f"OCENA {grade_text}" if grade_text else "OCENA"

    subject = raw.get("subject") or "(brak przedmiotu)"
    category = raw.get("category") or ""
    parts = [subject]
    if category:
        parts.append(category)
    body = " — ".join(parts)
    summary = f"📊 [{tag}] {body}"

    desc_parts: list[str] = []
    if grade_text and grade_type != "descriptive":
        desc_parts.append(f"Ocena: {grade_text}")
    if raw.get("title"):
        desc_parts.append(f"Tytuł: {raw['title']}")
    if raw.get("teacher"):
        desc_parts.append(f"Nauczyciel: {raw['teacher']}")
    weight = raw.get("weight")
    if weight is not None and weight != "":
        desc_parts.append(f"Waga: {weight}")
    if "counts" in raw:
        desc_parts.append(
            f"Liczy się do średniej: {'tak' if raw.get('counts') else 'nie'}"
        )
    if raw.get("description"):
        desc_parts.append(f"Opis: {raw['description']}")
    description = "\n".join(desc_parts)

    return CalendarEvent(
        start=event_date,
        end=event_date + timedelta(days=1),
        summary=summary,
        description=description,
    )


class LibrusBaseCalendar(LibrusBaseEntity, CalendarEntity):
    """Base class for Librus calendar entities."""

    def _convert(self, raw: dict) -> CalendarEvent | None:
        raise NotImplementedError

    def _all_events(self) -> list[dict]:
        raise NotImplementedError

    @property
    def event(self) -> CalendarEvent | None:
        # CalendarEntity.event must be the *currently active or next-future*
        # event, not the first item in the list. The timetable contains the
        # full current week including Monday-morning lessons; without this
        # filter, on Friday evening the state showed Monday's first lesson.
        now = dt_util.now()
        next_event: CalendarEvent | None = None
        for raw in self._all_events():
            ev = self._convert(raw)
            if ev is None:
                continue
            event_end = ev.end
            if isinstance(event_end, _date) and not isinstance(event_end, datetime):
                event_end_dt = datetime.combine(event_end, time.min, tzinfo=dt_util.DEFAULT_TIME_ZONE)
            else:
                event_end_dt = event_end
            if event_end_dt <= now:
                continue  # past event
            if next_event is None:
                next_event = ev
                continue
            # Keep the earliest future event (list may be sorted, but we
            # don't rely on that contract).
            current_start = next_event.start
            new_start = ev.start
            current_dt = (
                datetime.combine(current_start, time.min, tzinfo=dt_util.DEFAULT_TIME_ZONE)
                if isinstance(current_start, _date) and not isinstance(current_start, datetime)
                else current_start
            )
            new_dt = (
                datetime.combine(new_start, time.min, tzinfo=dt_util.DEFAULT_TIME_ZONE)
                if isinstance(new_start, _date) and not isinstance(new_start, datetime)
                else new_start
            )
            if new_dt < current_dt:
                next_event = ev
        return next_event

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        out: list[CalendarEvent] = []
        for raw in self._all_events():
            ev = self._convert(raw)
            if ev is None:
                continue
            event_start = ev.start
            if isinstance(event_start, _date) and not isinstance(event_start, datetime):
                event_dt = datetime.combine(event_start, time.min, tzinfo=dt_util.DEFAULT_TIME_ZONE)
            else:
                event_dt = event_start
            if event_dt < start_date or event_dt > end_date:
                continue
            out.append(ev)
        return out


class LibrusScheduleCalendar(LibrusBaseCalendar):
    """Full Librus schedule (terminarz) calendar with tagged summaries."""

    _attr_translation_key = "schedule"
    _attr_icon = "mdi:calendar-text"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_calendar_terminarz"

    def _all_events(self) -> list[dict]:
        return (self.coordinator.data or {}).get("schedule") or []

    def _convert(self, raw: dict) -> CalendarEvent | None:
        return _schedule_event_to_calendar_event(raw)


class LibrusTimetableCalendar(LibrusBaseCalendar):
    """Librus timetable (plan lekcji) calendar."""

    _attr_translation_key = "timetable"
    _attr_icon = "mdi:timetable"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_calendar_plan_lekcji"

    def _all_events(self) -> list[dict]:
        return (self.coordinator.data or {}).get("timetable") or []

    def _convert(self, raw: dict) -> CalendarEvent | None:
        return _lesson_to_calendar_event(raw)


class LibrusAttendanceCalendar(LibrusBaseCalendar):
    """Calendar of attendance entries — absences, lates, releases, etc."""

    _attr_translation_key = "attendance"
    _attr_icon = "mdi:calendar-account"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_calendar_obecnosci"

    def _all_events(self) -> list[dict]:
        return (self.coordinator.data or {}).get("attendance") or []

    def _convert(self, raw: dict) -> CalendarEvent | None:
        return _attendance_to_calendar_event(raw)


class LibrusGradesCalendar(LibrusBaseCalendar):
    """Calendar of grades — each grade as a full-day event with [OCENA …] tag."""

    _attr_translation_key = "grades_calendar"
    _attr_icon = "mdi:calendar-star"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_calendar_oceny"

    def _all_events(self) -> list[dict]:
        return (self.coordinator.data or {}).get("grades") or []

    def _convert(self, raw: dict) -> CalendarEvent | None:
        return _grade_to_calendar_event(raw)
