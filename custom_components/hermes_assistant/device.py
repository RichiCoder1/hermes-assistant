"""Home Assistant device metadata for Hermes Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DOMAIN


def gateway_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return the service device shared by one gateway config entry."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Nous Research",
        model="Hermes Agent Gateway",
        entry_type=DeviceEntryType.SERVICE,
    )
