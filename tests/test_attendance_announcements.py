"""Tests for the new coordinator fields: attendance + announcements (PR 1)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.librus_apix.coordinator import LibrusDataUpdateCoordinator


# ---------------------------------------------------------------------------
# Coordinator integration
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_client_with_attendance(mock_student_info):
    """Client zwracajacy realistyczne attendance + announcements."""
    client = MagicMock()
    client.username = "test_user"
    client.async_authenticate = AsyncMock(return_value=True)
    client.async_get_student_information = AsyncMock(return_value=mock_student_info)
    client.async_get_grades = AsyncMock(return_value=[])
    client.async_get_messages = AsyncMock(return_value=[])
    client.async_get_schedule_events = AsyncMock(return_value=[])
    client.async_get_timetable_events = AsyncMock(return_value=[])
    client.async_get_attendance = AsyncMock(return_value=[
        {
            "symbol": "ob", "type": "Obecność", "date": "2026-04-01",
            "subject": "Matematyka", "teacher": "Anna", "period": 1, "topic": "",
            "semester": 2, "excursion": False,
            "is_present": True, "is_absence": False, "is_unjustified": False,
            "is_excused": False, "is_late": False, "is_release": False,
        },
        {
            "symbol": "nb", "type": "Nieobecność", "date": "2026-04-02",
            "subject": "Polski", "teacher": "Marek", "period": 2, "topic": "",
            "semester": 2, "excursion": False,
            "is_present": False, "is_absence": True, "is_unjustified": True,
            "is_excused": False, "is_late": False, "is_release": False,
        },
        {
            "symbol": "sp", "type": "Spóźnienie", "date": "2026-04-03",
            "subject": "Historia", "teacher": "Pawel", "period": 3, "topic": "",
            "semester": 2, "excursion": False,
            "is_present": False, "is_absence": False, "is_unjustified": False,
            "is_excused": False, "is_late": True, "is_release": False,
        },
    ])
    client.async_get_homework = AsyncMock(return_value=[])
    client.async_get_notes = AsyncMock(return_value=[])
    client.async_get_behavior = AsyncMock(return_value={})
    client.async_get_attendance_stats = AsyncMock(return_value={
        "overall": {"semester_1": None, "semester_2": 90.0, "total": 90.0, "current": 90.0},
        "by_subject": {"Matematyka": {"present": 9, "missed": 1, "total": 10, "frequency": 90.0}},
    })
    client.async_get_announcements = AsyncMock(return_value=[
        {
            "title": "Wycieczka do Krakowa",
            "author": "Dyrekcja",
            "description": "Zapraszamy klasy 5-8 na wycieczkę 12 maja.",
            "date": "2026-04-15",
        },
    ])
    return client


async def test_coordinator_data_includes_attendance_fields(
    hass: HomeAssistant, fake_client_with_attendance
):
    """Po pierwszym refresh coordinator.data ma attendance + frequency + by_subject."""
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client_with_attendance)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    data = coordinator.data
    assert len(data["attendance"]) == 3
    # Frekwencja z gateway API (async_get_attendance_stats), nie z listy HTML.
    assert data["attendance_frequency"]["current"] == 90.0
    assert data["attendance_by_subject"]["Matematyka"]["frequency"] == 90.0


async def test_attendance_stats_none_keeps_cached(
    hass: HomeAssistant, fake_client_with_attendance
):
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client_with_attendance)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    fake_client_with_attendance.async_get_attendance_stats = AsyncMock(return_value=None)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.data["attendance_frequency"]["current"] == 90.0
    assert "Matematyka" in coordinator.data["attendance_by_subject"]


async def test_coordinator_data_includes_announcements(
    hass: HomeAssistant, fake_client_with_attendance
):
    """Po pierwszym refresh coordinator.data ma announcements."""
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client_with_attendance)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    items = coordinator.data["announcements"]
    assert len(items) == 1
    assert items[0]["title"] == "Wycieczka do Krakowa"
    assert items[0]["author"] == "Dyrekcja"


async def test_attendance_none_uses_cache(
    hass: HomeAssistant, fake_client_with_attendance
):
    """Gdy fetch attendance pada w drugim refresh, używamy cache."""
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client_with_attendance)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert len(coordinator.data["attendance"]) == 3

    # Drugi refresh: attendance None, ale grades None → wpadamy do cache fallback.
    fake_client_with_attendance.async_get_attendance = AsyncMock(return_value=None)
    fake_client_with_attendance.async_get_grades = AsyncMock(return_value=None)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Cache fallback ścieżka: attendance z poprzedniego refresh.
    assert len(coordinator.data["attendance"]) == 3
