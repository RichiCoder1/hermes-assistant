"""Minimal Home Assistant import doubles for isolated unit tests."""

from __future__ import annotations

import sys
from dataclasses import dataclass
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
conversation = ModuleType("homeassistant.components.conversation")
binary_sensor = ModuleType("homeassistant.components.binary_sensor")
sensor = ModuleType("homeassistant.components.sensor")
system_health = ModuleType("homeassistant.components.system_health")
intent = ModuleType("homeassistant.helpers.intent")
device_registry = ModuleType("homeassistant.helpers.device_registry")
entity_platform = ModuleType("homeassistant.helpers.entity_platform")
redact = ModuleType("homeassistant.helpers.redact")
update_coordinator = ModuleType("homeassistant.helpers.update_coordinator")


class ConfigEntry:
    """Import-only stand-in."""

    @classmethod
    def __class_getitem__(cls, item: object) -> type[ConfigEntry]:
        return cls


class Platform(StrEnum):
    BINARY_SENSOR = "binary_sensor"
    CONVERSATION = "conversation"
    SENSOR = "sensor"


class EntityCategory(StrEnum):
    DIAGNOSTIC = "diagnostic"


class BinarySensorDeviceClass(StrEnum):
    CONNECTIVITY = "connectivity"


class SensorDeviceClass(StrEnum):
    ENUM = "enum"


class DeviceEntryType(StrEnum):
    SERVICE = "service"


class HomeAssistant:
    """Import-only stand-in."""


def callback(func: object) -> object:
    """Return a callback unchanged."""
    return func


class ConfigEntryAuthFailed(Exception):
    """Import-only stand-in."""


class ConfigEntryNotReady(Exception):
    """Import-only stand-in."""


class ConversationEntity:
    """Small conversation entity stand-in."""

    available = True

    def async_write_ha_state(self) -> None:
        """Accept state writes from the entity under test."""


class AbstractConversationAgent:
    """Import-only stand-in."""


@dataclass
class AssistantContent:
    """Minimal assistant content value."""

    agent_id: str
    content: str | None = None


class ConverseError(Exception):
    """Import-only stand-in."""


class IntentResponseErrorCode(StrEnum):
    """Minimal intent error codes."""

    UNKNOWN = "unknown"


class IntentResponse:
    """Minimal intent response value."""

    def __init__(self, *, language: str) -> None:
        self.language = language

    def async_set_error(self, code: IntentResponseErrorCode, message: str) -> None:
        self.error_code = code
        self.error_message = message


class BinarySensorEntity:
    """Import-only stand-in."""


class SensorEntity:
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
        self.data = None


class CoordinatorEntity:
    """Small coordinator entity stand-in."""

    @classmethod
    def __class_getitem__(cls, item: object) -> type[CoordinatorEntity]:
        return cls

    def __init__(self, coordinator: DataUpdateCoordinator) -> None:
        self.coordinator = coordinator


class SystemHealthRegistration:
    """Capture a System Health callback."""

    def async_register_info(self, info_callback: object) -> None:
        self.info_callback = info_callback


def async_redact_data(
    data: dict[str, object], to_redact: set[str]
) -> dict[str, object]:
    """Redact selected top-level keys."""
    return {
        key: "**REDACTED**" if key in to_redact else value
        for key, value in data.items()
    }


config_entries.ConfigEntry = ConfigEntry
const.Platform = Platform
const.EntityCategory = EntityCategory
const.MATCH_ALL = "*"
core.HomeAssistant = HomeAssistant
core.callback = callback
exceptions.ConfigEntryAuthFailed = ConfigEntryAuthFailed
exceptions.ConfigEntryNotReady = ConfigEntryNotReady
aiohttp_client.async_get_clientsession = lambda hass: None
conversation.ConversationEntity = ConversationEntity
conversation.AbstractConversationAgent = AbstractConversationAgent
conversation.AssistantContent = AssistantContent
conversation.ConverseError = ConverseError
conversation.async_set_agent = lambda *args: None
conversation.async_unset_agent = lambda *args: None
conversation.async_get_result_from_chat_log = lambda user_input, chat_log: chat_log
intent.IntentResponse = IntentResponse
intent.IntentResponseErrorCode = IntentResponseErrorCode
binary_sensor.BinarySensorDeviceClass = BinarySensorDeviceClass
binary_sensor.BinarySensorEntity = BinarySensorEntity
sensor.SensorDeviceClass = SensorDeviceClass
sensor.SensorEntity = SensorEntity
system_health.SystemHealthRegistration = SystemHealthRegistration
device_registry.DeviceEntryType = DeviceEntryType
device_registry.DeviceInfo = DeviceInfo
entity_platform.AddConfigEntryEntitiesCallback = object
redact.async_redact_data = async_redact_data
update_coordinator.CoordinatorEntity = CoordinatorEntity
update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
update_coordinator.UpdateFailed = UpdateFailed
components.conversation = conversation
helpers.intent = intent

sys.modules.update(
    {
        "homeassistant": homeassistant,
        "homeassistant.config_entries": config_entries,
        "homeassistant.components": components,
        "homeassistant.components.conversation": conversation,
        "homeassistant.components.binary_sensor": binary_sensor,
        "homeassistant.components.sensor": sensor,
        "homeassistant.components.system_health": system_health,
        "homeassistant.const": const,
        "homeassistant.core": core,
        "homeassistant.exceptions": exceptions,
        "homeassistant.helpers": helpers,
        "homeassistant.helpers.aiohttp_client": aiohttp_client,
        "homeassistant.helpers.device_registry": device_registry,
        "homeassistant.helpers.entity_platform": entity_platform,
        "homeassistant.helpers.intent": intent,
        "homeassistant.helpers.redact": redact,
        "homeassistant.helpers.update_coordinator": update_coordinator,
    }
)
