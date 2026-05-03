"""Test setup/unload of the Librus APIX integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant


async def test_setup_and_unload(hass: HomeAssistant, mock_config_entry, mock_librus_client):
    """Happy path: setup creates entities, unload removes them cleanly."""
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED

    # runtime_data should be populated and contain our coordinator + client.
    assert mock_config_entry.runtime_data is not None
    assert mock_config_entry.runtime_data.client is mock_librus_client

    # Unload — runtime_data is cleaned by HA, state becomes NOT_LOADED.
    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_retries_on_auth_failure(hass: HomeAssistant, mock_config_entry):
    """Auth fail → coordinator raises ConfigEntryNotReady, state SETUP_RETRY."""
    from unittest.mock import AsyncMock, patch

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.librus_apix.LibrusApiClient", autospec=True
    ) as client_cls:
        instance = client_cls.return_value
        instance.username = "test_user"
        instance.async_authenticate = AsyncMock(return_value=False)

        result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # async_setup returns False when ConfigEntryNotReady is raised internally.
    assert result is False
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
