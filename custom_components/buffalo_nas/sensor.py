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
            BuffaloRaidUsage(coordinator),
            BuffaloEth0RxBytes(coordinator),
            BuffaloEth0TxBytes(coordinator),
        ],
        update_before_add=True,
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
# RAID USAGE (BUFFALO-WEB-UI STYLE, ALL RAID LEVELS)
# ==========================================================

class BuffaloRaidUsage(CoordinatorEntity, SensorEntity):
    """
    RAID usage sensor with full RAID level support.
    Matches Buffalo web UI presentation:

    - State: Percentage used
    - Attributes:
        * used_gb
        * total_gb
        * usage_text (e.g. "1265.8 GB / 7385.7 GB")
        * raid_level (human readable)
        * redundancy_disks
        * disk_count
    """

    _attr_name = "Buffalo RAID Usage"
    _attr_unique_id = "buffalo_raid_usage"
    _attr_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:chart-donut"

    def _array(self):
        return next(
            d for d in self.coordinator.data["devices"]
            if d["device_type"] == "array"
        )

    def _raid_info(self, raid_level):
        """Map RAID level to display name and redundancy."""
        mapping = {
            "0":  ("RAID 0", 0),
            "1":  ("RAID 1", 1),
            "5":  ("RAID 5", 1),
            "6":  ("RAID 6", 2),
            "10": ("RAID 10", 1),
            "linear": ("JBOD", 0),
            None: ("Single Disk", 0),
        }
        return mapping.get(str(raid_level), (f"RAID {raid_level}", None))

    @property
    def native_value(self):
        array = self._array()
        return round(array["used_percentage"], 2)

    @property
    def extra_state_attributes(self):
        array = self._array()

        # Buffalo API reports sizes in MB → convert to GB
        used_gb = array["used_size"] / 1024
        total_gb = array["total_size"] / 1024

        raid_label, redundancy = self._raid_info(array.get("raid_level"))

        return {
            # Capacity (Buffalo-style)
            "used_gb": round(used_gb, 1),
            "total_gb": round(total_gb, 1),
            "usage_text": f"{round(used_gb, 1)} GB / {round(total_gb, 1)} GB",

            # RAID details
            "raid_level_raw": array.get("raid_level"),
            "raid_level": raid_label,
            "redundancy_disks": redundancy,
            "disk_count": array.get("raid_devices"),
        }

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
