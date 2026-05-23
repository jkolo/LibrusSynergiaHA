"""Tests for initial: bool flag in librus_apix_nowa_wiadomosc bus event."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.librus_apix.const import EVENT_NOWA_WIADOMOSC
from custom_components.librus_apix.coordinator import (
    EVENT_KEY_NEW_MESSAGE,
    LibrusDataUpdateCoordinator,
)

_MSG = {
    "author": "Wychowawca",
    "title": "Zebranie",
    "date": "2025-11-01",
    "href": "111",
    "unread": True,
    "has_attachment": False,
}


@pytest.fixture
def coord_client(mock_student_info):
    from unittest.mock import MagicMock
    client = MagicMock()
    client.username = "test_user"
    client.async_authenticate = AsyncMock(return_value=True)
    client.async_get_student_information = AsyncMock(return_value=mock_student_info)
    client.async_get_grades = AsyncMock(return_value=[
        {"subject": "Mat", "grade": "5", "date": "2025-09-15",
         "category": "Sprawdzian", "teacher": "A", "semester": 1, "type": "numeric"},
    ])
    client.async_get_messages = AsyncMock(return_value=[dict(_MSG)])
    client.async_get_schedule_events = AsyncMock(return_value=[])
    client.async_get_timetable_events = AsyncMock(return_value=[])
    client.async_get_attendance = AsyncMock(return_value=[])
    client.async_get_announcements = AsyncMock(return_value=[])
    return client


async def test_first_run_fires_bus_event_with_initial_true(
    hass: HomeAssistant, coord_client
):
    """First refresh fires EVENT_NOWA_WIADOMOSC with initial=True for every message."""
    coordinator = LibrusDataUpdateCoordinator(hass, coord_client)

    received = []
    hass.bus.async_listen(EVENT_NOWA_WIADOMOSC, lambda e: received.append(e.data))

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(received) == 1
    assert received[0]["initial"] is True
    assert received[0]["href"] == "111"
    assert received[0]["sender"] == "Wychowawca"


async def test_first_run_does_not_add_to_pending_events(
    hass: HomeAssistant, coord_client
):
    """First run emits bus event but does NOT enqueue into _pending_events."""
    coordinator = LibrusDataUpdateCoordinator(hass, coord_client)

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.consume_pending_event(EVENT_KEY_NEW_MESSAGE) is None


async def test_second_run_new_message_fires_bus_event_with_initial_false(
    hass: HomeAssistant, coord_client
):
    """Second refresh with a new message fires EVENT_NOWA_WIADOMOSC initial=False."""
    coord_client.async_get_messages = AsyncMock(return_value=[])
    coordinator = LibrusDataUpdateCoordinator(hass, coord_client)

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    received = []
    hass.bus.async_listen(EVENT_NOWA_WIADOMOSC, lambda e: received.append(e.data))

    coord_client.async_get_messages = AsyncMock(return_value=[dict(_MSG)])
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(received) == 1
    assert received[0]["initial"] is False
    assert received[0]["href"] == "111"


async def test_second_run_pending_event_payload_has_href_and_initial(
    hass: HomeAssistant, coord_client
):
    """Second-run pending event payload includes href and initial=False."""
    coord_client.async_get_messages = AsyncMock(return_value=[])
    coordinator = LibrusDataUpdateCoordinator(hass, coord_client)

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    coord_client.async_get_messages = AsyncMock(return_value=[dict(_MSG)])
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    payload = coordinator.consume_pending_event(EVENT_KEY_NEW_MESSAGE)
    assert payload is not None
    assert payload["href"] == "111"
    assert payload["initial"] is False
