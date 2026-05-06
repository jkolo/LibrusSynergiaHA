"""Tests for persistent_notification opt-in (OPT_MESSAGE_NOTIFY)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.components.persistent_notification import (
    _async_get_or_create_notifications,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.librus_apix.const import DOMAIN, OPT_MESSAGE_NOTIFY


def _librus_notifications(hass: HomeAssistant) -> dict:
    """Return only librus_apix notifications from the PN store."""
    return {
        k: v
        for k, v in _async_get_or_create_notifications(hass).items()
        if "librus_apix" in k
    }

_MSG = {
    "author": "Wychowawca",
    "title": "Zebranie rodziców",
    "date": "2025-11-01",
    "href": "111",
    "unread": True,
    "has_attachment": False,
}


@pytest.fixture
async def entry_notify_on(hass: HomeAssistant, mock_config_entry, mock_librus_client):
    """Setup integration with OPT_MESSAGE_NOTIFY=True and one message."""
    mock_librus_client.async_get_messages = AsyncMock(return_value=[])
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, options={OPT_MESSAGE_NOTIFY: True}
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    return mock_config_entry


@pytest.fixture
async def entry_notify_off(hass: HomeAssistant, mock_config_entry, mock_librus_client):
    """Setup integration with OPT_MESSAGE_NOTIFY=False (default)."""
    mock_librus_client.async_get_messages = AsyncMock(return_value=[])
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    return mock_config_entry


async def test_notify_on_new_message_creates_notification(
    hass: HomeAssistant, entry_notify_on, mock_librus_client
):
    """With OPT_MESSAGE_NOTIFY=True, a new message creates a persistent_notification."""
    coordinator = entry_notify_on.runtime_data.coordinator

    mock_librus_client.async_get_messages = AsyncMock(return_value=[dict(_MSG)])
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(_librus_notifications(hass)) == 1


async def test_notify_off_no_notification(
    hass: HomeAssistant, entry_notify_off, mock_librus_client
):
    """With OPT_MESSAGE_NOTIFY=False, a new message does NOT create a notification."""
    coordinator = entry_notify_off.runtime_data.coordinator

    mock_librus_client.async_get_messages = AsyncMock(return_value=[dict(_MSG)])
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(_librus_notifications(hass)) == 0


async def test_notify_deduplication(
    hass: HomeAssistant, entry_notify_on, mock_librus_client
):
    """Second refresh with same message does not create a second notification."""
    coordinator = entry_notify_on.runtime_data.coordinator

    mock_librus_client.async_get_messages = AsyncMock(return_value=[dict(_MSG)])
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    count_after_first = len(_librus_notifications(hass))

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(_librus_notifications(hass)) == count_after_first


async def test_mark_read_dismisses_notification(
    hass: HomeAssistant, entry_notify_on, mock_librus_client
):
    """mark_message_read service auto-dismisses the notification for that href."""
    coordinator = entry_notify_on.runtime_data.coordinator

    mock_librus_client.async_get_messages = AsyncMock(return_value=[dict(_MSG)])
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(_librus_notifications(hass)) == 1

    await hass.services.async_call(
        DOMAIN, "dismiss_message_notification",
        {"entry": entry_notify_on.entry_id, "message_href": "111"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(_librus_notifications(hass)) == 0


async def test_first_run_no_notification(
    hass: HomeAssistant, mock_config_entry, mock_librus_client
):
    """First run (initial=True) does NOT create notifications even with notify=True."""
    mock_librus_client.async_get_messages = AsyncMock(return_value=[dict(_MSG)])
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, options={OPT_MESSAGE_NOTIFY: True}
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert len(_librus_notifications(hass)) == 0
