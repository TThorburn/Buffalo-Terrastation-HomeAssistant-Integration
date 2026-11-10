"""Buffalo TeraStation NAS integration."""

from asyncio import CancelledError
from datetime import timedelta

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .coordinator import BuffaloConfigEntry, BuffaloNASCoordinator

PLATFORMS = (Platform.SENSOR, Platform.BINARY_SENSOR)


async def async_setup_entry(hass: HomeAssistant, entry: BuffaloConfigEntry) -> bool:
    """Set up a NAS from its config entry."""
    coordinator = BuffaloNASCoordinator(hass, entry)
    try:
        await coordinator.async_config_entry_first_refresh()
        entry.runtime_data = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except (Exception, CancelledError):
        await coordinator.client.logout()
        raise
    entry.async_on_unload(entry.add_update_listener(_async_update_interval))
    return True


async def _async_update_interval(
    hass: HomeAssistant, entry: BuffaloConfigEntry
) -> None:
    interval = timedelta(
        seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    coordinator = entry.runtime_data
    if interval != coordinator.update_interval:
        coordinator.update_interval = interval
        await coordinator.async_request_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: BuffaloConfigEntry) -> bool:
    """Unload the platforms before releasing their NAS session."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await entry.runtime_data.client.logout()
    return True
