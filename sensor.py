from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coord = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        BuffaloRaidUsage(coord),
        BuffaloCpuUsage(coord),
        BuffaloMemoryUsage(coord),
        BuffaloEth0Rx(coord),
        BuffaloEth0Tx(coord),
    ])


class BuffaloRaidUsage(CoordinatorEntity, SensorEntity):
    _attr_unit_of_measurement = "%"
    _attr_name = "Buffalo RAID Used %"
    _attr_unique_id = "buffalo_raid_used_pct"

    @property
    def native_value(self):
        array = next(d for d in self.coordinator.data["devices"]
                     if d["device_type"] == "array")
        return array["used_percentage"]


class BuffaloCpuUsage(CoordinatorEntity, SensorEntity):
    _attr_unit_of_measurement = "%"
    _attr_name = "Buffalo CPU Usage"
    _attr_unique_id = "buffalo_cpu_usage"

    @property
    def native_value(self):
        return self.coordinator.data["cpu"]["cpu_usage_rate"]


class BuffaloMemoryUsage(CoordinatorEntity, SensorEntity):
    _attr_unit_of_measurement = "%"
    _attr_name = "Buffalo Memory Usage"
    _attr_unique_id = "buffalo_mem_usage"

    @property
    def native_value(self):
        return self.coordinator.data["cpu"]["mem_usage_rate"]


class BuffaloEth0Rx(CoordinatorEntity, SensorEntity):
    _attr_unit_of_measurement = "B"
    _attr_name = "Buffalo eth0 RX Bytes"
    _attr_unique_id = "buffalo_eth0_rx"

    @property
    def native_value(self):
        iface = next(i for i in self.coordinator.data["network"]
                     if i["name"] == "eth0")
        return int(iface["recevied_bytes"])


class BuffaloEth0Tx(CoordinatorEntity, SensorEntity):
    _attr_unit_of_measurement = "B"
    _attr_name = "Buffalo eth0 TX Bytes"
    _attr_unique_id = "buffalo_eth0_tx"

    @property
    def native_value(self):
        iface = next(i for i in self.coordinator.data["network"]
                     if i["name"] == "eth0")
        return int(iface["sent_bytes"])