"""System Health support for Hermes Assistant."""

from __future__ import annotations

from urllib.parse import urlsplit

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from . import HermesAssistantConfigEntry
from .const import CONF_BASE_URL, DOMAIN


@callback
def async_register(
    hass: HomeAssistant,
    register: system_health.SystemHealthRegistration,
) -> None:
    """Register cached Hermes gateway health information."""
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant) -> dict[str, object]:
    """Return a compact summary without making network requests."""
    entries: list[HermesAssistantConfigEntry] = (
        hass.config_entries.async_loaded_entries(DOMAIN)
    )
    gateways: dict[str, dict[str, object]] = {}

    for entry in entries:
        coordinator = entry.runtime_data.coordinator
        health = coordinator.data
        parsed = urlsplit(entry.data[CONF_BASE_URL])
        endpoint = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        gateways[endpoint] = {
            "name": entry.title,
            "model": entry.runtime_data.capabilities.model,
            "readiness": (
                health.status
                if coordinator.last_update_success and health
                else "unavailable"
            ),
            "last_successful_update": (
                coordinator.last_successful_update.isoformat()
                if coordinator.last_successful_update is not None
                else None
            ),
        }

    return {
        "configured_gateways": len(entries),
        "connected_gateways": sum(
            entry.runtime_data.coordinator.last_update_success for entry in entries
        ),
        "gateways": gateways,
    }
