"""Linking of Librus grade corrections ("Poprawa oceny") to the grades they replace."""

from __future__ import annotations

import copy

import pytest

from custom_components.librus_apix.grade_corrections import (
    link_grade_corrections,
    parse_correction,
)


def _grade(grade: str, date: str, category: str = "kartkówka", description: str = "") -> dict:
    return {
        "subject": "matematyka",
        "grade": grade,
        "date": date,
        "category": category,
        "description": description,
    }


# ---------------------------------------------------------------------------
# parse_correction — the "Poprawa oceny" tooltip line, e.g. "1 (kartkówka)"
# ---------------------------------------------------------------------------


def test_parse_grade_and_category():
    assert parse_correction("1 (kartkówka)") == {"grade": "1", "category": "kartkówka"}


def test_parse_keeps_plus_and_minus_modifiers():
    assert parse_correction("4+ (sprawdzian)") == {"grade": "4+", "category": "sprawdzian"}
    assert parse_correction("3- (odpowiedź ustna)") == {
        "grade": "3-", "category": "odpowiedź ustna",
    }


def test_parse_category_with_nested_parentheses():
    parsed = parse_correction("2 (praca klasowa (semestralna))")
    assert parsed == {"grade": "2", "category": "praca klasowa (semestralna)"}


def test_parse_grade_without_category():
    assert parse_correction("1") == {"grade": "1", "category": None}


def test_parse_unrecognised_text_is_still_a_correction():
    """Something is there, so it is a correction — just not one we can match."""
    assert parse_correction("coś nieoczekiwanego (x) y") == {"grade": None, "category": None}


@pytest.mark.parametrize("raw", ["", "   ", None])
def test_parse_empty_is_not_a_correction(raw):
    assert parse_correction(raw) is None


# ---------------------------------------------------------------------------
# link_grade_corrections
# ---------------------------------------------------------------------------


def test_correction_is_linked_to_the_grade_it_replaces():
    grades = [
        _grade("bz", "2026-09-10", category="zadanie"),
        _grade("1", "2026-09-17"),
        _grade("6", "2026-09-28", description="1 (kartkówka)"),
    ]

    linked = link_grade_corrections(grades)

    original, correction = linked[1], linked[2]
    assert correction["correction_of"] == {
        "grade": "1", "category": "kartkówka", "date": "2026-09-17",
    }
    assert original["corrected_by"] == {
        "grade": "6", "category": "kartkówka", "date": "2026-09-28",
    }
    # Ordinary grades are untouched but carry the keys, so the schema is stable.
    assert linked[0]["correction_of"] is None
    assert linked[0]["corrected_by"] is None
    assert original["correction_of"] is None
    assert correction["corrected_by"] is None


def test_input_is_not_mutated():
    grades = [_grade("1", "2026-09-17"), _grade("6", "2026-09-28", description="1 (kartkówka)")]
    before = copy.deepcopy(grades)

    link_grade_corrections(grades)

    assert grades == before


def test_order_of_input_does_not_matter():
    grades = [_grade("6", "2026-09-28", description="1 (kartkówka)"), _grade("1", "2026-09-17")]

    linked = link_grade_corrections(grades)

    assert linked[0]["correction_of"]["date"] == "2026-09-17"
    assert linked[1]["corrected_by"]["date"] == "2026-09-28"


def test_category_match_ignores_case_and_whitespace():
    grades = [
        _grade("1", "2026-09-17", category="Kartkówka "),
        _grade("6", "2026-09-28", category="kartkówka", description="1 (kartkówka)"),
    ]

    linked = link_grade_corrections(grades)

    assert linked[0]["corrected_by"] is not None
    assert linked[1]["correction_of"]["date"] == "2026-09-17"


def test_category_must_match():
    grades = [
        _grade("1", "2026-09-17", category="odpowiedź ustna"),
        _grade("6", "2026-09-28", description="1 (kartkówka)"),
    ]

    linked = link_grade_corrections(grades)

    assert linked[0]["corrected_by"] is None
    # Still known to be a correction — only the original could not be identified.
    assert linked[1]["correction_of"] == {"grade": "1", "category": "kartkówka", "date": None}


def test_correction_without_category_matches_on_grade_alone():
    grades = [_grade("1", "2026-09-17"), _grade("6", "2026-09-28", description="1")]

    linked = link_grade_corrections(grades)

    assert linked[1]["correction_of"]["date"] == "2026-09-17"


def test_original_missing_from_the_list():
    """E.g. the corrected grade belongs to another semester."""
    grades = [_grade("6", "2026-09-28", description="1 (kartkówka)")]

    linked = link_grade_corrections(grades)

    assert linked[0]["correction_of"] == {"grade": "1", "category": "kartkówka", "date": None}


def test_ambiguous_original_is_not_guessed():
    """Librus gives no date, so two identical candidates cannot be told apart."""
    grades = [
        _grade("1", "2026-09-10"),
        _grade("1", "2026-09-17"),
        _grade("4", "2026-09-28", description="1 (kartkówka)"),
    ]

    linked = link_grade_corrections(grades)

    assert linked[0]["corrected_by"] is None
    assert linked[1]["corrected_by"] is None
    assert linked[2]["correction_of"] == {"grade": "1", "category": "kartkówka", "date": None}


def test_original_dated_after_the_correction_is_not_a_candidate():
    grades = [_grade("6", "2026-09-17", description="1 (kartkówka)"), _grade("1", "2026-09-28")]

    linked = link_grade_corrections(grades)

    assert linked[1]["corrected_by"] is None
    assert linked[0]["correction_of"]["date"] is None


def test_same_day_original_is_a_candidate():
    grades = [_grade("1", "2026-09-28"), _grade("4", "2026-09-28", description="1 (kartkówka)")]

    linked = link_grade_corrections(grades)

    assert linked[0]["corrected_by"]["grade"] == "4"


def test_two_corrections_of_different_grades():
    grades = [
        _grade("1", "2026-09-10", category="sprawdzian"),
        _grade("2", "2026-09-12"),
        _grade("4", "2026-09-20", category="sprawdzian", description="1 (sprawdzian)"),
        _grade("5", "2026-09-25", description="2 (kartkówka)"),
    ]

    linked = link_grade_corrections(grades)

    assert linked[2]["correction_of"]["date"] == "2026-09-10"
    assert linked[3]["correction_of"]["date"] == "2026-09-12"
    assert linked[0]["corrected_by"]["grade"] == "4"
    assert linked[1]["corrected_by"]["grade"] == "5"


def test_a_correction_can_itself_be_corrected():
    grades = [
        _grade("1", "2026-09-10"),
        _grade("3", "2026-09-17", description="1 (kartkówka)"),
        _grade("5", "2026-09-24", description="3 (kartkówka)"),
    ]

    linked = link_grade_corrections(grades)

    assert linked[1]["correction_of"]["date"] == "2026-09-10"
    assert linked[1]["corrected_by"]["grade"] == "5"
    assert linked[2]["correction_of"]["date"] == "2026-09-17"
    assert linked[0]["corrected_by"]["grade"] == "3"


def test_mixed_date_formats_are_compared_as_dates():
    grades = [
        _grade("1", "17.09.2026"),
        _grade("6", "2026-09-28", description="1 (kartkówka)"),
    ]

    linked = link_grade_corrections(grades)

    assert linked[1]["correction_of"]["date"] == "17.09.2026"


def test_unparseable_description_still_marks_a_correction():
    grades = [_grade("1", "2026-09-17"), _grade("6", "2026-09-28", description="coś nieoczekiwanego (x) y")]

    linked = link_grade_corrections(grades)

    assert linked[1]["correction_of"] == {"grade": None, "category": None, "date": None}
    assert linked[0]["corrected_by"] is None


def test_links_never_form_a_loop():
    """Two identical same-day corrections must not replace each other."""
    grades = [
        _grade("1", "2026-09-28", description="1 (kartkówka)"),
        _grade("1", "2026-09-28", description="1 (kartkówka)"),
    ]

    linked = link_grade_corrections(grades)

    replaced = [g for g in linked if g["corrected_by"] is not None]
    assert len(replaced) <= 1
