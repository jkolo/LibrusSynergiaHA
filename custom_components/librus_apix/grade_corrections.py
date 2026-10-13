"""Link Librus grade corrections ("Poprawa oceny") to the grades they replace.

Librus flags a correcting grade with a tooltip line such as
``Poprawa oceny: 1 (kartkówka)`` — the value and category of the grade being
replaced, but not its date. The replaced grade carries no marker at all, so
the link is reconstructed here: same subject, same value and category, dated
on or before the correction.

When more than one grade fits, the original is not guessed: the correction
keeps ``date: None`` and no grade is marked as replaced.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

# "1 (kartkówka)", "4+ (sprawdzian)", "2 (praca klasowa (semestralna))", "1".
_CORRECTION_RE = re.compile(r"^(?P<grade>[^\s(]+)\s*(?:\((?P<category>.*)\))?$")

_DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y")


def parse_correction(raw: str | None) -> dict[str, str | None] | None:
    """Parse the ``Poprawa oceny`` value into the replaced grade and category.

    Returns ``None`` when there is no correction at all. Text that is present
    but not in the expected shape still is a correction — the result then
    carries ``None`` values, so the grade can be flagged without being matched.
    """
    text = (raw or "").strip()
    if not text:
        return None
    match = _CORRECTION_RE.match(text)
    if match is None:
        return {"grade": None, "category": None}
    category = (match.group("category") or "").strip()
    return {"grade": match.group("grade"), "category": category or None}


def _normalise(value: Any) -> str:
    return " ".join(str(value or "").split()).casefold()


def _parse_date(value: Any) -> date | None:
    text = str(value or "").strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _is_later(candidate: Any, reference: Any) -> bool:
    """True only when both dates are known and `candidate` is after `reference`."""
    first, second = _parse_date(candidate), _parse_date(reference)
    return first is not None and second is not None and first > second


def link_grade_corrections(grades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return copies of one subject's grades with correction links resolved.

    Every grade gets ``correction_of`` and ``corrected_by`` (``None`` when not
    applicable), so the shape is the same for all of them:

    * ``correction_of`` — on a correcting grade: ``{grade, category, date}`` of
      the grade it replaces; ``date`` is ``None`` when that grade could not be
      identified.
    * ``corrected_by`` — on a replaced grade: ``{grade, category, date}`` of
      the grade that corrected it.
    """
    linked = [{**grade, "correction_of": None, "corrected_by": None} for grade in grades]

    corrections: list[tuple[date, int, dict[str, str | None]]] = []
    for index, grade in enumerate(linked):
        parsed = parse_correction(grade.get("description"))
        if parsed is not None:
            corrections.append((_parse_date(grade.get("date")) or date.min, index, parsed))
    # Oldest correction first, so a chain (1 -> 3 -> 5) resolves in order.
    corrections.sort(key=lambda item: item[:2])

    replaces: dict[int, int] = {}  # correction index -> replaced grade's index

    def _closes_loop(original: int, correction: int) -> bool:
        """True when `original` is itself (transitively) a correction of `correction`."""
        seen: set[int] = set()
        current: int | None = original
        while current is not None and current not in seen:
            if current == correction:
                return True
            seen.add(current)
            current = replaces.get(current)
        return False

    for _, index, parsed in corrections:
        correction = linked[index]
        reference: dict[str, str | None] = {
            "grade": parsed["grade"],
            "category": parsed["category"],
            "date": None,
        }
        correction["correction_of"] = reference
        if parsed["grade"] is None:
            continue

        candidates = [
            position
            for position, other in enumerate(linked)
            if position != index
            and other["corrected_by"] is None
            and _normalise(other.get("grade")) == _normalise(parsed["grade"])
            and (
                parsed["category"] is None
                or _normalise(other.get("category")) == _normalise(parsed["category"])
            )
            and not _is_later(other.get("date"), correction.get("date"))
        ]
        if len(candidates) != 1 or _closes_loop(candidates[0], index):
            continue

        replaces[index] = candidates[0]
        original = linked[candidates[0]]
        reference["date"] = original.get("date")
        original["corrected_by"] = {
            "grade": correction.get("grade"),
            "category": correction.get("category"),
            "date": correction.get("date"),
        }

    return linked
