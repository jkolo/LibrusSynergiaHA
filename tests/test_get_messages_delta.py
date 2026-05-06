"""Unit tests for LibrusApiClient.async_get_messages delta-fetch algorithm.

Scenarios covered:
- empty inbox
- single page, no cache
- exactly 50 messages (1 full page), no cache
- multiple pages, no cache (fetch all)
- 23 pages, cache empty (fetch all)
- 27 pages, last 7 pages fully in cache (stop at page 20)
- last message on current page is known (stop after that page)
- first message on a page is known (stop immediately, include previous pages)
- all messages already known (return empty)
- mixed known/unknown on same page (include only unknowns)
- empty page mid-way (stop early)
- single unknown message
- single known message
- known_hrefs=None with multiple pages (fetch all)
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from custom_components.librus_apix import LibrusApiClient


def _msg(href: str, author: str = "A", title: str = "T", date: str = "2025-01-01") -> SimpleNamespace:
    """Build a fake librus-apix message object."""
    return SimpleNamespace(
        href=href,
        author=author,
        title=title,
        date=date,
        unread=True,
        has_attachment=False,
    )


def _make_page(hrefs: list[str]) -> list[SimpleNamespace]:
    return [_msg(h) for h in hrefs]


def _hrefs(msgs: list[dict]) -> list[str]:
    return [m["href"] for m in msgs]


@pytest.fixture
def client():
    """A LibrusApiClient with auth pre-seeded (no real Librus call)."""
    c = LibrusApiClient("user", "pass")
    c._client = MagicMock()
    c._token = "fake"
    return c


@pytest.fixture(autouse=True)
def no_headers_patch(client):
    """Skip browser-header injection — not relevant for these tests."""
    with patch.object(client, "_apply_headers"):
        yield


# ---------------------------------------------------------------------------
# helpers for parameterised patching
# ---------------------------------------------------------------------------

def _patch_librus(max_page: int, pages: list[list[SimpleNamespace]]):
    """Return a context-manager pair: patch max_page_number and get_received."""
    mock_max = MagicMock(return_value=max_page)
    call_count = [0]

    def _received(_, page):
        if page < len(pages):
            return pages[page]
        return []

    mock_received = MagicMock(side_effect=_received)
    return (
        patch("custom_components.librus_apix.get_max_page_number", mock_max),
        patch("custom_components.librus_apix.get_received", mock_received),
        mock_received,
    )


# ===========================================================================
# Tests
# ===========================================================================

async def test_empty_inbox(hass, client):
    """Empty inbox returns empty list."""
    p_max = patch("custom_components.librus_apix.get_max_page_number", return_value=0)
    p_recv = patch("custom_components.librus_apix.get_received", return_value=[])
    with p_max, p_recv:
        result = await client.async_get_messages(known_hrefs=None)
    assert result == []


async def test_single_page_no_cache(hass, client):
    """Single page, no cache: all 3 messages returned."""
    page0 = _make_page(["a", "b", "c"])
    p_max = patch("custom_components.librus_apix.get_max_page_number", return_value=0)
    p_recv = patch("custom_components.librus_apix.get_received", return_value=page0)
    with p_max, p_recv:
        result = await client.async_get_messages(known_hrefs=frozenset())
    assert _hrefs(result) == ["a", "b", "c"]


async def test_exactly_50_messages_one_page_no_cache(hass, client):
    """Exactly 50 messages in one page, no cache: all 50 returned."""
    page0 = _make_page([str(i) for i in range(50)])
    p_max = patch("custom_components.librus_apix.get_max_page_number", return_value=0)
    p_recv = patch("custom_components.librus_apix.get_received", return_value=page0)
    with p_max, p_recv:
        result = await client.async_get_messages(known_hrefs=None)
    assert len(result) == 50
    assert _hrefs(result) == [str(i) for i in range(50)]


async def test_two_pages_no_cache_fetches_all(hass, client):
    """Two pages, no cache: both pages fetched, all messages returned."""
    page0 = _make_page(["p0_0", "p0_1"])
    page1 = _make_page(["p1_0", "p1_1"])
    mock_received = MagicMock(side_effect=[page0, page1])
    p_max = patch("custom_components.librus_apix.get_max_page_number", return_value=1)
    p_recv = patch("custom_components.librus_apix.get_received", mock_received)
    with p_max, p_recv:
        result = await client.async_get_messages(known_hrefs=None)
    assert _hrefs(result) == ["p0_0", "p0_1", "p1_0", "p1_1"]
    assert mock_received.call_count == 2


async def test_23_pages_cache_empty_fetches_all_pages(hass, client):
    """23 pages, empty cache: all 23 pages fetched."""
    pages = [_make_page([f"p{p}_m{m}" for m in range(3)]) for p in range(23)]
    mock_received = MagicMock(side_effect=pages)
    p_max = patch("custom_components.librus_apix.get_max_page_number", return_value=22)
    p_recv = patch("custom_components.librus_apix.get_received", mock_received)
    with p_max, p_recv:
        result = await client.async_get_messages(known_hrefs=frozenset())
    assert mock_received.call_count == 23
    assert len(result) == 23 * 3


async def test_27_pages_last_7_in_cache_stops_at_page_20(hass, client):
    """27 pages, pages 20-26 are fully known: fetches pages 0-19 then stops on 20."""
    pages = [_make_page([f"p{p}_m{m}" for m in range(5)]) for p in range(27)]
    # known = all hrefs from pages 20-26
    known = frozenset(
        f"p{p}_m{m}" for p in range(20, 27) for m in range(5)
    )
    mock_received = MagicMock(side_effect=pages)
    p_max = patch("custom_components.librus_apix.get_max_page_number", return_value=26)
    p_recv = patch("custom_components.librus_apix.get_received", mock_received)
    with p_max, p_recv:
        result = await client.async_get_messages(known_hrefs=known)
    # Fetched pages 0..20 (stops after first hit on page 20)
    assert mock_received.call_count == 21
    # Returns only new messages (pages 0-19)
    assert len(result) == 20 * 5
    for href in _hrefs(result):
        assert href not in known


async def test_stops_after_page_with_last_known_message(hass, client):
    """Known href is the last message on a page: stop after that page."""
    page0 = _make_page(["new_0", "new_1"])
    page1 = _make_page(["new_2", "known_x"])  # known_x is last — still stops here
    page2 = _make_page(["old_0", "old_1"])
    mock_received = MagicMock(side_effect=[page0, page1, page2])
    p_max = patch("custom_components.librus_apix.get_max_page_number", return_value=2)
    p_recv = patch("custom_components.librus_apix.get_received", mock_received)
    with p_max, p_recv:
        result = await client.async_get_messages(known_hrefs=frozenset(["known_x"]))
    assert mock_received.call_count == 2  # page2 never fetched
    assert _hrefs(result) == ["new_0", "new_1", "new_2"]
    assert "known_x" not in _hrefs(result)


async def test_stops_immediately_when_first_msg_on_page_is_known(hass, client):
    """First message on page 1 is known: stop without adding anything from that page."""
    page0 = _make_page(["new_0", "new_1"])
    page1 = _make_page(["known_x", "new_2"])  # known_x first
    page2 = _make_page(["old_0"])
    mock_received = MagicMock(side_effect=[page0, page1, page2])
    p_max = patch("custom_components.librus_apix.get_max_page_number", return_value=2)
    p_recv = patch("custom_components.librus_apix.get_received", mock_received)
    with p_max, p_recv:
        result = await client.async_get_messages(known_hrefs=frozenset(["known_x"]))
    assert mock_received.call_count == 2
    # new_2 comes after known_x on page1 — should NOT be returned
    assert _hrefs(result) == ["new_0", "new_1"]


async def test_all_messages_already_known_returns_empty(hass, client):
    """All messages in inbox are already known: returns []."""
    page0 = _make_page(["a", "b", "c"])
    p_max = patch("custom_components.librus_apix.get_max_page_number", return_value=0)
    p_recv = patch("custom_components.librus_apix.get_received", return_value=page0)
    with p_max, p_recv:
        result = await client.async_get_messages(known_hrefs=frozenset(["a", "b", "c"]))
    assert result == []


async def test_mixed_known_unknown_on_same_page(hass, client):
    """Page has both known and unknown messages before the known one."""
    page0 = _make_page(["new_0", "known_1", "new_2"])
    # known_1 is in the middle; new_2 comes after — should NOT be returned
    p_max = patch("custom_components.librus_apix.get_max_page_number", return_value=0)
    p_recv = patch("custom_components.librus_apix.get_received", return_value=page0)
    with p_max, p_recv:
        result = await client.async_get_messages(known_hrefs=frozenset(["known_1"]))
    assert _hrefs(result) == ["new_0"]


async def test_empty_page_mid_way_stops_iteration(hass, client):
    """get_received returning [] in the middle of pages stops iteration."""
    page0 = _make_page(["a", "b"])
    mock_received = MagicMock(side_effect=[page0, []])
    p_max = patch("custom_components.librus_apix.get_max_page_number", return_value=5)
    p_recv = patch("custom_components.librus_apix.get_received", mock_received)
    with p_max, p_recv:
        result = await client.async_get_messages(known_hrefs=None)
    assert mock_received.call_count == 2
    assert _hrefs(result) == ["a", "b"]


async def test_single_unknown_message(hass, client):
    """Inbox with one new message, no cache: returns it."""
    page0 = _make_page(["only_one"])
    p_max = patch("custom_components.librus_apix.get_max_page_number", return_value=0)
    p_recv = patch("custom_components.librus_apix.get_received", return_value=page0)
    with p_max, p_recv:
        result = await client.async_get_messages(known_hrefs=frozenset())
    assert _hrefs(result) == ["only_one"]


async def test_single_known_message_returns_empty(hass, client):
    """Inbox with one message already known: returns []."""
    page0 = _make_page(["already_known"])
    p_max = patch("custom_components.librus_apix.get_max_page_number", return_value=0)
    p_recv = patch("custom_components.librus_apix.get_received", return_value=page0)
    with p_max, p_recv:
        result = await client.async_get_messages(known_hrefs=frozenset(["already_known"]))
    assert result == []


async def test_known_hrefs_none_fetches_all_pages(hass, client):
    """known_hrefs=None (no prior cache) fetches all pages."""
    pages = [_make_page([f"p{p}m{m}" for m in range(2)]) for p in range(5)]
    mock_received = MagicMock(side_effect=pages)
    p_max = patch("custom_components.librus_apix.get_max_page_number", return_value=4)
    p_recv = patch("custom_components.librus_apix.get_received", mock_received)
    with p_max, p_recv:
        result = await client.async_get_messages(known_hrefs=None)
    assert mock_received.call_count == 5
    assert len(result) == 10


async def test_known_href_on_page_0_stops_immediately(hass, client):
    """Cache contains a message on page 0 (first page): fetches only page 0."""
    page0 = _make_page(["new_0", "known_old"])
    page1 = _make_page(["p1_0"])
    mock_received = MagicMock(side_effect=[page0, page1])
    p_max = patch("custom_components.librus_apix.get_max_page_number", return_value=1)
    p_recv = patch("custom_components.librus_apix.get_received", mock_received)
    with p_max, p_recv:
        result = await client.async_get_messages(known_hrefs=frozenset(["known_old"]))
    assert mock_received.call_count == 1
    assert _hrefs(result) == ["new_0"]


async def test_message_fields_mapped_correctly(hass, client):
    """Returned dicts carry all required fields with correct values."""
    msg = SimpleNamespace(
        href="href1", author="Autor", title="Tytuł", date="2025-05-01",
        unread=True, has_attachment=True,
    )
    p_max = patch("custom_components.librus_apix.get_max_page_number", return_value=0)
    p_recv = patch("custom_components.librus_apix.get_received", return_value=[msg])
    with p_max, p_recv:
        result = await client.async_get_messages(known_hrefs=None)
    assert len(result) == 1
    m = result[0]
    assert m["href"] == "href1"
    assert m["author"] == "Autor"
    assert m["title"] == "Tytuł"
    assert m["date"] == "2025-05-01"
    assert m["unread"] is True
    assert m["has_attachment"] is True
