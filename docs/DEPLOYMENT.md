# HAOS and Hermes VM deployment

This deployment assumes HAOS is reachable as `homeassistant-1`, Hermes is
reachable as `hermes`, and the nodes carry `tag:ha` and `tag:agent` respectively.

## Hermes voice profile

Use a dedicated Hermes profile for in-room voice requests. Give it a separate
API key and only the tools that should be available to anyone who can activate a
voice satellite. Keep the existing Telegram profile separate.

Enable the gateway for the voice profile with a non-router-forwarded port. The
default Hermes API port is 8642; if a second profile needs its own process, choose
a distinct port and substitute it below.

## Tailscale policy

Merge this grant and test into the existing tailnet policy. Grants are additive,
so also audit broad rules that might already allow the port.

```jsonc
{
  "grants": [
    {
      "src": ["tag:ha"],
      "dst": ["tag:agent"],
      "ip": ["tcp:8642"]
    }
  ],
  "tests": [
    {
      "src": "tag:ha",
      "proto": "tcp",
      "accept": ["tag:agent:8642"],
      "deny": ["tag:agent:8641"]
    }
  ]
}
```

From Studio Code Server on `homeassistant-1`, verify the authenticated route:

```bash
curl -fsS \
  -H 'Authorization: Bearer [REDACTED]' \
  'http://hermes:8642/v1/capabilities'
```

The response must contain `"object":"hermes.api_server.capabilities"`,
`"platform":"hermes-agent"`, and `"features":{"chat_completions":true}`.

Use `http://hermes:8642` as the integration base URL. Do not include `/v1`.
HTTP is acceptable only because this traffic is inside the encrypted tailnet and
the port is restricted to `tag:ha`; use a trusted HTTPS reverse proxy if the
gateway is reachable through any other network.
