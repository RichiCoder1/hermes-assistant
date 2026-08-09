"""Tests for gateway device metadata and connectivity state."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.hermes_assistant.binary_sensor import (
    HermesConnectivityBinarySensor,
)
from custom_components.hermes_assistant.coordinator import HermesHealthCoordinator
from custom_components.hermes_assistant.device import gateway_device_info
from custom_components.hermes_assistant.gateway import (
    GatewayHealth,
    HermesAuthenticationError,
    HermesConnectionError,
)
from custom_components.hermes_assistant.sensor import HermesReadinessSensor


class FakeHealthClient:
    """Return or raise one configured health result."""

    def __init__(self, result: GatewayHealth | Exception) -> None:
        self.result = result

    async def async_health(self) -> GatewayHealth:
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def _coordinator(result: GatewayHealth | Exception) -> HermesHealthCoordinator:
    return HermesHealthCoordinator(
        cast(Any, SimpleNamespace()),
        cast(Any, SimpleNamespace()),
        cast(Any, FakeHealthClient(result)),
    )


def _entry(*, connected: bool = True, status: str = "ok") -> SimpleNamespace:
    coordinator = SimpleNamespace(
        data=GatewayHealth(status=status), last_update_success=connected
    )
    return SimpleNamespace(
        entry_id="entry-id",
        title="Hermes voice",
        runtime_data=SimpleNamespace(coordinator=coordinator),
    )


def test_gateway_device_is_a_service() -> None:
    device_info = gateway_device_info(_entry())

    assert device_info["identifiers"] == {("hermes_assistant", "entry-id")}
    assert device_info["name"] == "Hermes voice"
    assert device_info["manufacturer"] == "Nous Research"
    assert device_info["model"] == "Hermes Agent Gateway"
    assert device_info["entry_type"] == DeviceEntryType.SERVICE


def test_connectivity_reports_coordinator_result_without_becoming_unavailable() -> None:
    entry = _entry()
    entity = HermesConnectivityBinarySensor(entry)

    assert entity.is_on is True
    assert entity.available is True
    assert entity._attr_device_class == BinarySensorDeviceClass.CONNECTIVITY
    assert entity._attr_entity_category == EntityCategory.DIAGNOSTIC
    assert entity._attr_unique_id == "entry-id_connectivity"

    entry.runtime_data.coordinator.last_update_success = False
    assert entity.is_on is False
    assert entity.available is True


def test_readiness_reports_detailed_health_status() -> None:
    entity = HermesReadinessSensor(_entry(status="degraded"))

    assert entity.native_value == "degraded"
    assert entity.extra_state_attributes is None
    assert entity._attr_device_class == SensorDeviceClass.ENUM
    assert entity._attr_entity_category == EntityCategory.DIAGNOSTIC
    assert entity._attr_unique_id == "entry-id_readiness"


def test_readiness_preserves_unrecognized_status() -> None:
    entity = HermesReadinessSensor(_entry(status="starting"))

    assert entity.native_value == "unknown"
    assert entity.extra_state_attributes == {"gateway_status": "starting"}


async def test_coordinator_returns_gateway_health() -> None:
    coordinator = _coordinator(GatewayHealth(status="degraded"))

    assert await coordinator._async_update_data() == GatewayHealth(status="degraded")
    assert coordinator.last_successful_update is not None


async def test_coordinator_requests_reauthentication() -> None:
    coordinator = _coordinator(HermesAuthenticationError("bad key"))

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_coordinator_wraps_gateway_failure() -> None:
    coordinator = _coordinator(HermesConnectionError("offline"))

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
