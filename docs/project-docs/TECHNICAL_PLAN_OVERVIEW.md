## Technical Plan Overview

### Document
- **Product**: Lite GitHub MCP Server (context-minimized, CLI-first)
- **Doc owner**: Gerald Sornsen
- **Last updated**: 2025-10-15
- **Repo status**: Empty repo detected. We will scaffold from scratch.

### Executive Summary
This document is the complete plan to build and maintain `lite-github-mcp-server`, now updated per feedback to target Python ≥ 3.13, keep `uvloop` optional on Linux, and remove the `version:` key from `docker-compose.yml`. It covers goals, constraints, architecture, detailed module plan, tooling, CI/CD, Docker, testing, documentation, milestones, risks, and concrete configs/files.

### Goals and Constraints
- **Minimize LLM context usage**: tiny tool list/descriptions, small responses, lazy expansion, pagination by default, no verbose text.
- **CLI-first**: Prefer local `git` and `gh` CLI. Use REST/GraphQL only if `gh` lacks the feature. Wrap `gh api` for micro-queries.
- **Micro-endpoints**: Explicit fields and paging; favor many small calls over large payloads; strong caching; idempotency.
- **Primary stack**: Python 3.13+, FastMCP 2.0 (`jlowin/fastmcp`), Pydantic v2 for schemas, subprocess for CLI.
- **Agent compatibility**: Must work with IDE agents (Cursor, Claude Code, etc.) that may pre-load server context; avoid heavy metadata.

### Synthesis of Known Pain Points (community, up to 2024-10)
- Context bloat: servers register 50+ tools with long descriptions/examples wasting tokens at session start.
- Over-fetching: endpoints return full objects (files, PR bodies, timelines) when only IDs are needed.
- Missing pagination/field selection; naive list endpoints returning hundreds of entries.
- Chatty/narrative responses; markdown-heavy outputs.
- Weak caching; repeated identical calls blow rate limits.
- Not leveraging `git`/`gh` locally; everything via REST with heavy JSON.
- Unclear auth handling and scopes; failing on private repos.
- Large file content injection; no blob handles or partial reads.
- Non-deterministic outputs (unordered, time-dependent), hard for agents to diff.

### Key Design Takeaways
- Register minimal tool surface by default; optionally expose subtools via a single router tool.
- All list endpoints default small `page_size` (e.g., 20), include `next_page` token; strict field selection.
- Return handles/IDs; add explicit `expand_*` tools to fetch heavy fields on demand.
- Use `git` for repo/file/commit operations; `gh` for PR/issue metadata and actions; `gh api graphql` with tight selection sets when needed.
- Aggressive client-side caching (ETag/Last-Modified for REST, output-key caching for CLI calls) with TTL and invalidation on write.
- Deterministic ordering and stable identifiers in all outputs.

## Architecture
- **Process**: Python FastMCP server (stdio). Minimal memory footprint.
- **Modules**
  - `src/lite_github_mcp/server.py`: FastMCP app initialization and tool registration.
  - `src/lite_github_mcp/config.py`: settings (GH host, page_size defaults, timeouts, feature flags, mono-tool mode).
  - `src/lite_github_mcp/services/git_cli.py`: git wrapper (shallow clone, sparse checkout, ls-tree, show, blame, diff).
  - `src/lite_github_mcp/services/gh_cli.py`: gh wrapper (status, api calls, REST/GraphQL micro queries, --paginate control).
  - `src/lite_github_mcp/services/cache.py`: disk-backed cache (sqlite or diskcache), ETag store, content-addressable blobs.
  - `src/lite_github_mcp/services/pager.py`: page tokens, deterministic ordering helpers.
  - `src/lite_github_mcp/tools/*.py`: independent tool groups or a single router tool.
  - `src/lite_github_mcp/schemas/*.py`: Pydantic models for requests/responses.
  - `src/lite_github_mcp/utils/subprocess.py`: safe subprocess runner with timeouts, JSON parsing, redaction, retries.
- **Data flow**: Tools call service wrappers; outputs compressed/minified JSON; no markdown.
- **Caching strategy**: `key = (command|args|env|version|auth_user)` → value; TTL defaults (lists 30s, meta 5m, blobs 1h). ETag for REST via `gh api` with conditionals. Invalidate on mutating calls.

### Tooling Strategy to Reduce Context
- Two modes:
  1) Mono-tool router: tool name `gh` with subcommand enum; keeps tool list tiny for agents that load everything.
  2) Multi-tool: grouped tools (`repo.*`, `pr.*`, `issue.*`, `file.*`) for agents that prefer explicit tools.
- Minimal descriptions (<120 chars). Rich docs moved to a `help` subcommand returned on demand.
- Default small `page_size` and field selection; `fields` param to opt-in expansions.
- All tools support `dry_run` to preview.

### Planned MCP Tool Surface (mono-tool router; multi-tool maps in parentheses)
- `gh.ping` (core.ping): health check, returns {ok, version}
- `gh.whoami` (auth.whoami): gh auth status, user handle, scopes
- `gh.configure` (core.configure): set defaults (page_size, host, mono vs multi)
- `gh.repo.resolve` (repo.resolve): map repo_path|url → owner/name, default branch, HEAD sha
- `gh.repo.branches.list` (repo.branches.list): prefix filter, returns names only
- `gh.repo.refs.get` (repo.refs.get): resolve ref → sha
- `gh.file.tree` (file.tree): list files under path at ref; return paths+blob sha, no content
- `gh.file.blob` (file.blob): get file content by blob sha (with max_bytes, offset, length)
- `gh.search.files` (file.search): git grep or ripgrep via CLI; matches (path, line, col, excerpt)
- `gh.pr.list` (pr.list): return PR numbers only by filters (state, author, label), paged
- `gh.pr.get` (pr.get): meta only unless fields requested (title, head|base, small body_excerpt)
- `gh.pr.expand` (pr.expand): fetch specific heavy fields (full body, changed files summary, checks)
- `gh.pr.timeline` (pr.timeline): paged minimal timeline (event type, ids, actor, createdAt)
- `gh.pr.files` (pr.files): paged changed files (path, additions, deletions, patch optional)
- `gh.pr.comment` (pr.comment): add comment
- `gh.pr.review` (pr.review): submit review (approve|request_changes|comment) with summary
- `gh.pr.merge` (pr.merge): merge with strategy flags
- `gh.issue.list/get/comment` (issue.*): same micro patterns
- `gh.commit.diff` (commit.diff): git diff between refs with path filters; returns summary unless `expand=patch`
- `gh.branch.create` (repo.branch.create): from ref
- `gh.branch.delete` (repo.branch.delete)

### Response Discipline
- Always return minimal JSON; IDs first; include `next_page` tokens; avoid text.
- Servers never echo back large content unasked; heavy fields are opt-in.
- Deterministic sort and stable IDs.
- No markdown; structured JSON only.

### Field-selection Contract
- `fields`: comma-separated list of allowed field names for each tool; nested via dot-notation (`checks.status`).
- Omitted `fields` returns the minimal meta for the entity.
- Unknown fields are ignored with `unknown_fields: [..]` returned in `details` of the response if `debug=true`.

### Deterministic Ordering
- Default sorts:
  - `pr.list`: by PR number asc
  - `file.tree`: by path asc
  - `branches.list`: by branch name asc
- Sorting changes (if added) must be explicit; defaults remain stable.

### Canonical Schemas (Appendix)
- Error envelope:
```json
{"code":"RATE_LIMIT","message":"secondary rate limit","details":{},"retry_after":2.5}
```
- List envelope:
```json
{"repo":"owner/name","filters":{},"ids":[1,2,3],"count":3,"next_page":"opaque"}
```
- Pagination token payload (base64-encoded):
```json
{"cursor":"opaque","filters":{"state":"open"},"version":"v1"}
```

### Caching Keys and TTLs
- Cache key: `(tool, args_hash, env_hash, version, auth_user)`
- TTLs: lists 30s; meta 5m; blobs 1h
- Invalidate on: `pr.comment/review/merge`, `issue.comment`, `branch.create/delete`, and file mutations (future)

### Security and Permissions
- PAT scopes matrix:
  - Read-only flows: `repo:read`, `read:org` (if org data)
  - Write flows: add `repo` (PRs, issues) minimally
- Always redact tokens; never log command lines with secrets.

### Observability
- Log format: JSON (opt-in) or human-readable; levels: info/debug/warn/error.
- Metrics: optional counters/timers; disabled by default.
- Subprocess redaction: strip env and Authorization headers from logs.

### CI Performance
- Use Actions cache for `.uv/` and wheels keyed by Python version and `pyproject.toml` hash.
- Add concurrency group per workflow to cancel outdated runs.

## Repository Layout
```
.
├─ src/
│  └─ lite_github_mcp/
│     ├─ __init__.py
│     ├─ core/
│     ├─ github/
│     ├─ commands/
│     ├─ config.py
│     ├─ logging.py
│     └─ types.py
├─ tests/
├─ docker/
│  └─ Dockerfile
├─ docker-compose.yml
├─ pyproject.toml
├─ .github/workflows/
│  ├─ ci.yml
│  └─ release.yml
├─ README.md
└─ docs/
   └─ project-docs/
      └─ TECHNICAL_PLAN_OVERVIEW.md
```

## Dependencies and Version Policy
- **Python**: 3.13+ only.
- **Runtime**: `httpx` (or `requests`), `pydantic`, `tenacity`, `pyyaml`, `diskcache`, `typer`, `uvloop` (optional, Linux-only).
- **Dev**: `ruff`, `mypy`, `pytest`, `pytest-xdist`, `pytest-testmon`, `coverage[toml]`, `pytest-cov`, `pre-commit`, `commitizen`, `types-PyYAML`, `types-requests`.
- **Resolver/Installer**: `uv` (Astral).

... (unchanged content above retained; see file for full details) ...
