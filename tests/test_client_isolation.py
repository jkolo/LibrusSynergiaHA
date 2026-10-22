"""Kazde konto Librusa ma wlasny token i sloik ciasteczek.

`librus_apix.client.Client` ma mutowalne domyslne `extra_cookies` (i
`new_client` domyslny `Token()`), wiec bez izolacji wszystkie konta w procesie
HA dziela jeden `RequestsCookieJar` razem z `oauth_token` — zapytanie jednego
dziecka moze pojsc z ciasteczkami drugiego.
"""

from __future__ import annotations

from unittest.mock import patch

from librus_apix.client import Client, Token

from custom_components.librus_apix import LibrusApiClient, isolated_client
from custom_components.librus_apix.config_flow import validate_input


def _fake_get_token(self: Client, username: str, password: str) -> Token:
    self.token = Token(dzienniks=f"d-{username}", sdzienniks=f"s-{username}")
    return self.token


def test_isolated_clients_share_no_state() -> None:
    a, b = isolated_client(), isolated_client()

    assert a.cookies is not b.cookies
    assert a.token is not b.token
    a.cookies.set("oauth_token", "konto-a")
    assert b.cookies.get("oauth_token") is None


async def test_authenticated_accounts_have_separate_cookie_jars() -> None:
    with patch.object(Client, "get_token", _fake_get_token):
        ewa = LibrusApiClient(username="ewa", password="x", humanize=False)
        lukasz = LibrusApiClient(username="lukasz", password="x", humanize=False)
        assert await ewa.async_authenticate()
        assert await lukasz.async_authenticate()

    assert ewa._client.cookies is not lukasz._client.cookies
    ewa._client.cookies.update(ewa._client.token.access_cookies())
    assert lukasz._client.cookies.get("DZIENNIKSID") is None


async def test_config_flow_validation_uses_isolated_client(hass) -> None:
    seen: list[Client] = []

    def _record(self: Client, username: str, password: str) -> Token:
        seen.append(self)
        return _fake_get_token(self, username, password)

    with patch.object(Client, "get_token", _record):
        await validate_input(hass, {"username": "ewa", "password": "x"})
        await validate_input(hass, {"username": "lukasz", "password": "x"})

    assert seen[0].cookies is not seen[1].cookies
