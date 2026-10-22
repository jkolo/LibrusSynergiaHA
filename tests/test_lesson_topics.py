"""Tematy zrealizowanych lekcji: parser, stronicowanie, koordynator, encje.

Ksztalt wierszy strony "Zrealizowane lekcje" wg testow forka
procaktomasz/LibrusSynergiaHA (MIT, tests/test_tematy_frekwencja.py).
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.librus_apix import LibrusApiClient, _parse_completed_lessons


def _row(day, nr, subject_teacher, topic, etablica=True):
    etab = "<td></td>" if etablica else ""
    return (
        f'<tr><td class="center small">{day}</td><td class="tiny">pon.</td>'
        f"<td>{nr}</td><td>{subject_teacher}</td><td>{topic}</td><td></td>{etab}"
        '<td><p class="box"><a title="Rodzaj: obecność">ob</a></p></td></tr>'
    )


def _page(*rows):
    return '<table class="decorated"><tbody>' + "".join(rows) + "</tbody></table>"


def test_parse_substitution_and_etablica_column() -> None:
    html = _page(
        _row("2026-10-05", "6", "Matematyka , Kowalska Anna [Nowak Maria Ewa]", "Ułamki zwykłe"),
        _row("05.10.2026", "x", "Fizyka , Zielińska Joanna", "Ruch", etablica=False),
    )
    mat, fiz = _parse_completed_lessons(html)

    assert mat == {
        "date": "2026-10-05",
        "lesson_number": 6,
        "subject": "Matematyka",
        "teacher": "Kowalska Anna",
        "substitute": "Nowak Maria Ewa",
        "topic": "Ułamki zwykłe",
    }
    assert fiz["date"] == "2026-10-05"
    assert fiz["lesson_number"] is None
    assert fiz["substitute"] == ""


def test_parse_skips_rows_without_lesson_cells() -> None:
    html = _page('<tr><td colspan="8">Brak zrealizowanych lekcji</td></tr>')
    assert _parse_completed_lessons(html) == []


# ---------------------------------------------------------------------------
# Fetcher: stronicowanie po 15 wpisow, Librus powtarza ostatnia strone
# ---------------------------------------------------------------------------


def _full_page(day: str, start: int) -> str:
    return _page(*(
        _row(day, str(n % 9 + 1), f"Przedmiot {n} , Nauczyciel", f"Temat {n}")
        for n in range(start, start + 15)
    ))


@pytest.fixture
def client():
    c = LibrusApiClient("user", "pass")
    c._client = MagicMock()
    c._client.COMPLETED_LESSONS_URL = "https://synergia.librus.pl/zrealizowane_lekcje"
    c._token = "fake"
    with patch.object(c, "_apply_headers"):
        yield c


def _serve(client, pages):
    def _post(url, data):
        page = min(data["numer_strony1001"], len(pages) - 1)  # poza zakresem → ostatnia
        return MagicMock(text=pages[page])
    client._client.post.side_effect = _post


async def test_fetch_stops_on_short_page_and_sorts(hass, client) -> None:
    _serve(client, [
        _full_page("2026-10-05", 0),
        _page(_row("2026-10-06", "2", "Chemia , L", "Mieszaniny"),
              _row("2026-10-06", "1", "Biologia , B", "Komórka")),
    ])

    lessons = await client.async_get_completed_lessons()

    assert client._client.post.call_count == 2
    assert len(lessons) == 17
    assert [(l["date"], l["lesson_number"]) for l in lessons[:2]] == [
        ("2026-10-06", 1), ("2026-10-06", 2),
    ]
    data = client._client.post.call_args_list[0].kwargs["data"]
    assert data["data2"] == date.today().isoformat()
    assert data["data1"] == (date.today() - timedelta(days=7)).isoformat()


async def test_fetch_stops_when_librus_repeats_last_page(hass, client) -> None:
    _serve(client, [_full_page("2026-10-05", 0), _full_page("2026-10-06", 15)])

    lessons = await client.async_get_completed_lessons()

    assert client._client.post.call_count == 3  # trzecia = powtorka drugiej
    assert len(lessons) == 30


async def test_fetch_page_limit(hass, client) -> None:
    pages = [_full_page(f"2026-10-{d:02d}", d * 15) for d in range(1, 12)]
    _serve(client, pages)

    await client.async_get_completed_lessons()

    assert client._client.post.call_count == 6


async def test_fetch_error_returns_none(hass, client) -> None:
    client._client.post.side_effect = RuntimeError("boom")

    async def _reauth():
        client._token = "fake"
        return True

    with patch.object(client, "async_authenticate", AsyncMock(side_effect=_reauth)):
        assert await client.async_get_completed_lessons() is None


# ---------------------------------------------------------------------------
# Koordynator
# ---------------------------------------------------------------------------

from custom_components.librus_apix.coordinator import LibrusDataUpdateCoordinator  # noqa: E402

TODAY = date.today().isoformat()
TOPIC = {
    "date": TODAY, "lesson_number": 3, "subject": "Matematyka",
    "teacher": "J. Kowalska", "substitute": "", "topic": "Równania liniowe",
}
PERIOD = {
    "subject": "Matematyka", "teacher_and_classroom": "J. Kowalska s. 12",
    "date": TODAY, "time_from": "09:50", "time_to": "10:35",
    "weekday": "", "lesson_number": 3, "info": {},
}


@pytest.fixture
def coord_client(mock_student_info):
    client = MagicMock()
    client.username = "test_user"
    client.async_authenticate = AsyncMock(return_value=True)
    client.async_get_student_information = AsyncMock(return_value=mock_student_info)
    client.async_get_grades = AsyncMock(return_value=[])
    client.async_get_behavior = AsyncMock(return_value={})
    client.async_get_completed_lessons = AsyncMock(return_value=[TOPIC])
    client.async_get_messages = AsyncMock(return_value=[])
    client.async_get_schedule_events = AsyncMock(return_value=[])
    client.async_get_timetable_events = AsyncMock(
        return_value=[dict(PERIOD), dict(PERIOD, lesson_number=4, subject="Fizyka")]
    )
    client.async_get_attendance = AsyncMock(return_value=[])
    client.async_get_homework = AsyncMock(return_value=[])
    client.async_get_notes = AsyncMock(return_value=[])
    client.async_get_attendance_stats = AsyncMock(return_value=None)
    client.async_get_announcements = AsyncMock(return_value=[])
    return client


async def test_coordinator_exposes_topics_and_tags_timetable(hass, coord_client) -> None:
    coordinator = LibrusDataUpdateCoordinator(hass, coord_client)
    await coordinator.async_refresh()

    assert coordinator.data["lesson_topics"] == [TOPIC]
    math, physics = coordinator.data["timetable"]
    assert math["topic"] == "Równania liniowe"
    assert "topic" not in physics


async def test_coordinator_keeps_cached_topics_on_failure(hass, coord_client) -> None:
    coordinator = LibrusDataUpdateCoordinator(hass, coord_client)
    await coordinator.async_refresh()
    coord_client.async_get_completed_lessons = AsyncMock(return_value=None)
    await coordinator.async_refresh()

    assert coordinator.data["lesson_topics"] == [TOPIC]
    assert coordinator.data["timetable"][0]["topic"] == "Równania liniowe"


# ---------------------------------------------------------------------------
# Sensor i kalendarz
# ---------------------------------------------------------------------------

from custom_components.librus_apix.calendar import _lesson_to_calendar_event  # noqa: E402
from custom_components.librus_apix.sensor import (  # noqa: E402
    _attrs_lesson_topics,
    _val_lesson_topics,
)


def test_sensor_counts_today_and_latest_topic_per_subject() -> None:
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    topics = [
        TOPIC,
        dict(TOPIC, lesson_number=4, subject="Fizyka", topic="Ruch"),
        dict(TOPIC, date=yesterday, topic="Wyrażenia algebraiczne"),
    ]
    data = {"lesson_topics": topics}

    assert _val_lesson_topics(data) == 2
    attrs = _attrs_lesson_topics(data)
    assert attrs["by_subject"] == {"Matematyka": "Równania liniowe", "Fizyka": "Ruch"}
    assert attrs["lessons_truncated"] is False
    assert len(attrs["lessons"]) == 3


def test_sensor_attrs_fit_recorder_budget() -> None:
    import json

    topics = [dict(TOPIC, topic="x" * 400, lesson_number=n) for n in range(60)]
    attrs = _attrs_lesson_topics({"lesson_topics": topics})

    assert len(json.dumps(attrs, ensure_ascii=False).encode()) < 14_000
    assert attrs["lessons_truncated"] is True


def test_calendar_description_has_topic() -> None:
    ev = _lesson_to_calendar_event(dict(PERIOD, topic="Równania liniowe"))
    assert "Temat: Równania liniowe" in ev.description
    assert "Temat" not in _lesson_to_calendar_event(PERIOD).description
