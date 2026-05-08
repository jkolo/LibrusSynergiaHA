"""Platforma czujników dla integracji Librus APIX."""

from __future__ import annotations

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

from .coordinator import LibrusDataUpdateCoordinator
from .entity import LibrusBaseEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0  # All entities read from coordinator, no per-entity I/O.


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def _grade_average(grades: list[dict]) -> float | None:
    """Compute the numeric average of Polish-style grades (e.g. '4+', '5-').

    Plus modifier adds 0.5; minus subtracts 0.25. Invalid entries are skipped.
    """
    values: list[float] = []
    for g in grades:
        grade_str = g.get("grade", "")
        try:
            base = float(grade_str[0])
            if len(grade_str) > 1:
                if "+" in grade_str:
                    base += 0.5
                elif "-" in grade_str:
                    base -= 0.25
            values.append(base)
        except (ValueError, IndexError):
            continue
    return round(sum(values) / len(values), 2) if values else None


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


def _val_upcoming_exams_count(data: dict[str, Any]) -> StateType:
    """Number of upcoming exams within a 14-day window."""
    exams = data.get("upcoming_exams", []) or []
    return sum(1 for e in exams if e.get("days_until", 99) <= 14)


def _attrs_upcoming_exams(data: dict[str, Any]) -> dict[str, Any]:
    exams = data.get("upcoming_exams", []) or []
    return {
        "exams": exams,
        "count_in_3_days": sum(1 for e in exams if e.get("days_until", 99) <= 3),
        "count_in_7_days": sum(1 for e in exams if e.get("days_until", 99) <= 7),
        "count_in_14_days": sum(1 for e in exams if e.get("days_until", 99) <= 14),
        "total_count": len(exams),
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
    freq = data.get("attendance_frequency") or {}
    if not freq:
        return 0.0
    return freq.get("current", 0.0)


def _attrs_frequency(data: dict[str, Any]) -> dict[str, Any]:
    freq = data.get("attendance_frequency") or {}
    if not freq:
        return {}
    return {
        "semester_1": freq.get("semester_1", 0.0),
        "semester_2": freq.get("semester_2", 0.0),
        "total": freq.get("total", 0.0),
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


def _attrs_absences(data: dict[str, Any]) -> dict[str, Any]:
    entries = data.get("attendance") or []
    absences = [e for e in entries if e.get("is_absence")]
    lates = [e for e in entries if e.get("is_late")]
    excused = [e for e in entries if e.get("is_excused")]
    unjustified = [e for e in entries if e.get("is_unjustified")]
    return {
        "total_absences": len(absences),
        "unjustified_count": len(unjustified),
        "excused_count": len(excused),
        "lates_count": len(lates),
        "absences": [_absence_view(e) for e in absences],
        "lates": [_absence_view(e) for e in lates],
        "excused": [_absence_view(e) for e in excused],
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
        key="zapowiedzi",
        translation_key="upcoming_exams",
        icon="mdi:calendar-alert",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_val_upcoming_exams_count,
        attrs_fn=_attrs_upcoming_exams,
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
        return len(grades) if grades else None

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
