"""Tests for mark_message_read / mark_message_unread / clear_read_messages services."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from custom_components.librus_apix.const import DOMAIN

_MESSAGES = [
    {
        "author": "Wychowawca",
        "title": "Zebranie",
        "date": "2025-11-01",
        "href": "111",
        "unread": True,
        "has_attachment": False,
    },
    {
        "author": "Dyrektor",
        "title": "Komunikat",
        "date": "2025-11-02",
        "href": "222",
        "unread": True,
        "has_attachment": False,
    },
]


@pytest.fixture
async def loaded_entry(hass: HomeAssistant, mock_config_entry, mock_librus_client):
    """Setup integration with two mock messages and return the loaded config entry."""
    mock_librus_client.async_get_messages = AsyncMock(return_value=list(_MESSAGES))
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    return mock_config_entry


async def test_mark_message_read_sets_flag(hass: HomeAssistant, loaded_entry):
    """mark_message_read sets is_read_in_ha=True on the message and in the store."""
    coordinator = loaded_entry.runtime_data.coordinator
    entry_id = loaded_entry.entry_id

    await hass.services.async_call(
        DOMAIN, "mark_message_read",
        {"entry": entry_id, "message_href": "111"},
        blocking=True,
    )

    assert coordinator.read_messages_store.is_read("111")
    msgs = coordinator.data["messages"]
    msg_111 = next(m for m in msgs if m["href"] == "111")
    assert msg_111["is_read_in_ha"] is True
    # Other message unchanged
    msg_222 = next(m for m in msgs if m["href"] == "222")
    assert msg_222["is_read_in_ha"] is False


async def test_mark_message_read_unknown_href_raises(hass: HomeAssistant, loaded_entry):
    """mark_message_read with unknown href raises ServiceValidationError."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "mark_message_read",
            {"entry": loaded_entry.entry_id, "message_href": "nonexistent"},
            blocking=True,
        )


async def test_mark_message_unread(hass: HomeAssistant, loaded_entry):
    """mark_message_unread removes the is_read_in_ha flag."""
    coordinator = loaded_entry.runtime_data.coordinator
    entry_id = loaded_entry.entry_id

    # First mark as read
    await hass.services.async_call(
        DOMAIN, "mark_message_read",
        {"entry": entry_id, "message_href": "111"},
        blocking=True,
    )
    assert coordinator.read_messages_store.is_read("111")

    # Now unread it
    await hass.services.async_call(
        DOMAIN, "mark_message_unread",
        {"entry": entry_id, "message_href": "111"},
        blocking=True,
    )
    assert not coordinator.read_messages_store.is_read("111")
    msgs = coordinator.data["messages"]
    msg_111 = next(m for m in msgs if m["href"] == "111")
    assert msg_111["is_read_in_ha"] is False


async def test_mark_message_unread_unknown_href_raises(hass: HomeAssistant, loaded_entry):
    """mark_message_unread with unknown href raises ServiceValidationError."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "mark_message_unread",
            {"entry": loaded_entry.entry_id, "message_href": "nonexistent"},
            blocking=True,
        )


async def test_clear_read_messages(hass: HomeAssistant, loaded_entry):
    """clear_read_messages removes all local read flags."""
    coordinator = loaded_entry.runtime_data.coordinator
    entry_id = loaded_entry.entry_id

    # Mark both as read
    await hass.services.async_call(
        DOMAIN, "mark_message_read",
        {"entry": entry_id, "message_href": "111"},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN, "mark_message_read",
        {"entry": entry_id, "message_href": "222"},
        blocking=True,
    )
    assert coordinator.read_messages_store.is_read("111")
    assert coordinator.read_messages_store.is_read("222")

    # Clear all
    await hass.services.async_call(
        DOMAIN, "clear_read_messages",
        {"entry": entry_id},
        blocking=True,
    )
    assert not coordinator.read_messages_store.is_read("111")
    assert not coordinator.read_messages_store.is_read("222")
    msgs = coordinator.data["messages"]
    for m in msgs:
        assert m["is_read_in_ha"] is False


async def test_services_multi_entry_routing(
    hass: HomeAssistant, mock_librus_client
):
    """Services route calls to the correct coordinator per entry_id."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    mock_librus_client.async_get_messages = AsyncMock(return_value=list(_MESSAGES))

    entry_a = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "user_a", "password": "pass"},
        unique_id="user_a",
    )
    entry_b = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "user_b", "password": "pass"},
        unique_id="user_b",
    )
    entry_a.add_to_hass(hass)
    entry_b.add_to_hass(hass)
    # HA loads all domain entries when the integration is first set up,
    # so a single async_setup call is enough to load both entries.
    await hass.config_entries.async_setup(entry_a.entry_id)
    await hass.async_block_till_done()
    assert entry_a.state is ConfigEntryState.LOADED
    assert entry_b.state is ConfigEntryState.LOADED

    coord_a = entry_a.runtime_data.coordinator
    coord_b = entry_b.runtime_data.coordinator

    await hass.services.async_call(
        DOMAIN, "mark_message_read",
        {"entry": entry_a.entry_id, "message_href": "111"},
        blocking=True,
    )

    assert coord_a.read_messages_store.is_read("111")
    assert not coord_b.read_messages_store.is_read("111")
