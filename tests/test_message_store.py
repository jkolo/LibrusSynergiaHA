"""Tests for ReadMessagesStore — persistent local mark-as-read store."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from custom_components.librus_apix._message_store import ReadMessagesStore


async def test_load_empty_store(hass: HomeAssistant):
    """Fresh store has no read hrefs."""
    store = ReadMessagesStore(hass, "entry_abc")
    await store.async_load()
    assert not store.is_read("12345")


async def test_mark_read_persists_across_reload(hass: HomeAssistant):
    """Marking a href as read persists when a new instance reloads the store."""
    store1 = ReadMessagesStore(hass, "entry_abc")
    await store1.async_load()
    changed = await store1.async_mark_read("12345")
    assert changed is True
    assert store1.is_read("12345")

    store2 = ReadMessagesStore(hass, "entry_abc")
    await store2.async_load()
    assert store2.is_read("12345")


async def test_mark_read_idempotent(hass: HomeAssistant):
    """Marking the same href twice returns False on second call."""
    store = ReadMessagesStore(hass, "entry_abc")
    await store.async_load()
    assert await store.async_mark_read("12345") is True
    assert await store.async_mark_read("12345") is False
    assert store.is_read("12345")


async def test_mark_unread(hass: HomeAssistant):
    """Marking as unread removes the href from read set, second call returns False."""
    store = ReadMessagesStore(hass, "entry_abc")
    await store.async_load()
    await store.async_mark_read("12345")

    changed = await store.async_mark_unread("12345")
    assert changed is True
    assert not store.is_read("12345")
    assert await store.async_mark_unread("12345") is False


async def test_purge_stale(hass: HomeAssistant):
    """async_purge_stale removes hrefs absent from the active set."""
    store = ReadMessagesStore(hass, "entry_abc")
    await store.async_load()
    await store.async_mark_read("old")
    await store.async_mark_read("active")

    removed = await store.async_purge_stale({"active"})
    assert removed == 1
    assert not store.is_read("old")
    assert store.is_read("active")


async def test_purge_stale_nothing_to_remove(hass: HomeAssistant):
    """async_purge_stale with all active hrefs removes nothing."""
    store = ReadMessagesStore(hass, "entry_abc")
    await store.async_load()
    await store.async_mark_read("111")

    removed = await store.async_purge_stale({"111", "222"})
    assert removed == 0
    assert store.is_read("111")


async def test_clear_all(hass: HomeAssistant):
    """async_clear removes all read hrefs and returns their count."""
    store = ReadMessagesStore(hass, "entry_abc")
    await store.async_load()
    await store.async_mark_read("111")
    await store.async_mark_read("222")

    n = await store.async_clear()
    assert n == 2
    assert not store.is_read("111")
    assert not store.is_read("222")


async def test_multi_entry_isolation(hass: HomeAssistant):
    """Two entries use separate storage keys and don't bleed state."""
    store_a = ReadMessagesStore(hass, "entry_a")
    store_b = ReadMessagesStore(hass, "entry_b")
    await store_a.async_load()
    await store_b.async_load()

    await store_a.async_mark_read("12345")
    assert store_a.is_read("12345")
    assert not store_b.is_read("12345")
