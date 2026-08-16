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

The reconfigure flow validates replacement connection details before updating
the config entry. Leaving its API-key field blank preserves the stored key. The
entry's URL-derived unique ID and title change with the validated base URL, and
Home Assistant reloads the entry only after the update succeeds.

## Service device and health

Each config entry creates one Home Assistant service device representing the
configured Hermes Agent Gateway. The conversation entity and diagnostic
connectivity binary sensor share this device, giving gateway-level capabilities
and status one place in the device registry. The service device deliberately
omits a configuration URL because the configured API endpoint is not necessarily
a browser-accessible Hermes dashboard.

After setup validation succeeds, a coordinator makes an authenticated request to
`/health/detailed` every 60 seconds while the connectivity entity is loaded. Any
valid detailed-health response, including a `degraded` readiness status, means
the API connection itself is established. Authentication, connection, or
protocol failures make the connectivity sensor report disconnected. The sensor
remains available so a failed request is represented as an actionable off state
rather than an unknown or unavailable entity.

The diagnostic readiness enum sensor exposes `ok` or `degraded` from the same
cached health response. Transport, authentication, and protocol failures make
the readiness sensor unavailable. Any future status that the integration does
not recognize is represented as `unknown`, with the original value retained in
the `gateway_status` state attribute.

## Diagnostics and System Health

Config-entry diagnostics include redacted connection data, non-secret options,
the validated capability subset, and the cached health result. The base URL and
API key are both redacted because private network addresses and tailnet hostnames
may identify a user's environment.

The System Health platform summarizes configured and connected gateways, their
hosts and models, readiness states, and the last successful health-check times.
It reads only loaded config entries and coordinator state; opening System Health
or downloading diagnostics does not make another gateway request.

## Conversation requests

Hermes Assistant converts the current Home Assistant `ChatLog` into
system/user/assistant messages and sends the complete transcript to the
stateless `/v1/chat/completions` endpoint. The model and session-header names
come from the gateway's capability response.

When the gateway does not advertise streaming, the completed response is reduced
to predictable spoken text by removing Markdown and emoji, normalizing
whitespace, and applying the configured length limit. This processing preserves
non-Latin text.

When the gateway advertises streaming, Hermes Assistant forwards text deltas to
Home Assistant as they arrive and applies the configured limit cumulatively.
Markdown and emoji are not removed mid-stream because safe cleanup requires the
complete response, such as when matching code fences. SSE comments and Hermes
tool-progress events are transport metadata and are not added to the Home
Assistant conversation.

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
