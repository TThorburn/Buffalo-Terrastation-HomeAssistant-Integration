"""Normalize the TeraStation responses used by the entity platforms."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from math import isfinite
from time import monotonic, time
from typing import Any

from .client import BuffaloAuthError, BuffaloError, BuffaloNASClient

_LOGGER = logging.getLogger(__name__)


@dataclass
class Snapshot:
    """Current values, with None for a source that failed."""

    devices: dict[str, dict[str, Any]] | None = None
    usage: dict[str, Any] | None = None
    interfaces: dict[str, dict[str, Any]] | None = None
    errors: list[Any] | None = None
    information: list[Any] | None = None


def number(value: Any) -> int | float | None:
    """Read firmware numbers and numeric strings, ignoring placeholders."""
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value) if isinstance(value, str) else value
    except ValueError:
        try:
            parsed = float(value)
        except ValueError:
            return None
    if isinstance(parsed, int):
        return parsed if parsed >= 0 else None
    if isinstance(parsed, float) and isfinite(parsed) and parsed >= 0:
        return parsed
    return None


def percentage(value: Any) -> int | float | None:
    """A real utilization percentage."""
    parsed = number(value)
    return parsed if parsed is not None and parsed <= 100 else None


def statuses(record: dict[str, Any]) -> tuple[str, ...]:
    """Normalize single and multi-valued status fields."""
    raw = record.get("status")
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return ()
    return tuple(
        value.strip().lower()
        for value in raw
        if isinstance(value, str) and value.strip()
    )


def arrays(snapshot: Snapshot) -> list[str]:
    """Array IDs in firmware order for legacy migration."""
    return [
        key
        for key, device in (snapshot.devices or {}).items()
        if device.get("device_type") == "array"
    ]


def _indexed(result: Any, key: str, identifiers: tuple[str, ...]):
    if not isinstance(result, dict) or not isinstance(rows := result.get(key), list):
        return None
    records = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        for field in identifiers:
            value = row.get(field)
            if (
                isinstance(value, (str, int))
                and not isinstance(value, bool)
                and str(value).strip()
            ):
                records[str(value).strip()] = row
                break
    return records if records or not rows else None


SOURCES = ("devices", "usage", "interfaces", "errors", "information")


async def read_snapshot(
    client: BuffaloNASClient, sources: tuple[str, ...] = SOURCES
) -> Snapshot:
    """Poll read-only sources independently so partial responses remain useful."""
    await client.login()

    requests = {
        "devices": lambda: client.read("device.getlist", "device.get_list"),
        "usage": lambda: client.read(
            "get_cpu_mem_info", "getcpumeminfo", apply_log_output=False
        ),
        "interfaces": lambda: client.read(
            "network.list_interface_settings", "network.listinterfacesettings"
        ),
        "errors": lambda: client.read("get_errors", "geterrors"),
        "information": lambda: client.read("get_informations", "getinformations"),
    }
    results = await asyncio.gather(
        *(requests[source]() for source in sources), return_exceptions=True
    )
    for index, result in enumerate(results):
        if isinstance(result, BuffaloAuthError):
            raise result
        if isinstance(result, BuffaloError):
            _LOGGER.debug("NAS telemetry source failed: %s", result)
            results[index] = None
        elif isinstance(result, BaseException):
            raise result

    values = dict(zip(sources, results, strict=True))
    devices = values.get("devices")
    usage = values.get("usage")
    interfaces = values.get("interfaces")
    errors = values.get("errors")
    information = values.get("information")
    data = Snapshot(
        devices=_indexed(devices, "devices", ("device_file", "device_id")),
        usage=usage
        if isinstance(usage, dict)
        and any(
            percentage(usage.get(key)) is not None
            for key in ("cpu_usage_rate", "mem_usage_rate")
        )
        else None,
        interfaces=_indexed(interfaces, "interfaces", ("name", "ifname")),
        errors=errors if isinstance(errors, list) else None,
        information=information if isinstance(information, list) else None,
    )
    if all(getattr(data, source) is None for source in sources):
        raise BuffaloError(
            "NAS returned no usable data for the requested monitoring sources"
        )
    return data


class NetworkSamples:
    """Calculate rates from counter differences and actual elapsed time."""

    def __init__(self) -> None:
        self._previous: dict[str, tuple[float, dict]] = {}

    def reset(self) -> None:
        self._previous.clear()

    def update(self, interfaces: dict[str, dict]) -> None:
        sampled = monotonic()
        timestamp = time()
        previous, self._previous = self._previous, {}
        for name, interface in interfaces.items():
            counters = {
                "rx": next(
                    (
                        value
                        for key in ("recevied_bytes", "received_bytes", "rx_bytes")
                        if (value := number(interface.get(key))) is not None
                    ),
                    None,
                ),
                "tx": number(interface.get("sent_bytes", interface.get("tx_bytes"))),
            }
            old_time, old_counters = previous.get(name, (sampled, {}))
            elapsed = sampled - old_time
            interface["sampled_at"] = timestamp
            for direction, value in counters.items():
                before = old_counters.get(direction)
                rate = None
                if (
                    elapsed > 0
                    and value is not None
                    and before is not None
                    and value >= before
                ):
                    rate = (value - before) / elapsed
                interface[f"{direction}_bytes_per_second"] = rate
            self._previous[name] = (sampled, counters)
