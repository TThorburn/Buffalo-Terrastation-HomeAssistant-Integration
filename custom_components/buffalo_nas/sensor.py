"""Utilization, capacity, network counters and NAS events."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfDataRate,
    UnitOfInformation,
)

from .entity import BuffaloEntity, discover_entities
from .models import Snapshot, arrays, number, percentage

KIB_PER_GIB = 1024 * 1024
RAID_LEVELS = {
    "0": ("RAID 0", 0),
    "1": ("RAID 1", 1),
    "5": ("RAID 5", 1),
    "6": ("RAID 6", 2),
    "10": ("RAID 10", 1),
    "linear": ("JBOD", 0),
}


def gib(value: Any) -> float | None:
    parsed = number(value)
    return round(parsed / KIB_PER_GIB, 1) if parsed is not None else None


def raid_usage(record: dict[str, Any]) -> float | None:
    used = percentage(record.get("used_percentage"))
    if used is None:
        size = number(record.get("used_size"))
        total = number(record.get("total_size"))
        if size is not None and total:
            used = percentage(size / total * 100)
    return round(used, 2) if used is not None else None


def raid_attributes(record: dict[str, Any]) -> dict[str, Any]:
    """Keep the original dashboard attributes and use the firmware's KiB scale."""
    used = gib(record.get("used_size"))
    total = gib(record.get("total_size"))
    raw_level = record.get("raid_level")
    level, redundancy = RAID_LEVELS.get(
        str(raw_level).lower(),
        (f"RAID {raw_level}", None) if raw_level is not None else (None, None),
    )
    return {
        "used_gb": used,
        "total_gb": total,
        "usage_text": f"{used} GB / {total} GB"
        if used is not None and total is not None
        else None,
        "raid_level_raw": raw_level,
        "raid_level": level,
        "redundancy_disks": redundancy,
        "disk_count": record.get("raid_devices"),
    }


def received(record: dict[str, Any]) -> int | float | None:
    for key in ("recevied_bytes", "received_bytes", "rx_bytes"):
        if (value := number(record.get(key))) is not None:
            return value
    return None


def rx_attributes(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "sampled_at": record.get("sampled_at"),
        "bytes_per_second": record.get("rx_bytes_per_second"),
    }


def tx_attributes(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "sampled_at": record.get("sampled_at"),
        "bytes_per_second": record.get("tx_bytes_per_second"),
    }


@dataclass(frozen=True, kw_only=True)
class Metric(SensorEntityDescription):
    """A value and its Home Assistant metadata."""

    value: Callable[[Any], Any]
    attributes: Callable[[Any], dict[str, Any]] | None = None


CPU = Metric(
    key="cpu_usage",
    name="CPU Usage",
    icon="mdi:cpu-64-bit",
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
    value=lambda data: percentage(data.get("cpu_usage_rate")),
)
MEMORY = Metric(
    key="memory_usage",
    name="Memory Usage",
    icon="mdi:memory",
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
    value=lambda data: percentage(data.get("mem_usage_rate")),
)
RAID_USAGE = Metric(
    key="usage",
    name="Usage",
    icon="mdi:chart-donut",
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
    value=raid_usage,
    attributes=raid_attributes,
)
RAID_USED = Metric(
    key="used",
    name="Used Space",
    device_class=SensorDeviceClass.DATA_SIZE,
    native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
    state_class=SensorStateClass.MEASUREMENT,
    value=lambda data: gib(data.get("used_size")),
)
RAID_TOTAL = Metric(
    key="total",
    name="Capacity",
    device_class=SensorDeviceClass.DATA_SIZE,
    native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
    state_class=SensorStateClass.MEASUREMENT,
    value=lambda data: gib(data.get("total_size")),
)
RX = Metric(
    key="rx_bytes",
    name="RX Bytes",
    icon="mdi:download-network",
    device_class=SensorDeviceClass.DATA_SIZE,
    native_unit_of_measurement=UnitOfInformation.BYTES,
    state_class=SensorStateClass.TOTAL_INCREASING,
    value=received,
    attributes=rx_attributes,
)
TX = Metric(
    key="tx_bytes",
    name="TX Bytes",
    icon="mdi:upload-network",
    device_class=SensorDeviceClass.DATA_SIZE,
    native_unit_of_measurement=UnitOfInformation.BYTES,
    state_class=SensorStateClass.TOTAL_INCREASING,
    value=lambda data: number(data.get("sent_bytes", data.get("tx_bytes"))),
    attributes=tx_attributes,
)
RX_RATE = Metric(
    key="rx_rate",
    name="Receive Speed",
    icon="mdi:download-network",
    device_class=SensorDeviceClass.DATA_RATE,
    native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
    state_class=SensorStateClass.MEASUREMENT,
    value=lambda data: data.get("rx_bytes_per_second"),
    attributes=rx_attributes,
)
TX_RATE = Metric(
    key="tx_rate",
    name="Transmit Speed",
    icon="mdi:upload-network",
    device_class=SensorDeviceClass.DATA_RATE,
    native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
    state_class=SensorStateClass.MEASUREMENT,
    value=lambda data: data.get("tx_bytes_per_second"),
    attributes=tx_attributes,
)
EVENTS = Metric(
    key="information",
    name="NAS Information Count",
    icon="mdi:information-outline",
    entity_category=EntityCategory.DIAGNOSTIC,
    value=len,
)


class BuffaloSensor(BuffaloEntity, SensorEntity):
    """Read one measurement from the latest coordinator snapshot."""

    entity_description: Metric

    def __init__(
        self,
        coordinator,
        metric: Metric,
        source: Callable[[Snapshot], Any],
        prefix: str = "",
        label: str = "",
    ) -> None:
        super().__init__(coordinator, f"{prefix}{metric.key}", f"{label}{metric.name}")
        self.entity_description = metric
        # Preserve each monitoring sample even when CPU, RAM or counters are flat.
        self._attr_force_update = metric.key in {
            "cpu_usage",
            "memory_usage",
            "rx_bytes",
            "tx_bytes",
            "rx_rate",
            "tx_rate",
        }
        self._source = source

    @property
    def native_value(self):
        data = self._source(self.coordinator.data)
        return self.entity_description.value(data) if data is not None else None

    @property
    def available(self) -> bool:
        return super().available and self.native_value is not None

    @property
    def extra_state_attributes(self):
        data = self._source(self.coordinator.data)
        attributes = self.entity_description.attributes
        return attributes(data) if attributes is not None and data is not None else None


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Discover interfaces and arrays as the NAS reports them."""
    coordinator = entry.runtime_data

    def usage_entities():
        usage_coordinator = coordinator.usage
        for metric in (CPU, MEMORY):
            yield (
                BuffaloSensor(
                    usage_coordinator, metric, lambda snapshot: snapshot.usage
                ),
                f"buffalo_{metric.key}",
            )

    def storage_entities():
        data = coordinator.data
        if data.information is not None:
            yield (
                BuffaloSensor(
                    coordinator, EVENTS, lambda snapshot: snapshot.information
                ),
                None,
            )
        for index, key in enumerate(arrays(data)):
            label = data.devices[key].get("device_name") or f"RAID {key}"
            for metric in (RAID_USAGE, RAID_USED, RAID_TOTAL):
                yield (
                    BuffaloSensor(
                        coordinator,
                        metric,
                        lambda snap, key=key: (snap.devices or {}).get(key),
                        f"array:{key}:",
                        f"{label} ",
                    ),
                    "buffalo_raid_usage"
                    if index == 0 and metric is RAID_USAGE
                    else None,
                )

    def network_entities():
        network_coordinator = coordinator.network
        for key in network_coordinator.data.interfaces or {}:
            for metric in (RX, TX, RX_RATE, TX_RATE):
                yield (
                    BuffaloSensor(
                        network_coordinator,
                        metric,
                        lambda snap, key=key: (snap.interfaces or {}).get(key),
                        f"network:{key}:",
                        f"{key} ",
                    ),
                    f"buffalo_{key}_{metric.key}"
                    if key == "eth0" and metric in (RX, TX)
                    else None,
                )

    discover_entities(entry, "sensor", async_add_entities, storage_entities)
    discover_entities(
        entry, "sensor", async_add_entities, usage_entities, coordinator.usage
    )
    discover_entities(
        entry, "sensor", async_add_entities, network_entities, coordinator.network
    )
