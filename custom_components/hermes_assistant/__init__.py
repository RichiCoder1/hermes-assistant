"""Hermes Assistant integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_API_KEY, CONF_BASE_URL, CONF_TIMEOUT, DEFAULT_TIMEOUT
from .coordinator import HermesHealthCoordinator
from .gateway import (
    GatewayCapabilities,
    HermesAuthenticationError,
    HermesGatewayClient,
    HermesGatewayError,
)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.CONVERSATION]


@dataclass(slots=True)
class HermesAssistantRuntimeData:
    """Runtime objects shared by Hermes Assistant platforms."""

    client: HermesGatewayClient
    capabilities: GatewayCapabilities
    coordinator: HermesHealthCoordinator


type HermesAssistantConfigEntry = ConfigEntry[HermesAssistantRuntimeData]


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
        capabilities = await client.async_validate()
    except HermesAuthenticationError as err:
        raise ConfigEntryAuthFailed from err
    except HermesGatewayError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = HermesHealthCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = HermesAssistantRuntimeData(
        client=client,
        capabilities=capabilities,
        coordinator=coordinator,
    )
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
