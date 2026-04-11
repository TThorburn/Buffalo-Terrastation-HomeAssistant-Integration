from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coord = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for d in coord.data["devices"]:
        if d["device_type"] == "disk" and d["interface"] == "sata":
            entities.append(BuffaloDiskHealth(coord, d))
        elif d["device_type"] == "array":
            entities.append(BuffaloRaidHealth(coord, d))

    async_add_entities(entities)


class BuffaloDiskHealth(CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, disk):
        super().__init__(coordinator)
        self.disk = disk
        self._attr_name = f"Buffalo {disk['device_file']} Healthy"
        self._attr_unique_id = f"buffalo_disk_{disk['device_file']}"

    @property
    def is_on(self):
        return self.disk["status"] == ["fine"]


class BuffaloRaidHealth(CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_name = "Buffalo RAID Healthy"
    _attr_unique_id = "buffalo_raid_healthy"

    def __init__(self, coordinator, array):
        super().__init__(coordinator)
        self.array = array

    @property
    def is_on(self):
        return self.array["status"] == ["fine"]