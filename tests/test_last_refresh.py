"""„Ostatnie odświeżenie” must move on every completed cycle.

With always_update=False the coordinator did not notify listeners when the
fetched data equalled the previous cycle, so the diagnostic sensor (which
reads coordinator._last_full_refresh) kept an old timestamp although the
refresh ran (found on production 2026-10-13).
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.librus_apix.coordinator import LibrusDataUpdateCoordinator


async def test_listeners_notified_when_data_is_unchanged(
    hass: HomeAssistant, mock_librus_client
) -> None:
    coordinator = LibrusDataUpdateCoordinator(hass, mock_librus_client)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    calls: list[None] = []
    unsub = coordinator.async_add_listener(lambda: calls.append(None))
    await coordinator.async_refresh()  # te same dane z mocka
    await hass.async_block_till_done()
    unsub()

    assert calls, "encje (m.in. Ostatnie odświeżenie) muszą dostać powiadomienie"
