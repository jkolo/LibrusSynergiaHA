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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.util import slugify

from .const import DOMAIN
from .coordinator import LibrusDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0  # All entities read from coordinator, no per-entity I/O.


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def _srednia_ocen(oceny: list[dict]) -> float | None:
    """Oblicz srednia ocen z listy ocen."""
    wartosci: list[float] = []
    for g in oceny:
        grade_str = g.get("ocena", "")
        try:
            base = float(grade_str[0])
            if len(grade_str) > 1:
                if "+" in grade_str:
                    base += 0.5
                elif "-" in grade_str:
                    base -= 0.25
            wartosci.append(base)
        except (ValueError, IndexError):
            continue
    return round(sum(wartosci) / len(wartosci), 2) if wartosci else None


def _device_info(
    coordinator: DataUpdateCoordinator, config_entry: ConfigEntry
) -> dict[str, Any]:
    """Zwroc informacje o urzadzeniu (wspolne dla wszystkich encji)."""
    data = coordinator.data or {}
    student_info = data.get("student_info")
    name = student_info.name if student_info else "Librus"
    return {
        "identifiers": {(DOMAIN, config_entry.entry_id)},
        "name": f"Librus - {name}",
        "manufacturer": "Librus",
        "model": "Synergia",
    }


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


def _val_oceny(data: dict[str, Any]) -> StateType:
    return len(data.get("oceny", []))


def _attrs_oceny(data: dict[str, Any]) -> dict[str, Any]:
    oceny_wg_przedmiotu = data.get("oceny_wg_przedmiotu", {})
    sa_nowe = any(
        g["jest_nowa"]
        for grades in oceny_wg_przedmiotu.values()
        for g in grades
    )
    return {
        "oceny_wg_przedmiotu": oceny_wg_przedmiotu,
        "liczba_ocen": len(data.get("oceny", [])),
        "liczba_przedmiotow": len(oceny_wg_przedmiotu),
        "sa_nowe_oceny": sa_nowe,
        "semestr": data.get("semestr_biezacy"),
    }


def _val_srednia_ocen(data: dict[str, Any]) -> StateType:
    wszystkie = [
        g
        for oceny in data.get("oceny_wg_przedmiotu", {}).values()
        for g in oceny
    ]
    return _srednia_ocen(wszystkie)


def _attrs_srednia_ocen(data: dict[str, Any]) -> dict[str, Any]:
    srednie_przedmiotow = {
        subject: _srednia_ocen(oceny)
        for subject, oceny in data.get("oceny_wg_przedmiotu", {}).items()
        if _srednia_ocen(oceny) is not None
    }
    return {
        "srednie_wg_przedmiotow": srednie_przedmiotow,
        "semestr": data.get("semestr_biezacy"),
    }


def _val_wiadomosci(data: dict[str, Any]) -> StateType:
    msgs = data.get("wiadomosci", [])
    return sum(1 for m in msgs if m.get("unread", False))


def _attrs_wiadomosci(data: dict[str, Any]) -> dict[str, Any]:
    # Pelna lista (do 10) zeby liczniki byly spojne z native_value;
    # widok "wiadomosci" ograniczamy do 5.
    all_msgs = data.get("wiadomosci", [])
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


def _val_zapowiedzi(data: dict[str, Any]) -> StateType:
    """Liczba nadchodzacych sprawdzianow w oknie 14 dni."""
    zapowiedzi = data.get("zapowiedzi", []) or []
    return sum(1 for z in zapowiedzi if z.get("days_until", 99) <= 14)


def _attrs_zapowiedzi(data: dict[str, Any]) -> dict[str, Any]:
    zapowiedzi = data.get("zapowiedzi", []) or []
    next_event = zapowiedzi[0] if zapowiedzi else None
    return {
        "zapowiedzi": zapowiedzi,
        "liczba_w_3_dni": sum(1 for z in zapowiedzi if z.get("days_until", 99) <= 3),
        "liczba_w_7_dni": sum(1 for z in zapowiedzi if z.get("days_until", 99) <= 7),
        "liczba_w_14_dni": sum(1 for z in zapowiedzi if z.get("days_until", 99) <= 14),
        "liczba_lacznie": len(zapowiedzi),
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
        name="Informacje o uczniu",
        icon="mdi:account-school",
        value_fn=_val_uczen,
        attrs_fn=_attrs_uczen,
    ),
    LibrusSensorEntityDescription(
        key="szczesliwy_numerek",
        name="Szczesliwy numerek",
        icon="mdi:numeric",
        value_fn=_val_lucky,
    ),
    LibrusSensorEntityDescription(
        key="oceny",
        name="Oceny",
        icon="mdi:school",
        value_fn=_val_oceny,
        attrs_fn=_attrs_oceny,
    ),
    LibrusSensorEntityDescription(
        key="srednia_ocen",
        name="Srednia ocen",
        icon="mdi:chart-line",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_val_srednia_ocen,
        attrs_fn=_attrs_srednia_ocen,
    ),
    LibrusSensorEntityDescription(
        key="wiadomosci",
        name="Wiadomosci",
        icon="mdi:message-text",
        value_fn=_val_wiadomosci,
        attrs_fn=_attrs_wiadomosci,
    ),
    LibrusSensorEntityDescription(
        key="zapowiedzi",
        name="Zapowiedzi",
        icon="mdi:calendar-alert",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_val_zapowiedzi,
        attrs_fn=_attrs_zapowiedzi,
    ),
)


# ---------------------------------------------------------------------------
# Generic + per-subject sensor classes
# ---------------------------------------------------------------------------


class LibrusSensor(CoordinatorEntity[LibrusDataUpdateCoordinator], SensorEntity):
    """Generic sensor driven by a LibrusSensorEntityDescription."""

    _attr_has_entity_name = True
    entity_description: LibrusSensorEntityDescription

    def __init__(
        self,
        coordinator: LibrusDataUpdateCoordinator,
        config_entry: ConfigEntry,
        description: LibrusSensorEntityDescription,
    ) -> None:
        """Initialize the sensor from its description."""
        super().__init__(coordinator)
        self.entity_description = description
        self._config_entry = config_entry
        # Zachowujemy historyczny format unique_id zeby nie zlamac
        # istniejacych instalacji (entity registry mapping).
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"

    @property
    def device_info(self) -> dict[str, Any]:
        return _device_info(self.coordinator, self._config_entry)

    @property
    def native_value(self) -> StateType:
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs_fn = self.entity_description.attrs_fn
        if attrs_fn is None:
            return {}
        return attrs_fn(self.coordinator.data or {})


class LibrusPrzedmiotSensor(
    CoordinatorEntity[LibrusDataUpdateCoordinator], SensorEntity
):
    """Czujnik z ocenami dla konkretnego przedmiotu."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:book-open-variant"

    def __init__(
        self,
        coordinator: LibrusDataUpdateCoordinator,
        subject: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Inicjalizacja."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._subject = subject
        safe_name = slugify(subject)
        self._attr_name = subject
        self._attr_unique_id = f"{config_entry.entry_id}_przedmiot_{safe_name}"

    @property
    def device_info(self) -> dict[str, Any]:
        return _device_info(self.coordinator, self._config_entry)

    @property
    def native_value(self) -> int | None:
        # State HA jest ograniczony do 255 znakow - przy duzej liczbie ocen
        # zlaczona lista by sie ucinala. Trzymamy liczbe ocen jako state,
        # pelna lista jest w atrybucie "lista_ocen".
        oceny = (self.coordinator.data or {}).get("oceny_wg_przedmiotu", {}).get(
            self._subject, []
        )
        return len(oceny) if oceny else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        oceny = (self.coordinator.data or {}).get("oceny_wg_przedmiotu", {}).get(
            self._subject, []
        )
        if not oceny:
            return {}

        srednia = _srednia_ocen(oceny)

        # Najnowsza ocena wg daty
        najnowsza: dict | None = None
        najnowsza_data: date | None = None
        for g in oceny:
            for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
                try:
                    d = datetime.strptime(g["data"].strip(), fmt).date()
                    if najnowsza_data is None or d > najnowsza_data:
                        najnowsza_data = d
                        najnowsza = g
                    break
                except ValueError:
                    continue

        return {
            "oceny": oceny,
            "lista_ocen": ", ".join(g["ocena"] for g in oceny),
            "srednia": srednia,
            "najnowsza_ocena": najnowsza,
            "sa_nowe_oceny": any(g["jest_nowa"] for g in oceny),
        }


class LibrusSredniaPrzedmiotuSensor(
    CoordinatorEntity[LibrusDataUpdateCoordinator], SensorEntity
):
    """Czujnik ze srednia ocen dla konkretnego przedmiotu (do wykresu)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:chart-bar"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: LibrusDataUpdateCoordinator,
        subject: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Inicjalizacja."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._subject = subject
        safe_name = slugify(subject)
        self._attr_name = f"Srednia {subject}"
        self._attr_unique_id = f"{config_entry.entry_id}_srednia_{safe_name}"

    @property
    def device_info(self) -> dict[str, Any]:
        return _device_info(self.coordinator, self._config_entry)

    @property
    def native_value(self) -> float | None:
        oceny = (self.coordinator.data or {}).get("oceny_wg_przedmiotu", {}).get(
            self._subject, []
        )
        return _srednia_ocen(oceny)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        oceny = (self.coordinator.data or {}).get("oceny_wg_przedmiotu", {}).get(
            self._subject, []
        )
        return {
            "przedmiot": self._subject,
            "lista_ocen": ", ".join(g["ocena"] for g in oceny),
            "liczba_ocen": len(oceny),
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

    entities: list[SensorEntity] = [
        LibrusSensor(coordinator, config_entry, description)
        for description in SENSORS
    ]

    # Czujniki per przedmiot — na podstawie pierwszego pobrania danych.
    # Dynamic-device discovery (przedmiot pojawiajacy sie mid-semester)
    # jest planowany w EPIC 5b.
    for subject in coordinator.data.get("oceny_wg_przedmiotu", {}).keys():
        entities.append(LibrusPrzedmiotSensor(coordinator, subject, config_entry))
        entities.append(
            LibrusSredniaPrzedmiotuSensor(coordinator, subject, config_entry)
        )

    async_add_entities(entities)
