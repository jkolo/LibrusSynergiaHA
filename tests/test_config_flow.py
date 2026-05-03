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


# ---------- PR 6 — per-subject multi-select & enabled-by-default ----------


async def test_options_flow_includes_enabled_subjects_field(
    hass: HomeAssistant, mock_librus_client, mock_config_entry
):
    """Form options zawiera pole `enabled_subjects` z multi-select przedmiotow.

    Wymaga zeby coordinator mial juz pobrane oceny — pole jest pokazywane tylko
    gdy lista znanych przedmiotow nie jest pusta (multi-select bez opcji
    bylby bezuzyteczny).
    """
    mock_librus_client.async_get_grades = AsyncMock(return_value=[
        {"subject": "Matematyka", "grade": "5", "value": 5.0, "counts": True,
         "weight": 3, "date": "2025-09-15", "category": "Sprawdzian",
         "description": "", "title": "", "teacher": "A",
         "semester": 1, "type": "numeric"},
        {"subject": "Polski", "grade": "4", "value": 4.0, "counts": True,
         "weight": 2, "date": "2025-09-10", "category": "Kartkowka",
         "description": "", "title": "", "teacher": "B",
         "semester": 1, "type": "numeric"},
    ])
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] == FlowResultType.FORM

    schema_keys = [str(k) for k in result["data_schema"].schema.keys()]
    assert "enabled_subjects" in schema_keys


async def test_options_flow_saves_enabled_subjects(
    hass: HomeAssistant, mock_librus_client, mock_config_entry
):
    """Wybor przedmiotow zostaje zapisany w entry.options['enabled_subjects']."""
    mock_librus_client.async_get_grades = AsyncMock(return_value=[
        {"subject": "Matematyka", "grade": "5", "value": 5.0, "counts": True,
         "weight": 3, "date": "2025-09-15", "category": "Sprawdzian",
         "description": "", "title": "", "teacher": "A",
         "semester": 1, "type": "numeric"},
        {"subject": "Polski", "grade": "4", "value": 4.0, "counts": True,
         "weight": 2, "date": "2025-09-10", "category": "Kartkowka",
         "description": "", "title": "", "teacher": "B",
         "semester": 1, "type": "numeric"},
    ])
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "base_minutes": 120,
            "jitter": 0.25,
            "quiet_hours_enabled": False,
            "quiet_start": "22:30",
            "quiet_end": "06:30",
            "off_school_multiplier": 6.0,
            "humanize": True,
            "enabled_subjects": ["Matematyka"],
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options["enabled_subjects"] == ["Matematyka"]


async def test_per_subject_sensors_filtered_by_enabled_subjects(
    hass: HomeAssistant, mock_librus_client, mock_config_entry
):
    """Gdy enabled_subjects=['Matematyka'], NIE tworzymy encji dla 'Polski'."""
    from homeassistant.helpers import entity_registry as er

    # Symulacja danych ocen: 2 przedmioty.
    mock_librus_client.async_get_grades = AsyncMock(return_value=[
        {"subject": "Matematyka", "grade": "5", "value": 5.0, "counts": True,
         "weight": 3, "date": "2025-09-15", "category": "Sprawdzian",
         "description": "", "title": "", "teacher": "A",
         "semester": 1, "type": "numeric"},
        {"subject": "Polski", "grade": "4", "value": 4.0, "counts": True,
         "weight": 2, "date": "2025-09-10", "category": "Kartkowka",
         "description": "", "title": "", "teacher": "B",
         "semester": 1, "type": "numeric"},
    ])

    # Pre-set options BEFORE setup so async_setup_entry honors them.
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, options={"enabled_subjects": ["Matematyka"]}
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    sensor_entries = [
        e for e in registry.entities.values()
        if e.domain == "sensor"
        and e.config_entry_id == mock_config_entry.entry_id
        and ("przedmiot_" in e.unique_id or "srednia_" in e.unique_id)
    ]
    uids = [e.unique_id for e in sensor_entries]
    # Matematyka encje TAK, Polski NIE.
    assert any("przedmiot_matematyka" in u for u in uids)
    assert any("srednia_matematyka" in u for u in uids)
    assert not any("przedmiot_polski" in u for u in uids)
    assert not any("srednia_polski" in u for u in uids)


async def test_per_subject_sensor_enabled_by_default(
    hass: HomeAssistant, mock_librus_client, mock_config_entry
):
    """Per-subject sensory powinny byc enabled_by_default w v3 (zmiana z v2).

    Brak enabled_subjects w options → wszystkie przedmioty automatycznie wlaczone.
    """
    from homeassistant.helpers import entity_registry as er

    mock_librus_client.async_get_grades = AsyncMock(return_value=[
        {"subject": "Matematyka", "grade": "5", "value": 5.0, "counts": True,
         "weight": 3, "date": "2025-09-15", "category": "Sprawdzian",
         "description": "", "title": "", "teacher": "A",
         "semester": 1, "type": "numeric"},
    ])
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    matematyka = next(
        (e for e in registry.entities.values()
         if e.domain == "sensor" and "przedmiot_matematyka" in e.unique_id),
        None,
    )
    assert matematyka is not None
    # `disabled_by` is None gdy entity registry treats it as enabled.
    assert matematyka.disabled_by is None
