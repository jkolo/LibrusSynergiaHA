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
