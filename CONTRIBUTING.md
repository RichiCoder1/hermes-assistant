# Contributing

Bug reports, documentation improvements, tests, and focused pull requests are
welcome. Use
[Q&A Discussions](https://github.com/RichiCoder1/hermes-assistant/discussions/categories/q-a)
for support and
[Ideas Discussions](https://github.com/RichiCoder1/hermes-assistant/discussions/categories/ideas)
for feature proposals. Report vulnerabilities privately as described in
[SECURITY.md](SECURITY.md).

## Development setup

Hermes Assistant uses Python 3.14, uv for dependency management, Ruff for
formatting and linting, ty for type checking, and pytest for tests.

```powershell
uv sync --locked
uv pip install homeassistant==2026.7.3
uv run ruff check custom_components tests
uv run ruff format --check custom_components tests
uv run ty check custom_components/hermes_assistant
uv run pytest -q
uv run python -m compileall -q custom_components tests
```

## Pull requests

- Keep changes focused and explain the user-visible behavior.
- Add regression coverage for bug fixes and tests for new behavior.
- Update documentation and version metadata when the change affects a release.
- Preserve the boundary between Home Assistant-facing features and implementation
  details described in `docs/IMPLEMENTATION.md`.
- Never commit API keys, tokens, private hostnames, or personal conversation data.

By contributing, you agree that your contribution is licensed under the Apache
License 2.0 used by this repository.
