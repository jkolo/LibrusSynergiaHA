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


async def test_reauth_flow_happy_path(hass: HomeAssistant, mock_validate_input):
    """Reauth: user provides new password → entry updated, abort reauth_successful."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: "test_user", CONF_PASSWORD: "old_password"},
        unique_id="test_user",
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new_password"}
    )
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert entry.data[CONF_PASSWORD] == "new_password"


async def test_reauth_flow_invalid_credentials(hass: HomeAssistant):
    """Reauth: validate_input raises → form re-shown with cannot_connect."""
    from unittest.mock import AsyncMock, patch

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: "test_user", CONF_PASSWORD: "old"},
        unique_id="test_user",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.librus_apix.config_flow.validate_input",
        new=AsyncMock(side_effect=ValueError("nope")),
    ):
        result = await entry.start_reauth_flow(hass)
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "still_wrong"}
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_reconfigure_flow_changes_password(
    hass: HomeAssistant, mock_validate_input
):
    """Reconfigure: user updates password for same login → success."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: "test_user", CONF_PASSWORD: "old"},
        unique_id="test_user",
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "new"},
    )
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "reconfigure_successful"
    assert entry.data[CONF_PASSWORD] == "new"


async def test_reconfigure_flow_blocks_username_change(
    hass: HomeAssistant, mock_validate_input
):
    """Reconfigure: changing username to a different one is blocked."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: "test_user", CONF_PASSWORD: "old"},
        unique_id="test_user",
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "different_user", CONF_PASSWORD: "x"},
    )
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "account_mismatch"


# ---------- Options flow (PR 6 — humanize-sync tunables) ----------


async def test_options_flow_shows_form_with_defaults(
    hass: HomeAssistant, mock_validate_input
):
    """Otwarcie options pokazuje form z defaultami."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: "test_user", CONF_PASSWORD: "p"},
        unique_id="test_user",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_flow_saves_user_input(
    hass: HomeAssistant, mock_validate_input
):
    """Submit options → wartości lądują w entry.options i triggerują reload."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: "test_user", CONF_PASSWORD: "p"},
        unique_id="test_user",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "base_minutes": 60,
            "jitter": 0.1,
            "quiet_hours_enabled": True,
            "quiet_start": "23:00",
            "quiet_end": "07:00",
            "off_school_multiplier": 4.0,
            "humanize": True,
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options["base_minutes"] == 60
    assert entry.options["jitter"] == 0.1
    assert entry.options["quiet_hours_enabled"] is True
    assert entry.options["off_school_multiplier"] == 4.0
    assert entry.options["humanize"] is True


async def test_options_flow_humanize_off_disables_features(
    hass: HomeAssistant, mock_validate_input
):
    """humanize=False przelacza koordynator na legacy mode (sprawdz przez delay)."""
    import random as _random
    from datetime import datetime
    from unittest.mock import patch

    from freezegun import freeze_time

    from custom_components.librus_apix.coordinator import (
        LibrusDataUpdateCoordinator,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_USERNAME: "test_user", CONF_PASSWORD: "p"},
        options={
            "humanize": False,
            "base_minutes": 60,
        },
        unique_id="test_user",
    )
    entry.add_to_hass(hass)

    # Spawn coordinator with our entry directly so we control its options.
    from unittest.mock import MagicMock
    fake = MagicMock()
    fake.username = "x"
    fake.async_authenticate = AsyncMock(return_value=True)
    fake.async_get_student_information = AsyncMock(return_value=None)
    fake.async_get_grades = AsyncMock(return_value=[])
    fake.async_get_messages = AsyncMock(return_value=[])
    fake.async_get_schedule_events = AsyncMock(return_value=[])
    fake.async_get_timetable_events = AsyncMock(return_value=[])

    coordinator = LibrusDataUpdateCoordinator(
        hass, fake, config_entry=entry, rng=_random.Random(42)
    )

    # Saturday — legacy mode ignores off-school multiplier and jitter.
    with freeze_time("2026-05-09 10:00:00"):
        with patch(
            "custom_components.librus_apix.coordinator.async_call_later"
        ) as call_later:
            coordinator.schedule_next_refresh()

    delay = call_later.call_args.args[1]
    # Legacy: 60 min × 1.0 (no jitter, no off-school) → exactly 60*60 s.
    assert delay == pytest.approx(60 * 60, rel=1e-6)
