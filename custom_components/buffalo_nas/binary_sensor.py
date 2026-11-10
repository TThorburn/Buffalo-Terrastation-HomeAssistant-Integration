"""Drive, RAID and system health sensors."""

from collections.abc import Callable
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory

from .entity import BuffaloEntity, discover_entities
from .models import Snapshot, arrays, number, statuses

DEGRADED = {"degrade", "degraded"}


def problem(device: dict[str, Any]) -> bool | None:
    state = set(statuses(device))
    return state != {"fine"} if state else None


def degraded(device: dict[str, Any]) -> bool | None:
    state = set(statuses(device))
    return bool(state & DEGRADED) if state else None


def raid_attributes(device: dict[str, Any]) -> dict[str, Any]:
    return {
        "raw_status": device.get("status"),
        "raid_level": device.get("raid_level"),
        "disk_count": device.get("raid_devices"),
    }


def disk_attributes(device: dict[str, Any]) -> dict[str, Any]:
    capacity_kib = number(device.get("total_size"))
    return {
        "drive_name": device.get("device_name") or device.get("device_file"),
        "capacity_bytes": capacity_kib * 1024 if capacity_kib else None,
        "model": device.get("unit_name"),
        "interface": device.get("interface"),
        "raw_status": device.get("status"),
    }


def event_codes(events: list[Any]) -> dict[str, Any]:
    codes = [
        event["code"]
        for event in events
        if isinstance(event, dict) and isinstance(event.get("code"), (int, str))
    ]
    return {"error_count": len(events), "error_codes": codes}


class BuffaloProblem(BuffaloEntity, BinarySensorEntity):
    """Report health from the latest coordinator snapshot."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator,
        key: str,
        name: str,
        source: Callable[[Snapshot], Any],
        state: Callable[[Any], bool | None],
        attributes: Callable[[Any], dict[str, Any]],
        icon: str,
    ) -> None:
        super().__init__(coordinator, key, name)
        self._source = source
        self._state = state
        self._attributes = attributes
        self._attr_icon = icon

    @property
    def is_on(self) -> bool | None:
        data = self._source(self.coordinator.data)
        return self._state(data) if data is not None else None

    @property
    def available(self) -> bool:
        return super().available and self.is_on is not None

    @property
    def extra_state_attributes(self):
        data = self._source(self.coordinator.data)
        return self._attributes(data) if data is not None else None


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Discover drives and arrays as the NAS reports them."""
    coordinator = entry.runtime_data

    def entities():
        data = coordinator.data
        if data.errors is not None:
            yield (
                BuffaloProblem(
                    coordinator,
                    "system_errors",
                    "NAS Errors",
                    lambda snap: snap.errors,
                    bool,
                    event_codes,
                    "mdi:alert-circle-outline",
                ),
                None,
            )
        for key, device in (data.devices or {}).items():
            if (
                device.get("device_type") == "disk"
                and device.get("interface") == "sata"
            ):
                yield (
                    BuffaloProblem(
                        coordinator,
                        f"disk:{key}:problem",
                        f"{device.get('device_name') or key} Problem",
                        lambda snap, key=key: (snap.devices or {}).get(key),
                        problem,
                        disk_attributes,
                        "mdi:harddisk",
                    ),
                    f"buffalo_{key}_problem",
                )
        for index, key in enumerate(arrays(data)):
            label = data.devices[key].get("device_name") or f"RAID {key}"
            for kind, state, icon in (
                ("problem", problem, "mdi:shield-alert"),
                ("degraded", degraded, "mdi:alert"),
            ):
                yield (
                    BuffaloProblem(
                        coordinator,
                        f"array:{key}:{kind}",
                        f"{label} {kind.title()}",
                        lambda snap, key=key: (snap.devices or {}).get(key),
                        state,
                        raid_attributes,
                        icon,
                    ),
                    f"buffalo_raid_{kind}" if index == 0 else None,
                )

    discover_entities(entry, "binary_sensor", async_add_entities, entities)
