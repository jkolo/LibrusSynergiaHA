"""Base entity for the Librus APIX integration.

Wspolny CoordinatorEntity z `device_info` zeby wszystkie encje (sensor,
calendar, ...) trafialy do jednego device "Librus - {imie ucznia}" w HA.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LibrusDataUpdateCoordinator


class LibrusBaseEntity(CoordinatorEntity[LibrusDataUpdateCoordinator]):
    """Bazowa encja Librus z device_info wspolnym dla calej integracji."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LibrusDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._config_entry = config_entry

    @property
    def device_info(self) -> DeviceInfo:
        """Zwroc informacje o urzadzeniu (jedno per config entry / dziecko)."""
        data = self.coordinator.data or {}
        student_info = data.get("student_info")
        name = student_info.name if student_info else "Librus"
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name=f"Librus - {name}",
            manufacturer="Librus",
            model="Synergia",
        )

    def _data(self) -> dict[str, Any]:
        """Skrot dla `self.coordinator.data or {}` uzywany w propertach."""
        return self.coordinator.data or {}
