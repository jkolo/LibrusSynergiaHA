"""Attendance frequency from the Librus gateway API.

The HTML attendance list holds only absences/lates/releases, never "present"
entries, so frequency computed from it was always 0.0 (production
2026-10-15). The gateway `Attendances` payload has every entry including
type 100 ("ob"); each references a Lesson (teacher+subject assignment) that
maps to a subject via the bulk `Lessons` and `Subjects` endpoints.
Definition (as librus-apix overall): attended = ob/sp/wy, denominator = all
entries — the same at both levels, so by_subject sums to the total.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from custom_components.librus_apix import LibrusApiClient, _attendance_stats

# Type.Id: 1 nb, 2 sp, 3 u, 4 zw, 100 ob, 1266 wy
ATTENDANCES = [
    {"Lesson": {"Id": 11}, "Type": {"Id": 100}, "Semester": 1},
    {"Lesson": {"Id": 11}, "Type": {"Id": 100}, "Semester": 1},
    {"Lesson": {"Id": 11}, "Type": {"Id": 1}, "Semester": 1},
    {"Lesson": {"Id": 11}, "Type": {"Id": "2"}, "Semester": 1},   # Id jako string
    {"Lesson": {"Id": 12}, "Type": {"Id": 3}, "Semester": 1},
    {"Lesson": {"Id": 12}, "Type": {"Id": 1266}, "Semester": 1},
    {"Lesson": {"Id": 13}, "Type": {"Id": 100}, "Semester": 2},
    {"Lesson": {"Id": 13}, "Type": {"Id": 4}, "Semester": 2},
]
LESSON_SUBJECT = {11: "Matematyka", 12: "Język polski", 13: "Historia"}


def test_stats_overall_and_by_subject():
    stats = _attendance_stats(ATTENDANCES, LESSON_SUBJECT, current_semester=1)

    assert stats["by_subject"]["Matematyka"] == {
        "present": 3, "missed": 1, "total": 4, "frequency": 75.0,
    }
    assert stats["by_subject"]["Język polski"]["frequency"] == 50.0
    assert stats["by_subject"]["Historia"]["frequency"] == 50.0
    overall = stats["overall"]
    assert overall["semester_1"] == pytest.approx(66.67)  # 4 / 6
    assert overall["semester_2"] == 50.0
    assert overall["total"] == 62.5                      # 5 / 8
    assert overall["current"] == overall["semester_1"]
    # Suma per przedmiot zgadza się z całością (jedna definicja).
    present = sum(s["present"] for s in stats["by_subject"].values())
    total = sum(s["total"] for s in stats["by_subject"].values())
    assert round(present / total * 100, 2) == overall["total"]


def test_empty_semester_is_none_not_zero():
    stats = _attendance_stats(ATTENDANCES[:4], LESSON_SUBJECT, current_semester=2)
    assert stats["overall"]["semester_2"] is None
    assert stats["overall"]["current"] is None


def test_unmapped_lesson_goes_to_unknown_subject():
    stats = _attendance_stats(
        [{"Lesson": {"Id": 99}, "Type": {"Id": 100}, "Semester": 1}], {}, 1,
    )
    assert stats["by_subject"]["(nieznany przedmiot)"]["present"] == 1


# ---------------------------------------------------------------------------
# LibrusApiClient.async_get_attendance_stats
# ---------------------------------------------------------------------------


def _lib(payloads: dict) -> MagicMock:
    lib = MagicMock()
    lib.calls = []

    def _get(url: str):
        key = url.rsplit("/2.0/", 1)[1]
        lib.calls.append(key)
        resp = MagicMock()
        body = payloads.get(key, ValueError("404"))
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
        p = patch.object(c, "_apply_headers")
        p.start()
        patchers.append(p)
        return c

    yield _make
    for p in patchers:
        p.stop()


BULK = {
    "Attendances": {"Attendances": ATTENDANCES},
    "Lessons": {"Lessons": [
        {"Id": 11, "Subject": {"Id": 1}},
        {"Id": 12, "Subject": {"Id": 2}},
    ]},
    "Subjects": {"Subjects": [
        {"Id": 1, "Name": "Matematyka"},
        {"Id": 2, "Name": "Język polski"},
        {"Id": 3, "Name": "Historia"},
    ]},
    # Lekcja 13 nie ma jej w hurtowej liście — dociągana pojedynczo.
    "Lessons/13": {"Lesson": {"Id": 13, "Subject": {"Id": 3}}},
}


async def test_fetch_uses_bulk_then_per_item_fallback(hass, make_client):
    client = make_client(BULK)
    stats = await client.async_get_attendance_stats()

    assert set(stats["by_subject"]) == {"Matematyka", "Język polski", "Historia"}
    calls = client._client.calls
    assert calls[:3] == ["Attendances", "Lessons", "Subjects"]
    assert calls[3:] == ["Lessons/13"]
    client._client.refresh_oauth.assert_called_once()


@pytest.mark.parametrize("body", [{"Status": "Error"}, ValueError("not json")])
async def test_bad_attendances_response_gives_none_without_reauth(hass, make_client, body):
    client = make_client({"Attendances": body})
    assert await client.async_get_attendance_stats() is None
    assert client._token == "fake"


async def test_too_many_unmapped_lessons_gives_none(hass, make_client):
    """Gdyby Lesson.Id było instancją lekcji (setki ID), fallback per element
    zrobiłby setki zapytań — limit ucina to i zwraca None."""
    many = [{"Lesson": {"Id": i}, "Type": {"Id": 100}, "Semester": 1} for i in range(200)]
    client = make_client({"Attendances": {"Attendances": many},
                          "Lessons": {"Lessons": []}, "Subjects": {"Subjects": []}})
    assert await client.async_get_attendance_stats() is None
    assert len(client._client.calls) <= 3 + 30
