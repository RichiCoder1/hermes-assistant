"""Connectivity binary sensor for Hermes Assistant."""

from __future__ import annotations

from typing import override

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HermesAssistantConfigEntry
from .coordinator import HermesHealthCoordinator
from .device import gateway_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HermesAssistantConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the gateway connectivity entity."""
    async_add_entities([HermesConnectivityBinarySensor(entry)])


class HermesConnectivityBinarySensor(
    CoordinatorEntity[HermesHealthCoordinator], BinarySensorEntity
):
    """Report whether the authenticated Hermes gateway is connected."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_translation_key = "connectivity"

    def __init__(self, entry: HermesAssistantConfigEntry) -> None:
        runtime_data = entry.runtime_data
        super().__init__(runtime_data.coordinator)
        self._attr_unique_id = f"{entry.entry_id}_connectivity"
        self._attr_device_info = gateway_device_info(entry)

    @property
    @override
    def available(self) -> bool:
        """Keep the entity available so failed health checks show disconnected."""
        return True

    @property
    @override
    def is_on(self) -> bool:
        """Return whether the most recent health request succeeded."""
        return self.coordinator.last_update_success
