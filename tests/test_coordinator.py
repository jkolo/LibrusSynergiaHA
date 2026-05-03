"""Tests for the Librus APIX DataUpdateCoordinator."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.librus_apix import LibrusAuthError
from custom_components.librus_apix.const import DOMAIN
from custom_components.librus_apix.coordinator import (
    ISSUE_AUTH_FAILED,
    ISSUE_LIB_OUTDATED,
    LibrusDataUpdateCoordinator,
)


@pytest.fixture
def fake_client(mock_student_info):
    """Minimal fake LibrusApiClient."""
    client = MagicMock()
    client.username = "test_user"
    client.async_authenticate = AsyncMock(return_value=True)
    client.async_get_student_information = AsyncMock(return_value=mock_student_info)
    client.async_get_grades = AsyncMock(return_value=[
        {
            "subject": "Matematyka",
            "grade": "5",
            "date": "2025-09-15",
            "category": "Sprawdzian",
            "teacher": "Anna",
            "semester": 1,
            "type": "numeric",
        },
        {
            "subject": "Polski",
            "grade": "4+",
            "date": "2025-09-10",
            "category": "Kartkowka",
            "teacher": "Marek",
            "semester": 1,
            "type": "numeric",
        },
    ])
    client.async_get_messages = AsyncMock(return_value=[])
    client.async_get_schedule_events = AsyncMock(return_value=[])
    client.async_get_timetable_events = AsyncMock(return_value=[])
    return client


async def test_first_refresh_seeds_seen_sets(hass: HomeAssistant, fake_client):
    """Pierwszy refresh nie wysyla eventow, tylko zapamietuje stan."""
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client)
    fired_events: list[str] = []
    hass.bus.async_listen_once("librus_apix_new_grade", lambda e: fired_events.append("grade"))
    hass.bus.async_listen_once(
        "librus_apix_new_message", lambda e: fired_events.append("message")
    )

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Pierwszy run = seed only, nic nie poszlo na bus.
    assert fired_events == []
    # Ale dane sa: 2 oceny, 2 przedmioty.
    assert len(coordinator.data["grades"]) == 2
    assert "Matematyka" in coordinator.data["grades_by_subject"]
    assert "Polski" in coordinator.data["grades_by_subject"]


async def test_second_refresh_fires_event_for_new_grade(hass: HomeAssistant, fake_client):
    """Druga aktualizacja z nowa ocena emituje librus_apix_nowa_ocena."""
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Dorzuc nowa ocene do drugiego refresha.
    fake_client.async_get_grades = AsyncMock(return_value=[
        {
            "subject": "Matematyka",
            "grade": "5",
            "date": "2025-09-15",
            "category": "Sprawdzian",
            "teacher": "Anna",
            "semester": 1,
            "type": "numeric",
        },
        {
            "subject": "Polski",
            "grade": "4+",
            "date": "2025-09-10",
            "category": "Kartkowka",
            "teacher": "Marek",
            "semester": 1,
            "type": "numeric",
        },
        {
            "subject": "Historia",
            "grade": "6",
            "date": "2025-09-20",
            "category": "Kartkowka",
            "teacher": "Pawel",
            "semester": 1,
            "type": "numeric",
        },
    ])

    fired = []
    hass.bus.async_listen_once(
        "librus_apix_new_grade",
        lambda e: fired.append(e.data),
    )

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(fired) == 1
    assert fired[0]["subject"] == "Historia"
    assert fired[0]["grade"] == "6"


async def test_grades_none_uses_cache(hass: HomeAssistant, fake_client):
    """Jesli kolejny fetch ocen zwroci None, koordynator uzywa cache zamiast fail."""
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.last_update_success is True

    fake_client.async_get_grades = AsyncMock(return_value=None)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Refresh sukces — cache podstawiony.
    assert coordinator.last_update_success is True
    assert len(coordinator.data["grades"]) == 2


async def test_first_refresh_fail_then_recovery(hass: HomeAssistant, fake_client):
    """Pierwszy refresh z grades=None i pustym cache → UpdateFailed."""
    fake_client.async_get_grades = AsyncMock(return_value=None)
    coordinator = LibrusDataUpdateCoordinator(hass, fake_client)

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.last_update_success is False


async def test_repair_issue_lib_outdated_after_threshold(
    hass: HomeAssistant, fake_client, mock_config_entry
):
    """5 kolejnych refresh-y gdzie KAŻDY endpoint zwraca None → repair issue."""
    mock_config_entry.add_to_hass(hass)
    coordinator = LibrusDataUpdateCoordinator(
        hass, fake_client, config_entry=mock_config_entry
    )
    # Pierwszy refresh — happy path, by ominąć grades-None branch.
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Symuluj pełną niedostępność API: każdy endpoint zwraca None.
    fake_client.async_get_student_information = AsyncMock(return_value=None)
    fake_client.async_get_grades = AsyncMock(return_value=None)
    fake_client.async_get_messages = AsyncMock(return_value=None)
    fake_client.async_get_schedule_events = AsyncMock(return_value=None)
    fake_client.async_get_timetable_events = AsyncMock(return_value=None)

    issue_id = coordinator._issue_id(ISSUE_LIB_OUTDATED)
    registry = ir.async_get(hass)

    # 4 kolejne fail-e — issue jeszcze NIE powinien istnieć.
    for _ in range(4):
        await coordinator.async_refresh()
        await hass.async_block_till_done()
    assert registry.async_get_issue(DOMAIN, issue_id) is None

    # 5-ty fail — issue pojawia się.
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    issue = registry.async_get_issue(DOMAIN, issue_id)
    assert issue is not None
    assert issue.severity == ir.IssueSeverity.WARNING
    assert issue.translation_key == ISSUE_LIB_OUTDATED


async def test_repair_issue_lib_outdated_clears_on_recovery(
    hass: HomeAssistant, fake_client, mock_config_entry
):
    """Issue jest usuwane po powrocie do działającego API."""
    mock_config_entry.add_to_hass(hass)
    coordinator = LibrusDataUpdateCoordinator(
        hass, fake_client, config_entry=mock_config_entry
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Wymuś issue: zwróć None ze wszystkiego 5 razy.
    fake_client.async_get_student_information = AsyncMock(return_value=None)
    fake_client.async_get_grades = AsyncMock(return_value=None)
    fake_client.async_get_messages = AsyncMock(return_value=None)
    fake_client.async_get_schedule_events = AsyncMock(return_value=None)
    fake_client.async_get_timetable_events = AsyncMock(return_value=None)
    for _ in range(5):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    issue_id = coordinator._issue_id(ISSUE_LIB_OUTDATED)
    registry = ir.async_get(hass)
    assert registry.async_get_issue(DOMAIN, issue_id) is not None

    # API wraca: student_info != None → wszystkie endpointy nie są None →
    # licznik resetuje się i issue znika.
    fake_client.async_get_student_information = AsyncMock(
        return_value=MagicMock(name="recovered", lucky_number=7, class_name="5A",
                               number="12", tutor="A", school="SP1")
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert registry.async_get_issue(DOMAIN, issue_id) is None


async def test_random_order_uses_injected_rng(
    hass: HomeAssistant, fake_client, monkeypatch
):
    """Coordinator z deterministycznym Random(42) odpala fetchery w predictable kolejnosci."""
    import random as _random

    coordinator = LibrusDataUpdateCoordinator(
        hass, fake_client, rng=_random.Random(42)
    )

    # Track call order via spy on each fetcher.
    call_order: list[str] = []

    async def _record(name: str, original):
        async def wrapper(*args, **kwargs):
            call_order.append(name)
            return await original(*args, **kwargs)
        return wrapper

    fake_client.async_get_student_information = await _record(
        "student_info", fake_client.async_get_student_information
    )
    fake_client.async_get_grades = await _record("grades", fake_client.async_get_grades)
    fake_client.async_get_messages = await _record("messages", fake_client.async_get_messages)
    fake_client.async_get_schedule_events = await _record(
        "schedule", fake_client.async_get_schedule_events
    )
    fake_client.async_get_timetable_events = await _record(
        "timetable", fake_client.async_get_timetable_events
    )

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Each fetcher called exactly once.
    assert sorted(call_order) == sorted(
        ["student_info", "grades", "messages", "schedule", "timetable"]
    )
    # Order is NOT the natural dict order (would be the listing above) —
    # the shuffle should produce something different. Lock-in: with seed 42,
    # the order is deterministic and we just check that *some* shuffle happened.
    assert call_order != ["student_info", "grades", "messages", "schedule", "timetable"]


async def test_pause_invoked_between_endpoints(hass: HomeAssistant, fake_client):
    """Po kazdym z pierwszych N-1 endpointow leci asyncio.sleep z jitter pause."""
    import random as _random
    from unittest.mock import patch

    coordinator = LibrusDataUpdateCoordinator(
        hass, fake_client, rng=_random.Random(42)
    )

    # Count only the calls our coordinator makes (deterministic 0.0 from
    # the jitter_pause_seconds patch in the autouse fixture). Other library
    # code may also call asyncio.sleep, so we filter by argument.
    pause_seconds: list[float] = []
    real_sleep = asyncio.sleep

    async def spy_sleep(seconds, *args, **kwargs):
        # Sentinel value 0.0001 from the no_human_pauses fixture marks
        # our coordinator's inter-fetch pauses; ignore other sleeps.
        if seconds == 0.0001:
            pause_seconds.append(seconds)
        return await real_sleep(seconds, *args, **kwargs)

    with patch(
        "custom_components.librus_apix.coordinator.asyncio.sleep", spy_sleep
    ):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    # 5 fetcherow → 4 pauzy między nimi.
    assert len(pause_seconds) == 4


async def test_schedule_next_refresh_uses_async_call_later(
    hass: HomeAssistant, fake_client
):
    """schedule_next_refresh wola async_call_later z delay z next_run_delay."""
    import random as _random
    from unittest.mock import patch

    coordinator = LibrusDataUpdateCoordinator(
        hass, fake_client, rng=_random.Random(42)
    )

    with patch(
        "custom_components.librus_apix.coordinator.async_call_later"
    ) as call_later:
        coordinator.schedule_next_refresh()

    assert call_later.called
    args = call_later.call_args.args
    # Sygnatura: async_call_later(hass, delay_seconds, callback).
    assert args[0] is hass
    delay = args[1]
    # Default base 120 min × ±25 % jitter → [90, 150] min.
    assert 90 * 60 <= delay <= 150 * 60


async def test_async_shutdown_cancels_pending_refresh(
    hass: HomeAssistant, fake_client
):
    """async_shutdown anuluje zaplanowany async_call_later."""
    import random as _random
    from unittest.mock import MagicMock, patch

    coordinator = LibrusDataUpdateCoordinator(
        hass, fake_client, rng=_random.Random(42)
    )

    cancel_handle = MagicMock()
    with patch(
        "custom_components.librus_apix.coordinator.async_call_later",
        return_value=cancel_handle,
    ):
        coordinator.schedule_next_refresh()
        assert coordinator._unsub_next is cancel_handle

        await coordinator.async_shutdown()

    cancel_handle.assert_called_once()
    assert coordinator._unsub_next is None


async def test_repair_issue_auth_failed_on_libraryauth_error(
    hass: HomeAssistant, fake_client, mock_config_entry
):
    """LibrusAuthError podczas refresh → ConfigEntryAuthFailed + repair issue."""
    mock_config_entry.add_to_hass(hass)
    fake_client.async_get_student_information = AsyncMock(
        side_effect=LibrusAuthError("token persisted")
    )
    coordinator = LibrusDataUpdateCoordinator(
        hass, fake_client, config_entry=mock_config_entry
    )

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    issue_id = coordinator._issue_id(ISSUE_AUTH_FAILED)
    registry = ir.async_get(hass)
    issue = registry.async_get_issue(DOMAIN, issue_id)
    assert issue is not None
    assert issue.severity == ir.IssueSeverity.ERROR
    assert issue.translation_key == ISSUE_AUTH_FAILED
