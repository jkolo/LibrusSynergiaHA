"""Tests for the Librus APIX DataUpdateCoordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.librus_apix.coordinator import LibrusDataUpdateCoordinator


@pytest.fixture
def fake_client(mock_student_info):
    """Minimal fake LibrusApiClient."""
    client = MagicMock()
    client.username = "test_user"
    client.async_authenticate = AsyncMock(return_value=True)
    client.async_get_student_information = AsyncMock(return_value=mock_student_info)
    client.async_get_grades = AsyncMock(return_value=[
        {
            "subject": "Matematyka",
            "grade": "5",
            "date": "2025-09-15",
            "category": "Sprawdzian",
            "teacher": "Anna",
            "semester": 1,
            "type": "numeric",
        },
        {
            "subject": "Polski",
            "grade": "4+",
            "date": "2025-09-10",
            "category": "Kartkowka",
            "teacher": "Marek",
            "semester": 1,
            "type": "numeric",
        },
    ])
    client.async_get_messages = AsyncMock(return_value=[])
    client.async_get_schedule_events = AsyncMock(return_value=[])
    client.async_get_timetable_events = AsyncMock(return_value=[])
    return client


async def test_first_refresh_seeds_seen_sets(hass: HomeAssistant, fake_client):
    """Pierwszy refresh nie wysyla eventow, tylko zapamietuje stan."""
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client)
    fired_events: list[str] = []
    hass.bus.async_listen_once("librus_apix_nowa_ocena", lambda e: fired_events.append("ocena"))
    hass.bus.async_listen_once(
        "librus_apix_nowa_wiadomosc", lambda e: fired_events.append("wiadomosc")
    )

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Pierwszy run = seed only, nic nie poszlo na bus.
    assert fired_events == []
    # Ale dane sa: 2 oceny, 2 przedmioty.
    assert len(coordinator.data["grades"]) == 2
    assert "Matematyka" in coordinator.data["grades_by_subject"]
    assert "Polski" in coordinator.data["grades_by_subject"]


async def test_second_refresh_fires_event_for_new_grade(hass: HomeAssistant, fake_client):
    """Druga aktualizacja z nowa ocena emituje librus_apix_nowa_ocena."""
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Dorzuc nowa ocene do drugiego refresha.
    fake_client.async_get_grades = AsyncMock(return_value=[
        {
            "subject": "Matematyka",
            "grade": "5",
            "date": "2025-09-15",
            "category": "Sprawdzian",
            "teacher": "Anna",
            "semester": 1,
            "type": "numeric",
        },
        {
            "subject": "Polski",
            "grade": "4+",
            "date": "2025-09-10",
            "category": "Kartkowka",
            "teacher": "Marek",
            "semester": 1,
            "type": "numeric",
        },
        {
            "subject": "Historia",
            "grade": "6",
            "date": "2025-09-20",
            "category": "Kartkowka",
            "teacher": "Pawel",
            "semester": 1,
            "type": "numeric",
        },
    ])

    fired = []
    hass.bus.async_listen_once(
        "librus_apix_nowa_ocena",
        lambda e: fired.append(e.data),
    )

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(fired) == 1
    assert fired[0]["przedmiot"] == "Historia"
    assert fired[0]["ocena"] == "6"


async def test_grades_none_uses_cache(hass: HomeAssistant, fake_client):
    """Jesli kolejny fetch ocen zwroci None, koordynator uzywa cache zamiast fail."""
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.last_update_success is True

    fake_client.async_get_grades = AsyncMock(return_value=None)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Refresh sukces — cache podstawiony.
    assert coordinator.last_update_success is True
    assert len(coordinator.data["grades"]) == 2


async def test_first_refresh_fail_then_recovery(hass: HomeAssistant, fake_client):
    """Pierwszy refresh z grades=None i pustym cache → UpdateFailed."""
    fake_client.async_get_grades = AsyncMock(return_value=None)
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client)

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.last_update_success is False
