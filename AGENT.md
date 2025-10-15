## AGENT HANDBOOK

Purpose: Keep all agents (humans and LLMs) aligned on patterns, guardrails, and where to look up details quickly. Reduce drift, avoid duplicative patterns, and speed up contributions.

### Golden Rules
- Follow the PRD and Technical Plan. If in doubt, prefer minimal, deterministic JSON and CLI-first approaches.
- Target Python 3.13+. Keep `uvloop` optional on Linux.
- Prefer mono-tool router with tiny descriptions; move rich docs behind `gh.help`.
- Always paginate and support field selection; return IDs/handles first, expand on demand.
- Never emit markdown from server responses; JSON only. Deterministic order.

### Quick References
- Product Requirements: `docs/project-docs/PRODUCT_REQUIREMENTS_DOCUMENT.md`
- Technical Plan: `docs/project-docs/TECHNICAL_PLAN_OVERVIEW.md`
- Milestones/Epics/Stories: `docs/project-docs/PROJECT_PLAN_MILESTONES_EPICS_AND_STORIES.md`
- ADRs: `docs/adr/`
- FastMCP Docs (latest, MDX source): https://github.com/jlowin/fastmcp/tree/main/docs
  - Server API and patterns: https://github.com/jlowin/fastmcp/tree/main/docs/server
  - Tools API: https://github.com/jlowin/fastmcp/tree/main/docs/tools
  - Client usage: https://github.com/jlowin/fastmcp/tree/main/docs/client
  - Deployment and configuration: https://github.com/jlowin/fastmcp/tree/main/docs/deployment

### Canonical JSON Shapes
- Error:
```json
{"code":"RATE_LIMIT","message":"secondary rate limit","details":{},"retry_after":2.5}
```
- List:
```json
{"repo":"owner/name","filters":{},"ids":[1,2,3],"count":3,"next_page":"opaque"}
```
- Pagination token payload (base64 of this object):
```json
{"cursor":"opaque","filters":{"state":"open"},"version":"v1"}
```

### Developer Workflow
- Install tools via uv: `uv sync --dev`
- Common tasks: `just fmt`, `just lint`, `just typecheck`, `just test`, `just precommit`
- Run server: `just run` (stdio FastMCP)
- Docker dev: `just docker-build` and `just compose-up`
- CI locally: `just ci`

### Tooling Conventions
- Lint/format: `ruff` (format + lint), no `black`.
- Types: `mypy` strict; Python 3.13 features allowed; avoid `Any`.
- Tests: `pytest` + `xdist` + `testmon` for affected tests; coverage ≥85% core modules.
- Commits: Conventional Commits. Use Commitizen for versioning and CHANGELOG.
- Pre-commit hooks must pass before merging.

### Server Design Tenets
- CLI-first: use `git` for repo/file/commit operations; `gh` for PR/issue metadata/actions.
- Micro-queries: tiny selection sets with `gh api graphql`; conditional requests with ETag.
- Caching: TTLs per category (lists 30s, meta 5m, blobs 1h); invalidate on writes.
- Errors: machine-readable envelopes with codes and `retry_after` hints.

### Response Discipline (Do/Don't)
- Do: return `{ids: [...], next_page}` for list endpoints.
- Do: stable sort, explicit fields, small payloads.
- Don't: echo inputs unless necessary.
- Don't: send markdown or long prose.

### Context Budget Guardrail
- Registry JSON size budget ≤ 8KB by default. CI enforces via `scripts/context_budget_check.py`.

### Security Hygiene
- Read tokens from env/`gh auth status`. Never log secrets. Validate scopes; return `missing_scopes`.

### Patterns To Avoid
- Duplicating REST calls when CLI provides the same; avoid heavy JSON when IDs suffice.
- Multiple patterns for same task; use the router + services modules defined in the plan.
- Non-deterministic outputs (unordered sets, time-variant formatting without timestamps/ids).

### Directory and Module Canon
- `src/lite_github_mcp/server.py`: FastMCP init + tool registration
- `src/lite_github_mcp/services/`: `git_cli.py`, `gh_cli.py`, `cache.py`, `pager.py`
- `src/lite_github_mcp/tools/`: mono-tool router (and grouped tools if needed)
- `src/lite_github_mcp/schemas/`: Pydantic v2 models
- `src/lite_github_mcp/utils/subprocess.py`: safe subprocess runner

### Documentation for Users (Exit Criteria Addendum)
For each milestone, ensure docs/examples for:
- Cursor IDE
- Claude Code
- Cursor Agent
- OpenWebUI
- Project CLI (for users without the above)
See milestone exit criteria in: `docs/project-docs/PROJECT_PLAN_MILESTONES_EPICS_AND_STORIES.md`.

### Dogfooding Mandate
- Use this MCP server (or the project CLI) to:
  - open PRs, request reviews, post comments
  - create and triage GitHub issues
  - participate in Discussions for feedback
  - perform merges and release notes where feasible
Record learnings as issues/ADRs.

### Decision Log
- Record deviations in PR descriptions and update the Technical Plan if adopted.

### Contribution Checklist (per PR)
- [ ] Conventional Commit message
- [ ] ruff format + lint clean
- [ ] mypy strict passes
- [ ] tests pass, coverage unchanged or improved
- [ ] registry size budget respected
- [ ] docs updated (README + milestone how-tos if applicable)

### Useful Commands
```bash
# Setup dev
uv sync --dev && pre-commit install --install-hooks

# Run all quality gates
just precommit

# Run server locally
just run

# Build and run via Docker
just docker-build && just compose-up

# CLI smoke tests (paging, cursors, ranges)
just cli_tools
just cli_call gh.file.tree '{"repo_path": ".", "ref": "HEAD", "limit": 3}'
just cli_call gh.search.files '{"repo_path": ".", "pattern": "FastMCP", "limit": 2}'
just cli_call gh.search.files '{"repo_path": ".", "pattern": "TODO", "paths": ["src/", "docs/"]}'
just cli_call gh.file.blob '{"repo_path": ".", "blob_sha": "<sha>", "max_bytes": 128, "offset": 0}'
just cli_call gh.pr.list '{"repo": "gsornsen/home-k8s", "state": "open", "limit": 10}'
just cli_call gh.pr.get '{"repo": "gsornsen/home-k8s", "number": 3}'
just cli_call gh.pr.timeline '{"repo": "gsornsen/home-k8s", "number": 3, "limit": 5}'
```

### Future-Proofing
- Keep mono-tool router default; multi-tool as opt-in for specific agents.
- Evaluate GitHub App auth in a later milestone; keep PAT scope requirements minimal.
- Favor explicit version pins for dev tools in `pyproject.toml` when stability matters.
