"""Gateway health coordination for Hermes Assistant."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .gateway import (
    GatewayHealth,
    HermesAuthenticationError,
    HermesGatewayClient,
    HermesGatewayError,
)

_LOGGER = logging.getLogger(__name__)
_HEALTH_UPDATE_INTERVAL = timedelta(seconds=60)


class HermesHealthCoordinator(DataUpdateCoordinator[GatewayHealth]):
    """Poll authenticated Hermes gateway health."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: HermesGatewayClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name="Hermes Agent Gateway health",
            update_interval=_HEALTH_UPDATE_INTERVAL,
            always_update=False,
        )
        self._client = client

    async def _async_update_data(self) -> GatewayHealth:
        """Fetch the latest authenticated gateway health."""
        try:
            return await self._client.async_health()
        except HermesAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except HermesGatewayError as err:
            raise UpdateFailed("Unable to refresh Hermes gateway health") from err
