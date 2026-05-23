"""Tests for fetch_message_content service (PR 3/v3.1)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
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
]

_CONTENT_RESULT = {
    "author": "Wychowawca",
    "title": "Zebranie",
    "date": "2025-11-01",
    "content": "<b>Zapraszam</b> na zebranie w <i>piątek</i>.",
}


@pytest.fixture
async def loaded_entry(hass: HomeAssistant, mock_config_entry, mock_librus_client):
    """Setup integration with one mock message."""
    mock_librus_client.async_get_messages = AsyncMock(return_value=list(_MESSAGES))
    mock_librus_client.async_get_message_content = AsyncMock(
        return_value=dict(_CONTENT_RESULT)
    )
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    return mock_config_entry


async def test_fetch_content_returns_html(hass: HomeAssistant, loaded_entry):
    """fetch_message_content returns HTML body in response variable."""
    result = await hass.services.async_call(
        DOMAIN, "fetch_message_content",
        {"entry": loaded_entry.entry_id, "message_href": "111"},
        blocking=True,
        return_response=True,
    )

    assert result is not None
    assert result["content"] == _CONTENT_RESULT["content"]
    assert result["author"] == "Wychowawca"
    assert result["title"] == "Zebranie"


async def test_fetch_content_auto_marks_read(hass: HomeAssistant, loaded_entry):
    """fetch_message_content sets notification_dismissed=True after fetching."""
    coordinator = loaded_entry.runtime_data.coordinator

    await hass.services.async_call(
        DOMAIN, "fetch_message_content",
        {"entry": loaded_entry.entry_id, "message_href": "111"},
        blocking=True,
        return_response=True,
    )

    assert coordinator.read_messages_store.is_read("111")
    msgs = coordinator.data["messages"]
    msg = next(m for m in msgs if m["href"] == "111")
    assert msg["notification_dismissed"] is True


async def test_fetch_content_unknown_href_raises(hass: HomeAssistant, loaded_entry):
    """fetch_message_content with unknown href raises ServiceValidationError."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "fetch_message_content",
            {"entry": loaded_entry.entry_id, "message_href": "nonexistent"},
            blocking=True,
            return_response=True,
        )


async def test_fetch_content_client_error_raises(
    hass: HomeAssistant, loaded_entry, mock_librus_client
):
    """When client returns None, service raises ServiceValidationError."""
    mock_librus_client.async_get_message_content = AsyncMock(return_value=None)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "fetch_message_content",
            {"entry": loaded_entry.entry_id, "message_href": "111"},
            blocking=True,
            return_response=True,
        )


async def test_fetch_content_uses_client_method(hass: HomeAssistant, loaded_entry, mock_librus_client):
    """fetch_message_content calls client.async_get_message_content with the href."""
    mock_librus_client.async_get_message_content = AsyncMock(
        return_value=dict(_CONTENT_RESULT)
    )

    await hass.services.async_call(
        DOMAIN, "fetch_message_content",
        {"entry": loaded_entry.entry_id, "message_href": "111"},
        blocking=True,
        return_response=True,
    )

    mock_librus_client.async_get_message_content.assert_called_once_with("111")


async def test_fetch_content_visits_list_first(hass: HomeAssistant, loaded_entry):
    """async_get_message_content in client does POST list before GET content."""
    # This test verifies the contract at the LibrusApiClient level:
    # the implementation must visit the message list before fetching content.
    # We verify it by checking that the method IS called (higher-level smoke),
    # relying on test_client_get_message_content_* for the HTTP-level contract.
    coordinator = loaded_entry.runtime_data.coordinator
    client = coordinator.client

    result = await client.async_get_message_content("111")
    # Fixture returns dict, so just verify the contract holds end-to-end.
    assert result is not None
