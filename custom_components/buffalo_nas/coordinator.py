"""Shared polling for each configured TeraStation."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import BuffaloAuthError, BuffaloError, BuffaloNASClient
from .const import (
    CONF_DEVICE_IDENTIFIER,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .models import Snapshot, read_snapshot

_LOGGER = logging.getLogger(__name__)

type BuffaloConfigEntry = ConfigEntry[BuffaloNASCoordinator]


def make_client(hass: HomeAssistant, config) -> BuffaloNASClient:
    return BuffaloNASClient(
        async_get_clientsession(hass),
        config[CONF_HOST],
        config[CONF_USERNAME],
        config[CONF_PASSWORD],
        config.get(CONF_VERIFY_SSL, False),
    )


class BuffaloNASCoordinator(DataUpdateCoordinator[Snapshot]):
    """Manage one NAS session and a shared telemetry snapshot."""

    config_entry: BuffaloConfigEntry

    def __init__(self, hass: HomeAssistant, entry: BuffaloConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
            always_update=True,
        )
        self.client = make_client(hass, entry.data)
        identifier = entry.data.get(
            CONF_DEVICE_IDENTIFIER,
            entry.data[CONF_HOST]
            if CONF_VERIFY_SSL not in entry.data
            else entry.entry_id,
        )
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=entry.title,
            manufacturer="Buffalo",
            model="TeraStation",
            configuration_url=str(self.client.url.with_path("/detail.html")),
        )

    async def _async_setup(self) -> None:
        """Read device identity once per load."""
        try:
            info = await self.client.portal_info()
        except BuffaloAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except BuffaloError as err:
            _LOGGER.debug("NAS device information unavailable: %s", err)
            return

        serial = info.get("serial_number")
        entry = self.config_entry
        if isinstance(serial, str) and serial.strip():
            serial = serial.strip()
            if entry.unique_id is not None and entry.unique_id != serial:
                raise UpdateFailed(
                    "The NAS at this address has a different serial number"
                )
            self.device_info["serial_number"] = serial
            if entry.unique_id is None and not any(
                existing.unique_id == serial
                for existing in self.hass.config_entries.async_entries(DOMAIN)
            ):
                self.hass.config_entries.async_update_entry(entry, unique_id=serial)
        for key, field in (("name", "hostname"), ("model", "product_name")):
            if isinstance(value := info.get(field), str) and value.strip():
                self.device_info[key] = value.strip()
        version = [
            part
            for key in ("fw_version_major", "fw_version_minor")
            if (part := info.get(key)) is not None and str(part)
        ]
        if version:
            self.device_info["sw_version"] = "-".join(map(str, version))

    async def _async_update_data(self) -> Snapshot:
        try:
            return await read_snapshot(self.client)
        except BuffaloAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except BuffaloError as err:
            raise UpdateFailed(str(err)) from err
