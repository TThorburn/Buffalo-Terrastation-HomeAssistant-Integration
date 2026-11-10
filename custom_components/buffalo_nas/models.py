"""Normalize the TeraStation responses used by the entity platforms."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from math import isfinite
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


async def read_snapshot(client: BuffaloNASClient) -> Snapshot:
    """Poll read-only sources independently so partial responses remain useful."""
    await client.login()

    requests = (
        client.read("device.getlist", "device.get_list"),
        client.read("get_cpu_mem_info", "getcpumeminfo", apply_log_output=False),
        client.read("network.list_interface_settings", "network.listinterfacesettings"),
        client.read("get_errors", "geterrors"),
        client.read("get_informations", "getinformations"),
    )
    results = await asyncio.gather(*requests, return_exceptions=True)
    for index, result in enumerate(results):
        if isinstance(result, BuffaloAuthError):
            raise result
        if isinstance(result, BuffaloError):
            _LOGGER.debug("NAS telemetry source failed: %s", result)
            results[index] = None
        elif isinstance(result, BaseException):
            raise result

    devices, usage, interfaces, errors, information = results
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
    if all(group is None for group in (data.devices, data.usage, data.interfaces)):
        raise BuffaloError(
            "NAS returned no usable storage, utilization or network data"
        )
    return data
