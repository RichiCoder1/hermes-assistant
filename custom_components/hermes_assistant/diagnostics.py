"""Diagnostics support for Hermes Assistant."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import async_redact_data

from . import HermesAssistantConfigEntry
from .const import CONF_API_KEY, CONF_BASE_URL

_TO_REDACT = {CONF_API_KEY, CONF_BASE_URL}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: HermesAssistantConfigEntry
) -> dict[str, Any]:
    """Return privacy-safe diagnostics for one gateway entry."""
    runtime_data = entry.runtime_data
    coordinator = runtime_data.coordinator
    health = coordinator.data
    return {
        "config_entry": {
            "data": async_redact_data(dict(entry.data), _TO_REDACT),
            "options": dict(entry.options),
            "version": entry.version,
            "minor_version": entry.minor_version,
        },
        "gateway": {
            "model": runtime_data.capabilities.model,
            "session_continuity": bool(runtime_data.capabilities.session_id_header),
            "long_term_memory_scoping": bool(
                runtime_data.capabilities.session_key_header
            ),
        },
        "health": {
            "connected": coordinator.last_update_success,
            "readiness": health.status if health is not None else None,
            "last_successful_update": (
                coordinator.last_successful_update.isoformat()
                if coordinator.last_successful_update is not None
                else None
            ),
        },
    }
