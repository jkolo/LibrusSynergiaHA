"""Platforma czujników dla integracji Librus APIX."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
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
        grade_str = g.get("ocena", "")
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
        "klasa": info.class_name,
        "numer_w_klasie": info.number,
        "wychowawca": info.tutor,
        "szkola": info.school,
        "szczesliwy_numerek": info.lucky_number,
    }


def _val_lucky(data: dict[str, Any]) -> StateType:
    info = data.get("student_info")
    return info.lucky_number if info else None


def _val_grades_count(data: dict[str, Any]) -> StateType:
    return len(data.get("grades", []))


def _attrs_grades(data: dict[str, Any]) -> dict[str, Any]:
    grades_by_subject = data.get("grades_by_subject", {})
    has_new = any(
        g["jest_nowa"]
        for subject_grades in grades_by_subject.values()
        for g in subject_grades
    )
    return {
        # Polish keys = public API; renamed in EPIC 9 (BREAKING).
        "oceny_wg_przedmiotu": grades_by_subject,
        "liczba_ocen": len(data.get("grades", [])),
        "liczba_przedmiotow": len(grades_by_subject),
        "sa_nowe_oceny": has_new,
        "semestr": data.get("current_semester"),
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
        "srednie_wg_przedmiotow": averages_by_subject,
        "semestr": data.get("current_semester"),
    }


def _val_unread_count(data: dict[str, Any]) -> StateType:
    msgs = data.get("messages", [])
    return sum(1 for m in msgs if m.get("unread", False))


def _attrs_messages(data: dict[str, Any]) -> dict[str, Any]:
    # Full list (up to 10) for consistent counters with native_value;
    # the displayed "wiadomosci" list is limited to 5.
    all_msgs = data.get("messages", [])
    return {
        "wiadomosci": [
            {
                "nadawca": m["author"],
                "temat": m["title"],
                "data": m["date"],
                "nieprzeczytana": m.get("unread", False),
                "jest_nowa": m.get("jest_nowa", False),
                "ma_zalacznik": m.get("has_attachment", False),
            }
            for m in all_msgs[:5]
        ],
        "liczba_nieprzeczytanych": sum(1 for m in all_msgs if m.get("unread", False)),
        "sa_nowe_wiadomosci": any(m.get("jest_nowa", False) for m in all_msgs),
    }


def _val_upcoming_exams_count(data: dict[str, Any]) -> StateType:
    """Number of upcoming exams within a 14-day window."""
    exams = data.get("upcoming_exams", []) or []
    return sum(1 for e in exams if e.get("days_until", 99) <= 14)


def _attrs_upcoming_exams(data: dict[str, Any]) -> dict[str, Any]:
    exams = data.get("upcoming_exams", []) or []
    next_event = exams[0] if exams else None
    return {
        "zapowiedzi": exams,
        "liczba_w_3_dni": sum(1 for e in exams if e.get("days_until", 99) <= 3),
        "liczba_w_7_dni": sum(1 for e in exams if e.get("days_until", 99) <= 7),
        "liczba_w_14_dni": sum(1 for e in exams if e.get("days_until", 99) <= 14),
        "liczba_lacznie": len(exams),
        "najblizsza_data": next_event["date"] if next_event else None,
        "najblizszy_przedmiot": next_event["subject"] if next_event else None,
        "najblizszy_tytul": next_event["title"] if next_event else None,
        "najblizsza_kategoria": next_event["category"] if next_event else None,
        "najblizsza_dni_do": next_event["days_until"] if next_event else None,
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
        value_fn=_val_uczen,
        attrs_fn=_attrs_uczen,
    ),
    LibrusSensorEntityDescription(
        key="szczesliwy_numerek",
        translation_key="lucky_number",
        icon="mdi:numeric",
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
                    d = datetime.strptime(g["data"].strip(), fmt).date()
                    if latest_date is None or d > latest_date:
                        latest_date = d
                        latest = g
                    break
                except ValueError:
                    continue

        # Polish keys = public API; renamed in EPIC 9 (BREAKING).
        return {
            "oceny": grades,
            "lista_ocen": ", ".join(g["ocena"] for g in grades),
            "srednia": average,
            "najnowsza_ocena": latest,
            "sa_nowe_oceny": any(g["jest_nowa"] for g in grades),
        }


class LibrusSubjectAverageSensor(LibrusBaseEntity, SensorEntity):
    """Sensor exposing the numeric average for a single subject (for charts)."""

    _attr_icon = "mdi:chart-bar"
    _attr_state_class = SensorStateClass.MEASUREMENT

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
            "przedmiot": self._subject,
            "lista_ocen": ", ".join(g["ocena"] for g in grades),
            "liczba_ocen": len(grades),
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
        known_subjects.update(new_subjects)
        new_entities: list[SensorEntity] = []
        for subject in new_subjects:
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
