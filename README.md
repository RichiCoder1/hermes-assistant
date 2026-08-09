# Hermes for Home Assistant 🏠🪽

[![Validate](https://github.com/RichiCoder1/hermes-assistant/actions/workflows/validate.yml/badge.svg)](https://github.com/RichiCoder1/hermes-assistant/actions/workflows/validate.yml)

Hermes Assistant is a Home Assistant custom integration that makes
a Hermes Agent Gateway available as a conversation agent for Assist and Home
Assistant Voice devices.

## Features

- Adds Hermes Agent Gateway as a selectable conversation agent for Assist and
  Home Assistant Voice devices.
- Supports continued conversations and configurable Hermes memory sharing.
- Provides voice-focused prompt, timeout, and spoken-response controls.
- Handles gateway availability and credential changes through Home Assistant.

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
guidance.

## Memory sharing

Choose how broadly Hermes may reuse memory from the integration's **Configure**
screen. Conversation sharing remains the privacy-preserving default. See
[docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md#memory-scoping) for the exact
scope behavior and privacy boundaries.

## Support and contributing

Use [Q&A Discussions](https://github.com/RichiCoder1/hermes-assistant/discussions/categories/q-a)
for setup help and
[Ideas Discussions](https://github.com/RichiCoder1/hermes-assistant/discussions/categories/ideas)
for feature proposals. Reserve
[GitHub Issues](https://github.com/RichiCoder1/hermes-assistant/issues) for
reproducible bugs. Contributions are welcome; see
[CONTRIBUTING.md](CONTRIBUTING.md). Report vulnerabilities privately according to
[SECURITY.md](SECURITY.md).

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
