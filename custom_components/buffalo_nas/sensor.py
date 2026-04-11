from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .device import buffalo_device_info


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            BuffaloCpuUsage(coordinator),
            BuffaloMemoryUsage(coordinator),
            BuffaloRaidUsedPct(coordinator),
            BuffaloEth0RxBytes(coordinator),
            BuffaloEth0TxBytes(coordinator),
        ]
    )


# ==========================================================
# CPU & MEMORY
# ==========================================================

class BuffaloCpuUsage(CoordinatorEntity, SensorEntity):
    _attr_name = "Buffalo CPU Usage"
    _attr_unique_id = "buffalo_cpu_usage"
    _attr_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:cpu-64-bit"

    @property
    def native_value(self):
        return self.coordinator.data["cpu"]["cpu_usage_rate"]

    @property
    def device_info(self):
        return buffalo_device_info(self.coordinator.host)


class BuffaloMemoryUsage(CoordinatorEntity, SensorEntity):
    _attr_name = "Buffalo Memory Usage"
    _attr_unique_id = "buffalo_memory_usage"
    _attr_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:memory"

    @property
    def native_value(self):
        return self.coordinator.data["cpu"]["mem_usage_rate"]

    @property
    def device_info(self):
        return buffalo_device_info(self.coordinator.host)


# ==========================================================
# RAID USAGE
# ==========================================================

class BuffaloRaidUsedPct(CoordinatorEntity, SensorEntity):
    _attr_name = "Buffalo RAID Used %"
    _attr_unique_id = "buffalo_raid_used_pct"
    _attr_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:chart-donut"

    @property
    def native_value(self):
        array = next(
            d for d in self.coordinator.data["devices"]
            if d["device_type"] == "array"
        )
        return array["used_percentage"]

    @property
    def device_info(self):
        return buffalo_device_info(self.coordinator.host)


# ==========================================================
# NETWORK
# ==========================================================

class BuffaloEth0RxBytes(CoordinatorEntity, SensorEntity):
    _attr_name = "Buffalo eth0 RX Bytes"
    _attr_unique_id = "buffalo_eth0_rx_bytes"
    _attr_unit_of_measurement = "B"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:download-network"

    @property
    def native_value(self):
        iface = next(
            i for i in self.coordinator.data["network"]
            if i["name"] == "eth0"
        )
        return int(iface["recevied_bytes"])

    @property
    def device_info(self):
        return buffalo_device_info(self.coordinator.host)


class BuffaloEth0TxBytes(CoordinatorEntity, SensorEntity):
    _attr_name = "Buffalo eth0 TX Bytes"
    _attr_unique_id = "buffalo_eth0_tx_bytes"
    _attr_unit_of_measurement = "B"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:upload-network"

    @property
    def native_value(self):
        iface = next(
            i for i in self.coordinator.data["network"]
            if i["name"] == "eth0"
        )
        return int(iface["sent_bytes"])

    @property
    def device_info(self):
        return buffalo_device_info(self.coordinator.host)
