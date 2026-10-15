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
    _homework_to_calendar_event,
    _lesson_to_calendar_event,
    _schedule_event_to_calendar_event,
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


def test_grade_to_event_unknown_counts_and_weight_are_omitted():
    """Librus without weighted averages gives no "Licz do średniej" / "Waga"."""
    raw = {
        "subject": "Geografia",
        "grade": "3",
        "value": 3.0,
        "counts": None,
        "weight": None,
        "date": "2026-09-27",
        "category": "sprawdzian",
        "teacher": "Anna Nowak",
        "semester": 1,
        "type": "numeric",
    }
    ev = _grade_to_calendar_event(raw)
    assert ev is not None
    desc = ev.description or ""
    assert "Liczy się do średniej" not in desc
    assert "Waga" not in desc


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
# _schedule_event_to_calendar_event
# ---------------------------------------------------------------------------


def test_schedule_event_description_contains_opis_and_teacher():
    ev = _schedule_event_to_calendar_event({
        "date": "2026-10-02",
        "title": "Sprawdzian",
        "subject": "matematyka",
        "event_type": "exam",
        "description": "Funkcje liniowe",
        "teacher": "Jan Kowalski",
    })
    assert ev is not None
    assert "Opis: Funkcje liniowe" in ev.description
    assert "Nauczyciel: Jan Kowalski" in ev.description


def test_schedule_event_description_skips_empty_opis():
    ev = _schedule_event_to_calendar_event({
        "date": "2026-10-02",
        "title": "Sprawdzian",
        "subject": "matematyka",
        "event_type": "exam",
        "description": "",
        "teacher": "",
    })
    assert ev is not None
    assert "Opis:" not in ev.description
    assert "Nauczyciel:" not in ev.description


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


# ---------------------------------------------------------------------------
# _homework_to_calendar_event
# ---------------------------------------------------------------------------


def _hw(**kw):
    base = {
        "subject": "matematyka", "category": "Zadanie domowe",
        "teacher": "Jan Kowalski", "lesson": "Funkcje liniowe",
        "task_date": "2026-09-25", "due_date": "2026-10-02",
        "due_date_raw": "2026-10-02 piątek", "days_until": 7, "href": "1",
    }
    base.update(kw)
    return base


def test_homework_to_event_is_all_day_on_due_date():
    from datetime import date

    ev = _homework_to_calendar_event(_hw())
    assert ev is not None
    assert ev.start == date(2026, 10, 2)
    assert ev.end == date(2026, 10, 3)
    assert ev.summary == "📚 [ZADANIE] matematyka — Zadanie domowe"


def test_homework_to_event_description_has_context():
    ev = _homework_to_calendar_event(_hw())
    assert "Temat: Funkcje liniowe" in ev.description
    assert "Nauczyciel: Jan Kowalski" in ev.description
    assert "Zadane: 2026-09-25" in ev.description


def test_homework_without_due_date_returns_none():
    assert _homework_to_calendar_event(_hw(due_date=None)) is None


async def test_setup_entry_creates_five_calendars(
    hass: HomeAssistant, mock_librus_client, mock_config_entry
):
    """Setup integracji rejestruje 5 calendar entities per config entry:
    terminarz, plan_lekcji, obecnosci, oceny, zadania (v4.0)."""
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
    assert f"{mock_config_entry.entry_id}_calendar_zadania" in unique_ids
    assert len(calendar_entries) == 5


def test_schedule_reading_has_lektura_tag():
    ev = _schedule_event_to_calendar_event({
        "date": "2026-10-19", "title": "Inne.", "subject": "język polski",
        "event_type": "reading",
        "description": "Lektury - Katarynka, Janko Muzykant.",
    })
    assert ev.summary.startswith("📖 [LEKTURA] język polski")



# ---------------------------------------------------------------------------
# _lesson_to_calendar_event — zastępstwa, odwołania, dni wolne (info z Librusa)
# ---------------------------------------------------------------------------


def _lesson(info: dict) -> dict:
    return {
        "subject": "matematyka", "teacher_and_classroom": "Jan Kowalski s31",
        "date": "2026-10-13", "time_from": "08:00", "time_to": "08:45",
        "weekday": "wtorek", "lesson_number": 1, "info": info,
    }


def test_lesson_substitution_is_readable_and_tagged():
    ev = _lesson_to_calendar_event(_lesson({"zastępstwo": {
        "teacher_swap": "wakat matematyka -> Głuchowska Monika",
        "subject_swap": "",
        "classroom_swap": "s31 -> [brak]",
        "date_added": "2026-10-12 14:03:11",
    }}))
    assert ev.summary == "🔄 [ZASTEPSTWO] 1. matematyka"
    assert "{" not in ev.description and "_swap" not in ev.description
    assert "Zastępstwo" in ev.description
    assert "Nauczyciel: wakat matematyka → Głuchowska Monika" in ev.description
    assert "Sala: s31 → brak" in ev.description
    assert "Przedmiot" not in ev.description  # pusty — pomijany
    assert "Dodano: 2026-10-12 14:03:11" in ev.description


def test_lesson_cancelled_is_tagged():
    ev = _lesson_to_calendar_event(_lesson({"odwołane": ""}))
    assert ev.summary == "❌ [ODWOLANE] 1. matematyka"
    assert "odwołane" in ev.description


def test_lesson_on_school_day_off_is_tagged():
    ev = _lesson_to_calendar_event(_lesson({"dzień wolny szkoły: Dzień Edukacji Narodowej": ""}))
    assert ev.summary == "🏖️ [WOLNE] 1. matematyka"
    assert "dzień wolny szkoły: Dzień Edukacji Narodowej" in ev.description


def test_regular_lesson_has_no_tag():
    ev = _lesson_to_calendar_event(_lesson({}))
    assert ev.summary == "1. matematyka"
    assert ev.description == "Jan Kowalski s31"



def test_schedule_description_has_no_technical_lines():
    ev = _schedule_event_to_calendar_event({
        "date": "2026-10-23", "title": "Prace klasowe sprawdziany.", "subject": "historia",
        "event_type": "exam", "description": "Odkrycia geograficzne",
        "teacher": "Golenia Rafał", "day_label": "23", "hour": "unknown",
        "lesson_number": "unknown",
    })
    assert "unknown" not in ev.description
    assert "event_type" not in ev.description
    assert "Dzień:" not in ev.description
    assert ev.description == "Opis: Odkrycia geograficzne\nNauczyciel: Golenia Rafał"


def test_schedule_description_keeps_real_lesson_number():
    ev = _schedule_event_to_calendar_event({
        "date": "2026-10-23", "title": "Sprawdzian", "subject": "historia",
        "event_type": "exam", "lesson_number": 7, "hour": "",
    })
    assert "Lekcja nr: 7" in ev.description
