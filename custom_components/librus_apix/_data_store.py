"""Persystentny cache pełnych danych Librusa (coordinator.data)."""

from __future__ import annotations

import dataclasses
import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
_KEY_FORMAT = "librus_apix.{entry_id}.data_cache"


class LibrusDataStore:
    """Cache wszystkich danych pobieranych przez coordinator.

    Zapis: po każdym udanym refreshie.
    Odczyt: przy async_setup_entry — jeśli cache istnieje, coordinator
    startuje z nim bez połączenia z Librusem.
    """

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store = Store(
            hass,
            STORAGE_VERSION,
            _KEY_FORMAT.format(entry_id=entry_id),
        )

    async def async_load(self) -> tuple[dict[str, Any], datetime] | None:
        """Wczytaj cache.

        Zwraca (coordinator_data, saved_at) lub None gdy brak/uszkodzony cache.
        """
        raw = await self._store.async_load()
        if not raw:  # None lub {} (wyczyszczony przez async_clear)
            return None
        try:
            saved_at_str = raw.get("_saved_at")
            saved_at = dt_util.parse_datetime(saved_at_str) if saved_at_str else None
            if saved_at is None:
                return None
            data = self._from_json_safe(raw.get("data") or {})
            return data, saved_at
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Librus data cache corrupted — ignoring, will re-fetch")
            return None

    async def async_save(self, data: dict[str, Any], timestamp: datetime) -> None:
        """Zapisz coordinator.data i timestamp do storage."""
        try:
            await self._store.async_save({
                "_saved_at": timestamp.isoformat(),
                "data": self._to_json_safe(data),
            })
        except (TypeError, ValueError) as err:
            _LOGGER.warning("Librus data cache save failed (non-serializable data): %s", err)

    async def async_clear(self) -> None:
        """Usuń cache (np. po reauthentykacji)."""
        await self._store.async_save({})

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    def _to_json_safe(self, data: dict[str, Any]) -> dict[str, Any]:
        """Konwertuj coordinator.data do formatu JSON-safe."""
        result = dict(data)
        student_info = result.get("student_info")
        if student_info is not None and dataclasses.is_dataclass(student_info) and not isinstance(student_info, type):
            result["student_info"] = dataclasses.asdict(student_info)
        return result

    def _from_json_safe(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Przywróć coordinator.data z formatu JSON."""
        from librus_apix.student_information import StudentInformation  # local import — avoid circular

        result = dict(raw)
        student_info_raw = result.get("student_info")
        if isinstance(student_info_raw, dict):
            try:
                result["student_info"] = StudentInformation(**student_info_raw)
            except (TypeError, KeyError):
                _LOGGER.warning("Could not deserialize student_info from cache")
                result["student_info"] = None
        return result
