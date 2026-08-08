# Clean-room implementation record

Hermes Assistant was authored as a new implementation on 2026-08-08.

## Inputs used

- Home Assistant Developer Documentation for conversation entities, config
  entries, config flows, and managed HTTP sessions.
- Home Assistant Core's public conversation API declarations and examples.
- Hermes Agent's public API Server documentation for `/v1/capabilities`,
  `/v1/chat/completions`, `X-Hermes-Session-Id`, and
  `X-Hermes-Session-Key`.
- Tailscale's public grants and policy-test documentation.

## Boundary

No files, code, prompts, tests, names, documentation, commits, or Git history
were imported from an existing third-party Home Assistant-to-Hermes integration.
The project uses the distinct `hermes_assistant` Home Assistant domain and began
with a new Git repository.
