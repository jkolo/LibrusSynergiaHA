"""Tests for _async_ensure_lovelace_resource deduplication.

Production had every Librus card registered several times
(?v=3.8.0, ?v=3.8.1 twice, ?v=4.0.0). The browser loads each URL, so
customElements.define() throws for the duplicates and whichever version
loads first wins — possibly a stale card. Ensuring a resource must leave
exactly one entry per card path.
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from custom_components.librus_apix import _async_ensure_lovelace_resource

_PATH = "/librus_apix/librus-grades-card.js"
_OTHER = "/hacsfiles/mini-graph-card/mini-graph-card-bundle.js"


def _storage(*urls: str) -> dict[str, Any]:
    return {
        "version": 1,
        "minor_version": 1,
        "key": "lovelace_resources",
        "data": {
            "items": [
                {"id": f"id{i}", "url": u, "type": "module"}
                for i, u in enumerate(urls)
            ]
        },
    }


class _FakeResources:
    """Minimal stand-in for the live ResourceStorageCollection."""

    def __init__(self, urls: list[str]) -> None:
        self.items = [
            {"id": f"live{i}", "url": u, "type": "module"}
            for i, u in enumerate(urls)
        ]

    def async_items(self) -> list[dict]:
        return list(self.items)

    async def async_create_item(self, data: dict) -> dict:
        item = {"id": f"live{len(self.items)}", "url": data["url"], "type": "module"}
        self.items.append(item)
        return item

    async def async_update_item(self, item_id: str, data: dict) -> dict:
        for item in self.items:
            if item["id"] == item_id:
                item["url"] = data["url"]
                return item
        raise KeyError(item_id)

    async def async_delete_item(self, item_id: str) -> None:
        self.items = [i for i in self.items if i["id"] != item_id]


async def test_store_duplicates_collapse_to_single_current_url(
    hass: HomeAssistant, hass_storage: dict[str, Any]
):
    hass_storage["lovelace_resources"] = _storage(
        f"{_PATH}?v=3.8.0", _OTHER, f"{_PATH}?v=3.8.1", f"{_PATH}?v=3.8.1",
    )

    await _async_ensure_lovelace_resource(hass, f"{_PATH}?v=4.0.0")
    await hass.async_block_till_done()

    urls = [i["url"] for i in hass_storage["lovelace_resources"]["data"]["items"]]
    assert urls.count(f"{_PATH}?v=4.0.0") == 1
    assert [u for u in urls if u.startswith(_PATH)] == [f"{_PATH}?v=4.0.0"]
    assert _OTHER in urls


async def test_live_collection_duplicates_are_deleted(
    hass: HomeAssistant, hass_storage: dict[str, Any]
):
    hass_storage["lovelace_resources"] = _storage(f"{_PATH}?v=4.0.0")
    live = _FakeResources([f"{_PATH}?v=3.8.0", _OTHER, f"{_PATH}?v=4.0.0"])
    hass.data["lovelace"] = type("LovelaceData", (), {"resources": live})()

    await _async_ensure_lovelace_resource(hass, f"{_PATH}?v=4.0.0")

    urls = [i["url"] for i in live.items]
    assert [u for u in urls if u.startswith(_PATH)] == [f"{_PATH}?v=4.0.0"]
    assert _OTHER in urls


async def test_concurrent_calls_keep_all_cards(
    hass: HomeAssistant, hass_storage: dict[str, Any]
):
    """Trzy karty rejestrowane równolegle (jak w async_setup) — każda ma
    dokładnie jeden wpis. Test regresji; nie odtwarza wyścigu load/save
    (Store w testach serializuje zapisy), przed którym chroni blokada."""
    import asyncio

    hass_storage["lovelace_resources"] = _storage(_OTHER)
    paths = [
        "/librus_apix/librus-messages-card.js",
        "/librus_apix/librus-grades-card.js",
        "/librus_apix/librus-subject-grades-card.js",
    ]
    await asyncio.gather(*(
        _async_ensure_lovelace_resource(hass, f"{p}?v=4.0.0") for p in paths
    ))
    await hass.async_block_till_done()

    urls = [i["url"] for i in hass_storage["lovelace_resources"]["data"]["items"]]
    for p in paths:
        assert urls.count(f"{p}?v=4.0.0") == 1
    assert _OTHER in urls
