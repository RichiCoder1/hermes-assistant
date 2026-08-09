"""Minimal Home Assistant import doubles for isolated unit tests."""

from __future__ import annotations

import sys
from enum import StrEnum
from types import ModuleType

homeassistant = ModuleType("homeassistant")
config_entries = ModuleType("homeassistant.config_entries")
const = ModuleType("homeassistant.const")
core = ModuleType("homeassistant.core")
exceptions = ModuleType("homeassistant.exceptions")
helpers = ModuleType("homeassistant.helpers")
aiohttp_client = ModuleType("homeassistant.helpers.aiohttp_client")
components = ModuleType("homeassistant.components")
binary_sensor = ModuleType("homeassistant.components.binary_sensor")
device_registry = ModuleType("homeassistant.helpers.device_registry")
entity_platform = ModuleType("homeassistant.helpers.entity_platform")
update_coordinator = ModuleType("homeassistant.helpers.update_coordinator")


class ConfigEntry:
    """Import-only stand-in."""

    @classmethod
    def __class_getitem__(cls, item: object) -> type[ConfigEntry]:
        return cls


class Platform(StrEnum):
    BINARY_SENSOR = "binary_sensor"
    CONVERSATION = "conversation"


class EntityCategory(StrEnum):
    DIAGNOSTIC = "diagnostic"


class BinarySensorDeviceClass(StrEnum):
    CONNECTIVITY = "connectivity"


class DeviceEntryType(StrEnum):
    SERVICE = "service"


class HomeAssistant:
    """Import-only stand-in."""


class ConfigEntryAuthFailed(Exception):
    """Import-only stand-in."""


class ConfigEntryNotReady(Exception):
    """Import-only stand-in."""


class BinarySensorEntity:
    """Import-only stand-in."""


class DeviceInfo(dict):
    """Import-only stand-in."""


class UpdateFailed(Exception):
    """Import-only stand-in."""


class DataUpdateCoordinator:
    """Small coordinator stand-in."""

    @classmethod
    def __class_getitem__(cls, item: object) -> type[DataUpdateCoordinator]:
        return cls

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.last_update_success = True


class CoordinatorEntity:
    """Small coordinator entity stand-in."""

    @classmethod
    def __class_getitem__(cls, item: object) -> type[CoordinatorEntity]:
        return cls

    def __init__(self, coordinator: DataUpdateCoordinator) -> None:
        self.coordinator = coordinator


config_entries.ConfigEntry = ConfigEntry
const.Platform = Platform
const.EntityCategory = EntityCategory
core.HomeAssistant = HomeAssistant
exceptions.ConfigEntryAuthFailed = ConfigEntryAuthFailed
exceptions.ConfigEntryNotReady = ConfigEntryNotReady
aiohttp_client.async_get_clientsession = lambda hass: None
binary_sensor.BinarySensorDeviceClass = BinarySensorDeviceClass
binary_sensor.BinarySensorEntity = BinarySensorEntity
device_registry.DeviceEntryType = DeviceEntryType
device_registry.DeviceInfo = DeviceInfo
entity_platform.AddConfigEntryEntitiesCallback = object
update_coordinator.CoordinatorEntity = CoordinatorEntity
update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
update_coordinator.UpdateFailed = UpdateFailed

sys.modules.update(
    {
        "homeassistant": homeassistant,
        "homeassistant.config_entries": config_entries,
        "homeassistant.components": components,
        "homeassistant.components.binary_sensor": binary_sensor,
        "homeassistant.const": const,
        "homeassistant.core": core,
        "homeassistant.exceptions": exceptions,
        "homeassistant.helpers": helpers,
        "homeassistant.helpers.aiohttp_client": aiohttp_client,
        "homeassistant.helpers.device_registry": device_registry,
        "homeassistant.helpers.entity_platform": entity_platform,
        "homeassistant.helpers.update_coordinator": update_coordinator,
    }
)
