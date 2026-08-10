"""Tests for diagnostics and cached System Health information."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

from custom_components.hermes_assistant.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.hermes_assistant.gateway import (
    GatewayCapabilities,
    GatewayHealth,
)
from custom_components.hermes_assistant.system_health import system_health_info


def _entry() -> SimpleNamespace:
    coordinator = SimpleNamespace(
        data=GatewayHealth(status="degraded"),
        last_update_success=True,
        last_successful_update=datetime(2026, 8, 9, 12, 30, tzinfo=UTC),
    )
    capabilities = GatewayCapabilities(
        model="hermes-agent",
        session_id_header="X-Hermes-Session-Id",
        session_key_header="X-Hermes-Session-Key",
        supports_streaming=True,
    )
    return SimpleNamespace(
        entry_id="entry-id",
        title="Hermes voice",
        unique_id="http://hermes:8642",
        version=1,
        minor_version=1,
        data={"base_url": "http://hermes:8642", "api_key": "secret"},
        options={"memory_scope": "conversation"},
        runtime_data=SimpleNamespace(
            coordinator=coordinator,
            capabilities=capabilities,
        ),
    )


async def test_diagnostics_redact_connection_details() -> None:
    diagnostics = await async_get_config_entry_diagnostics(
        cast(Any, SimpleNamespace()), cast(Any, _entry())
    )

    assert diagnostics["config_entry"]["data"] == {
        "base_url": "**REDACTED**",
        "api_key": "**REDACTED**",
    }
    assert diagnostics["gateway"]["model"] == "hermes-agent"
    assert diagnostics["health"] == {
        "connected": True,
        "readiness": "degraded",
        "last_successful_update": "2026-08-09T12:30:00+00:00",
    }


async def test_system_health_uses_cached_coordinator_data() -> None:
    entry = _entry()
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_loaded_entries=lambda domain: [entry])
    )

    info = await system_health_info(cast(Any, hass))

    assert info == {
        "configured_gateways": 1,
        "connected_gateways": 1,
        "gateways": {
            "http://hermes:8642": {
                "name": "Hermes voice",
                "model": "hermes-agent",
                "readiness": "degraded",
                "last_successful_update": "2026-08-09T12:30:00+00:00",
            }
        },
    }
