"""Calendar platform dla Librus Synergia HA.

Dwa kalendarze per config_entry (per dziecko):
- calendar.librus_<dziecko>_terminarz - cały terminarz Librusa (sprawdziany, dni wolne, inne)
- calendar.librus_<dziecko>_sprawdziany - tylko sprawdziany / kartkówki / prace klasowe
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


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Skonfiguruj calendar entities z config entry."""
    coordinator = hass.data[DOMAIN][f"{config_entry.entry_id}_coordinator"]
    async_add_entities([
        LibrusTerminarzCalendar(coordinator, config_entry),
        LibrusSprawdzianyCalendar(coordinator, config_entry),
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
    """Sparsuj 'HH:MM - HH:MM' (lub 'HH:MM') do tuple czasow.

    Librus zwraca godzine jako 'HH:MM - HH:MM' dla lekcji albo pusty string
    dla calodniowych eventow (sprawdziany w terminarzu maja godzine, ale nie
    zawsze; dni wolne nie maja).
    """
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


def _event_to_calendar_event(event_dict: dict, default_summary_prefix: str = "") -> CalendarEvent:
    """Konwertuj event z coordinator data na HA CalendarEvent."""
    date_iso = event_dict.get("date")
    if not date_iso:
        raise ValueError("event without date")
    event_date = _date.fromisoformat(date_iso)
    title = event_dict.get("title") or ""
    subject = event_dict.get("subject") or ""
    category = event_dict.get("category") or ""

    summary_parts = []
    if subject:
        summary_parts.append(subject)
    if category and category != subject:
        summary_parts.append(f"({category})")
    if title and title.lower() not in (s.lower() for s in summary_parts):
        summary_parts.append(title)
    summary = (default_summary_prefix + " ".join(p for p in summary_parts if p)).strip()
    if not summary:
        summary = title or subject or "Wydarzenie Librus"

    description_parts = []
    if title and title not in summary:
        description_parts.append(title)
    if category:
        description_parts.append(f"Kategoria: {category}")
    if event_dict.get("day_label"):
        description_parts.append(f"Dzień: {event_dict['day_label']}")
    if event_dict.get("hour"):
        description_parts.append(f"Godzina: {event_dict['hour']}")
    if event_dict.get("lesson_number") is not None:
        description_parts.append(f"Lekcja nr: {event_dict['lesson_number']}")
    description = "\n".join(description_parts)

    start_time, end_time = _parse_hour_range(event_dict.get("hour", ""))
    tz = dt_util.DEFAULT_TIME_ZONE

    if start_time:
        start_dt = datetime.combine(event_date, start_time, tzinfo=tz)
        if end_time:
            end_dt = datetime.combine(event_date, end_time, tzinfo=tz)
        else:
            end_dt = start_dt + timedelta(minutes=45)
        return CalendarEvent(
            start=start_dt,
            end=end_dt,
            summary=summary,
            description=description,
        )
    # All-day event
    return CalendarEvent(
        start=event_date,
        end=event_date + timedelta(days=1),
        summary=summary,
        description=description,
    )


class LibrusBaseCalendar(CoordinatorEntity, CalendarEntity):
    """Bazowa klasa kalendarza Librus."""

    _attr_has_entity_name = False

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry

    @property
    def device_info(self) -> Dict[str, Any]:
        return _device_info(self.coordinator, self._config_entry)

    def _all_events(self) -> List[dict]:
        """Override - zwroc raw event dicts (z coordinator data)."""
        raise NotImplementedError

    def _summary_prefix(self) -> str:
        return ""

    @property
    def event(self) -> Optional[CalendarEvent]:
        """Najblizszy event."""
        events = self._all_events()
        if not events:
            return None
        try:
            return _event_to_calendar_event(events[0], self._summary_prefix())
        except ValueError:
            return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> List[CalendarEvent]:
        """Zwroc eventy w zakresie [start_date, end_date]."""
        events = self._all_events()
        out: List[CalendarEvent] = []
        prefix = self._summary_prefix()
        for ev in events:
            try:
                cal_event = _event_to_calendar_event(ev, prefix)
            except ValueError:
                continue
            event_start = cal_event.start
            if isinstance(event_start, _date) and not isinstance(event_start, datetime):
                event_dt = datetime.combine(event_start, time.min, tzinfo=dt_util.DEFAULT_TIME_ZONE)
            else:
                event_dt = event_start
            if event_dt < start_date or event_dt > end_date:
                continue
            out.append(cal_event)
        return out


class LibrusTerminarzCalendar(LibrusBaseCalendar):
    """Caly terminarz Librusa (wszystkie wydarzenia)."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry)
        student = (coordinator.data or {}).get("student_info")
        student_name = student.name if student else "Uczen"
        self._attr_name = f"Librus {student_name} Terminarz"
        self._attr_unique_id = f"{config_entry.entry_id}_calendar_terminarz"
        self._attr_icon = "mdi:calendar-text"

    def _all_events(self) -> List[dict]:
        return (self.coordinator.data or {}).get("terminarz") or []


class LibrusSprawdzianyCalendar(LibrusBaseCalendar):
    """Tylko sprawdziany / kartkówki / prace klasowe."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry)
        student = (coordinator.data or {}).get("student_info")
        student_name = student.name if student else "Uczen"
        self._attr_name = f"Librus {student_name} Sprawdziany"
        self._attr_unique_id = f"{config_entry.entry_id}_calendar_sprawdziany"
        self._attr_icon = "mdi:calendar-alert"

    def _all_events(self) -> List[dict]:
        return (self.coordinator.data or {}).get("zapowiedzi") or []

    def _summary_prefix(self) -> str:
        return "📝 "
