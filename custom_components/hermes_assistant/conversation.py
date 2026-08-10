"""Home Assistant conversation entity backed by Hermes Agent."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Literal, override

from homeassistant.components import conversation
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HermesAssistantConfigEntry
from .const import (
    CONF_MAX_RESPONSE_CHARS,
    CONF_MEMORY_SCOPE,
    CONF_PROMPT,
    DEFAULT_MAX_RESPONSE_CHARS,
    DEFAULT_MEMORY_SCOPE,
    DEFAULT_NAME,
    DEFAULT_PROMPT,
    DOMAIN,
)
from .device import gateway_device_info
from .gateway import HermesAuthenticationError, HermesGatewayClient, HermesGatewayError
from .transcript import (
    memory_session_key,
    messages_from_chat_log,
    session_id_value,
    spoken_text,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HermesAssistantConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the conversation entity."""
    async_add_entities([HermesConversationEntity(entry)])


class HermesConversationEntity(
    conversation.ConversationEntity, conversation.AbstractConversationAgent
):
    """A Home Assistant conversation agent that delegates to Hermes."""

    _attr_has_entity_name = True
    _attr_name = DEFAULT_NAME
    _attr_supports_streaming = True

    def __init__(self, entry: HermesAssistantConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = gateway_device_info(entry)

    @property
    @override
    def supported_languages(self) -> list[str] | Literal["*"]:
        return MATCH_ALL

    @override
    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self._entry, self)

    @override
    async def async_will_remove_from_hass(self) -> None:
        conversation.async_unset_agent(self.hass, self._entry)
        await super().async_will_remove_from_hass()

    @override
    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Send the current Home Assistant chat log to Hermes."""
        options = self._entry.options
        prompt = options.get(CONF_PROMPT, DEFAULT_PROMPT)
        try:
            await chat_log.async_provide_llm_data(
                user_input.as_llm_context(DOMAIN),
                None,
                prompt,
                user_input.extra_system_prompt,
            )
        except conversation.ConverseError as err:
            return err.as_conversation_result()

        conversation_id = chat_log.conversation_id
        context = user_input.context
        session_id = session_id_value(self._entry.entry_id, conversation_id)
        session_key = memory_session_key(
            self._entry.entry_id,
            conversation_id,
            options.get(CONF_MEMORY_SCOPE, DEFAULT_MEMORY_SCOPE),
            device_id=user_input.device_id,
            user_id=context.user_id if context else None,
        )

        client = self._entry.runtime_data.client
        messages = messages_from_chat_log(chat_log.content)
        max_chars = options.get(CONF_MAX_RESPONSE_CHARS, DEFAULT_MAX_RESPONSE_CHARS)

        try:
            capabilities = client.capabilities or await client.async_validate()
            if capabilities.supports_streaming:
                await self._async_stream_response(
                    chat_log,
                    user_input,
                    client,
                    messages,
                    session_id=session_id,
                    session_key=session_key,
                    max_chars=max_chars,
                )
            else:
                await self._async_complete_response(
                    chat_log,
                    user_input,
                    client,
                    messages,
                    session_id=session_id,
                    session_key=session_key,
                    max_chars=max_chars,
                )
        except HermesAuthenticationError:
            self._attr_available = False
            self.async_write_ha_state()
            self._entry.async_start_reauth(self.hass)
            return _error_result(
                user_input, conversation_id, "Hermes authentication failed."
            )
        except HermesGatewayError as err:
            self._attr_available = False
            self.async_write_ha_state()
            _LOGGER.warning("Hermes conversation request failed: %s", err)
            return _error_result(
                user_input, conversation_id, "Hermes is unavailable right now."
            )

        if not self.available:
            self._attr_available = True
            self.async_write_ha_state()
        return conversation.async_get_result_from_chat_log(user_input, chat_log)

    async def _async_complete_response(
        self,
        chat_log: conversation.ChatLog,
        user_input: conversation.ConversationInput,
        client: HermesGatewayClient,
        messages: list[dict[str, str]],
        *,
        session_id: str,
        session_key: str,
        max_chars: int,
    ) -> None:
        """Fetch one full Hermes response and add it to the chat log.

        Used when the gateway does not advertise streaming support.
        """
        answer = await client.async_complete(
            messages, session_id=session_id, session_key=session_key
        )
        answer = spoken_text(answer, max_chars)
        if not answer:
            raise HermesGatewayError("Hermes returned no speakable text")
        chat_log.async_add_assistant_content_without_tools(
            conversation.AssistantContent(agent_id=user_input.agent_id, content=answer)
        )

    async def _async_stream_response(
        self,
        chat_log: conversation.ChatLog,
        user_input: conversation.ConversationInput,
        client: HermesGatewayClient,
        messages: list[dict[str, str]],
        *,
        session_id: str,
        session_key: str,
        max_chars: int,
    ) -> None:
        """Stream a Hermes response into the chat log as deltas arrive."""
        chunks = client.async_stream_complete(
            messages, session_id=session_id, session_key=session_key
        )
        spoke = False
        async for content in chat_log.async_add_delta_content_stream(
            user_input.agent_id, _stream_deltas(chunks, max_chars)
        ):
            if (
                isinstance(content, conversation.AssistantContent)
                and content.content
                and content.content.strip()
            ):
                spoke = True
        if not spoke:
            raise HermesGatewayError("Hermes returned no speakable text")


async def _stream_deltas(
    chunks: AsyncIterator[str], max_chars: int
) -> AsyncIterator[conversation.AssistantContentDeltaDict]:
    """Turn raw Hermes text chunks into Home Assistant assistant deltas.

    Caps total emitted text at `max_chars`, matching the non-streaming
    path's response length limit. Unlike `spoken_text`, this does not
    clean up markdown or emoji mid-stream: doing that safely requires
    seeing the whole response (e.g. matched code fences), which streaming
    does not provide.
    """
    yield {"role": "assistant"}
    emitted = 0
    async for chunk in chunks:
        if emitted >= max_chars:
            break
        remaining = max_chars - emitted
        if len(chunk) > remaining:
            chunk = chunk[:remaining]
        emitted += len(chunk)
        yield {"content": chunk}


def _error_result(
    user_input: conversation.ConversationInput,
    conversation_id: str,
    message: str,
) -> conversation.ConversationResult:
    response = intent.IntentResponse(language=user_input.language)
    response.async_set_error(intent.IntentResponseErrorCode.UNKNOWN, message)
    return conversation.ConversationResult(
        response=response,
        conversation_id=conversation_id,
        continue_conversation=False,
    )
