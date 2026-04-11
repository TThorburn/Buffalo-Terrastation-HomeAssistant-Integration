from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN


def buffalo_device_info(host: str) -> DeviceInfo:
    """Return device information for the Buffalo NAS."""
    return DeviceInfo(
        identifiers={(DOMAIN, host)},
        name="Buffalo TeraStation NAS",
        manufacturer="Buffalo",
        model="TeraStation TS-Series",
        configuration_url=f"https://{host}",
    )
