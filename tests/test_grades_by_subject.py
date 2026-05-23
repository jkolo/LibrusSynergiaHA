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
