# Implementation

This document describes how Hermes Assistant maps Home Assistant's conversation
model onto the Hermes Agent Gateway API. The public README focuses on the
capabilities added to Home Assistant.

## Integration lifecycle

The config flow collects a complete gateway base URL and API key. Before saving
the entry, Hermes Assistant authenticates to `/v1/capabilities` and verifies the
Hermes platform identity, bearer-auth requirement, model, and chat-completions
support.

Home Assistant owns the HTTP session and reloads the integration after options
change. Authentication failures start Home Assistant's reauthentication flow;
temporary gateway failures mark the conversation entity unavailable.

## Conversation requests

Hermes Assistant converts the current Home Assistant `ChatLog` into
system/user/assistant messages and sends the complete transcript to the
stateless `/v1/chat/completions` endpoint. The model and session-header names
come from the gateway's capability response.

The response is reduced to predictable spoken text by removing Markdown and
emoji, normalizing whitespace, and applying the configured length limit. This
processing preserves non-Latin text.

## Memory scoping

Hermes distinguishes short-lived transcript continuity from long-term memory:

- `X-Hermes-Session-Id` always follows the Home Assistant conversation.
- `X-Hermes-Session-Key` follows the memory-sharing option selected in Home
  Assistant.

| Selection | Session-key source | Behavior |
| --- | --- | --- |
| `conversation` | Conversation ID | Memory is isolated to one HA conversation. |
| `device` | Voice device ID | Memory is shared across conversations on one device. If no device is available, it falls back to the conversation. |
| `user` | Authenticated HA user ID | Memory is shared for one user across devices. If no user is available, it falls back to the conversation. |
| `assistant` | Integration entry | Memory is shared across every user and device using that configured Hermes Assistant entry. |

Conversation is the default because voice devices are often shared. Assistant
scope is the broadest option and should be enabled only when all users of the
connected voice devices may share the same Hermes memory context.

All sources are namespaced by the Home Assistant config-entry ID and hashed with
SHA-256 before transmission. Hermes receives a bounded opaque value rather than
the raw entry, conversation, device, or user identifier. Removing and recreating
the integration creates a new memory namespace.

Hermes Assistant supplies the scope identifier; the configured Hermes memory
provider remains responsible for storing, retrieving, and expiring memories.

## Security boundary

Hermes Assistant calls the gateway with its bearer API key and does not expose
arbitrary Hermes tools as Home Assistant services. Use a dedicated Hermes voice
profile whose enabled tools are appropriate for anyone able to activate the
voice devices.

The integration provides the conversation-agent platform only. Speech-to-text,
text-to-speech, wake-word detection, and notification delivery remain separate
Home Assistant pipeline or integration responsibilities.
