"""Tests for Librus maintenance mode detection and handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from librus_apix.exceptions import MaintananceError

from custom_components.librus_apix import LibrusApiClient, LibrusMaintenanceError


# ---------------------------------------------------------------------------
# LibrusApiClient.async_authenticate — unit tests
# ---------------------------------------------------------------------------


async def test_authenticate_raises_maintenance_on_503(mock_student_info) -> None:
    """MaintananceError from get_token() should raise LibrusMaintenanceError, not return False."""
    with (
        patch("custom_components.librus_apix.new_client") as mock_new_client,
        patch("custom_components.librus_apix.build_headers", return_value={}),
        patch("custom_components.librus_apix.pick_user_agent", return_value="ua"),
    ):
        fake_client = MagicMock()
        fake_client.get_token.side_effect = MaintananceError("maintenance")
        mock_new_client.return_value = fake_client

        api_client = LibrusApiClient(username="user", password="pass", humanize=False)
        with pytest.raises(LibrusMaintenanceError):
            await api_client.async_authenticate()


async def test_authenticate_returns_false_on_auth_error(mock_student_info) -> None:
    """AuthorizationError (wrong password) should return False, not raise."""
    from librus_apix.exceptions import AuthorizationError

    with (
        patch("custom_components.librus_apix.new_client") as mock_new_client,
        patch("custom_components.librus_apix.build_headers", return_value={}),
        patch("custom_components.librus_apix.pick_user_agent", return_value="ua"),
    ):
        fake_client = MagicMock()
        fake_client.get_token.side_effect = AuthorizationError("bad password")
        mock_new_client.return_value = fake_client

        api_client = LibrusApiClient(username="user", password="pass", humanize=False)
        result = await api_client.async_authenticate()
        assert result is False


# ---------------------------------------------------------------------------
# LibrusApiClient._with_retry — maintenance doesn't count as auth failure
# ---------------------------------------------------------------------------


async def test_with_retry_returns_none_on_maintenance_not_auth_failure() -> None:
    """_with_retry() should return None on maintenance, NOT raise LibrusAuthError."""
    from custom_components.librus_apix import LibrusAuthError

    with (
        patch("custom_components.librus_apix.build_headers", return_value={}),
        patch("custom_components.librus_apix.pick_user_agent", return_value="ua"),
    ):
        api_client = LibrusApiClient(username="user", password="pass", humanize=False)
        api_client.async_authenticate = AsyncMock(
            side_effect=LibrusMaintenanceError("maintenance")
        )

        result = await api_client._with_retry("test_label", lambda c: None)
        assert result is None  # transient, not auth failure


async def test_with_retry_raises_auth_error_on_repeated_auth_failure() -> None:
    """_with_retry() should still raise LibrusAuthError when password is wrong (not maintenance)."""
    from custom_components.librus_apix import LibrusAuthError

    with (
        patch("custom_components.librus_apix.build_headers", return_value={}),
        patch("custom_components.librus_apix.pick_user_agent", return_value="ua"),
    ):
        api_client = LibrusApiClient(username="user", password="pass", humanize=False)
        # async_authenticate returns False twice → auth failure
        api_client.async_authenticate = AsyncMock(return_value=False)

        with pytest.raises(LibrusAuthError):
            await api_client._with_retry("test_label", lambda c: None)


# ---------------------------------------------------------------------------
# Coordinator — _async_setup raises ConfigEntryNotReady on maintenance
# ---------------------------------------------------------------------------


async def test_setup_entry_not_ready_on_maintenance(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """ConfigEntryNotReady (not reauth flow) when Librus is in maintenance at startup."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.librus_apix.LibrusApiClient", autospec=True
    ) as client_cls:
        instance = client_cls.return_value
        instance.username = "test_user"
        instance.async_authenticate = AsyncMock(
            side_effect=LibrusMaintenanceError("Librus maintenance")
        )

        result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Entry must be in setup-retry state (HA will retry with backoff)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


# ---------------------------------------------------------------------------
# Coordinator — _async_update_data returns cache on maintenance
# ---------------------------------------------------------------------------


async def test_update_data_uses_cached_grades_when_fetch_returns_none(
    hass: HomeAssistant, mock_config_entry, mock_librus_client
) -> None:
    """When grades fetch returns None (maintenance), coordinator falls back to cached grades."""
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED

    coordinator = mock_config_entry.runtime_data.coordinator
    assert coordinator.data is not None
    original_grades = coordinator.data["grades"]

    # Simulate next refresh where grades fetch returns None (as _with_retry does on maintenance)
    mock_librus_client.async_get_grades = AsyncMock(return_value=None)

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Coordinator should still be loaded and grades preserved from previous data
    assert coordinator.data is not None
    assert coordinator.data["grades"] == original_grades


async def test_update_data_maintenance_exception_falls_back_to_cache(
    hass: HomeAssistant, mock_config_entry, mock_librus_client
) -> None:
    """LibrusMaintenanceError at _async_update_data level returns cached data (defensive handler)."""
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED

    coordinator = mock_config_entry.runtime_data.coordinator
    original_data = dict(coordinator.data)

    # Simulate LibrusMaintenanceError bubbling directly to _async_update_data
    # (defensive scenario — not the normal path, but the handler should work)
    from custom_components.librus_apix import LibrusMaintenanceError as _LME

    mock_librus_client.async_get_grades = AsyncMock(side_effect=_LME("maintenance"))

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Coordinator must remain loaded, not trigger auth error
    assert mock_config_entry.state is ConfigEntryState.LOADED
    # Data preserved from cache
    assert coordinator.data is not None
