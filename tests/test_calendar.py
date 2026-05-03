"""Tests for the calendar platform — attendance and grades calendars (PR 5).

Two new calendars per config entry, on top of legacy `terminarz` + `plan_lekcji`:
- LibrusAttendanceCalendar — `[NIEOBECNOSC]/[SPOZNIENIE]/[ZWOLNIENIE]/...` events.
- LibrusGradesCalendar — `[OCENA 5]/[OCENA 4+]/[OCENA OPISOWA]` events.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.librus_apix.calendar import (
    ATTENDANCE_TAGS,
    LibrusAttendanceCalendar,
    LibrusGradesCalendar,
    _attendance_to_calendar_event,
    _grade_to_calendar_event,
)


# ---------------------------------------------------------------------------
# _attendance_to_calendar_event
# ---------------------------------------------------------------------------


def test_attendance_to_event_unjustified_absence_has_nieobecnosc_tag():
    raw = {
        "symbol": "nb",
        "type": "Nieobecność",
        "date": "2026-04-15",
        "subject": "Matematyka",
        "teacher": "Anna Nowak",
        "period": 3,
        "topic": "Funkcje kwadratowe",
        "semester": 2,
        "is_present": False,
        "is_absence": True,
        "is_unjustified": True,
        "is_excused": False,
        "is_late": False,
        "is_release": False,
    }
    ev = _attendance_to_calendar_event(raw)
    assert ev is not None
    assert "[NIEOBECNOSC]" in ev.summary
    assert "Matematyka" in ev.summary


def test_attendance_to_event_late_uses_spoznienie_tag():
    raw = {
        "symbol": "sp",
        "type": "Spóźnienie",
        "date": "2026-04-15",
        "subject": "Polski",
        "teacher": "X",
        "period": 1,
        "topic": "",
        "semester": 2,
        "is_late": True,
        "is_absence": False,
        "is_unjustified": False,
        "is_excused": False,
        "is_present": False,
        "is_release": False,
    }
    ev = _attendance_to_calendar_event(raw)
    assert ev is not None
    assert "[SPOZNIENIE]" in ev.summary


def test_attendance_to_event_excused_uses_usprawiedliwiona_tag():
    raw = {
        "symbol": "u",
        "type": "Nieobecność usprawiedliwiona",
        "date": "2026-04-10",
        "subject": "Historia",
        "teacher": "Y",
        "period": 4,
        "topic": "",
        "semester": 2,
        "is_excused": True,
        "is_absence": True,
    }
    ev = _attendance_to_calendar_event(raw)
    assert ev is not None
    assert "[USPRAWIEDLIWIONA]" in ev.summary


def test_attendance_to_event_release_uses_zwolnienie_tag():
    raw = {
        "symbol": "zw",
        "type": "Zwolnienie",
        "date": "2026-04-08",
        "subject": "WF",
        "teacher": "Z",
        "period": 5,
        "topic": "",
        "semester": 2,
        "is_release": True,
    }
    ev = _attendance_to_calendar_event(raw)
    assert ev is not None
    assert "[ZWOLNIENIE]" in ev.summary


def test_attendance_to_event_present_returns_none():
    """Ob. (present) wpisy NIE pojawiaja sie w kalendarzu — to nie wydarzenie."""
    raw = {
        "symbol": "ob",
        "type": "Obecność",
        "date": "2026-04-15",
        "subject": "Matematyka",
        "is_present": True,
    }
    ev = _attendance_to_calendar_event(raw)
    assert ev is None


def test_attendance_to_event_unknown_symbol_returns_none():
    """Zupelnie nieznany symbol nie ma sensownego mapowania — pomijamy."""
    raw = {
        "symbol": "??",
        "date": "2026-04-15",
        "subject": "Matematyka",
    }
    ev = _attendance_to_calendar_event(raw)
    assert ev is None


def test_attendance_to_event_description_contains_period_and_topic():
    raw = {
        "symbol": "nb",
        "type": "Nieobecność",
        "date": "2026-04-15",
        "subject": "Matematyka",
        "teacher": "Anna Nowak",
        "period": 3,
        "topic": "Funkcje kwadratowe",
        "semester": 2,
        "is_unjustified": True,
        "is_absence": True,
    }
    ev = _attendance_to_calendar_event(raw)
    assert ev is not None
    desc = ev.description or ""
    assert "Funkcje kwadratowe" in desc
    assert "Anna Nowak" in desc
    # period 3 → "Lekcja: 3"
    assert "3" in desc


def test_attendance_to_event_is_full_day():
    """Brak mapowania period→godzina w v1 — eventy sa full-day."""
    from datetime import date as _date

    raw = {
        "symbol": "nb",
        "date": "2026-04-15",
        "subject": "Matematyka",
        "is_unjustified": True,
        "is_absence": True,
    }
    ev = _attendance_to_calendar_event(raw)
    assert ev is not None
    # full-day events have date (not datetime) in CalendarEvent
    assert isinstance(ev.start, _date)
    assert ev.start.isoformat() == "2026-04-15"


def test_attendance_to_event_invalid_date_returns_none():
    raw = {"symbol": "nb", "date": "not-a-date", "subject": "X", "is_unjustified": True}
    ev = _attendance_to_calendar_event(raw)
    assert ev is None


# ---------------------------------------------------------------------------
# _grade_to_calendar_event
# ---------------------------------------------------------------------------


def test_grade_to_event_numeric_5_has_ocena_5_tag():
    raw = {
        "subject": "Matematyka",
        "grade": "5",
        "value": 5.0,
        "counts": True,
        "weight": 3,
        "date": "2026-04-12",
        "category": "Sprawdzian",
        "description": "Bardzo dobra praca",
        "teacher": "Anna Nowak",
        "title": "Funkcje kwadratowe",
        "semester": 2,
        "type": "numeric",
    }
    ev = _grade_to_calendar_event(raw)
    assert ev is not None
    assert "[OCENA 5]" in ev.summary
    assert "Matematyka" in ev.summary
    assert "Sprawdzian" in ev.summary


def test_grade_to_event_with_plus_modifier():
    raw = {
        "subject": "Polski",
        "grade": "4+",
        "value": 4.5,
        "date": "2026-04-10",
        "category": "Kartkowka",
        "description": "",
        "teacher": "X",
        "title": "",
        "semester": 2,
        "type": "numeric",
    }
    ev = _grade_to_calendar_event(raw)
    assert ev is not None
    assert "[OCENA 4+]" in ev.summary


def test_grade_to_event_descriptive_uses_opisowa_tag():
    raw = {
        "subject": "Zachowanie",
        "grade": "wzorowe",
        "date": "2026-01-20",
        "category": "Semestralna",
        "description": "Uczeń wzorowo zachowuje się…",
        "teacher": "Y",
        "title": "",
        "semester": 1,
        "type": "descriptive",
    }
    ev = _grade_to_calendar_event(raw)
    assert ev is not None
    assert "[OCENA OPISOWA]" in ev.summary
    assert "Zachowanie" in ev.summary


def test_grade_to_event_description_contains_full_context():
    raw = {
        "subject": "Matematyka",
        "grade": "5",
        "value": 5.0,
        "counts": True,
        "weight": 3,
        "date": "2026-04-12",
        "category": "Sprawdzian",
        "description": "Bardzo dobra praca",
        "teacher": "Anna Nowak",
        "title": "Funkcje kwadratowe",
        "semester": 2,
        "type": "numeric",
    }
    ev = _grade_to_calendar_event(raw)
    assert ev is not None
    desc = ev.description or ""
    assert "Anna Nowak" in desc
    assert "Bardzo dobra praca" in desc
    assert "3" in desc  # waga
    # liczy się do średniej:
    assert "tak" in desc.lower() or "true" in desc.lower()


def test_grade_to_event_invalid_date_returns_none():
    raw = {
        "subject": "Mat",
        "grade": "5",
        "date": "",
        "category": "X",
        "type": "numeric",
    }
    ev = _grade_to_calendar_event(raw)
    assert ev is None


def test_grade_to_event_is_full_day():
    from datetime import date as _date

    raw = {
        "subject": "Mat",
        "grade": "5",
        "date": "2026-04-12",
        "category": "Sprawdzian",
        "type": "numeric",
    }
    ev = _grade_to_calendar_event(raw)
    assert ev is not None
    assert isinstance(ev.start, _date)
    assert ev.start.isoformat() == "2026-04-12"


# ---------------------------------------------------------------------------
# Tag table integrity
# ---------------------------------------------------------------------------


def test_attendance_tags_cover_all_known_symbols():
    """ATTENDANCE_TAGS musi pokrywac wszystkie symbole z biblioteki."""
    expected = {"nb", "u", "sp", "zw", "wy", "k", "sz"}
    assert expected.issubset(set(ATTENDANCE_TAGS.keys()))


# ---------------------------------------------------------------------------
# Calendar entity setup wired in async_setup_entry
# ---------------------------------------------------------------------------


async def test_setup_entry_creates_four_calendars(
    hass: HomeAssistant, mock_librus_client, mock_config_entry
):
    """Setup integracji rejestruje 4 calendar entities per config entry:
    terminarz, plan_lekcji, obecnosci (NEW), oceny (NEW)."""
    from homeassistant.helpers import entity_registry as er

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    calendar_entries = [
        e for e in registry.entities.values()
        if e.domain == "calendar" and e.config_entry_id == mock_config_entry.entry_id
    ]
    unique_ids = {e.unique_id for e in calendar_entries}
    assert f"{mock_config_entry.entry_id}_calendar_terminarz" in unique_ids
    assert f"{mock_config_entry.entry_id}_calendar_plan_lekcji" in unique_ids
    assert f"{mock_config_entry.entry_id}_calendar_obecnosci" in unique_ids
    assert f"{mock_config_entry.entry_id}_calendar_oceny" in unique_ids
    assert len(calendar_entries) == 4
