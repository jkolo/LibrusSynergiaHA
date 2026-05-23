"""Tests for the new coordinator fields: attendance + announcements (PR 1)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.librus_apix.coordinator import (
    LibrusDataUpdateCoordinator,
    _attendance_by_subject,
    _attendance_frequency,
)


# ---------------------------------------------------------------------------
# Pure helper functions
# ---------------------------------------------------------------------------


class TestAttendanceFrequency:
    def test_empty_returns_zeros(self):
        result = _attendance_frequency([], current_semester=1)
        assert result == {
            "semester_1": 0.0,
            "semester_2": 0.0,
            "total": 0.0,
            "current": 0.0,
        }

    def test_all_present_is_100_percent(self):
        attendance = [
            {"semester": 1, "is_present": True, "is_absence": False, "is_late": False, "excursion": False},
            {"semester": 1, "is_present": True, "is_absence": False, "is_late": False, "excursion": False},
        ]
        result = _attendance_frequency(attendance, current_semester=1)
        assert result["semester_1"] == 100.0
        assert result["current"] == 100.0

    def test_one_absence_in_three_lessons(self):
        attendance = [
            {"semester": 1, "is_present": True, "is_absence": False, "is_late": False, "excursion": False},
            {"semester": 1, "is_present": True, "is_absence": False, "is_late": False, "excursion": False},
            {"semester": 1, "is_present": False, "is_absence": True, "is_late": False, "excursion": False},
        ]
        result = _attendance_frequency(attendance, current_semester=1)
        # 2 / 3 ≈ 66.67 %
        assert result["semester_1"] == pytest.approx(66.67, abs=0.01)

    def test_excursion_counts_as_present(self):
        attendance = [
            {"semester": 1, "is_present": False, "is_absence": False, "is_late": False, "excursion": True},
            {"semester": 1, "is_present": False, "is_absence": True, "is_late": False, "excursion": False},
        ]
        result = _attendance_frequency(attendance, current_semester=1)
        # 1 (excursion) / 2 = 50 %
        assert result["semester_1"] == 50.0

    def test_late_counts_as_missed(self):
        attendance = [
            {"semester": 1, "is_present": True, "is_absence": False, "is_late": False, "excursion": False},
            {"semester": 1, "is_present": False, "is_absence": False, "is_late": True, "excursion": False},
        ]
        result = _attendance_frequency(attendance, current_semester=1)
        assert result["semester_1"] == 50.0

    def test_current_picks_right_semester(self):
        attendance = [
            {"semester": 1, "is_present": True, "is_absence": False, "is_late": False, "excursion": False},
            {"semester": 2, "is_present": False, "is_absence": True, "is_late": False, "excursion": False},
        ]
        sem1 = _attendance_frequency(attendance, current_semester=1)
        sem2 = _attendance_frequency(attendance, current_semester=2)
        assert sem1["current"] == 100.0
        assert sem2["current"] == 0.0


class TestAttendanceBySubject:
    def test_empty_returns_empty_dict(self):
        assert _attendance_by_subject([]) == {}

    def test_groups_by_subject(self):
        attendance = [
            {"subject": "Matematyka", "is_present": True, "is_absence": False, "is_late": False, "excursion": False},
            {"subject": "Matematyka", "is_present": False, "is_absence": True, "is_late": False, "excursion": False},
            {"subject": "Polski", "is_present": True, "is_absence": False, "is_late": False, "excursion": False},
        ]
        result = _attendance_by_subject(attendance)
        assert result["Matematyka"] == {"present": 1, "missed": 1, "frequency": 50.0}
        assert result["Polski"] == {"present": 1, "missed": 0, "frequency": 100.0}


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
    # frequency: 1 obecny / (1 + 1 nieobecny + 1 spóźnienie) = 33.33 %
    freq = data["attendance_frequency"]
    assert freq["semester_2"] == pytest.approx(33.33, abs=0.01)
    assert "current" in freq

    by_subj = data["attendance_by_subject"]
    assert by_subj["Matematyka"]["present"] == 1
    assert by_subj["Polski"]["missed"] == 1


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
