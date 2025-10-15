# Contributing

Thanks for contributing to Lite GitHub MCP Server!

## Getting started
- Prereqs: Python 3.13+, Docker, `git`, `gh`, `uv`, `just`, `pre-commit`.
- Setup: `uv sync --dev && pre-commit install --install-hooks`
- Useful: `just precommit`, `just run`, `just test`, `just docker-build && just compose-up`.

## Branching and PRs
- Create feature branches from `main`.
- Keep PRs small and focused; include context and links to PRD/Tech Plan sections.
- Conventional Commits required. Commitizen assists: `uv run cz bump --changelog` (release only).

## Definition of Done (for every story)
- Tests added/updated; core coverage ≥85% where applicable
- ruff format/lint clean; mypy strict passes
- Deterministic outputs; pagination/fields enforced where relevant
- Context budget respected (`scripts/context_budget_check.py`)
- Docs updated (README, milestone how-tos, or examples)
- When touching server or tooling patterns, consult FastMCP MDX docs for current APIs and guidance: https://github.com/jlowin/fastmcp/tree/main/docs

## Running tests
- Unit tests: `just test`
- Affected tests: `just test-changed`
- Integration (guarded): set `GH_TOKEN` and target a public repo; mark with `-m integration`

## Reporting issues
- Use issue templates and include: tool name, input, expected vs actual, repo/ref, logs (sanitized).

## Security
- Do not include secrets in logs or PRs. Use `GH_TOKEN` and scope minimally.

## Dogfooding
- Prefer using this MCP server itself (via CLI or agent) to create issues, PRs, reviews, and releases when possible.
