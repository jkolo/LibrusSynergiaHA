"""Tests for LibrusApiClient._apply_headers — UA + browser-like headers patch."""

from __future__ import annotations

import random

from librus_apix import urls as librus_urls

from custom_components.librus_apix import LibrusApiClient
from custom_components.librus_apix.humanize import USER_AGENTS


def test_user_agent_picked_from_pool():
    """Constructor picks a User-Agent from our pool."""
    client = LibrusApiClient("u", "p", rng=random.Random(42))
    assert client._user_agent in USER_AGENTS


def test_user_agent_deterministic_per_seed():
    """Same RNG seed → same UA (so each entry is stable across restarts)."""
    a = LibrusApiClient("u", "p", rng=random.Random(123))
    b = LibrusApiClient("u", "p", rng=random.Random(123))
    assert a._user_agent == b._user_agent


def test_apply_headers_replaces_global_dict_contents():
    """`_apply_headers` mutates `librus_apix.urls.HEADERS` in place.

    Critical for the patch strategy — librus_apix client.py does
    `s.headers = urls.HEADERS` (reference), so we must mutate, not rebind.
    """
    client = LibrusApiClient("u", "p", rng=random.Random(42))

    # Snapshot the dict identity before our patch.
    headers_id_before = id(librus_urls.HEADERS)
    client._apply_headers()
    headers_id_after = id(librus_urls.HEADERS)

    # Same dict object — we did NOT rebind.
    assert headers_id_before == headers_id_after

    # Contents are our headers.
    assert librus_urls.HEADERS["User-Agent"] == client._user_agent
    assert librus_urls.HEADERS["User-Agent"] in USER_AGENTS
    assert librus_urls.HEADERS["Accept-Language"].startswith("pl-PL")
    assert "Content-Type" in librus_urls.HEADERS  # POST auth still works.


def test_apply_headers_idempotent():
    """Calling twice produces the same headers dict."""
    client = LibrusApiClient("u", "p", rng=random.Random(42))
    client._apply_headers()
    snapshot1 = dict(librus_urls.HEADERS)
    client._apply_headers()
    snapshot2 = dict(librus_urls.HEADERS)
    assert snapshot1 == snapshot2


def test_default_constructor_works_without_rng():
    """RNG is optional — without seed we still get a valid UA."""
    client = LibrusApiClient("u", "p")
    assert client._user_agent in USER_AGENTS
    assert client._headers["User-Agent"] == client._user_agent


async def test_attendance_fetcher_applies_headers():
    """`async_get_attendance` patchuje `urls.HEADERS` przez `_with_retry`.

    Zabezpiecza nas przed bypassem _apply_headers dla nowych fetcherów —
    jeśli ktoś by je dodał omijając `_with_retry`, nie patchowałyby UA
    i ujawniły bot.
    """
    import random

    from unittest.mock import patch
    client = LibrusApiClient("u", "p", rng=random.Random(42))

    # Pre-seed headers with a sentinel — verify _apply_headers replaced it.
    librus_urls.HEADERS.clear()
    librus_urls.HEADERS["User-Agent"] = "SENTINEL"

    # Mock _with_retry to capture whether _apply_headers was called via the
    # real path. Easiest: spy _apply_headers directly.
    with patch.object(client, "_apply_headers", wraps=client._apply_headers) as spy:
        # Stub authenticate so the body of _with_retry runs to executor.
        async def _ok():
            client._client = object()  # any truthy non-None
            client._token = object()
            return True

        with patch.object(client, "async_authenticate", side_effect=_ok):
            # get_attendance patched at module level — return empty list.
            with patch(
                "custom_components.librus_apix.get_attendance", return_value=[]
            ):
                await client.async_get_attendance()

    assert spy.called, "_apply_headers should be invoked before executor call"
    assert librus_urls.HEADERS["User-Agent"] != "SENTINEL"
    assert librus_urls.HEADERS["User-Agent"] in USER_AGENTS


async def test_announcements_fetcher_applies_headers():
    """`async_get_announcements` analogicznie."""
    import random

    from unittest.mock import patch
    client = LibrusApiClient("u", "p", rng=random.Random(42))

    librus_urls.HEADERS.clear()
    librus_urls.HEADERS["User-Agent"] = "SENTINEL"

    with patch.object(client, "_apply_headers", wraps=client._apply_headers) as spy:
        async def _ok():
            client._client = object()
            client._token = object()
            return True

        with patch.object(client, "async_authenticate", side_effect=_ok):
            with patch(
                "custom_components.librus_apix.get_announcements", return_value=[]
            ):
                await client.async_get_announcements()

    assert spy.called
    assert librus_urls.HEADERS["User-Agent"] != "SENTINEL"
