"""Conversation routing and streaming tests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import Any

from homeassistant.components import conversation

from custom_components.hermes_assistant.conversation import (
    HermesConversationEntity,
    _stream_deltas,
)
from custom_components.hermes_assistant.gateway import HermesTimeoutError


class FakeClient:
    """Record which completion path the entity selects."""

    def __init__(
        self, *, supports_streaming: bool, error: Exception | None = None
    ) -> None:
        self.capabilities = SimpleNamespace(supports_streaming=supports_streaming)
        self.error = error
        self.complete_calls: list[dict[str, Any]] = []
        self.stream_calls: list[dict[str, Any]] = []

    async def async_complete(
        self, messages: list[dict[str, str]], **kwargs: Any
    ) -> str:
        self.complete_calls.append({"messages": messages, **kwargs})
        return "**Hello** 😀 there"

    async def async_stream_complete(
        self, messages: list[dict[str, str]], **kwargs: Any
    ) -> AsyncIterator[str]:
        self.stream_calls.append({"messages": messages, **kwargs})
        if self.error:
            raise self.error
        yield "Hello"
        yield " there"


class FakeChatLog:
    """Minimal chat log supporting both completion paths."""

    def __init__(self) -> None:
        self.conversation_id = "conversation-id"
        self.content = [
            SimpleNamespace(role="system", content="System prompt"),
            SimpleNamespace(role="user", content="Hi"),
        ]
        self.added: list[conversation.AssistantContent] = []

    async def async_provide_llm_data(self, *args: object) -> None:
        """Accept prompt configuration."""

    def async_add_assistant_content_without_tools(
        self, content: conversation.AssistantContent
    ) -> None:
        self.added.append(content)

    async def async_add_delta_content_stream(
        self,
        agent_id: str,
        stream: AsyncIterator[dict[str, str]],
    ) -> AsyncIterator[conversation.AssistantContent]:
        text = ""
        async for delta in stream:
            text += delta.get("content", "")
        content = conversation.AssistantContent(agent_id=agent_id, content=text)
        self.added.append(content)
        yield content


def _entity(client: FakeClient) -> HermesConversationEntity:
    entry = SimpleNamespace(
        entry_id="entry-id",
        title="Hermes",
        options={"max_response_chars": 1200},
        runtime_data=SimpleNamespace(client=client),
    )
    return HermesConversationEntity(entry)


def _user_input() -> SimpleNamespace:
    return SimpleNamespace(
        agent_id="conversation.hermes",
        context=SimpleNamespace(user_id="user-id"),
        device_id="device-id",
        extra_system_prompt=None,
        language="en",
        as_llm_context=lambda domain: SimpleNamespace(domain=domain),
    )


async def test_handle_message_uses_streaming_when_advertised() -> None:
    client = FakeClient(supports_streaming=True)
    chat_log = FakeChatLog()

    await _entity(client)._async_handle_message(_user_input(), chat_log)

    assert not client.complete_calls
    assert len(client.stream_calls) == 1
    assert chat_log.added[-1].content == "Hello there"


async def test_handle_message_falls_back_and_cleans_spoken_text() -> None:
    client = FakeClient(supports_streaming=False)
    chat_log = FakeChatLog()

    await _entity(client)._async_handle_message(_user_input(), chat_log)

    assert not client.stream_calls
    assert len(client.complete_calls) == 1
    assert chat_log.added[-1].content == "Hello there"


async def test_handle_message_keeps_entity_available_after_timeout() -> None:
    client = FakeClient(
        supports_streaming=True,
        error=HermesTimeoutError("Hermes request timed out after 10 seconds"),
    )
    entity = _entity(client)

    result = await entity._async_handle_message(_user_input(), FakeChatLog())

    assert result.response.error_message == (
        "Hermes took too long to respond. Please try again."
    )
    assert not hasattr(entity, "_attr_available")


async def test_stream_deltas_caps_cumulative_content() -> None:
    async def chunks() -> AsyncIterator[str]:
        yield "Hello"
        yield " world"

    deltas = [delta async for delta in _stream_deltas(chunks(), 8)]

    assert deltas == [{"role": "assistant"}, {"content": "Hello"}, {"content": " wo"}]
