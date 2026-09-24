"""Unit tests for LibrusApiClient.async_get_homework.

librus-apix `get_homework` returns Homework dataclasses whose dates are two
table cells glued with a space (e.g. "2026-10-02 piątek"). The fetcher maps
them to English-keyed dicts with an ISO `due_date` parsed tolerantly.
Only the list endpoint is used — `homework_detail` is never called.
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from librus_apix.exceptions import ParseError
from librus_apix.homework import Homework

from custom_components.librus_apix import LibrusApiClient


@pytest.fixture
def client():
    """A LibrusApiClient with auth pre-seeded (no real Librus call)."""
    c = LibrusApiClient("user", "pass")
    c._client = MagicMock()
    c._token = "fake"
    with patch.object(c, "_apply_headers"):
        yield c


def _hw(completion: str, subject: str = "matematyka", task: str = "2026-09-20 pon.") -> Homework:
    return Homework(
        lesson="Funkcje",
        teacher="Jan Kowalski",
        subject=subject,
        category="Zadanie domowe",
        task_date=task,
        completion_date=completion,
        href="123456",
    )


async def test_maps_homework_and_sorts_by_due_date(hass, client):
    later = (date.today() + timedelta(days=5)).isoformat()
    sooner = (date.today() + timedelta(days=2)).isoformat()
    items = [_hw(f"{later} piątek", "polski"), _hw(f"{sooner} wtorek")]
    with patch(
        "custom_components.librus_apix.get_homework", return_value=items
    ) as mock_get:
        result = await client.async_get_homework(days_ahead=30)

    _, date_from, date_to = mock_get.call_args.args
    assert date_from == date.today().isoformat()
    assert date_to == (date.today() + timedelta(days=30)).isoformat()

    assert [h["subject"] for h in result] == ["matematyka", "polski"]
    first = result[0]
    assert first["due_date"] == sooner
    assert first["due_date_raw"] == f"{sooner} wtorek"
    assert first["days_until"] == 2
    assert first["task_date"] == "2026-09-20"
    assert first["teacher"] == "Jan Kowalski"
    assert first["lesson"] == "Funkcje"
    assert first["category"] == "Zadanie domowe"
    assert first["href"] == "123456"


async def test_polish_date_format_is_parsed(hass, client):
    due = date.today() + timedelta(days=3)
    with patch(
        "custom_components.librus_apix.get_homework",
        return_value=[_hw(due.strftime("%d.%m.%Y"))],
    ):
        result = await client.async_get_homework()
    assert result[0]["due_date"] == due.isoformat()


async def test_unparseable_date_goes_last_with_none(hass, client):
    due = (date.today() + timedelta(days=1)).isoformat()
    with patch(
        "custom_components.librus_apix.get_homework",
        return_value=[_hw("brak terminu"), _hw(due)],
    ):
        result = await client.async_get_homework()
    assert result[0]["due_date"] == due
    assert result[1]["due_date"] is None
    assert result[1]["days_until"] is None


async def test_parse_error_returns_none(hass, client):
    """ParseError is transient for _with_retry: re-auth, retry, then None."""
    async def _reauth():
        client._client = MagicMock()
        client._token = "fake"
        return True

    with patch(
        "custom_components.librus_apix.get_homework",
        side_effect=ParseError("layout changed"),
    ) as mock_get, patch.object(
        client, "async_authenticate", AsyncMock(side_effect=_reauth)
    ):
        assert await client.async_get_homework() is None
    assert mock_get.call_count == 2
