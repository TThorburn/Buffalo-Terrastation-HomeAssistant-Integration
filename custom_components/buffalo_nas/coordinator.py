from datetime import timedelta
import aiohttp

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant

from .client import BuffaloNASClient
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL


class BuffaloNASCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, config, options):
        self.client = BuffaloNASClient(
            config["host"],
            config["username"],
            config["password"],
        )

        scan_interval = options.get("scan_interval", DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        async with aiohttp.ClientSession() as session:
            storage = await self.client.call(session, "device.getlist")
            cpu = await self.client.call(
                session,
                "get_cpu_mem_info",
                {"apply_log_output": False},
            )
            network = await self.client.call(
                session,
                "network.list_interface_settings",
            )

            return {
                "devices": storage["result"]["devices"],
                "cpu": cpu["result"],
                "network": network["result"]["interfaces"],
            }
