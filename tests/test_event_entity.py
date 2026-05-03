"""Tests for the new event entity platform (PR 4)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.librus_apix.const import DOMAIN
from custom_components.librus_apix.coordinator import LibrusDataUpdateCoordinator


# ---------------------------------------------------------------------------
# Coordinator pending-events queue
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "test_user", "password": "p"},
        unique_id="test_user",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def fake_client_with_messages(mock_student_info):
    client = MagicMock()
    client.username = "test_user"
    client.async_authenticate = AsyncMock(return_value=True)
    client.async_get_student_information = AsyncMock(return_value=mock_student_info)
    client.async_get_grades = AsyncMock(return_value=[])
    client.async_get_messages = AsyncMock(return_value=[])
    client.async_get_schedule_events = AsyncMock(return_value=[])
    client.async_get_timetable_events = AsyncMock(return_value=[])
    client.async_get_attendance = AsyncMock(return_value=[])
    client.async_get_announcements = AsyncMock(return_value=[])
    return client


async def test_consume_pending_event_returns_none_when_empty(
    hass: HomeAssistant, fake_client_with_messages
):
    """Bez pending eventow, consume zwraca None."""
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client_with_messages)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.consume_pending_event("new_message") is None


async def test_new_message_creates_pending_event_and_consume_clears_it(
    hass: HomeAssistant, fake_client_with_messages
):
    """Druga sync z nowa wiadomoscia → consume_pending_event('new_message')
    zwraca payload, kolejne wywolanie zwraca None."""
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client_with_messages)
    # 1st refresh: seed only.
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # 2nd refresh: new message.
    fake_client_with_messages.async_get_messages = AsyncMock(return_value=[
        {"author": "Anna", "title": "Wycieczka", "date": "2026-04-15",
         "href": "/m/1", "unread": True, "has_attachment": False},
    ])
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    payload = coordinator.consume_pending_event("new_message")
    assert payload is not None
    assert payload["sender"] == "Anna"
    assert payload["title"] == "Wycieczka"
    assert payload["date"] == "2026-04-15"
    assert payload["has_attachment"] is False

    # Konsumpcja czysci kolejke.
    assert coordinator.consume_pending_event("new_message") is None


async def test_new_grade_creates_pending_event(
    hass: HomeAssistant, fake_client_with_messages
):
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client_with_messages)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    fake_client_with_messages.async_get_grades = AsyncMock(return_value=[
        {"subject": "Mat", "grade": "5", "value": 5.0, "counts": True,
         "weight": 3, "date": "2026-04-15", "category": "Sprawdzian",
         "description": "", "title": "", "teacher": "Anna",
         "semester": 2, "type": "numeric"},
    ])
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    payload = coordinator.consume_pending_event("new_grade")
    assert payload is not None
    assert payload["subject"] == "Mat"
    assert payload["grade"] == "5"
    assert payload["category"] == "Sprawdzian"


# ---------------------------------------------------------------------------
# Event entity
# ---------------------------------------------------------------------------


async def test_event_entities_exist_after_setup(
    hass: HomeAssistant, mock_librus_client, mock_config_entry
):
    """Po setup integracji w entity_registry istnieje 5 event entities,
    po jednym dla kazdego klucza (new_grade/_message/_exam/_announcement/_absence)."""
    from homeassistant.helpers import entity_registry as er

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expected_keys = (
        "new_grade", "new_message", "new_exam",
        "new_announcement", "new_absence",
    )
    registry = er.async_get(hass)
    event_entries = [
        entry for entry in registry.entities.values()
        if entry.domain == "event" and entry.config_entry_id == mock_config_entry.entry_id
    ]
    unique_ids = {entry.unique_id for entry in event_entries}
    for key in expected_keys:
        expected_uid = f"{mock_config_entry.entry_id}_{key}"
        assert expected_uid in unique_ids, (
            f"event entity z unique_id={expected_uid} powinno istniec po setup"
        )
    assert len(event_entries) == 5


# ---------------------------------------------------------------------------
# Bus events removed (BREAKING)
# ---------------------------------------------------------------------------


async def test_no_bus_events_fired_on_new_message(
    hass: HomeAssistant, fake_client_with_messages
):
    """v3 BREAKING: stary `librus_apix_new_message` bus event NIE leci.

    Migracja: automation triggeruje sie po state event entity, nie po bus.
    """
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client_with_messages)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    fired: list = []
    hass.bus.async_listen("librus_apix_new_message", lambda e: fired.append(e))

    fake_client_with_messages.async_get_messages = AsyncMock(return_value=[
        {"author": "Anna", "title": "Wycieczka", "date": "2026-04-15",
         "href": "/m/1", "unread": True, "has_attachment": False},
    ])
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert fired == []
