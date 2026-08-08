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


class ConfigEntry:
    """Import-only stand-in."""

    @classmethod
    def __class_getitem__(cls, item: object) -> type[ConfigEntry]:
        return cls


class Platform(StrEnum):
    CONVERSATION = "conversation"


class HomeAssistant:
    """Import-only stand-in."""


class ConfigEntryAuthFailed(Exception):
    """Import-only stand-in."""


class ConfigEntryNotReady(Exception):
    """Import-only stand-in."""


config_entries.ConfigEntry = ConfigEntry
const.Platform = Platform
core.HomeAssistant = HomeAssistant
exceptions.ConfigEntryAuthFailed = ConfigEntryAuthFailed
exceptions.ConfigEntryNotReady = ConfigEntryNotReady
aiohttp_client.async_get_clientsession = lambda hass: None

sys.modules.update(
    {
        "homeassistant": homeassistant,
        "homeassistant.config_entries": config_entries,
        "homeassistant.const": const,
        "homeassistant.core": core,
        "homeassistant.exceptions": exceptions,
        "homeassistant.helpers": helpers,
        "homeassistant.helpers.aiohttp_client": aiohttp_client,
    }
)
