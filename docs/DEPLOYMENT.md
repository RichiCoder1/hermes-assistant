# HAOS and Hermes VM deployment

This deployment assumes Home Assistant OS and Hermes are separate tailnet
devices. Substitute your own hostnames, tags, and port where appropriate.

## Hermes voice profile

Use a dedicated Hermes profile for in-room voice requests. Give it a separate
API key and only the tools that should be available to anyone who can activate a
voice satellite. Keep the existing Telegram profile separate.

Enable the gateway for the voice profile with a non-router-forwarded port. The
default Hermes API port is 8642; if a second profile needs its own process, choose
a distinct port and substitute it below.

## Tailscale policy

Allow the Home Assistant device or tag to reach the Hermes device or tag on the
gateway port. Tailnet grants are additive, so also audit broader rules that may
already allow the port. The names below are examples; replace them with the tags
used by your tailnet.

```jsonc
{
  "grants": [
    {
      "src": ["tag:home-assistant"],
      "dst": ["tag:hermes"],
      "ip": ["tcp:8642"]
    }
  ],
  "tests": [
    {
      "src": "tag:home-assistant",
      "proto": "tcp",
      "accept": ["tag:hermes:8642"],
      "deny": ["tag:hermes:8641"]
    }
  ]
}
```

### Home Assistant OS Tailscale add-on

If HAOS joins the tailnet through the
[Tailscale add-on](https://github.com/hassio-addons/app-tailscale), set:

```yaml
userspace_networking: false
```

Userspace networking is sufficient for inbound access from the tailnet to Home
Assistant, but it does not give Home Assistant outbound access to other tailnet
clients. Disabling it creates a host `tailscale0` interface so Home Assistant
Core can reach the Hermes gateway.

To resolve tailnet device names from Home Assistant, configure HAOS to query
Tailscale's DNS resolver:

```bash
ha dns options --servers dns://100.100.100.100
```

Use the device's fully qualified MagicDNS name, such as
`hermes.example-tailnet.ts.net`, rather than the short name `hermes`. The
Tailscale IP is also useful for diagnosing whether a failure is routing or DNS,
but the fully qualified name is preferable for the saved integration
configuration.

From a terminal on the Home Assistant host, verify the authenticated route:

```bash
curl -fsS \
  -H 'Authorization: Bearer [REDACTED]' \
  'http://hermes.example-tailnet.ts.net:8642/v1/capabilities'
```

The response must contain `"object":"hermes.api_server.capabilities"`,
`"platform":"hermes-agent"`, and `"features":{"chat_completions":true}`.

Use `http://hermes.example-tailnet.ts.net:8642` as the integration base URL. Do
not include `/v1`.
HTTP is acceptable only because this traffic is inside the encrypted tailnet and
the port is restricted by tailnet policy; use a trusted HTTPS reverse proxy if
the gateway is reachable through any other network.
