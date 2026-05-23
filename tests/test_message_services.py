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
    """mark_message_read sets notification_dismissed=True on the message and in the store."""
    coordinator = loaded_entry.runtime_data.coordinator
    entry_id = loaded_entry.entry_id

    await hass.services.async_call(
        DOMAIN, "dismiss_message_notification",
        {"entry": entry_id, "message_href": "111"},
        blocking=True,
    )

    assert coordinator.read_messages_store.is_read("111")
    msgs = coordinator.data["messages"]
    msg_111 = next(m for m in msgs if m["href"] == "111")
    assert msg_111["notification_dismissed"] is True
    # Other message unchanged
    msg_222 = next(m for m in msgs if m["href"] == "222")
    assert msg_222["notification_dismissed"] is False


async def test_mark_message_read_unknown_href_raises(hass: HomeAssistant, loaded_entry):
    """mark_message_read with unknown href raises ServiceValidationError."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "dismiss_message_notification",
            {"entry": loaded_entry.entry_id, "message_href": "nonexistent"},
            blocking=True,
        )


async def test_mark_message_unread(hass: HomeAssistant, loaded_entry):
    """mark_message_unread removes the notification_dismissed flag."""
    coordinator = loaded_entry.runtime_data.coordinator
    entry_id = loaded_entry.entry_id

    # First mark as read
    await hass.services.async_call(
        DOMAIN, "dismiss_message_notification",
        {"entry": entry_id, "message_href": "111"},
        blocking=True,
    )
    assert coordinator.read_messages_store.is_read("111")

    # Now unread it
    await hass.services.async_call(
        DOMAIN, "restore_message_notification",
        {"entry": entry_id, "message_href": "111"},
        blocking=True,
    )
    assert not coordinator.read_messages_store.is_read("111")
    msgs = coordinator.data["messages"]
    msg_111 = next(m for m in msgs if m["href"] == "111")
    assert msg_111["notification_dismissed"] is False


async def test_mark_message_unread_unknown_href_raises(hass: HomeAssistant, loaded_entry):
    """mark_message_unread with unknown href raises ServiceValidationError."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "restore_message_notification",
            {"entry": loaded_entry.entry_id, "message_href": "nonexistent"},
            blocking=True,
        )


async def test_clear_read_messages(hass: HomeAssistant, loaded_entry):
    """clear_read_messages removes all local read flags."""
    coordinator = loaded_entry.runtime_data.coordinator
    entry_id = loaded_entry.entry_id

    # Mark both as read
    await hass.services.async_call(
        DOMAIN, "dismiss_message_notification",
        {"entry": entry_id, "message_href": "111"},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN, "dismiss_message_notification",
        {"entry": entry_id, "message_href": "222"},
        blocking=True,
    )
    assert coordinator.read_messages_store.is_read("111")
    assert coordinator.read_messages_store.is_read("222")

    # Clear all
    await hass.services.async_call(
        DOMAIN, "clear_dismissed_notifications",
        {"entry": entry_id},
        blocking=True,
    )
    assert not coordinator.read_messages_store.is_read("111")
    assert not coordinator.read_messages_store.is_read("222")
    msgs = coordinator.data["messages"]
    for m in msgs:
        assert m["notification_dismissed"] is False


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
        DOMAIN, "dismiss_message_notification",
        {"entry": entry_a.entry_id, "message_href": "111"},
        blocking=True,
    )

    assert coord_a.read_messages_store.is_read("111")
    assert not coord_b.read_messages_store.is_read("111")


# ---------------------------------------------------------------------------
# list_messages service
# ---------------------------------------------------------------------------

def _make_messages(n: int) -> list[dict]:
    """Build n fake annotated messages (author/title/date/href/unread/...)."""
    return [
        {
            "author": f"Nadawca{i}",
            "title": f"Temat{i}",
            "date": "2025-11-01",
            "href": str(i),
            "unread": i % 2 == 0,
            "has_attachment": False,
            "is_recent": False,
            "notification_dismissed": False,
        }
        for i in range(n)
    ]


@pytest.fixture
async def loaded_entry_25(hass: HomeAssistant, mock_config_entry, mock_librus_client):
    """Setup integration with 25 mock messages in coordinator.data."""
    mock_librus_client.async_get_messages = AsyncMock(
        return_value=_make_messages(25)
    )
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    return mock_config_entry


async def test_list_messages_first_page(hass: HomeAssistant, loaded_entry_25):
    """list_messages returns first page with has_more=True."""
    result = await hass.services.async_call(
        DOMAIN, "list_messages",
        {"entry": loaded_entry_25.entry_id, "offset": 0, "count": 10},
        blocking=True,
        return_response=True,
    )

    assert result is not None
    assert len(result["messages"]) == 10
    assert result["has_more"] is True
    assert result["total_count"] == 25
    assert result["messages"][0]["sender"] == "Nadawca0"
    assert result["messages"][9]["sender"] == "Nadawca9"


async def test_list_messages_last_page(hass: HomeAssistant, loaded_entry_25):
    """list_messages returns remaining messages with has_more=False."""
    result = await hass.services.async_call(
        DOMAIN, "list_messages",
        {"entry": loaded_entry_25.entry_id, "offset": 20, "count": 10},
        blocking=True,
        return_response=True,
    )

    assert result is not None
    assert len(result["messages"]) == 5
    assert result["has_more"] is False
    assert result["total_count"] == 25


async def test_list_messages_maps_fields(hass: HomeAssistant, loaded_entry_25):
    """list_messages maps coordinator 'author' → frontend 'sender'."""
    result = await hass.services.async_call(
        DOMAIN, "list_messages",
        {"entry": loaded_entry_25.entry_id, "offset": 0, "count": 1},
        blocking=True,
        return_response=True,
    )

    msg = result["messages"][0]
    assert "sender" in msg
    assert "author" not in msg
    assert msg["href"] == "0"


async def test_list_messages_no_librus_call(hass: HomeAssistant, loaded_entry_25, mock_librus_client):
    """list_messages reads from coordinator cache — does NOT call async_get_messages."""
    mock_librus_client.async_get_messages.reset_mock()

    await hass.services.async_call(
        DOMAIN, "list_messages",
        {"entry": loaded_entry_25.entry_id, "offset": 0, "count": 10},
        blocking=True,
        return_response=True,
    )

    mock_librus_client.async_get_messages.assert_not_called()
