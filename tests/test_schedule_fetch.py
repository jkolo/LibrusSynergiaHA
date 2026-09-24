"""Unit tests for LibrusApiClient.async_get_schedule_events enrichment.

librus-apix parses the Librus tooltip into `Event.data` (e.g. `Nauczyciel`,
`Opis`); missing values come back as the literal string "unknown". The
fetcher exposes them as `teacher` / `description` / `details`, plus a Polish
`weekday` name, so dashboards can show what the exam is about.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from librus_apix.schedule import Event

from custom_components.librus_apix import LibrusApiClient

_WEEKDAYS = (
    "poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela",
)


@pytest.fixture
def client():
    """A LibrusApiClient with auth pre-seeded (no real Librus call)."""
    c = LibrusApiClient("user", "pass")
    c._client = MagicMock()
    c._token = "fake"
    with patch.object(c, "_apply_headers"):
        yield c


def _event(data: dict, title: str = "Sprawdzian") -> Event:
    today = date.today()
    return Event(
        title=title,
        subject="matematyka",
        data=data,
        day=str(today.day),
        number=3,
        hour="unknown",
        href="terminarz/szczegoly/123",
    )


async def _fetch(client, event: Event) -> list[dict]:
    schedule = defaultdict(list)
    schedule[date.today().day].append(event)
    with patch(
        "custom_components.librus_apix.get_schedule", return_value=schedule
    ):
        return await client.async_get_schedule_events(
            months_ahead=1, only_exams=False
        )


async def test_exposes_description_teacher_and_weekday(hass, client):
    result = await _fetch(
        client,
        _event({"Nauczyciel": "Jan Kowalski", "Opis": "Funkcje liniowe"}),
    )

    assert len(result) == 1
    ev = result[0]
    assert ev["description"] == "Funkcje liniowe"
    assert ev["teacher"] == "Jan Kowalski"
    assert ev["weekday"] == _WEEKDAYS[date.today().weekday()]
    assert ev["details"] == {"Nauczyciel": "Jan Kowalski", "Opis": "Funkcje liniowe"}


async def test_unknown_placeholders_become_empty(hass, client):
    result = await _fetch(
        client,
        _event({"Nauczyciel": "unknown", "Opis": "unknown", "Sala": "12"}),
    )

    ev = result[0]
    assert ev["description"] == ""
    assert ev["teacher"] == ""
    assert ev["details"] == {"Sala": "12"}
