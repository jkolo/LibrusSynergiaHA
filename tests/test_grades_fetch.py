"""Unit tests for LibrusApiClient.async_get_grades — counts / weight / value.

librus-apix reads "Licz do średniej" and "Waga" from the grade tooltip and
defaults them to False / 0 when the lines are missing. Schools that do not
use weighted averages never show those lines, so the library reports every
grade as "does not count" with weight 0 and `value == "Does not count"`.
The fetcher reads both lines from the tooltip itself and uses None when
Librus does not say.
"""

from __future__ import annotations

from collections import defaultdict
from unittest.mock import MagicMock, patch

import pytest
from librus_apix.grades import Grade, GradeDescriptive

from custom_components.librus_apix import LibrusApiClient, _current_semester


@pytest.fixture
def client():
    """A LibrusApiClient with auth pre-seeded (no real Librus call)."""
    c = LibrusApiClient("user", "pass")
    c._client = MagicMock()
    c._token = "fake"
    with patch.object(c, "_apply_headers"):
        yield c


def _grade(grade: str, desc_tail: str, counts: bool, weight: int) -> Grade:
    desc = (
        f"Ocena: {grade}\nPrzedmiot: geografia\n"
        "Kategoria: kartkówka\nData: 2026-09-28 (pon.)\n"
        "Nauczyciel: Jan Kowalski\n" + desc_tail + "Dodał: Jan Kowalski\n"
    )
    return Grade(
        "geografia", grade, counts, "2026-09-28", "", desc,
        _current_semester(), "kartkówka", "Jan Kowalski", weight,
    )


async def _fetch(client, grades: list[Grade]) -> list[dict]:
    numeric = [defaultdict(list), defaultdict(list)]
    numeric[_current_semester() - 1]["geografia"] = grades
    with patch(
        "custom_components.librus_apix.get_grades",
        return_value=(numeric, {}, [defaultdict(list), defaultdict(list)]),
    ):
        return await client.async_get_grades()


async def test_missing_tooltip_lines_give_none_not_false(hass, client):
    # Tooltip without "Licz do średniej" / "Waga" — library defaults False / 0.
    result = await _fetch(client, [_grade("4+", "", counts=False, weight=0)])

    g = result[0]
    assert g["counts"] is None
    assert g["weight"] is None
    assert g["value"] == 4.5


async def test_explicit_tooltip_lines_are_kept(hass, client):
    yes = _grade("5", "Licz do średniej: tak\nWaga: 3\n", counts=True, weight=3)
    no = _grade("3-", "Licz do średniej: nie\nWaga: 1\n", counts=False, weight=1)
    result = await _fetch(client, [yes, no])

    by_grade = {g["grade"]: g for g in result}
    assert by_grade["5"]["counts"] is True
    assert by_grade["5"]["weight"] == 3
    assert by_grade["5"]["value"] == 5.0
    assert by_grade["3-"]["counts"] is False
    assert by_grade["3-"]["weight"] == 1
    # Value is the grade's number even when it does not count.
    assert by_grade["3-"]["value"] == 2.75


async def test_non_numeric_grade_has_no_value(hass, client):
    result = await _fetch(client, [_grade("np", "", counts=False, weight=0)])
    assert result[0]["value"] is None


async def test_descriptive_digit_grade_has_unknown_counts_and_weight(hass, client):
    """Ocena opisowa z cyfrą: Librus nie podaje wagi — None, nie False/0
    (False wyrzucałoby ją ze średniej)."""
    desc = [defaultdict(list), defaultdict(list)]
    desc[_current_semester() - 1]["edukacja polonistyczna"] = [
        GradeDescriptive(
            "edukacja polonistyczna", "5", "2026-09-28", "", "Nauczyciel: Jan Kowalski",
            _current_semester(), "Jan Kowalski",
        )
    ]
    with patch(
        "custom_components.librus_apix.get_grades",
        return_value=([defaultdict(list), defaultdict(list)], {}, desc),
    ):
        result = await client.async_get_grades()

    g = next(r for r in result if r["type"] == "descriptive")
    assert g["counts"] is None
    assert g["weight"] is None
