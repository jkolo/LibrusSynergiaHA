"""Persystentny store lokalnych mark-as-read flag dla wiadomości Librus."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

STORAGE_VERSION = 1
STORAGE_VERSION_MINOR = 1
_KEY_FORMAT = "librus_apix.{entry_id}.read_messages"


class ReadMessagesStore:
    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store = Store(
            hass,
            STORAGE_VERSION,
            _KEY_FORMAT.format(entry_id=entry_id),
            minor_version=STORAGE_VERSION_MINOR,
        )
        self._read_hrefs: set[str] = set()

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self._read_hrefs = set(data.get("read_hrefs", []))

    def is_read(self, href: str) -> bool:
        return href in self._read_hrefs

    async def async_mark_read(self, href: str) -> bool:
        if href in self._read_hrefs:
            return False
        self._read_hrefs.add(href)
        await self._save()
        return True

    async def async_mark_unread(self, href: str) -> bool:
        if href not in self._read_hrefs:
            return False
        self._read_hrefs.discard(href)
        await self._save()
        return True

    async def async_clear(self) -> int:
        n = len(self._read_hrefs)
        self._read_hrefs.clear()
        await self._save()
        return n

    async def async_purge_stale(self, active_hrefs: set[str]) -> int:
        before = len(self._read_hrefs)
        self._read_hrefs &= active_hrefs
        removed = before - len(self._read_hrefs)
        if removed > 0:
            await self._save()
        return removed

    async def _save(self) -> None:
        await self._store.async_save({
            "read_hrefs": sorted(self._read_hrefs),
            "last_updated": dt_util.utcnow().isoformat(),
        })
