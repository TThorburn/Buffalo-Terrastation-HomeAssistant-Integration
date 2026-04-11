from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .device import buffalo_device_info


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for device in coordinator.data["devices"]:
        if device["device_type"] == "disk" and device["interface"] == "sata":
            entities.append(BuffaloDiskProblem(coordinator, device))

        elif device["device_type"] == "array":
            entities.append(BuffaloRaidProblem(coordinator, device))
            entities.append(BuffaloRaidDegraded(coordinator, device))

    async_add_entities(entities)


# ==========================================================
# DISK PROBLEM SENSORS
# ==========================================================

class BuffaloDiskProblem(CoordinatorEntity, BinarySensorEntity):
    """ON when the disk has a problem."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:harddisk"

    def __init__(self, coordinator, disk):
        super().__init__(coordinator)
        self._disk = disk
        self._attr_name = f"Buffalo {disk['device_file']} Problem"
        self._attr_unique_id = f"buffalo_{disk['device_file']}_problem"

    @property
    def is_on(self):
        # PROBLEM semantics: True == problem exists
        return self._disk.get("status") != ["fine"]

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self):
        return {
            "model": self._disk.get("unit_name"),
            "interface": self._disk.get("interface"),
            "raw_status": self._disk.get("status"),
        }

    @property
    def device_info(self):
        return buffalo_device_info(self.coordinator.host)


# ==========================================================
# RAID PROBLEM (AUTOMATION-GRADE)
# ==========================================================

class BuffaloRaidProblem(CoordinatorEntity, BinarySensorEntity):
    """ON when RAID is not healthy."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:shield-alert"
    _attr_name = "Buffalo RAID Problem"
    _attr_unique_id = "buffalo_raid_problem"

    def __init__(self, coordinator, array):
        super().__init__(coordinator)
        self._array = array

    @property
    def is_on(self):
        return self._array.get("status") != ["fine"]

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self):
        return {
            "raw_status": self._array.get("status"),
            "raid_level": self._array.get("raid_level"),
        }

    @property
    def device_info(self):
        return buffalo_device_info(self.coordinator.host)


# ==========================================================
# RAID DEGRADED (FRIENDLY UI SENSOR)
# ==========================================================

class BuffaloRaidDegraded(CoordinatorEntity, BinarySensorEntity):
    """Friendly RAID degraded indicator."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:alert"
    _attr_name = "Buffalo RAID Degraded"
    _attr_unique_id = "buffalo_raid_degraded"

    def __init__(self, coordinator, array):
        super().__init__(coordinator)
        self._array = array

    @property
    def is_on(self):
        return self._array.get("status") != ["fine"]

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self):
        return {
            "raw_status": self._array.get("status"),
            "raid_level": self._array.get("raid_level"),
            "disk_count": self._array.get("raid_devices"),
        }

    @property
    def device_info(self):
        return buffalo_device_info(self.coordinator.host)
