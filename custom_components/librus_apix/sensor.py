"""Platforma czujników dla integracji Librus APIX."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import slugify

from .coordinator import _BEHAVIOR_GRADE_FIELDS, LibrusDataUpdateCoordinator
from .entity import LibrusBaseEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0  # All entities read from coordinator, no per-entity I/O.


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def _grade_average(grades: list[dict]) -> float | None:
    """Compute the (weighted) average of Polish-style grades (e.g. '4+', '5-').

    Plus modifier adds 0.5; minus subtracts 0.25. Invalid entries are skipped,
    and so are grades that were replaced by a correction (`corrected_by`) —
    the correction counts instead.

    Weights apply only where Librus states them: `counts is False` or
    `weight == 0` leaves a grade out, a missing weight (None) counts as 1.
    Schools without weighted averages give None everywhere — plain mean.
    """
    total = 0.0
    weights = 0
    for g in grades:
        if g.get("corrected_by") or g.get("counts") is False:
            continue
        weight = g.get("weight")
        if weight is None:
            weight = 1
        if weight <= 0:
            continue
        grade_str = g.get("grade", "")
        try:
            base = float(grade_str[0])
            if len(grade_str) > 1:
                if "+" in grade_str:
                    base += 0.5
                elif "-" in grade_str:
                    base -= 0.25
        except (ValueError, IndexError):
            continue
        total += base * weight
        weights += weight
    return round(total / weights, 2) if weights else None


# ---------------------------------------------------------------------------
# value_fn / attrs_fn for static sensors
# ---------------------------------------------------------------------------


def _val_uczen(data: dict[str, Any]) -> StateType:
    info = data.get("student_info")
    return info.name if info else None


def _attrs_uczen(data: dict[str, Any]) -> dict[str, Any]:
    info = data.get("student_info")
    if not info:
        return {}
    return {
        "class_name": info.class_name,
        "class_number": info.number,
        "homeroom_teacher": info.tutor,
        "school": info.school,
        "lucky_number": info.lucky_number,
    }


def _val_lucky(data: dict[str, Any]) -> StateType:
    info = data.get("student_info")
    return info.lucky_number if info else None


def _val_grades_count(data: dict[str, Any]) -> StateType:
    return len(data.get("grades", []))


def _attrs_grades(data: dict[str, Any]) -> dict[str, Any]:
    grades_by_subject = data.get("grades_by_subject", {})
    has_new = any(
        g["is_recent"]
        for subject_grades in grades_by_subject.values()
        for g in subject_grades
    )
    return {
        "grade_count": len(data.get("grades", [])),
        "subject_count": len(grades_by_subject),
        "has_new_grades": has_new,
        "semester": data.get("current_semester"),
    }


def _val_overall_average(data: dict[str, Any]) -> StateType:
    all_grades = [
        g
        for subject_grades in data.get("grades_by_subject", {}).values()
        for g in subject_grades
    ]
    return _grade_average(all_grades)


def _attrs_overall_average(data: dict[str, Any]) -> dict[str, Any]:
    averages_by_subject = {
        subject: _grade_average(subject_grades)
        for subject, subject_grades in data.get("grades_by_subject", {}).items()
        if _grade_average(subject_grades) is not None
    }
    return {
        "averages_by_subject": averages_by_subject,
        "semester": data.get("current_semester"),
    }


def _val_unread_count(data: dict[str, Any]) -> StateType:
    msgs = data.get("messages", [])
    return sum(1 for m in msgs if m.get("unread", False))


def _attrs_messages(data: dict[str, Any]) -> dict[str, Any]:
    # Full list (up to 10) for consistent counters with native_value;
    # the displayed "messages" list is limited to 5.
    all_msgs = data.get("messages", [])
    return {
        "messages": [
            {
                "sender": m["author"],
                "title": m["title"],
                "date": m["date"],
                "unread": m.get("unread", False),
                "is_recent": m.get("is_recent", False),
                "notification_dismissed": m.get("notification_dismissed", False),
                "has_attachment": m.get("has_attachment", False),
                "href": m.get("href", ""),
            }
            for m in all_msgs[:10]
        ],
        "unread_count": sum(1 for m in all_msgs if m.get("unread", False)),
        "undismissed_count": sum(
            1 for m in all_msgs
            if m.get("unread", False) and not m.get("notification_dismissed", False)
        ),
        "has_new_messages": any(m.get("is_recent", False) for m in all_msgs),
    }


# Pola wpisu terminarza wystawiane w atrybutach sensora. Pomijamy `href`,
# `details` i `day_label` — duplikaty/techniczne, a atrybuty musza zmiescic
# sie w 16 KB limicie recordera HA.
_SCHEDULE_ATTR_FIELDS = (
    "date", "weekday", "title", "subject", "category", "description",
    "teacher", "hour", "lesson_number", "event_type", "is_exam",
    "is_day_off", "days_until",
)
# Budzet na liste `events` (bajty JSON). Reszta atrybutow to kilkaset
# bajtow; calosc musi zmiescic sie w 16 KB limicie recordera. Pelny
# terminarz zawsze jest w calendar.terminarz.
_SCHEDULE_EVENTS_BUDGET = 12_000
_SCHEDULE_DESCRIPTION_MAX = 150


def _compact_schedule_event(e: dict[str, Any]) -> dict[str, Any]:
    view = {k: e.get(k) for k in _SCHEDULE_ATTR_FIELDS}
    desc = view.get("description") or ""
    if len(desc) > _SCHEDULE_DESCRIPTION_MAX:
        view["description"] = desc[: _SCHEDULE_DESCRIPTION_MAX - 1] + "…"
    return view


def _val_schedule_count(data: dict[str, Any]) -> StateType:
    """Number of upcoming schedule (terminarz) entries."""
    return len(data.get("schedule") or [])


def _attrs_schedule(data: dict[str, Any]) -> dict[str, Any]:
    events = data.get("schedule") or []
    exams = [e for e in events if e.get("is_exam")]
    by_type: dict[str, int] = {}
    for e in events:
        t = e.get("event_type", "other")
        by_type[t] = by_type.get(t, 0) + 1
    # Budzet najpierw dla sprawdzianow i lektur, potem reszta (np. dziesiatki
    # wpisow "wakat" nie moga wypchnac sprawdzianu z listy); wynik po dacie.
    def _important(e: dict[str, Any]) -> bool:
        return bool(e.get("is_exam")) or e.get("event_type") == "reading"

    indexed = list(enumerate(events))
    picked: list[tuple[int, dict[str, Any]]] = []
    used = 0
    for group in (
        [(i, e) for i, e in indexed if _important(e)],
        [(i, e) for i, e in indexed if not _important(e)],
    ):
        for i, e in group:
            view = _compact_schedule_event(e)
            size = len(json.dumps(view, ensure_ascii=False).encode())
            if used + size > _SCHEDULE_EVENTS_BUDGET:
                break
            picked.append((i, view))
            used += size
    shown = [view for _, view in sorted(picked, key=lambda p: (p[1].get("date") or "", p[0]))]
    return {
        "events": shown,
        "events_truncated": len(shown) < len(events),
        "count": len(events),
        "by_type": by_type,
        "exams_in_3_days": sum(1 for e in exams if e.get("days_until", 99) <= 3),
        "exams_in_7_days": sum(1 for e in exams if e.get("days_until", 99) <= 7),
        "exams_in_14_days": sum(1 for e in exams if e.get("days_until", 99) <= 14),
        "exams_total": len(exams),
    }


# Tematy lekcji: lista od najnowszej w budzecie bajtow + ostatni temat per
# przedmiot; temat przycinany (opisy potrafia miec kilkaset znakow).
_TOPICS_LESSONS_BUDGET = 10_000
_TOPIC_MAX = 200


def _short_topic(topic: str) -> str:
    return topic if len(topic) <= _TOPIC_MAX else topic[: _TOPIC_MAX - 1] + "…"


def _val_lesson_topics(data: dict[str, Any]) -> StateType:
    """Liczba dzisiejszych zrealizowanych lekcji."""
    today = date.today().isoformat()
    return sum(1 for l in data.get("lesson_topics") or [] if l.get("date") == today)


def _attrs_lesson_topics(data: dict[str, Any]) -> dict[str, Any]:
    lessons = data.get("lesson_topics") or []  # od najnowszej
    by_subject: dict[str, str] = {}
    for l in lessons:
        by_subject.setdefault(l.get("subject", ""), _short_topic(l.get("topic") or ""))
    shown: list[dict[str, Any]] = []
    used = 0
    for l in lessons:
        view = dict(l, topic=_short_topic(l.get("topic") or ""))
        size = len(json.dumps(view, ensure_ascii=False).encode())
        if used + size > _TOPICS_LESSONS_BUDGET:
            break
        shown.append(view)
        used += size
    return {
        "lessons": shown,
        "lessons_truncated": len(shown) < len(lessons),
        "by_subject": by_subject,
    }


# Uwagi: 20 najnowszych, tresc przycinana — limit 16 KB recordera.
_NOTES_ATTR_MAX = 20
_NOTE_TEXT_MAX = 300


def _val_notes_count(data: dict[str, Any]) -> StateType:
    """Number of notes (uwagi) in the current school year."""
    return len(data.get("notes") or [])


def _compact_note(n: dict[str, Any]) -> dict[str, Any]:
    view = dict(n)
    text = view.get("text") or ""
    if len(text) > _NOTE_TEXT_MAX:
        view["text"] = text[: _NOTE_TEXT_MAX - 1] + "…"
    return view


def _attrs_notes(data: dict[str, Any]) -> dict[str, Any]:
    notes = data.get("notes") or []  # od najnowszej
    kinds = [n.get("kind") for n in notes]
    shown = [_compact_note(n) for n in notes[:_NOTES_ATTR_MAX]]
    return {
        "notes": shown,
        "notes_truncated": len(shown) < len(notes),
        "count": len(notes),
        "positive": kinds.count("positive"),
        "negative": kinds.count("negative"),
        "neutral": kinds.count("neutral"),
        "latest": shown[0] if shown else None,
    }


# Zachowanie: ocena (tekst) i osobny sensor punktow — stan liczbowy i tekstowy
# w jednej encji psulby state_class/jednostke i historie.
_BEHAVIOR_ENTRIES_MAX = 20


def _val_behavior(data: dict[str, Any]) -> StateType:
    """Najnowsza ocena z zachowania: wystawiona przed przewidywana."""
    behavior = data.get("behavior") or {}
    order = ("grade_sem1", "predicted_sem1")
    if data.get("current_semester") == 2:
        order = ("grade_year", "predicted_year") + order
    return next((behavior[k] for k in order if behavior.get(k)), None)


def _attrs_behavior(data: dict[str, Any]) -> dict[str, Any]:
    behavior = data.get("behavior") or {}
    attrs = {k: behavior.get(k, "") for k in _BEHAVIOR_GRADE_FIELDS}
    attrs["system"] = behavior.get("system")
    return attrs


def _val_behavior_points(data: dict[str, Any]) -> StateType:
    """Suma punktow z zachowania w biezacym okresie."""
    behavior = data.get("behavior") or {}
    return behavior.get(f"points_sem{data.get('current_semester', 1)}")


def _attrs_behavior_points(data: dict[str, Any]) -> dict[str, Any]:
    behavior = data.get("behavior") or {}
    entries = behavior.get("entries") or []  # od najnowszego
    semester = data.get("current_semester", 1)
    points = [
        e.get("points") or 0 for e in entries if e.get("semester") == semester
    ]
    shown = entries[:_BEHAVIOR_ENTRIES_MAX]
    return {
        "points_start": behavior.get("points_start"),
        "points_sem1": behavior.get("points_sem1"),
        "points_sem2": behavior.get("points_sem2"),
        "positive_sum": sum(p for p in points if p > 0),
        "negative_sum": sum(p for p in points if p < 0),
        "entries": shown,
        "entries_truncated": len(shown) < len(entries),
    }


# Pola zadania domowego wystawiane w atrybutach (bez href/due_date_raw).
_HOMEWORK_ATTR_FIELDS = (
    "subject", "category", "teacher", "lesson", "task_date", "due_date",
    "days_until",
)


def _val_homework_count(data: dict[str, Any]) -> StateType:
    """Number of homework items due in the fetched window (30 days)."""
    return len(data.get("homework") or [])


def _attrs_homework(data: dict[str, Any]) -> dict[str, Any]:
    items = data.get("homework") or []
    by_subject: dict[str, int] = {}
    for h in items:
        subj = h.get("subject", "")
        by_subject[subj] = by_subject.get(subj, 0) + 1

    def _due_within(days: int) -> int:
        return sum(
            1 for h in items
            if h.get("days_until") is not None and h["days_until"] <= days
        )

    return {
        "homework": [{k: h.get(k) for k in _HOMEWORK_ATTR_FIELDS} for h in items],
        "count": len(items),
        "by_subject": by_subject,
        "due_in_3_days": _due_within(3),
        "due_in_7_days": _due_within(7),
    }


def _parse_grade_date(date_str: str) -> date | None:
    """Parse a Librus date string in either ISO or DD.MM.YYYY format."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _latest_grade_entry(data: dict[str, Any]) -> dict[str, Any] | None:
    """Return the grade dict with the latest parseable date, or None."""
    grades = data.get("grades") or []
    latest: dict[str, Any] | None = None
    latest_date: date | None = None
    for grade in grades:
        d = _parse_grade_date(grade.get("date", ""))
        if d is None:
            continue
        if latest_date is None or d > latest_date:
            latest_date = d
            latest = grade
    return latest


def _val_latest_grade(data: dict[str, Any]) -> StateType:
    grade = _latest_grade_entry(data)
    return grade["grade"] if grade else None


def _val_latest_message(data: dict[str, Any]) -> StateType:
    msgs = data.get("messages") or []
    if not msgs:
        return None
    return msgs[0].get("author") or None


def _attrs_latest_message(data: dict[str, Any]) -> dict[str, Any]:
    msgs = data.get("messages") or []
    if not msgs:
        return {}
    msg = msgs[0]
    return {
        "sender": msg.get("author", ""),
        "title": msg.get("title", ""),
        "date": msg.get("date", ""),
        "unread": bool(msg.get("unread", False)),
        "has_attachment": bool(msg.get("has_attachment", False)),
        "is_recent": bool(msg.get("is_recent", False)),
        "notification_dismissed": bool(msg.get("notification_dismissed", False)),
        "href": msg.get("href", ""),
    }


def _val_next_exam(data: dict[str, Any]) -> StateType:
    exams = data.get("upcoming_exams") or []
    if not exams:
        return None
    return exams[0].get("days_until")


def _attrs_next_exam(data: dict[str, Any]) -> dict[str, Any]:
    exams = data.get("upcoming_exams") or []
    if not exams:
        return {}
    e = exams[0]
    return {
        "subject": e.get("subject", ""),
        "title": e.get("title", ""),
        "category": e.get("category", ""),
        "date": e.get("date", ""),
        "hour": e.get("hour", ""),
    }


def _val_frequency(data: dict[str, Any]) -> StateType:
    # None (brak danych), nigdy 0.0 — wczesniej 0.0 udawalo prawdziwa wartosc.
    return (data.get("attendance_frequency") or {}).get("current")


def _attrs_frequency(data: dict[str, Any]) -> dict[str, Any]:
    freq = data.get("attendance_frequency") or {}
    if not freq:
        return {}
    return {
        "semester_1": freq.get("semester_1"),
        "semester_2": freq.get("semester_2"),
        "total": freq.get("total"),
        "by_subject": data.get("attendance_by_subject", {}),
    }


def _absence_view(entry: dict[str, Any]) -> dict[str, Any]:
    """Public-facing view of an attendance entry (subset of fields)."""
    return {
        "date": entry.get("date", ""),
        "subject": entry.get("subject", ""),
        "period": entry.get("period"),
        "teacher": entry.get("teacher", ""),
        "topic": entry.get("topic", ""),
        "type": entry.get("type", ""),
        "symbol": entry.get("symbol", ""),
        "is_unjustified": bool(entry.get("is_unjustified", False)),
        "is_excused": bool(entry.get("is_excused", False)),
        "is_late": bool(entry.get("is_late", False)),
    }


def _val_absences_count(data: dict[str, Any]) -> StateType:
    """Total entries that are absences (any kind) or lates."""
    return sum(
        1
        for e in (data.get("attendance") or [])
        if e.get("is_absence") or e.get("is_late")
    )


# Atrybuty nieobecnosci: N najnowszych wpisow — limit 16 KB recordera
# (produkcja: 63 nieobecnosci = 26,5 KB). Pelne dane: kalendarz Obecnosci.
_ABSENCES_ATTR_MAX = 30
_LATES_ATTR_MAX = 15


def _attrs_absences(data: dict[str, Any]) -> dict[str, Any]:
    entries = data.get("attendance") or []  # rosnaco po dacie
    absences = [e for e in entries if e.get("is_absence")]
    lates = [e for e in entries if e.get("is_late")]
    excused = [e for e in entries if e.get("is_excused")]
    unjustified = [e for e in entries if e.get("is_unjustified")]
    shown_absences = absences[-_ABSENCES_ATTR_MAX:]
    shown_lates = lates[-_LATES_ATTR_MAX:]
    return {
        "total_absences": len(absences),
        "unjustified_count": len(unjustified),
        "excused_count": len(excused),
        "lates_count": len(lates),
        "absences": [_absence_view(e) for e in shown_absences],
        "absences_truncated": len(shown_absences) < len(absences),
        "lates": [_absence_view(e) for e in shown_lates],
        "lates_truncated": len(shown_lates) < len(lates),
        "absence_dates": [e.get("date", "") for e in absences],
        "late_dates": [e.get("date", "") for e in lates],
    }


def _latest_absence_entry(data: dict[str, Any]) -> dict[str, Any] | None:
    entries = [
        e
        for e in (data.get("attendance") or [])
        if e.get("is_absence") or e.get("is_late")
    ]
    if not entries:
        return None
    # Coordinator already sorts ascending by date; take the last one.
    latest: dict[str, Any] | None = None
    latest_date: date | None = None
    for e in entries:
        d = _parse_grade_date(e.get("date", ""))
        if d is None:
            continue
        if latest_date is None or d > latest_date:
            latest_date = d
            latest = e
    return latest


def _val_latest_absence(data: dict[str, Any]) -> StateType:
    e = _latest_absence_entry(data)
    return e.get("date") if e else None


def _attrs_latest_absence(data: dict[str, Any]) -> dict[str, Any]:
    e = _latest_absence_entry(data)
    return _absence_view(e) if e else {}


def _val_announcements_count(data: dict[str, Any]) -> StateType:
    return len(data.get("announcements") or [])


def _attrs_announcements(data: dict[str, Any]) -> dict[str, Any]:
    items = data.get("announcements") or []
    # Top 5 — full lista mogłaby przekroczyć limit atrybutów HA przy bardzo
    # długich opisach.
    return {
        "announcements": [
            {
                "title": a.get("title", ""),
                "author": a.get("author", ""),
                "date": a.get("date", ""),
                "description": a.get("description", ""),
            }
            for a in items[:5]
        ],
        "total_count": len(items),
    }


def _val_latest_announcement(data: dict[str, Any]) -> StateType:
    items = data.get("announcements") or []
    if not items:
        return None
    return items[0].get("title") or None


def _attrs_latest_announcement(data: dict[str, Any]) -> dict[str, Any]:
    items = data.get("announcements") or []
    if not items:
        return {}
    a = items[0]
    return {
        "author": a.get("author", ""),
        "date": a.get("date", ""),
        "description": a.get("description", ""),
    }


def _grade_details_view(grades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a per-subject grade history with full per-grade context."""
    return [
        {
            "subject": g.get("subject", ""),
            "grade": g.get("grade", ""),
            "value": g.get("value"),
            "date": g.get("date", ""),
            "category": g.get("category", ""),
            "description": g.get("description", ""),
            "weight": g.get("weight"),
            "counts": g.get("counts"),
            "teacher": g.get("teacher", ""),
            "title": g.get("title", ""),
            "comment": g.get("comment", ""),
            "is_recent": bool(g.get("is_recent", False)),
            "correction_of": g.get("correction_of"),
            "corrected_by": g.get("corrected_by"),
        }
        for g in grades
    ]


def _attrs_latest_grade(data: dict[str, Any]) -> dict[str, Any]:
    grade = _latest_grade_entry(data)
    if not grade:
        return {}
    return {
        "subject": grade.get("subject", ""),
        "grade": grade.get("grade", ""),
        "value": grade.get("value"),
        "counts": grade.get("counts"),
        "weight": grade.get("weight"),
        "date": grade.get("date", ""),
        "category": grade.get("category", ""),
        "description": grade.get("description", ""),
        "title": grade.get("title", ""),
        "teacher": grade.get("teacher", ""),
        "semester": grade.get("semester"),
    }


# ---------------------------------------------------------------------------
# EntityDescription
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class LibrusSensorEntityDescription(SensorEntityDescription):
    """Entity description for static (non-per-subject) Librus sensors."""

    value_fn: Callable[[dict[str, Any]], StateType]
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


# Klucze (`key`) zostaja po polsku zeby nie złamać unique_id istniejących
# instalacji — to stabilny identyfikator. translation_key bedzie po angielsku
# w EPIC 8 (translations), wtedy strings.json/translations/pl.json dostarcza
# czytelne nazwy w UI.
SENSORS: tuple[LibrusSensorEntityDescription, ...] = (
    LibrusSensorEntityDescription(
        key="uczen",
        translation_key="student_info",
        icon="mdi:account-school",
        # Diagnostic — student name/class is metadata, not the primary value.
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_val_uczen,
        attrs_fn=_attrs_uczen,
    ),
    LibrusSensorEntityDescription(
        key="szczesliwy_numerek",
        translation_key="lucky_number",
        icon="mdi:numeric",
        # Diagnostic — daily fun number, not actionable telemetry.
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_val_lucky,
    ),
    LibrusSensorEntityDescription(
        key="oceny",
        translation_key="grades",
        icon="mdi:school",
        value_fn=_val_grades_count,
        attrs_fn=_attrs_grades,
    ),
    LibrusSensorEntityDescription(
        key="srednia_ocen",
        translation_key="overall_average",
        icon="mdi:chart-line",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_val_overall_average,
        attrs_fn=_attrs_overall_average,
    ),
    LibrusSensorEntityDescription(
        key="wiadomosci",
        translation_key="messages",
        icon="mdi:message-text",
        value_fn=_val_unread_count,
        attrs_fn=_attrs_messages,
    ),
    LibrusSensorEntityDescription(
        key="terminarz",
        translation_key="schedule",
        icon="mdi:calendar-month",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_val_schedule_count,
        attrs_fn=_attrs_schedule,
    ),
    LibrusSensorEntityDescription(
        key="zadania",
        translation_key="homework",
        icon="mdi:book-open-page-variant",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_val_homework_count,
        attrs_fn=_attrs_homework,
    ),
    LibrusSensorEntityDescription(
        key="uwagi",
        translation_key="notes",
        icon="mdi:alert-box-outline",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_val_notes_count,
        attrs_fn=_attrs_notes,
    ),
    LibrusSensorEntityDescription(
        key="tematy",
        translation_key="lesson_topics",
        icon="mdi:book-open-variant",
        value_fn=_val_lesson_topics,
        attrs_fn=_attrs_lesson_topics,
    ),
    LibrusSensorEntityDescription(
        key="zachowanie",
        translation_key="behavior",
        icon="mdi:emoticon-outline",
        value_fn=_val_behavior,
        attrs_fn=_attrs_behavior,
    ),
    # ---- v3.0 NEW: latest_/next_ sensors ----
    LibrusSensorEntityDescription(
        key="latest_grade",
        translation_key="latest_grade",
        icon="mdi:school-outline",
        value_fn=_val_latest_grade,
        attrs_fn=_attrs_latest_grade,
    ),
    LibrusSensorEntityDescription(
        key="latest_message",
        translation_key="latest_message",
        icon="mdi:email-outline",
        value_fn=_val_latest_message,
        attrs_fn=_attrs_latest_message,
    ),
    LibrusSensorEntityDescription(
        key="next_exam",
        translation_key="next_exam",
        icon="mdi:calendar-clock",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="d",
        value_fn=_val_next_exam,
        attrs_fn=_attrs_next_exam,
    ),
    # ---- v3.0 NEW: attendance domain ----
    LibrusSensorEntityDescription(
        key="frekwencja",
        translation_key="attendance_frequency",
        icon="mdi:account-check",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        value_fn=_val_frequency,
        attrs_fn=_attrs_frequency,
    ),
    LibrusSensorEntityDescription(
        key="nieobecnosci",
        translation_key="absences",
        icon="mdi:account-minus",
        value_fn=_val_absences_count,
        attrs_fn=_attrs_absences,
    ),
    LibrusSensorEntityDescription(
        key="latest_absence",
        translation_key="latest_absence",
        icon="mdi:calendar-remove",
        value_fn=_val_latest_absence,
        attrs_fn=_attrs_latest_absence,
    ),
    # ---- v3.0 NEW: announcements domain ----
    LibrusSensorEntityDescription(
        key="ogloszenia",
        translation_key="announcements",
        icon="mdi:bullhorn",
        value_fn=_val_announcements_count,
        attrs_fn=_attrs_announcements,
    ),
    LibrusSensorEntityDescription(
        key="latest_announcement",
        translation_key="latest_announcement",
        icon="mdi:bullhorn-outline",
        value_fn=_val_latest_announcement,
        attrs_fn=_attrs_latest_announcement,
    ),
)

# Poza SENSORS — tworzony dopiero, gdy szkola ma punktowy system zachowania.
BEHAVIOR_POINTS_SENSOR = LibrusSensorEntityDescription(
    key="punkty_zachowania",
    translation_key="behavior_points",
    icon="mdi:counter",
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement="pkt",
    value_fn=_val_behavior_points,
    attrs_fn=_attrs_behavior_points,
)


# ---------------------------------------------------------------------------
# Generic + per-subject sensor classes
# ---------------------------------------------------------------------------


class LibrusSensor(LibrusBaseEntity, SensorEntity):
    """Generic sensor driven by a LibrusSensorEntityDescription."""

    entity_description: LibrusSensorEntityDescription

    def __init__(
        self,
        coordinator: LibrusDataUpdateCoordinator,
        config_entry: ConfigEntry,
        description: LibrusSensorEntityDescription,
    ) -> None:
        """Initialize the sensor from its description."""
        super().__init__(coordinator, config_entry)
        self.entity_description = description
        # Zachowujemy historyczny format unique_id zeby nie zlamac
        # istniejacych instalacji (entity registry mapping).
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        return self.entity_description.value_fn(self._data())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs_fn = self.entity_description.attrs_fn
        if attrs_fn is None:
            return {}
        return attrs_fn(self._data())


class LibrusSubjectGradesSensor(LibrusBaseEntity, SensorEntity):
    """Sensor exposing grades for a single subject."""

    _attr_icon = "mdi:book-open-variant"
    # v3.0: enabled by default. Users opt-out via OptionsFlow `enabled_subjects`
    # multi-select — sensor.py refuses to instantiate excluded subjects, the
    # entity registry handles cleanup on reload.
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        coordinator: LibrusDataUpdateCoordinator,
        subject: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the per-subject grades sensor."""
        super().__init__(coordinator, config_entry)
        self._subject = subject
        safe_name = slugify(subject)
        self._attr_name = subject
        self._attr_unique_id = f"{config_entry.entry_id}_przedmiot_{safe_name}"

    @property
    def native_value(self) -> int | None:
        # HA state is capped at 255 characters; for many grades the joined
        # list would truncate. We keep the grade count as state and the
        # full list in the "lista_ocen" attribute.
        grades = self._data().get("grades_by_subject", {}).get(self._subject, [])
        return len(grades)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        grades = self._data().get("grades_by_subject", {}).get(self._subject, [])
        if not grades:
            return {}

        average = _grade_average(grades)

        # Latest grade by date.
        latest: dict | None = None
        latest_date: date | None = None
        for g in grades:
            for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
                try:
                    d = datetime.strptime(g["date"].strip(), fmt).date()
                    if latest_date is None or d > latest_date:
                        latest_date = d
                        latest = g
                    break
                except ValueError:
                    continue

        return {
            "subject": self._subject,
            "grade_list": ", ".join(g["grade"] for g in grades),
            "grade_details": _grade_details_view(grades),
            "average": average,
            "latest_grade": latest,
            "has_new_grades": any(g["is_recent"] for g in grades),
        }


class LibrusSubjectAverageSensor(LibrusBaseEntity, SensorEntity):
    """Sensor exposing the numeric average for a single subject (for charts)."""

    _attr_icon = "mdi:chart-bar"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        coordinator: LibrusDataUpdateCoordinator,
        subject: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the per-subject average sensor."""
        super().__init__(coordinator, config_entry)
        self._subject = subject
        safe_name = slugify(subject)
        self._attr_name = f"Srednia {subject}"
        self._attr_unique_id = f"{config_entry.entry_id}_srednia_{safe_name}"

    @property
    def native_value(self) -> float | None:
        grades = self._data().get("grades_by_subject", {}).get(self._subject, [])
        return _grade_average(grades)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        grades = self._data().get("grades_by_subject", {}).get(self._subject, [])
        return {
            "subject": self._subject,
            "grade_list": ", ".join(g["grade"] for g in grades),
            "grade_count": len(grades),
        }


# ---------------------------------------------------------------------------
# Diagnostic: last refresh timestamps
# ---------------------------------------------------------------------------


class LibrusRefreshDiagSensor(LibrusBaseEntity, SensorEntity):
    """Sensor diagnostyczny z timestampem ostatniego odświeżenia per krok."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-sync"
    _attr_translation_key = "last_refresh"

    def __init__(
        self,
        coordinator: LibrusDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, config_entry)

    @property
    def unique_id(self) -> str:
        return f"{self._config_entry.entry_id}_odswiezenie"

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator._last_full_refresh

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        return {
            step: ts.isoformat() if ts else None
            for step, ts in self.coordinator._step_timestamps.items()
        }


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Konfiguracja platformy czujnikow Librus APIX."""
    coordinator: LibrusDataUpdateCoordinator = config_entry.runtime_data.coordinator

    static_entities: list[SensorEntity] = [
        LibrusSensor(coordinator, config_entry, description)
        for description in SENSORS
    ]
    static_entities.append(LibrusRefreshDiagSensor(coordinator, config_entry))
    async_add_entities(static_entities)

    # Per-subject sensors — track newly appearing subjects. The first refresh
    # already ran, so the initial subject list is immediately available; the
    # coordinator listener picks up entries added mid-semester (Gold rule
    # dynamic-devices).
    known_subjects: set[str] = set()

    @callback
    def _add_subject_sensors() -> None:
        current_subjects = set(
            (coordinator.data or {}).get("grades_by_subject", {}).keys()
        )
        new_subjects = current_subjects - known_subjects
        if not new_subjects:
            return
        # User-side filter: gdy w options ustawiona jest lista wybranych
        # przedmiotow, omijamy te poza listy. None / brak klucza = wszystko
        # wlaczone (zachowanie default w v3).
        enabled = config_entry.options.get("enabled_subjects")
        known_subjects.update(new_subjects)
        new_entities: list[SensorEntity] = []
        for subject in new_subjects:
            if enabled is not None and subject not in enabled:
                continue
            new_entities.append(
                LibrusSubjectGradesSensor(coordinator, subject, config_entry)
            )
            new_entities.append(
                LibrusSubjectAverageSensor(coordinator, subject, config_entry)
            )
        async_add_entities(new_entities)

    # Initial add + listener for every subsequent refresh.
    _add_subject_sensors()
    config_entry.async_on_unload(coordinator.async_add_listener(_add_subject_sensors))

    # Punkty z zachowania — tylko w szkolach z systemem punktowym; szkola
    # moze go wlaczyc w trakcie roku, wiec tez przez listener.
    points_added = False

    @callback
    def _add_behavior_points_sensor() -> None:
        nonlocal points_added
        behavior = (coordinator.data or {}).get("behavior") or {}
        if points_added or behavior.get("system") != "points":
            return
        points_added = True
        async_add_entities([
            LibrusSensor(coordinator, config_entry, BEHAVIOR_POINTS_SENSOR)
        ])

    _add_behavior_points_sensor()
    config_entry.async_on_unload(
        coordinator.async_add_listener(_add_behavior_points_sensor)
    )
