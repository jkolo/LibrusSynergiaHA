"""Test setup/unload of the Librus APIX integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from librus_apix.student_information import StudentInformation

from custom_components.librus_apix._data_store import LibrusDataStore


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


async def test_setup_uses_cache_skips_first_refresh(
    hass: HomeAssistant, mock_config_entry, mock_librus_client
) -> None:
    """Gdy cache istnieje, first_refresh nie jest wywoływany — integracja startuje z danymi z cache."""
    cached_data = {
        "student_info": StudentInformation(
            name="Jan Kowalski", class_name="5A", number=12,
            tutor="Anna Nowak", school="SP 1", lucky_number=7,
        ),
        "grades": [],
        "messages": [],
        "grades_by_subject": {},
        "upcoming_exams": [],
        "schedule": [],
        "timetable": [],
        "attendance": [],
        "attendance_frequency": {},
        "attendance_by_subject": {},
        "announcements": [],
        "current_semester": 1,
    }
    saved_at = dt_util.utcnow()

    with patch(
        "custom_components.librus_apix.LibrusDataStore",
        autospec=True,
    ) as store_cls:
        store_instance = store_cls.return_value
        store_instance.async_load = AsyncMock(return_value=(cached_data, saved_at))
        store_instance.async_save = AsyncMock()

        mock_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED

    # first_refresh nie powinien być wywołany (coordinator.data pochodzi z cache)
    coordinator = mock_config_entry.runtime_data.coordinator
    assert coordinator.data is cached_data
    # _first_run powinno być False (seed already done from cache)
    assert coordinator._first_run is False
