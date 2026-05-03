"""Calendar platform dla Librus Synergia HA.

Dwa kalendarze per config_entry (per dziecko):
- calendar.librus_<dziecko>_terminarz - cały terminarz Librusa (sprawdziany, dni
  wolne, inne) z tagami [SPRAWDZIAN]/[KARTKOWKA]/[PRACA-KLASOWA]/[WOLNE]/[INFO]
  na poczatku summary do filtrowania.
- calendar.librus_<dziecko>_plan_lekcji - plan lekcji (timetable).
"""
from __future__ import annotations

import logging
from datetime import date as _date, datetime, time, timedelta
from typing import Any, Dict, List, Optional

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


# Mapowanie event_type → (tag, emoji) dla terminarza
EVENT_TYPE_TAGS = {
    "sprawdzian": ("SPRAWDZIAN", "📝"),
    "kartkowka": ("KARTKOWKA", "✏️"),
    "praca_klasowa": ("PRACA-KLASOWA", "📋"),
    "praca_kontrolna": ("PRACA-KONTROLNA", "📋"),
    "wypracowanie_klasowe": ("WYPRACOWANIE", "📜"),
    "test": ("TEST", "🧪"),
    "dzien_wolny": ("WOLNE", "🏖️"),
    "inne": ("INFO", "📌"),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Skonfiguruj calendar entities z config entry."""
    coordinator = hass.data[DOMAIN][f"{config_entry.entry_id}_coordinator"]
    async_add_entities([
        LibrusTerminarzCalendar(coordinator, config_entry),
        LibrusPlanLekcjiCalendar(coordinator, config_entry),
    ])


def _device_info(coordinator, config_entry: ConfigEntry) -> Dict[str, Any]:
    """Zwroc informacje o urzadzeniu (wspolny z sensor.py)."""
    data = coordinator.data or {}
    student_info = data.get("student_info")
    name = student_info.name if student_info else "Librus"
    return {
        "identifiers": {(DOMAIN, config_entry.entry_id)},
        "name": f"Librus - {name}",
        "manufacturer": "Librus",
        "model": "Synergia",
    }


def _parse_hour_range(hour_str: str) -> tuple[Optional[time], Optional[time]]:
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


def _terminarz_event_to_calendar_event(event_dict: dict) -> Optional[CalendarEvent]:
    """Konwertuj event z terminarza Librusa na HA CalendarEvent z tagami."""
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
    event_type = event_dict.get("event_type") or "inne"

    tag, emoji = EVENT_TYPE_TAGS.get(event_type, EVENT_TYPE_TAGS["inne"])

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


def _lekcja_to_calendar_event(period: dict) -> Optional[CalendarEvent]:
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


class LibrusBaseCalendar(CoordinatorEntity, CalendarEntity):
    """Bazowa klasa kalendarza Librus."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry

    @property
    def device_info(self) -> Dict[str, Any]:
        return _device_info(self.coordinator, self._config_entry)

    def _convert(self, raw: dict) -> Optional[CalendarEvent]:
        raise NotImplementedError

    def _all_events(self) -> List[dict]:
        raise NotImplementedError

    @property
    def event(self) -> Optional[CalendarEvent]:
        for raw in self._all_events():
            ev = self._convert(raw)
            if ev:
                return ev
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> List[CalendarEvent]:
        out: List[CalendarEvent] = []
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


class LibrusTerminarzCalendar(LibrusBaseCalendar):
    """Caly terminarz Librusa z tagami w summary."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_name = "Terminarz"
        self._attr_unique_id = f"{config_entry.entry_id}_calendar_terminarz"
        self._attr_icon = "mdi:calendar-text"

    def _all_events(self) -> List[dict]:
        return (self.coordinator.data or {}).get("terminarz") or []

    def _convert(self, raw: dict) -> Optional[CalendarEvent]:
        return _terminarz_event_to_calendar_event(raw)


class LibrusPlanLekcjiCalendar(LibrusBaseCalendar):
    """Plan lekcji (timetable) Librusa."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry)
        self._attr_name = "Plan Lekcji"
        self._attr_unique_id = f"{config_entry.entry_id}_calendar_plan_lekcji"
        self._attr_icon = "mdi:timetable"

    def _all_events(self) -> List[dict]:
        return (self.coordinator.data or {}).get("plan_lekcji") or []

    def _convert(self, raw: dict) -> Optional[CalendarEvent]:
        return _lekcja_to_calendar_event(raw)
