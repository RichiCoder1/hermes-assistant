"""Diagnostic readiness sensor for Hermes Assistant."""

from __future__ import annotations

from typing import Any, override

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HermesAssistantConfigEntry
from .coordinator import HermesHealthCoordinator
from .device import gateway_device_info

_KNOWN_STATUSES = {"ok", "degraded"}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HermesAssistantConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the gateway readiness entity."""
    async_add_entities([HermesReadinessSensor(entry)])


class HermesReadinessSensor(CoordinatorEntity[HermesHealthCoordinator], SensorEntity):
    """Report the gateway's authenticated detailed-health status."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_translation_key = "readiness"

    def __init__(self, entry: HermesAssistantConfigEntry) -> None:
        runtime_data = entry.runtime_data
        super().__init__(runtime_data.coordinator)
        self._attr_options = ["ok", "degraded", "unknown"]
        self._attr_unique_id = f"{entry.entry_id}_readiness"
        self._attr_device_info = gateway_device_info(entry)

    @property
    @override
    def native_value(self) -> str | None:
        """Return a stable enum value for the current gateway status."""
        health = self.coordinator.data
        if health is None:
            return None
        normalized = health.status.casefold()
        return normalized if normalized in _KNOWN_STATUSES else "unknown"

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Preserve an unrecognized raw status for troubleshooting."""
        health = self.coordinator.data
        if health is None or health.status.casefold() in _KNOWN_STATUSES:
            return None
        return {"gateway_status": health.status}
