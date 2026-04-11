from __future__ import annotations

from datetime import timedelta
import logging
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import BuffaloNASClient
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class BuffaloNASCoordinator(DataUpdateCoordinator):
    """Coordinator for Buffalo NAS data updates."""

    def __init__(self, hass: HomeAssistant, config: dict, options: dict):
        self.host = config["host"]

        self.client = BuffaloNASClient(
            host=config["host"],
            username=config["username"],
            password=config["password"],
        )

        scan_interval = options.get("scan_interval", DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,  # ✅ REQUIRED by HA
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from the Buffalo NAS."""
        try:
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

        except Exception as err:
            raise UpdateFailed(f"Failed to update Buffalo NAS data: {err}") from err
