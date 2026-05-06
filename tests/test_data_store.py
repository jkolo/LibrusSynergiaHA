"""Tests for LibrusDataStore."""

from __future__ import annotations

from datetime import timezone

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from librus_apix.student_information import StudentInformation

from custom_components.librus_apix._data_store import LibrusDataStore


@pytest.fixture
def real_student_info() -> StudentInformation:
    return StudentInformation(
        name="Jan Kowalski",
        class_name="5A",
        number=12,
        tutor="Anna Nowak",
        school="SP 1",
        lucky_number=7,
    )


@pytest.fixture
def sample_data(real_student_info) -> dict:
    return {
        "student_info": real_student_info,
        "grades": [{"subject": "Matematyka", "grade": "5", "date": "2025-09-15",
                     "category": "Sprawdzian", "teacher": "Anna", "semester": 1, "type": "numeric"}],
        "messages": [{"href": "/msg/1", "title": "Zebranie", "author": "Dyrektor",
                       "date": "2025-09-10", "unread": True, "notification_dismissed": False}],
        "grades_by_subject": {"Matematyka": []},
        "upcoming_exams": [{"date": "2025-09-20", "subject": "Polski", "title": "Wypracowanie"}],
        "schedule": [],
        "timetable": [],
        "attendance": [],
        "attendance_frequency": {},
        "attendance_by_subject": {},
        "announcements": [{"date": "2025-09-01", "title": "Nowy rok"}],
        "current_semester": 1,
    }


async def test_load_returns_none_when_no_cache(hass: HomeAssistant) -> None:
    """async_load zwraca None gdy storage jest pusty."""
    store = LibrusDataStore(hass, "entry_abc")
    result = await store.async_load()
    assert result is None


async def test_save_and_load_roundtrip(hass: HomeAssistant, sample_data) -> None:
    """Zapis i odczyt roundtrip zachowuje wszystkie klucze danych."""
    store = LibrusDataStore(hass, "entry_abc")
    ts = dt_util.utcnow()

    await store.async_save(sample_data, ts)
    result = await store.async_load()

    assert result is not None
    data, saved_at = result

    # Timestamp zwrócony zgodnie z zapisanym
    assert saved_at.replace(tzinfo=timezone.utc) == ts.replace(tzinfo=timezone.utc) or abs(
        (saved_at - ts).total_seconds()
    ) < 1

    # student_info deserializowany do StudentInformation
    si = data["student_info"]
    assert isinstance(si, StudentInformation)
    assert si.name == "Jan Kowalski"
    assert si.class_name == "5A"
    assert si.number == 12
    assert si.tutor == "Anna Nowak"
    assert si.lucky_number == 7

    # Inne klucze zachowane
    assert data["grades"] == sample_data["grades"]
    assert data["messages"] == sample_data["messages"]
    assert data["current_semester"] == 1
    assert data["upcoming_exams"] == sample_data["upcoming_exams"]
    assert data["announcements"] == sample_data["announcements"]


async def test_load_returns_none_on_corrupted_cache(hass: HomeAssistant) -> None:
    """async_load zwraca None gdy cache jest uszkodzony (brak _saved_at)."""
    store = LibrusDataStore(hass, "entry_xyz")
    # Zapisz bezpośrednio do wewnętrznego store z brakującym _saved_at
    await store._store.async_save({"data": {"current_semester": 1}})
    result = await store.async_load()
    assert result is None


async def test_student_info_none_survives_roundtrip(hass: HomeAssistant) -> None:
    """None w student_info nie psuje zapisu/odczytu."""
    store = LibrusDataStore(hass, "entry_abc")
    data = {"student_info": None, "grades": [], "current_semester": 2}
    ts = dt_util.utcnow()

    await store.async_save(data, ts)
    result = await store.async_load()

    assert result is not None
    loaded_data, _ = result
    assert loaded_data["student_info"] is None
    assert loaded_data["current_semester"] == 2


async def test_lucky_number_string_preserved(hass: HomeAssistant) -> None:
    """lucky_number='?' (str) zachowuje typ po roundtrip."""
    store = LibrusDataStore(hass, "entry_abc")
    si = StudentInformation(
        name="Ewa", class_name="3B", number=5,
        tutor="Jan", school="SP2", lucky_number="?",
    )
    data = {"student_info": si, "grades": [], "current_semester": 1}
    await store.async_save(data, dt_util.utcnow())

    result = await store.async_load()
    assert result is not None
    loaded_si = result[0]["student_info"]
    assert isinstance(loaded_si, StudentInformation)
    assert loaded_si.lucky_number == "?"


async def test_async_clear_removes_cache(hass: HomeAssistant, sample_data) -> None:
    """async_clear usuwa cache — kolejny load zwraca None."""
    store = LibrusDataStore(hass, "entry_abc")
    await store.async_save(sample_data, dt_util.utcnow())
    assert await store.async_load() is not None

    await store.async_clear()
    assert await store.async_load() is None
