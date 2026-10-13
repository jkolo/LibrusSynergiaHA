"""Tests for grades_by_subject enrichment + per-subject sensor attrs (PR 3)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.librus_apix.coordinator import LibrusDataUpdateCoordinator


@pytest.fixture
def fake_client_with_rich_grades(mock_student_info):
    """Client zwracający oceny z pełnym kontekstem (po wzbogaceniu z PR 1)."""
    client = MagicMock()
    client.username = "test_user"
    client.async_authenticate = AsyncMock(return_value=True)
    client.async_get_student_information = AsyncMock(return_value=mock_student_info)
    client.async_get_grades = AsyncMock(return_value=[
        {
            "subject": "Matematyka", "grade": "5", "value": 5.0, "counts": True,
            "weight": 3, "date": "2026-04-15", "category": "Sprawdzian",
            "description": "Świetna praca, drobne błędy w zad. 4.",
            "title": "Funkcje kwadratowe", "teacher": "Anna Nowak",
            "semester": 2, "type": "numeric",
        },
        {
            "subject": "Matematyka", "grade": "4+", "value": 4.5, "counts": True,
            "weight": 1, "date": "2026-04-10", "category": "Kartkówka",
            "description": "", "title": "", "teacher": "Anna Nowak",
            "semester": 2, "type": "numeric",
        },
    ])
    client.async_get_messages = AsyncMock(return_value=[])
    client.async_get_schedule_events = AsyncMock(return_value=[])
    client.async_get_timetable_events = AsyncMock(return_value=[])
    client.async_get_attendance = AsyncMock(return_value=[])
    client.async_get_homework = AsyncMock(return_value=[])
    client.async_get_notes = AsyncMock(return_value=[])
    client.async_get_announcements = AsyncMock(return_value=[])
    return client


async def test_grades_by_subject_carries_full_context(
    hass: HomeAssistant, fake_client_with_rich_grades
):
    """Po refresh coordinator.data['grades_by_subject'][<subject>] ma pełen
    kontekst każdej oceny (value, weight, description, title, counts)."""
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client_with_rich_grades)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    by_subj = coordinator.data["grades_by_subject"]
    assert "Matematyka" in by_subj
    grades = by_subj["Matematyka"]
    assert len(grades) == 2

    first = grades[0]
    assert first["grade"] == "5"
    assert first["value"] == 5.0
    assert first["counts"] is True
    assert first["weight"] == 3
    assert first["description"] == "Świetna praca, drobne błędy w zad. 4."
    assert first["title"] == "Funkcje kwadratowe"
    assert first["category"] == "Sprawdzian"


# ---------------------------------------------------------------------------
# Per-subject sensor attributes — grade_details
# ---------------------------------------------------------------------------


from custom_components.librus_apix.sensor import (
    LibrusSubjectAverageSensor,
    LibrusSubjectGradesSensor,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.librus_apix.const import DOMAIN


@pytest.fixture
def mock_entry_in_hass(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Librus APIX (test_user)",
        data={"username": "test_user", "password": "test_password"},
        unique_id="test_user",
    )
    entry.add_to_hass(hass)
    return entry


async def test_subject_grades_sensor_attrs_include_grade_details(
    hass: HomeAssistant, fake_client_with_rich_grades, mock_entry_in_hass
):
    """LibrusSubjectGradesSensor.extra_state_attributes ma grade_details."""
    coordinator = LibrusDataUpdateCoordinator(
        hass, fake_client_with_rich_grades, config_entry=mock_entry_in_hass
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    sensor = LibrusSubjectGradesSensor(coordinator, "Matematyka", mock_entry_in_hass)
    attrs = sensor.extra_state_attributes
    details = attrs["grade_details"]
    assert isinstance(details, list)
    assert len(details) == 2
    first = details[0]
    # Pełen kontekst — wszystkie pola dostępne w atrybucie, w tym subject (dla karty Lovelace).
    for key in (
        "subject", "grade", "value", "date", "category", "description", "weight",
        "counts", "teacher", "title", "is_recent",
    ):
        assert key in first, f"grade_details should expose {key}"
    assert first["subject"] == "Matematyka"
    assert first["description"] == "Świetna praca, drobne błędy w zad. 4."
    # Surowy słownik grades został usunięty z atrybutów (redundantny z grade_details).
    assert "grades" not in attrs
    # librus-subject-grades-card czyta attributes.subject jako tytuł karty.
    assert attrs["subject"] == "Matematyka"


async def test_subject_average_sensor_attrs_compact(
    hass: HomeAssistant, fake_client_with_rich_grades, mock_entry_in_hass
):
    """LibrusSubjectAverageSensor.extra_state_attributes ma tylko kompaktowe pola
    (subject, grade_list, grade_count) — bez grade_details (16KB limit HA)."""
    coordinator = LibrusDataUpdateCoordinator(
        hass, fake_client_with_rich_grades, config_entry=mock_entry_in_hass
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    sensor = LibrusSubjectAverageSensor(coordinator, "Matematyka", mock_entry_in_hass)
    attrs = sensor.extra_state_attributes
    assert "grade_details" not in attrs
    assert attrs["subject"] == "Matematyka"
    assert "grade_list" in attrs
    assert attrs["grade_count"] == 2
    # State pozostaje floatem (średnia).
    assert isinstance(sensor.native_value, float)


# ---------------------------------------------------------------------------
# Poprawy ocen ("Poprawa oceny") — powiązanie poprawy z poprawianą oceną
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_client_with_correction(mock_student_info):
    """Klient z oceną poprawioną (1 z kartkówki) i jej poprawą (6)."""
    client = MagicMock()
    client.username = "test_user"
    client.async_authenticate = AsyncMock(return_value=True)
    client.async_get_student_information = AsyncMock(return_value=mock_student_info)
    client.async_get_grades = AsyncMock(return_value=[
        {
            "subject": "matematyka", "grade": "1", "value": 1.0,
            "counts": None, "weight": None, "date": "2026-09-17",
            "category": "kartkówka", "description": "", "title": "Ułamki",
            "teacher": "Anna Nowak", "semester": 1, "type": "numeric",
        },
        {
            "subject": "matematyka", "grade": "6", "value": 6.0,
            "counts": None, "weight": None, "date": "2026-09-28",
            "category": "kartkówka", "description": "1 (kartkówka)", "title": "",
            "teacher": "Anna Nowak", "semester": 1, "type": "numeric",
        },
        {
            "subject": "historia", "grade": "4", "value": 4.0,
            "counts": None, "weight": None, "date": "2026-09-20",
            "category": "kartkówka", "description": "", "title": "",
            "teacher": "Jan Kowal", "semester": 1, "type": "numeric",
        },
    ])
    client.async_get_messages = AsyncMock(return_value=[])
    client.async_get_schedule_events = AsyncMock(return_value=[])
    client.async_get_timetable_events = AsyncMock(return_value=[])
    client.async_get_attendance = AsyncMock(return_value=[])
    client.async_get_homework = AsyncMock(return_value=[])
    client.async_get_notes = AsyncMock(return_value=[])
    client.async_get_announcements = AsyncMock(return_value=[])
    return client


async def test_coordinator_links_corrections_within_a_subject(
    hass: HomeAssistant, fake_client_with_correction
):
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client_with_correction)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    by_subj = coordinator.data["grades_by_subject"]
    original, correction = by_subj["matematyka"]
    assert correction["correction_of"] == {
        "grade": "1", "category": "kartkówka", "date": "2026-09-17",
    }
    assert original["corrected_by"] == {
        "grade": "6", "category": "kartkówka", "date": "2026-09-28",
    }
    # Another subject's identical-looking grades are never pulled in.
    (history,) = by_subj["historia"]
    assert history["correction_of"] is None
    assert history["corrected_by"] is None


async def test_subject_sensor_grade_details_expose_correction_links(
    hass: HomeAssistant, fake_client_with_correction, mock_entry_in_hass
):
    coordinator = LibrusDataUpdateCoordinator(
        hass, fake_client_with_correction, config_entry=mock_entry_in_hass
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    sensor = LibrusSubjectGradesSensor(coordinator, "matematyka", mock_entry_in_hass)
    details = sensor.extra_state_attributes["grade_details"]

    by_grade = {d["grade"]: d for d in details}
    assert by_grade["6"]["correction_of"]["date"] == "2026-09-17"
    assert by_grade["6"]["corrected_by"] is None
    assert by_grade["1"]["corrected_by"]["grade"] == "6"
    assert by_grade["1"]["correction_of"] is None


async def test_averages_leave_out_the_corrected_grade(
    hass: HomeAssistant, fake_client_with_correction, mock_entry_in_hass
):
    """1 poprawione na 6 daje średnią 6.0, nie (1 + 6) / 2."""
    coordinator = LibrusDataUpdateCoordinator(
        hass, fake_client_with_correction, config_entry=mock_entry_in_hass
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    grades = LibrusSubjectGradesSensor(coordinator, "matematyka", mock_entry_in_hass)
    average = LibrusSubjectAverageSensor(coordinator, "matematyka", mock_entry_in_hass)

    assert grades.extra_state_attributes["average"] == 6.0
    assert average.native_value == 6.0
    # The history still lists both: only the average changes.
    assert average.extra_state_attributes["grade_count"] == 2
