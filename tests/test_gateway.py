"""Tests for the Hermes gateway client."""

from __future__ import annotations

from typing import Any

import pytest

from custom_components.hermes_assistant.gateway import (
    HermesAuthenticationError,
    HermesGatewayClient,
    HermesProtocolError,
    normalize_base_url,
)


class FakeResponse:
    def __init__(self, status: int, payload: object) -> None:
        self.status = status
        self.payload = payload

    async def __aenter__(self) -> FakeResponse:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def json(self, *, content_type: object = None) -> object:
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class FakeSession:
    def __init__(self, *responses: FakeResponse) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.requests.append({"method": method, "url": url, **kwargs})
        return self.responses.pop(0)


def capabilities(**features: object) -> dict[str, object]:
    return {
        "object": "hermes.api_server.capabilities",
        "platform": "hermes-agent",
        "model": "voice",
        "auth": {"type": "bearer", "required": True},
        "features": {"chat_completions": True, **features},
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("http://hermes:8642/", "http://hermes:8642"),
        (" https://hermes.example/p/voice/ ", "https://hermes.example/p/voice"),
    ],
)
def test_normalize_base_url(value: str, expected: str) -> None:
    assert normalize_base_url(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "hermes:8642",
        "ftp://hermes",
        "http:///gateway",
        "http://hermes/?x=1",
        "http://user:password@hermes:8642",
    ],
)
def test_normalize_base_url_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        normalize_base_url(value)


async def test_validate_capabilities() -> None:
    session = FakeSession(
        FakeResponse(
            200,
            capabilities(
                session_continuity_header="X-Hermes-Session-Id",
                session_key_header="X-Hermes-Session-Key",
            ),
        )
    )
    client = HermesGatewayClient(session, "http://hermes:8642", "secret", timeout=10)

    result = await client.async_validate()

    assert result.model == "voice"
    assert result.session_id_header == "X-Hermes-Session-Id"
    assert session.requests[0]["headers"]["Authorization"] == "Bearer secret"
    assert session.requests[0]["url"].endswith("/v1/capabilities")


async def test_validate_rejects_wrong_service() -> None:
    client = HermesGatewayClient(
        FakeSession(FakeResponse(200, {"object": "list"})),
        "http://hermes:8642",
        "secret",
        timeout=10,
    )
    with pytest.raises(HermesProtocolError):
        await client.async_validate()


async def test_validate_requires_gateway_authentication() -> None:
    payload = capabilities()
    payload["auth"] = {"type": "bearer", "required": False}
    client = HermesGatewayClient(
        FakeSession(FakeResponse(200, payload)),
        "http://hermes:8642",
        "secret",
        timeout=10,
    )
    with pytest.raises(HermesProtocolError):
        await client.async_validate()


async def test_validate_rejects_bad_key() -> None:
    client = HermesGatewayClient(
        FakeSession(FakeResponse(401, {})),
        "http://hermes:8642",
        "secret",
        timeout=10,
    )
    with pytest.raises(HermesAuthenticationError):
        await client.async_validate()


async def test_health_uses_authenticated_detailed_endpoint() -> None:
    session = FakeSession(FakeResponse(200, {"status": "degraded"}))
    client = HermesGatewayClient(session, "http://hermes:8642", "secret", timeout=10)

    result = await client.async_health()

    assert result.status == "degraded"
    assert session.requests[0]["url"].endswith("/health/detailed")
    assert session.requests[0]["headers"]["Authorization"] == "Bearer secret"


async def test_health_rejects_missing_status() -> None:
    client = HermesGatewayClient(
        FakeSession(FakeResponse(200, {"readiness": {}})),
        "http://hermes:8642",
        "secret",
        timeout=10,
    )

    with pytest.raises(HermesProtocolError):
        await client.async_health()


async def test_complete_sends_transcript_and_session_headers() -> None:
    session = FakeSession(
        FakeResponse(
            200,
            capabilities(
                session_continuity_header="X-Hermes-Session-Id",
                session_key_header="X-Hermes-Session-Key",
            ),
        ),
        FakeResponse(200, {"choices": [{"message": {"content": " Hello "}}]}),
    )
    client = HermesGatewayClient(session, "http://hermes:8642", "secret", timeout=10)
    messages = [{"role": "user", "content": "Hi"}]

    answer = await client.async_complete(
        messages, session_id="session-a", session_key="scope-a"
    )

    assert answer == "Hello"
    request = session.requests[1]
    assert request["json"] == {
        "model": "voice",
        "messages": messages,
        "stream": False,
    }
    assert request["headers"]["X-Hermes-Session-Id"] == "session-a"
    assert request["headers"]["X-Hermes-Session-Key"] == "scope-a"


async def test_complete_rejects_empty_content() -> None:
    session = FakeSession(
        FakeResponse(200, capabilities()),
        FakeResponse(200, {"choices": [{"message": {"content": ""}}]}),
    )
    client = HermesGatewayClient(session, "http://hermes:8642", "secret", timeout=10)
    with pytest.raises(HermesProtocolError):
        await client.async_complete([], session_id="a", session_key="a")
