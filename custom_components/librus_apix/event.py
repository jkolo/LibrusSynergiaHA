"""Event entities for the Librus APIX integration (v3.0).

Replaces the legacy `hass.bus.fire` mechanism. Each event entity (`new_grade`,
`new_message`, `new_exam`, `new_announcement`, `new_absence`) reads pending
payloads from the coordinator on every refresh — when present, it triggers
an event of type `"new"` carrying the payload as attributes.

Automation migrates from `trigger.platform=event, event_type=librus_apix_*`
to `trigger.platform=state, entity_id=event.<student>_<key>` — state-based
triggers are easier to write, history is persisted, and dashboard cards see
the latest event without a custom template.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.event import EventEntity, EventEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import LibrusDataUpdateCoordinator
from .entity import LibrusBaseEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class LibrusEventEntityDescription(EventEntityDescription):
    """Description for Librus event entities."""


EVENTS: tuple[LibrusEventEntityDescription, ...] = (
    LibrusEventEntityDescription(
        key="new_grade",
        translation_key="new_grade",
        icon="mdi:school",
        event_types=["new"],
    ),
    LibrusEventEntityDescription(
        key="new_message",
        translation_key="new_message",
        icon="mdi:email",
        event_types=["new"],
    ),
    LibrusEventEntityDescription(
        key="new_exam",
        translation_key="new_exam",
        icon="mdi:calendar-alert",
        event_types=["new"],
    ),
    LibrusEventEntityDescription(
        key="new_announcement",
        translation_key="new_announcement",
        icon="mdi:bullhorn",
        event_types=["new"],
    ),
    LibrusEventEntityDescription(
        key="new_absence",
        translation_key="new_absence",
        icon="mdi:account-remove",
        event_types=["new"],
    ),
)


class LibrusEvent(LibrusBaseEntity, EventEntity):
    """Generic event entity backed by a coordinator pending-events queue."""

    entity_description: LibrusEventEntityDescription

    def __init__(
        self,
        coordinator: LibrusDataUpdateCoordinator,
        config_entry: ConfigEntry,
        description: LibrusEventEntityDescription,
    ) -> None:
        super().__init__(coordinator, config_entry)
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Pop and emit pending event for this entity's key, if any."""
        pending = self.coordinator.consume_pending_event(self.entity_description.key)
        if pending is not None:
            self._trigger_event("new", pending)
        super()._handle_coordinator_update()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Librus event entities from a config entry."""
    coordinator: LibrusDataUpdateCoordinator = config_entry.runtime_data.coordinator
    async_add_entities(
        LibrusEvent(coordinator, config_entry, description)
        for description in EVENTS
    )
