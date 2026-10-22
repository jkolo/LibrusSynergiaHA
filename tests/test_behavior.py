"""Zachowanie ze strony ocen: parser, przechwycenie HTML w async_get_grades.

Fixture `behavior_points.html` pochodzi z forka procaktomasz/LibrusSynergiaHA
(MIT, tests/test_zachowanie.py) — zanonimizowany HTML z prawdziwego konta.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.librus_apix import LibrusApiClient, _parse_behavior

FIXTURES = Path(__file__).parent / "fixtures"
POINTS_HTML = (FIXTURES / "behavior_points.html").read_text(encoding="utf-8")
GRADES_ONLY_HTML = (FIXTURES / "behavior_grades_only.html").read_text(encoding="utf-8")


def test_points_system() -> None:
    res = _parse_behavior(POINTS_HTML)

    assert res["system"] == "points"
    assert res["points_start"] == 240
    assert res["points_sem1"] == 215
    assert res["points_sem2"] == 240
    assert res["predicted_sem1"] == "poprawne"
    assert res["predicted_year"] == "wzorowe"
    assert res["grade_sem1"] == ""
    assert res["grade_year"] == ""


def test_points_entries_newest_first() -> None:
    entries = _parse_behavior(POINTS_HTML)["entries"]

    assert [e["date"] for e in entries] == ["2026-10-08", "2026-09-22", "2026-09-21"]
    assert entries[0] == {
        "date": "2026-10-08",
        "category": "Akcje charytatywne",
        "points": 5,
        "kind": "positive",
        "teacher": "NAUCZYCIEL2",
        "comment": "Zbiórka karmy",
        "semester": 1,
    }
    assert entries[1]["points"] == -10
    assert entries[1]["kind"] == "negative"


def test_grades_only_system() -> None:
    res = _parse_behavior(GRADES_ONLY_HTML)

    assert res["system"] == "grades"
    assert res["grade_sem1"] == "bardzo dobre"
    assert res["points_start"] is None
    assert res["points_sem1"] is None
    assert res["entries"] == []


def test_no_behavior_table_returns_none() -> None:
    assert _parse_behavior("<table><tr><td>Matematyka</td><td>5</td></tr></table>") is None


@pytest.fixture
def client():
    c = LibrusApiClient("user", "pass")
    c._client = MagicMock()
    c._client.GRADES_URL = "https://synergia.librus.pl/przegladaj_oceny/uczen"
    c._client.post.return_value = MagicMock(text=POINTS_HTML)
    c._token = "fake"
    with patch.object(c, "_apply_headers"):
        yield c


def _fake_get_grades(client, sort_by):
    client.post(client.GRADES_URL, data={"zmiany_logowanie_wszystkie": "1"})
    empty = [defaultdict(list), defaultdict(list)]
    return empty, {}, [defaultdict(list), defaultdict(list)]


async def test_grades_fetch_captures_behavior_without_extra_request(hass, client) -> None:
    with patch("custom_components.librus_apix.get_grades", side_effect=_fake_get_grades):
        assert await client.async_get_grades() == []

    assert client._client.post.call_count == 1
    behavior = await client.async_get_behavior()
    assert behavior["points_sem1"] == 215
    # Odbior czysci bufor — kolejny cykl bez udanego pobrania ocen da None.
    assert await client.async_get_behavior() is None


async def test_grades_page_without_behavior_gives_empty_dict(hass, client) -> None:
    client._client.post.return_value = MagicMock(text="<table></table>")
    with patch("custom_components.librus_apix.get_grades", side_effect=_fake_get_grades):
        await client.async_get_grades()

    assert await client.async_get_behavior() == {}


async def test_failed_grades_fetch_gives_none(hass, client) -> None:
    # Najpierw udany cykl — bufor musi zostac wyczyszczony przy bledzie.
    with patch("custom_components.librus_apix.get_grades", side_effect=_fake_get_grades):
        await client.async_get_grades()

    async def _reauth():
        client._client = MagicMock()
        client._token = "fake"
        return True

    with patch(
        "custom_components.librus_apix.get_grades", side_effect=RuntimeError("boom")
    ), patch.object(client, "async_authenticate", AsyncMock(side_effect=_reauth)):
        assert await client.async_get_grades() is None

    assert await client.async_get_behavior() is None


# ---------------------------------------------------------------------------
# Koordynator: klucz `behavior`, cache, zdarzenie new_behavior_entry
# ---------------------------------------------------------------------------

from custom_components.librus_apix.coordinator import LibrusDataUpdateCoordinator  # noqa: E402

ENTRY = {
    "date": "2026-10-08", "category": "Akcje charytatywne", "points": 5,
    "kind": "positive", "teacher": "N2", "comment": "Zbiórka", "semester": 1,
}


def _behavior(entries=(), **overrides):
    data = {
        "system": "points", "points_start": 240, "points_sem1": 245,
        "points_sem2": None, "predicted_sem1": "", "predicted_year": "",
        "grade_sem1": "", "grade_year": "", "entries": list(entries),
    }
    data.update(overrides)
    return data


@pytest.fixture
def coord_client(mock_student_info):
    client = MagicMock()
    client.username = "test_user"
    client.async_authenticate = AsyncMock(return_value=True)
    client.async_get_student_information = AsyncMock(return_value=mock_student_info)
    client.async_get_grades = AsyncMock(return_value=[])
    client.async_get_behavior = AsyncMock(return_value=_behavior())
    client.async_get_completed_lessons = AsyncMock(return_value=[])
    client.async_get_messages = AsyncMock(return_value=[])
    client.async_get_schedule_events = AsyncMock(return_value=[])
    client.async_get_timetable_events = AsyncMock(return_value=[])
    client.async_get_attendance = AsyncMock(return_value=[])
    client.async_get_homework = AsyncMock(return_value=[])
    client.async_get_notes = AsyncMock(return_value=[])
    client.async_get_attendance_stats = AsyncMock(return_value=None)
    client.async_get_announcements = AsyncMock(return_value=[])
    return client


async def test_coordinator_exposes_behavior(hass, coord_client) -> None:
    coordinator = LibrusDataUpdateCoordinator(hass, coord_client)
    await coordinator.async_refresh()

    assert coordinator.data["behavior"]["points_sem1"] == 245


async def test_coordinator_keeps_cached_behavior_on_failure(hass, coord_client) -> None:
    coordinator = LibrusDataUpdateCoordinator(hass, coord_client)
    await coordinator.async_refresh()
    coord_client.async_get_behavior = AsyncMock(return_value=None)
    coord_client.async_get_completed_lessons = AsyncMock(return_value=[])
    await coordinator.async_refresh()

    assert coordinator.data["behavior"]["points_sem1"] == 245


async def test_new_behavior_entry_event_after_first_run(hass, coord_client) -> None:
    coordinator = LibrusDataUpdateCoordinator(hass, coord_client)
    await coordinator.async_refresh()  # seed
    assert coordinator.consume_pending_event("new_behavior_entry") is None

    coord_client.async_get_behavior = AsyncMock(return_value=_behavior([ENTRY]))

    coord_client.async_get_completed_lessons = AsyncMock(return_value=[])
    await coordinator.async_refresh()

    payload = coordinator.consume_pending_event("new_behavior_entry")
    assert payload == {"type": "entry", **ENTRY}


async def test_behavior_grade_change_fires_event(hass, coord_client) -> None:
    coordinator = LibrusDataUpdateCoordinator(hass, coord_client)
    await coordinator.async_refresh()

    coord_client.async_get_behavior = AsyncMock(
        return_value=_behavior(predicted_sem1="bardzo dobre")
    )
    await coordinator.async_refresh()

    assert coordinator.consume_pending_event("new_behavior_entry") == {
        "type": "grade", "field": "predicted_sem1", "grade": "bardzo dobre",
    }


async def test_existing_entries_on_first_run_do_not_fire(hass, coord_client) -> None:
    coord_client.async_get_behavior = AsyncMock(return_value=_behavior([ENTRY]))
    coord_client.async_get_completed_lessons = AsyncMock(return_value=[])
    coordinator = LibrusDataUpdateCoordinator(hass, coord_client)
    await coordinator.async_refresh()
    await coordinator.async_refresh()

    assert coordinator.consume_pending_event("new_behavior_entry") is None


# ---------------------------------------------------------------------------
# Sensory
# ---------------------------------------------------------------------------

from custom_components.librus_apix.sensor import (  # noqa: E402
    _attrs_behavior,
    _attrs_behavior_points,
    _val_behavior,
    _val_behavior_points,
)


def _data(behavior, semester=1):
    return {"behavior": behavior, "current_semester": semester}


def test_behavior_state_prefers_final_over_predicted() -> None:
    assert _val_behavior(_data(_behavior(predicted_sem1="dobre"))) == "dobre"
    assert _val_behavior(_data(_behavior(predicted_sem1="dobre", grade_sem1="wzorowe"))) == "wzorowe"
    assert _val_behavior(_data(_behavior())) is None
    assert _val_behavior(_data({})) is None


def test_behavior_state_second_semester_uses_year_grades() -> None:
    b = _behavior(grade_sem1="dobre", predicted_year="bardzo dobre")
    assert _val_behavior(_data(b, semester=2)) == "bardzo dobre"
    assert _val_behavior(_data(_behavior(grade_sem1="dobre"), semester=2)) == "dobre"


def test_behavior_points_state_follows_semester() -> None:
    b = _behavior(points_sem1=215, points_sem2=240)
    assert _val_behavior_points(_data(b, 1)) == 215
    assert _val_behavior_points(_data(b, 2)) == 240
    assert _val_behavior_points(_data({})) is None


def test_behavior_attrs_without_entries_and_points_attrs_trimmed() -> None:
    b = _behavior([ENTRY] * 30, predicted_sem1="dobre")
    attrs = _attrs_behavior(_data(b))
    assert "entries" not in attrs
    assert attrs["predicted_sem1"] == "dobre"
    assert attrs["system"] == "points"

    pattrs = _attrs_behavior_points(_data(b))
    assert len(pattrs["entries"]) == 20
    assert pattrs["entries_truncated"] is True
    assert pattrs["points_start"] == 240
    assert pattrs["positive_sum"] == 150
    assert pattrs["negative_sum"] == 0


async def _setup_entities(hass, entry, client, behavior) -> set[str]:
    from homeassistant.helpers import entity_registry as er

    client.async_get_behavior = AsyncMock(return_value=behavior)

    client.async_get_completed_lessons = AsyncMock(return_value=[])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return {
        e.unique_id for e in er.async_entries_for_config_entry(
            er.async_get(hass), entry.entry_id
        )
    }


async def test_points_sensor_only_for_points_system(
    hass, mock_config_entry, mock_librus_client
) -> None:
    ids = await _setup_entities(
        hass, mock_config_entry, mock_librus_client, _behavior(system="grades")
    )
    entry_id = mock_config_entry.entry_id
    assert f"{entry_id}_zachowanie" in ids
    assert f"{entry_id}_punkty_zachowania" not in ids


async def test_points_sensor_created_for_points_system(
    hass, mock_config_entry, mock_librus_client
) -> None:
    ids = await _setup_entities(
        hass, mock_config_entry, mock_librus_client, _behavior([ENTRY])
    )
    from homeassistant.helpers import entity_registry as er

    unique_id = f"{mock_config_entry.entry_id}_punkty_zachowania"
    assert unique_id in ids
    entity_id = er.async_get(hass).async_get_entity_id("sensor", "librus_apix", unique_id)
    state = hass.states.get(entity_id)
    assert state.state == "245"
    assert state.attributes["unit_of_measurement"] == "pkt"
