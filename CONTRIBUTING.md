# Contributing

Bug reports, documentation improvements, tests, and focused pull requests are
welcome. Use
[Q&A Discussions](https://github.com/RichiCoder1/hermes-assistant/discussions/categories/q-a)
for support and
[Ideas Discussions](https://github.com/RichiCoder1/hermes-assistant/discussions/categories/ideas)
for feature proposals. Report vulnerabilities privately as described in
[SECURITY.md](SECURITY.md).

## Before you contribute

- Search existing Discussions, issues, and pull requests before opening a new
  submission.
- Start significant features, architectural changes, new platforms, and broad
  refactors in an Ideas Discussion. Wait for maintainer alignment before
  investing in an implementation. A discussion is not a guarantee that a
  proposal will be accepted.
- Use issues for actionable, reproducible bugs. Use Discussions for support,
  ideas, design questions, and feature requests.

## AI-assisted contributions

Contributions created or augmented with AI tools are welcome. The contributor,
not the tool, is the author and is fully responsible for the submission.

If AI materially helped draft code, documentation, an issue, or a pull request,
briefly disclose how it was used. Routine completion, spelling, and grammar
assistance do not need disclosure. In every case, contributors must:

- understand and be able to explain every part of the submission;
- review, test, and validate the result before submitting it;
- verify that generated material does not introduce secrets, fabricated claims,
  incompatible code, or licensing and attribution problems; and
- respond to review feedback themselves and remain willing to maintain the
  contribution.

AI use must not shift the work of understanding, debugging, or validating a
submission onto maintainers. Raw generated output, speculative bulk changes,
fabricated test results or citations, and submissions the author cannot explain
are not acceptable.

## Keep submissions reviewable

Make the smallest coherent change that solves the stated problem. Separate
unrelated work, avoid generated churn and drive-by formatting, and explain
non-obvious decisions. Bug reports should contain enough information to
reproduce the problem. Pull requests should link related issues or Discussions,
describe user-visible effects, and include relevant validation results.

Maintainers may close submissions without detailed review when they are
low-effort, substantially generated but not author-reviewed, unreasonably broad,
difficult to understand or reproduce, or implement a major change that was not
discussed first. Submissions may also be closed when the author does not answer
reasonable follow-up questions or repeatedly ignores the contribution
guidelines. This protects limited review time; it is not a judgment about which
tools a contributor chooses to use.

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
- Link the prior Ideas Discussion for a major change.
- Add regression coverage for bug fixes and tests for new behavior.
- Update documentation and version metadata when the change affects a release.
- Preserve the boundary between Home Assistant-facing features and implementation
  details described in `docs/IMPLEMENTATION.md`.
- Never commit API keys, tokens, private hostnames, or personal conversation data.

By contributing, you agree that your contribution is licensed under the Apache
License 2.0 used by this repository.
