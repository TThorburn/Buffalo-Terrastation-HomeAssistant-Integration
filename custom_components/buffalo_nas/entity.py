"""Shared entity identity and discovery."""

from collections.abc import Callable, Iterable

from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BuffaloConfigEntry, BuffaloNASCoordinator


class BuffaloEntity(CoordinatorEntity[BuffaloNASCoordinator]):
    """An entity associated with a single NAS."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: BuffaloNASCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}:{key}"
        self._attr_name = name
        self._attr_device_info = coordinator.device_info


@callback
def discover_entities(
    entry: BuffaloConfigEntry,
    platform: str,
    async_add_entities,
    build_entities: Callable[[], Iterable[tuple[BuffaloEntity, str | None]]],
) -> None:
    """Add new entities and attach old registry IDs before their first registration."""
    coordinator = entry.runtime_data
    registry = er.async_get(coordinator.hass)
    known: set[str] = set()

    @callback
    def discover() -> None:
        new_entities = []
        for entity, legacy_id in build_entities():
            unique_id = entity.unique_id
            if unique_id in known:
                continue
            known.add(unique_id)
            if legacy_id and (
                entity_id := registry.async_get_entity_id(platform, DOMAIN, legacy_id)
            ):
                old_entry = registry.async_get(entity_id)
                if (
                    old_entry.config_entry_id == entry.entry_id
                    and registry.async_get_entity_id(platform, DOMAIN, unique_id)
                    is None
                ):
                    registry.async_update_entity(entity_id, new_unique_id=unique_id)
            new_entities.append(entity)
        if new_entities:
            async_add_entities(new_entities)

    discover()
    entry.async_on_unload(coordinator.async_add_listener(discover))
