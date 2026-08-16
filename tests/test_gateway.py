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


def sse_body(*events: str) -> list[bytes]:
    """Encode SSE `data:` lines the way aiohttp's StreamReader yields them."""
    return [f"data: {event}\n".encode() for event in events]


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


class FakeStreamContent:
    def __init__(self, lines: list[bytes]) -> None:
        self._lines = lines

    def __aiter__(self) -> FakeStreamContent:
        return self

    async def __anext__(self) -> bytes:
        if not self._lines:
            raise StopAsyncIteration
        return self._lines.pop(0)


class FakeStreamResponse:
    def __init__(self, status: int, lines: list[bytes]) -> None:
        self.status = status
        self.content = FakeStreamContent(lines)

    async def __aenter__(self) -> FakeStreamResponse:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class FakeSession:
    def __init__(self, *responses: FakeResponse | FakeStreamResponse) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, Any]] = []

    def request(
        self, method: str, url: str, **kwargs: Any
    ) -> FakeResponse | FakeStreamResponse:
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


async def test_validate_detects_streaming_support() -> None:
    client = HermesGatewayClient(
        FakeSession(FakeResponse(200, capabilities(chat_completions_streaming=True))),
        "http://hermes:8642",
        "secret",
        timeout=10,
    )
    result = await client.async_validate()
    assert result.supports_streaming is True


async def test_validate_defaults_streaming_to_unsupported() -> None:
    client = HermesGatewayClient(
        FakeSession(FakeResponse(200, capabilities())),
        "http://hermes:8642",
        "secret",
        timeout=10,
    )
    result = await client.async_validate()
    assert result.supports_streaming is False


async def test_stream_complete_yields_deltas_and_stops_on_done() -> None:
    session = FakeSession(
        FakeResponse(
            200,
            capabilities(
                chat_completions_streaming=True,
                session_continuity_header="X-Hermes-Session-Id",
                session_key_header="X-Hermes-Session-Key",
            ),
        ),
        FakeStreamResponse(
            200,
            sse_body(
                '{"choices":[{"delta":{"role":"assistant"}}]}',
                '{"choices":[{"delta":{"content":"Hel"}}]}',
                '{"choices":[{"delta":{"content":"lo"}}]}',
                '{"choices":[],"usage":{"total_tokens":5}}',
                "[DONE]",
                '{"choices":[{"delta":{"content":"ignored"}}]}',
            ),
        ),
    )
    client = HermesGatewayClient(session, "http://hermes:8642", "secret", timeout=10)
    messages = [{"role": "user", "content": "Hi"}]

    chunks = [
        chunk
        async for chunk in client.async_stream_complete(
            messages, session_id="session-a", session_key="scope-a"
        )
    ]

    assert chunks == ["Hel", "lo"]
    request = session.requests[1]
    assert request["json"] == {
        "model": "voice",
        "messages": messages,
        "stream": True,
    }
    assert request["headers"]["X-Hermes-Session-Id"] == "session-a"
    assert request["headers"]["X-Hermes-Session-Key"] == "scope-a"


async def test_stream_complete_ignores_hermes_tool_progress_events() -> None:
    session = FakeSession(
        FakeResponse(200, capabilities(chat_completions_streaming=True)),
        FakeStreamResponse(
            200,
            [
                b": keepalive\n",
                b"\n",
                b"event: hermes.tool.progress\n",
                b'data: {"tool":"web_search","status":"running"}\n',
                b"\n",
                b'data: {"choices":[{"delta":{"content":"Found it"}}]}\n',
                b"data: [DONE]\n",
            ],
        ),
    )
    client = HermesGatewayClient(session, "http://hermes:8642", "secret", timeout=10)

    chunks = [
        chunk
        async for chunk in client.async_stream_complete(
            [], session_id="a", session_key="a"
        )
    ]

    assert chunks == ["Found it"]


async def test_stream_complete_rejects_unknown_named_event() -> None:
    session = FakeSession(
        FakeResponse(200, capabilities(chat_completions_streaming=True)),
        FakeStreamResponse(
            200,
            [b"event: hermes.future\n", b"data: {}\n"],
        ),
    )
    client = HermesGatewayClient(session, "http://hermes:8642", "secret", timeout=10)

    with pytest.raises(HermesProtocolError, match="unsupported stream event"):
        async for _ in client.async_stream_complete(
            [], session_id="a", session_key="a"
        ):
            pass


async def test_stream_complete_rejects_terminal_error_finish_reason() -> None:
    session = FakeSession(
        FakeResponse(200, capabilities(chat_completions_streaming=True)),
        FakeStreamResponse(
            200,
            sse_body(
                '{"choices":[{"delta":{"content":"partial"}}]}',
                '{"choices":[{"delta":{},"finish_reason":"error"}]}',
                "[DONE]",
            ),
        ),
    )
    client = HermesGatewayClient(session, "http://hermes:8642", "secret", timeout=10)
    with pytest.raises(HermesProtocolError):
        async for _ in client.async_stream_complete(
            [], session_id="a", session_key="a"
        ):
            pass


async def test_stream_complete_rejects_top_level_error_event() -> None:
    session = FakeSession(
        FakeResponse(200, capabilities(chat_completions_streaming=True)),
        FakeStreamResponse(
            200,
            sse_body(
                '{"choices":[{"delta":{"content":"partial"}}]}',
                '{"error":{"message":"agent failed"}}',
                "[DONE]",
            ),
        ),
    )
    client = HermesGatewayClient(session, "http://hermes:8642", "secret", timeout=10)
    with pytest.raises(HermesProtocolError, match="streaming error"):
        async for _ in client.async_stream_complete(
            [], session_id="a", session_key="a"
        ):
            pass


async def test_stream_complete_rejects_end_of_file_before_done() -> None:
    session = FakeSession(
        FakeResponse(200, capabilities(chat_completions_streaming=True)),
        FakeStreamResponse(
            200,
            sse_body('{"choices":[{"delta":{"content":"partial"}}]}'),
        ),
    )
    client = HermesGatewayClient(session, "http://hermes:8642", "secret", timeout=10)
    with pytest.raises(HermesProtocolError, match="ended before completion"):
        async for _ in client.async_stream_complete(
            [], session_id="a", session_key="a"
        ):
            pass


async def test_stream_complete_rejects_bad_chunk() -> None:
    session = FakeSession(
        FakeResponse(200, capabilities(chat_completions_streaming=True)),
        FakeStreamResponse(200, sse_body("not json")),
    )
    client = HermesGatewayClient(session, "http://hermes:8642", "secret", timeout=10)
    with pytest.raises(HermesProtocolError):
        async for _ in client.async_stream_complete(
            [], session_id="a", session_key="a"
        ):
            pass


async def test_stream_complete_rejects_auth_failure() -> None:
    session = FakeSession(
        FakeResponse(200, capabilities(chat_completions_streaming=True)),
        FakeStreamResponse(401, []),
    )
    client = HermesGatewayClient(session, "http://hermes:8642", "secret", timeout=10)
    with pytest.raises(HermesAuthenticationError):
        async for _ in client.async_stream_complete(
            [], session_id="a", session_key="a"
        ):
            pass
