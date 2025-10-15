## Project Plan: Milestones, Epics, and Stories

### Document
- Product: Lite GitHub MCP Server (context-minimized, CLI-first)
- Doc owner: Gerald Sornsen
- Last updated: 2025-10-15
- Docs basis: PRODUCT_REQUIREMENTS_DOCUMENT.md, TECHNICAL_PLAN_OVERVIEW.md

### Principles
- Minimal, deterministic JSON; tiny tool registry
- CLI-first (`git`, `gh`) with REST/GraphQL micro-queries as fallback
- Python 3.13+, FastMCP 2.0, Pydantic v2; `uvloop` optional (Linux)
- Pagination, field selection, ids-first, expand-on-demand
- CI: ruff, mypy, pytest, budgets; Docker image and Compose for demo

---

## Milestone 1: Scaffolding and Health (Week 1)
Goal: Repo bootstrapped, runnable server, basic health/auth, tiny registry

### Epics
- E1.1 Tooling and repo scaffolding
- E1.2 Minimal FastMCP server and router
- E1.3 Auth discovery and config
- E1.4 CI + containerization

### Stories
- S1.1 Create project scaffolding
  - Create `pyproject.toml` (Python 3.13+, tools), `.editorconfig`, `.gitignore`, `README.md`, MIT `LICENSE`.
  - Add `Justfile`; `scripts/ensure_gh.sh`.
  - Pre-commit with ruff, mypy, testmon.
- S1.2 Set up CI
  - Add `.github/workflows/ci.yml` (setup-python@3.13, uv sync, lint/type/test, budget checks).
  - Add `.github/workflows/release.yml` (cz-based tagging/changelog).
- S1.3 Docker + Compose
  - `docker/Dockerfile` (uv 3.13 base; install git, gh) and `docker-compose.yml` (no version key).
- S1.4 Minimal server
  - `server.py` with mono-tool router; register `gh.ping`, `gh.whoami`, `gh.configure` (short descriptions).
- S1.5 Config
  - `config.py` with `page_size`, host, timeouts, mono/multi mode; env parsing.

### Exit Criteria
- Working tests cover: config parsing, `gh.ping`/`gh.whoami` stubs, router registration, CLI budget script
- `uv sync --dev` succeeds; `just run` starts server; `just ci` green locally
- Docker image builds; `docker compose up` starts; README quickstart validated by a new user
- Registry JSON ≤ 8KB (checked by script) and deterministic responses
- Documentation/examples show usage via: Cursor IDE, Claude Code, Cursor Agent, OpenWebUI, and project CLI
- Dogfooding: use the project CLI or server to open the Milestone 1 PR and log any setup issues as GitHub issues

---

## Milestone 2: Repo + File Surface (Week 2)
Goal: Git-first repo introspection, file listings, safe blobs, searches

### Epics
- E2.1 Git wrapper (repo lifecycle and queries)
- E2.2 File tree and blob endpoints
- E2.3 Search tooling (grep/rg)
- E2.4 Pager + schemas

### Stories
- S2.1 `services/git_cli.py`
  - ensure_repo (shallow/partial clone), resolve_repo, ls_tree, show_blob, diff
- S2.2 `services/pager.py` and schemas
  - Opaque token model, deterministic ordering helpers; Pydantic models
- S2.3 File tools
  - `gh.file.tree` (paths+blob sha), `gh.file.blob` (max_bytes, offset, length)
- S2.4 Search tool
  - `gh.search.files` using git grep first; support path filters, excerpts
- S2.5 Repo tools (basics)
  - `gh.repo.resolve`, `gh.repo.branches.list`, `gh.repo.refs.get` (git-first; gh fallback)

### Exit Criteria
- Unit tests: pager token encode/decode, deterministic ordering; git wrapper behaviors (mocked)
- Integration tests: against a known public repo (guarded); safe blob slicing limits
- Performance: p50 < 500ms cached listing; p95 < 2s uncached on typical repo
- Docs updated; new user can use repo+file endpoints end-to-end
- Documentation/examples show usage via: Cursor IDE, Claude Code, Cursor Agent, OpenWebUI, and project CLI
- Dogfooding: use file and search tools to prepare and commit example updates via the server/CLI

---

## Milestone 3: PR Basics (Week 3)
Goal: Minimal PR triage endpoints with ids-first and expand-on-demand strategy

### Epics
- E3.1 gh CLI wrapper (REST/GraphQL micro-queries, ETag)
- E3.2 PR listing/get/timeline
- E3.3 Cache layer (ETag/TTL)

### Stories
- S3.1 `services/gh_cli.py`
  - status, exec_json, api_rest, api_graphql, field selection builder, ETag headers
- S3.2 Cache
  - `services/cache.py`: diskcache/sqlite; per-category TTLs; conditional request metadata store
- S3.3 PR tools (minimal)
  - `gh.pr.list` (IDs only), `gh.pr.get` (meta fields), `gh.pr.timeline` (event type, ids, actor, createdAt)

### Exit Criteria
- Unit tests: gh wrapper request building, ETag caching, cache invalidation
- Integration tests: PR listing and timeline on a public repo (guarded)
- Deterministic outputs: stable sorting, field selection honored; pagination enforced
- New user flow: triage PRs by IDs, expand selected PRs via a follow-up call
- Documentation/examples show usage via: Cursor IDE, Claude Code, Cursor Agent, OpenWebUI, and project CLI
- Dogfooding: raise the PR for Milestone 3 changes using this server; review via `gh.pr.*` tools

---

## Milestone 4: PR Actions and Issues (Week 4)
Goal: PR actions and basic issue tools with micro-patterns

### Epics
- E4.1 PR expansions and actions
- E4.2 Issue list/get/comment
- E4.3 Error envelopes and backoff

### Stories
- S4.1 PR expansions
  - `gh.pr.files` (summary), `gh.pr.expand` (selectable heavy fields)
- S4.2 PR actions
  - `gh.pr.comment`, `gh.pr.review` (approve/request_changes/comment), `gh.pr.merge`
- S4.3 Issues
  - `issue.list`, `issue.get`, `issue.comment` with ids-first pattern
- S4.4 Error model
  - Machine-readable error envelopes; backoff on 403/secondary limits; retry_after hints

### Exit Criteria
- Unit tests: error model envelopes; action parameter validation
- Integration tests: comment/review on a test PR (guarded), issue list/get/comment
- Docs: examples for PR actions; security notes on scopes; deterministic outputs
- New user validates end-to-end PR review flow with clear errors on missing scopes
- Documentation/examples show usage via: Cursor IDE, Claude Code, Cursor Agent, OpenWebUI, and project CLI
- Dogfooding: use the server to comment/review/merge the milestone PR; log feedback as GitHub issues via the server

---

## Milestone 5: Hardening and Telemetry (Week 5)
Goal: Reliability, budgets, and visibility

### Epics
- E5.1 Context budget measurement
- E5.2 Logging/metrics toggle
- E5.3 Release automation

### Stories
- S5.1 Budget checks
  - `scripts/context_budget_check.py` hooked in CI, asserting registry ≤ 8KB and sample responses within thresholds
- S5.2 Observability
  - Structured logs; basic counters/timers; opt-in metrics
- S5.3 Release
  - Commitizen-based version bump, CHANGELOG, GitHub Release on main; container publish (optional)

### Exit Criteria
- CI green with budget gates; coverage thresholds met (≥85% core); flaky tests eliminated
- Logs/metrics demonstrably toggleable; no secrets in logs; deterministic formatting
- New user can install, run, and provide feedback through documented flows and issues
- Documentation/examples show usage via: Cursor IDE, Claude Code, Cursor Agent, OpenWebUI, and project CLI
- Dogfooding: use the server/CLI to publish the release notes and create the GitHub Release

---

## Cross-cutting Quality Gates
- Tests: unit + integration; ≥85% coverage for core logic, meaningful assertions
- Determinism: stable sort, explicit fields, ids-first; no markdown in responses
- Performance: p50 < 500ms cached, p95 < 2s uncached typical flows
- Security: no secret logging; scope validation; actionable errors
- Docs: quickstart, examples per tool, PRD/Tech Plan kept in sync

## Backlog (Post-M5)
- Multi-tool mode with grouped tools (`repo.*`, `pr.*`, `issue.*`, `file.*`)
- GitHub App auth (JWT) and installation flow
- Local caching adapters (SQLite/duckdb) for larger data windows
- Advanced search and code intelligence helpers (LSP hooks, symbol xref)
