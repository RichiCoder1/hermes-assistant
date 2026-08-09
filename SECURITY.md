# Security policy

## Supported versions

Only the latest published Hermes Assistant release receives security fixes.
Update through HACS and restart Home Assistant before reporting an issue that may
already be resolved.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's
[private vulnerability reporting](https://github.com/RichiCoder1/hermes-assistant/security/advisories/new)
to share the affected version, impact, reproduction steps, and a minimal redacted
log or proof of concept.

Remove API keys, Home Assistant tokens, private hostnames, and personal
conversation content. You should receive an acknowledgement through the private
advisory within seven days. Please allow time for investigation and a coordinated
fix before public disclosure.

## Security boundary

Hermes Assistant authenticates to a Hermes Agent Gateway that may have access to
powerful tools. Use a dedicated Hermes voice profile, restrict network access,
and enable only tools appropriate for everyone who can activate the connected
voice devices. See [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md#security-boundary).
