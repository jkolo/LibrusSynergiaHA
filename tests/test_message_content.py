"""Tests for fetch_message_content (attachments) and download_attachment service."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import ServiceValidationError

from custom_components.librus_apix.const import DOMAIN

_MSG = {
    "author": "Pan Kowalski",
    "title": "Zebranie",
    "date": "2025-11-01",
    "href": "111",
    "unread": True,
    "has_attachment": True,
}


@pytest.fixture
async def loaded_entry(hass: object, mock_config_entry, mock_librus_client):
    mock_librus_client.async_get_messages = AsyncMock(return_value=[_MSG])
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    return mock_config_entry


# ---------------------------------------------------------------------------
# fetch_message_content — attachments field
# ---------------------------------------------------------------------------

async def test_fetch_content_passes_attachments(hass, loaded_entry, mock_librus_client):
    """fetch_message_content passes attachments list from client to service response."""
    mock_librus_client.async_get_message_content = AsyncMock(return_value={
        "author": "Pan Kowalski",
        "title": "Zebranie",
        "date": "2025-11-01",
        "content": "<p>Treść</p>",
        "attachments": [
            {"name": "protokol.pdf", "url": "/wiadomosci/1/5/111/pobierz/777"},
            {"name": "agenda.docx", "url": "/wiadomosci/1/5/111/pobierz/888"},
        ],
    })

    result = await hass.services.async_call(
        DOMAIN, "fetch_message_content",
        {"entry": loaded_entry.entry_id, "message_href": "111"},
        blocking=True,
        return_response=True,
    )

    assert result is not None
    assert "attachments" in result
    assert len(result["attachments"]) == 2
    assert result["attachments"][0]["name"] == "protokol.pdf"
    assert result["attachments"][0]["url"] == "/wiadomosci/1/5/111/pobierz/777"
    assert result["attachments"][1]["name"] == "agenda.docx"


async def test_fetch_content_empty_attachments(hass, loaded_entry, mock_librus_client):
    """fetch_message_content returns empty attachments list when no attachments."""
    mock_librus_client.async_get_message_content = AsyncMock(return_value={
        "author": "Pan Kowalski",
        "title": "Zebranie",
        "date": "2025-11-01",
        "content": "<p>Treść.</p>",
        "attachments": [],
    })

    result = await hass.services.async_call(
        DOMAIN, "fetch_message_content",
        {"entry": loaded_entry.entry_id, "message_href": "111"},
        blocking=True,
        return_response=True,
    )

    assert result["attachments"] == []


async def test_fetch_content_missing_attachments_key_defaults_empty(
    hass, loaded_entry, mock_librus_client
):
    """fetch_message_content is robust when client omits 'attachments' key."""
    mock_librus_client.async_get_message_content = AsyncMock(return_value={
        "author": "Pan Kowalski",
        "title": "Zebranie",
        "date": "2025-11-01",
        "content": "<p>Treść.</p>",
        # no 'attachments' key — legacy client behaviour
    })

    result = await hass.services.async_call(
        DOMAIN, "fetch_message_content",
        {"entry": loaded_entry.entry_id, "message_href": "111"},
        blocking=True,
        return_response=True,
    )

    assert "attachments" in result
    assert result["attachments"] == []


# ---------------------------------------------------------------------------
# download_attachment service
# ---------------------------------------------------------------------------

async def test_download_attachment_returns_base64(hass, loaded_entry, mock_librus_client):
    """download_attachment returns filename, content_type, and base64 data."""
    mock_librus_client.async_download_attachment = AsyncMock(return_value={
        "filename": "protokol.pdf",
        "content_type": "application/pdf",
        "data": "JVBERi0xLjQ=",
    })

    result = await hass.services.async_call(
        DOMAIN, "download_attachment",
        {
            "entry": loaded_entry.entry_id,
            "attachment_url": "/wiadomosci/1/5/111/pobierz/777",
        },
        blocking=True,
        return_response=True,
    )

    assert result is not None
    assert result["filename"] == "protokol.pdf"
    assert result["content_type"] == "application/pdf"
    assert result["data"] == "JVBERi0xLjQ="
    mock_librus_client.async_download_attachment.assert_called_once_with(
        "/wiadomosci/1/5/111/pobierz/777"
    )


async def test_download_attachment_client_failure_raises(
    hass, loaded_entry, mock_librus_client
):
    """download_attachment raises ServiceValidationError when client returns None."""
    mock_librus_client.async_download_attachment = AsyncMock(return_value=None)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "download_attachment",
            {
                "entry": loaded_entry.entry_id,
                "attachment_url": "/wiadomosci/1/5/111/pobierz/999",
            },
            blocking=True,
            return_response=True,
        )


async def test_download_attachment_unknown_entry_raises(hass, loaded_entry):
    """download_attachment raises ServiceValidationError for unknown entry_id."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "download_attachment",
            {
                "entry": "nonexistent-entry-id",
                "attachment_url": "/some/url",
            },
            blocking=True,
            return_response=True,
        )
