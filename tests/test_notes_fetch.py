"""Unit tests for LibrusApiClient.async_get_notes (uwagi).

Notes come from the Librus gateway JSON API (`Notes`, `Notes/Categories`,
`Users`), the same way librus-apix reads attendance. Field meaning of
`Positive` (0 negative, 1 positive, 2 neutral) follows the
procaktomasz/LibrusSynergiaHA fork, verified there on real accounts.
Data below is fictional.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from custom_components.librus_apix import LibrusApiClient

NOTES = [
    {"Id": 1, "Date": "2026-09-14", "Positive": 1, "Text": "Pomoc koledze w lekcji.",
     "Category": {"Id": 10}, "Teacher": {"Id": 100}},
    {"Id": 2, "Date": "2026-10-01 10:15:00", "Positive": 0, "Text": " Rozmowy na lekcji. ",
     "Category": {"Id": 11}, "Teacher": {"Id": 101}},
    {"Id": 3, "Date": "2026-10-05", "Positive": 2, "Text": "Brak stroju.",
     "Category": {"Id": 12}, "Teacher": {"Id": 999}},
]
CATEGORIES = {"Categories": [
    {"Id": 10, "CategoryName": "Pomoc innym"},
    {"Id": 11, "CategoryName": "Zachowanie na lekcji"},
    {"Id": 12, "CategoryName": "Strój"},
]}
USERS = {"Users": [
    {"Id": 100, "FirstName": "Anna", "LastName": "Kowalska"},
    {"Id": 101, "FirstName": "Jan", "LastName": "Nowak"},
]}


def _lib(payloads: dict) -> MagicMock:
    lib = MagicMock()

    def _get(url: str):
        resp = MagicMock()
        body = payloads[url.rsplit("/2.0/", 1)[1]]
        if isinstance(body, Exception):
            resp.json.side_effect = body
        else:
            resp.json.return_value = body
        return resp

    lib.get.side_effect = _get
    return lib


@pytest.fixture
def make_client():
    patchers = []

    def _make(payloads: dict) -> LibrusApiClient:
        c = LibrusApiClient("user", "pass")
        c._client = _lib(payloads)
        c._token = "fake"
        patcher = patch.object(c, "_apply_headers")
        patcher.start()
        patchers.append(patcher)
        return c

    yield _make
    for patcher in patchers:
        patcher.stop()


async def test_maps_notes_newest_first(hass, make_client):
    client = make_client({
        "Notes": {"Notes": NOTES}, "Notes/Categories": CATEGORIES, "Users": USERS,
    })
    notes = await client.async_get_notes()

    assert [n["id"] for n in notes] == [3, 2, 1]
    neutral, negative, positive = notes
    assert positive == {
        "id": 1, "date": "2026-09-14", "text": "Pomoc koledze w lekcji.",
        "kind": "positive", "category": "Pomoc innym", "teacher": "Anna Kowalska",
    }
    assert negative["kind"] == "negative"
    assert negative["date"] == "2026-10-01"
    assert negative["text"] == "Rozmowy na lekcji."
    assert neutral["kind"] == "neutral"
    assert neutral["teacher"] == ""  # nauczyciel spoza listy Users
    client._client.refresh_oauth.assert_called_once()


async def test_no_notes_gives_empty_list(hass, make_client):
    client = make_client({"Notes": {"Notes": []}})
    assert await client.async_get_notes() == []


async def test_missing_categories_and_users_still_maps(hass, make_client):
    client = make_client({
        "Notes": {"Notes": NOTES[:1]},
        "Notes/Categories": ValueError("not json"),
        "Users": ValueError("not json"),
    })
    notes = await client.async_get_notes()
    assert notes[0]["category"] == ""
    assert notes[0]["teacher"] == ""


@pytest.mark.parametrize("body", [{"Status": "Error"}, ValueError("not json")])
async def test_bad_notes_response_gives_none_without_reauth(hass, make_client, body):
    """Brak uwag w API (np. szkoła bez modułu) nie może co cykl resetować
    logowania — _with_retry robi _reset_auth() przy każdym wyjątku."""
    client = make_client({"Notes": body})
    assert await client.async_get_notes() is None
    assert client._token == "fake"


async def test_missing_notes_module_warns_once(hass, make_client, caplog):
    client = make_client({"Notes": {"Status": "Error"}})
    await client.async_get_notes()
    await client.async_get_notes()
    warnings = [r for r in caplog.records if r.levelname == "WARNING" and "Uwagi" in r.message]
    assert len(warnings) == 1
