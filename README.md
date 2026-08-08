# Hermes Assistant

Hermes Assistant is an independent Home Assistant custom integration that makes
a Hermes Agent Gateway available as a conversation agent for Assist and Home
Assistant Voice devices.

## Features

- Configures a complete Hermes base URL and required bearer API key in the UI.
- Verifies `/v1/capabilities` before accepting the configuration.
- Sends Home Assistant's current chat transcript to the stateless
  `/v1/chat/completions` endpoint.
- Uses Hermes-advertised session headers when available.
- Offers conversation, device, or user memory scope; conversation scope is the
  privacy-preserving default for shared voice hardware.
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
5. Enter the gateway base URL (for example, `http://hermes:8642`) and API key.
6. Edit the Assist pipeline assigned to the voice device and choose
   **Hermes Assistant** as its conversation agent.

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the recommended Tailscale policy
and [docs/LIVE_TEST.md](docs/LIVE_TEST.md) for the rollout checklist.

## Development

```powershell
uv sync --locked
uv run pytest -q
uv run ruff check custom_components tests
uv run ty check custom_components/hermes_assistant
```

## License

Apache License 2.0. See [LICENSE](LICENSE).
