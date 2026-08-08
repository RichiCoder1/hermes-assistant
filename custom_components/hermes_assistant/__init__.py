"""Hermes Assistant integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_API_KEY, CONF_BASE_URL, CONF_TIMEOUT, DEFAULT_TIMEOUT
from .gateway import (
    HermesAuthenticationError,
    HermesGatewayClient,
    HermesGatewayError,
)

PLATFORMS = [Platform.CONVERSATION]
type HermesAssistantConfigEntry = ConfigEntry[HermesGatewayClient]


async def async_setup_entry(
    hass: HomeAssistant, entry: HermesAssistantConfigEntry
) -> bool:
    """Set up Hermes Assistant from a config entry."""
    client = HermesGatewayClient(
        async_get_clientsession(hass),
        entry.data[CONF_BASE_URL],
        entry.data[CONF_API_KEY],
        timeout=entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
    )
    try:
        await client.async_validate()
    except HermesAuthenticationError as err:
        raise ConfigEntryAuthFailed from err
    except HermesGatewayError as err:
        raise ConfigEntryNotReady(str(err)) from err

    entry.runtime_data = client
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: HermesAssistantConfigEntry
) -> bool:
    """Unload Hermes Assistant."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload_entry(
    hass: HomeAssistant, entry: HermesAssistantConfigEntry
) -> None:
    """Reload after options change."""
    await hass.config_entries.async_reload(entry.entry_id)
