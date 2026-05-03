"""Tests for the Librus APIX config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.librus_apix.const import DOMAIN


@pytest.fixture
def mock_validate_input():
    """Patch validate_input AND LibrusApiClient — config flow create entry
    triggers async_setup_entry which would otherwise hit the network.
    """
    with (
        patch(
            "custom_components.librus_apix.config_flow.validate_input",
            new=AsyncMock(return_value={"title": "Librus APIX (test_user)"}),
        ) as m,
        patch(
            "custom_components.librus_apix.LibrusApiClient", autospec=True
        ) as client_cls,
    ):
        instance = client_cls.return_value
        instance.username = "test_user"
        instance.async_authenticate = AsyncMock(return_value=True)
        instance.async_get_student_information = AsyncMock(return_value=None)
        instance.async_get_grades = AsyncMock(return_value=[])
        instance.async_get_messages = AsyncMock(return_value=[])
        instance.async_get_schedule_events = AsyncMock(return_value=[])
        instance.async_get_timetable_events = AsyncMock(return_value=[])
        yield m


async def test_user_step_happy_path(hass: HomeAssistant, mock_validate_input):
    """Form → submit → entry created."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "secret"},
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Librus APIX (test_user)"
    assert result2["data"] == {CONF_USERNAME: "test_user", CONF_PASSWORD: "secret"}


async def test_user_step_invalid_auth(hass: HomeAssistant):
    """validate_input rzuca ValueError → form with cannot_connect error."""
    with patch(
        "custom_components.librus_apix.config_flow.validate_input",
        new=AsyncMock(side_effect=ValueError("Cannot connect")),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "test_user", CONF_PASSWORD: "wrong"},
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_user_step_already_configured(
    hass: HomeAssistant, mock_validate_input
):
    """Adding the same login twice aborts on already_configured."""
    existing = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: "test_user", CONF_PASSWORD: "x"},
        unique_id="test_user",
    )
    existing.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "secret"},
    )
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


async def test_user_step_unique_id_lowercase(
    hass: HomeAssistant, mock_validate_input
):
    """unique_id is normalized to lowercase to be case-insensitive."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "Test_User", CONF_PASSWORD: "secret"},
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    # Unique id stored on the entry should be lowercased.
    entries = hass.config_entries.async_entries(DOMAIN)
    assert entries[0].unique_id == "test_user"
