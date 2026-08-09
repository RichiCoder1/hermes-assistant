# Hermes Assistant

Hermes Assistant is an independent Home Assistant custom integration that makes
a Hermes Agent Gateway available as a conversation agent for Assist and Home
Assistant Voice devices.

## Features

- Configures a complete Hermes base URL and required bearer API key in the UI.
- Verifies `/v1/capabilities` before accepting the configuration.
- Sends Home Assistant's current chat transcript to the stateless
  `/v1/chat/completions` endpoint.
- Separates transcript continuity from Hermes long-term memory scoping.
- Offers conversation, device, user, or assistant memory scope; conversation
  scope is the privacy-preserving default for shared voice hardware.
- Produces concise TTS text while preserving non-Latin languages.
- Supports reauthentication and configurable prompt, timeout, and spoken length.

## Requirements

- Home Assistant 2025.12.0 or newer.
- A current Hermes Agent Gateway with an `API_SERVER_KEY`.
- Network access from Home Assistant to the Hermes gateway.

## Install with HACS

1. In HACS, open **Integrations** and then **Custom repositories**.
2. Add `https://github.com/RichiCoder1/hermes-assistant` as an **Integration**.
3. Install **Hermes Assistant** and restart Home Assistant.
4. Go to **Settings -> Devices & services -> Add integration** and select
   **Hermes Assistant**.
5. Enter the gateway base URL (for example,
   `http://hermes.example-tailnet.ts.net:8642`) and API key.
6. Edit the Assist pipeline assigned to the voice device and choose
   **Hermes Assistant** as its conversation agent.

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for Tailscale and HAOS networking
guidance and [docs/LIVE_TEST.md](docs/LIVE_TEST.md) for the rollout checklist.

## Memory scopes

Hermes Assistant sends an opaque, conversation-specific
`X-Hermes-Session-Id` for transcript continuity and an independent
`X-Hermes-Session-Key` for long-term memory:

- `conversation` resets long-term memory with each Home Assistant conversation.
- `device` shares memory across conversations on one voice device.
- `user` shares memory for one authenticated Home Assistant user across devices.
  If no user is available, it safely falls back to conversation scope.
- `assistant` shares memory across every device and user connected through that
  Hermes Assistant integration entry.

Session values are hashed before transmission so Home Assistant's raw entry,
conversation, device, and user identifiers are not disclosed to Hermes.

## Development

```powershell
uv sync --locked
uv pip install homeassistant==2026.7.3
uv run pytest -q
uv run ruff check custom_components tests
uv run ty check custom_components/hermes_assistant
```

## License

Apache License 2.0. See [LICENSE](LICENSE).
