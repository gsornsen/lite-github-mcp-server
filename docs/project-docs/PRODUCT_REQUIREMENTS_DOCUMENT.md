## Product Requirements Document (PRD)

### Product
- Name: Lite GitHub MCP Server (context-minimized, CLI-first)
- Doc owner: Gerald Sornsen
- Last updated: 2025-10-15

### 1) Problem Statement
Software agents and IDE copilots increasingly rely on MCP servers for repository-aware actions. Current GitHub-oriented MCP servers tend to:
- Register large numbers of tools with verbose descriptions, inflating token budgets before a session begins
- Over-fetch heavy payloads (full PR bodies, file contents) when agents only need IDs or small summaries
- Omit pagination and field selection, leading to rate-limit issues and slow responses
- Use REST for everything instead of leveraging local `git` and `gh` CLI, adding latency and complexity
- Produce chatty, markdown-heavy responses that are hard for downstream agents to parse deterministically

We need a minimal, deterministic, and CLI-first GitHub MCP server that keeps the tool registry tiny, fetches only what is needed, and returns stable, small JSON suited for agent consumption—without compromising usability.

### 2) Evidence from the Community (selected references)
- Token/context bloat and tool registration concerns (agents loading entire registries):
  - OpenAI/Anthropic community threads and GitHub issues discussing startup token costs and tool flooding. Examples:
    - Anthropic community: "Tooling context size and latency" — `https://community.anthropic.com/` (general discussion hub)
    - OpenAI community forum: "Function/tool overload increases token usage" — `https://community.openai.com/`
- Over-fetching and pagination gaps in bot integrations:
  - GitHub REST API best practices (conditional requests, pagination): `https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api`
  - GraphQL: selecting minimal fields and pagination connections: `https://docs.github.com/en/graphql`
- Preference for `gh` CLI in workflows (auth, speed, ergonomics):
  - GitHub CLI docs: `https://cli.github.com/`
  - `gh api` usage patterns and conditional requests: `https://cli.github.com/manual/gh_api`
- Caching and ETag usage to reduce rate limits:
  - GitHub REST conditional requests: `https://docs.github.com/en/rest/using-the-rest-api/conditional-requests`
- Agent determinism requirements and structured JSON responses:
  - MCP discussions emphasizing stable outputs and minimal prose (e.g., LangChain/LLM tooling issues): `https://github.com/langchain-ai/langchain/issues` (pattern of determinism/formatting requests)

Note: These links represent canonical documentation and discussion hubs that reflect recurring themes in 2024-2025 community feedback.

### 3) Target Users and Primary Use Cases
- IDE agent users (Cursor, Claude Code, VS Code extensions) who want:
  - Fast repo insights without blowing context/token budgets
  - Deterministic, small JSON responses suitable for follow-up tool calls
- Repo maintainers and contributors who want:
  - Lightweight PR and issue triage surfaces (IDs first, expand on demand)
  - File tree, blob slices, and diffs without cloning entire repos
- Automation scripts/bots seeking:
  - Minimal, composable endpoints to chain actions safely (idempotent, cached)

Primary use cases:
- List PRs by filters (state/label) returning IDs only; expand specific fields when needed
- List files at a ref and fetch a blob slice safely with byte ranges
- Resolve repo info (default branch, head sha) with minimal calls
- Post comments or reviews with minimal payloads and clear error surfaces

### 4) Minimal Lovable Product (MLP) Requirements
Non-functional (experience) requirements:
- Registry size budget: tool registry JSON ≤ 8KB by default
- Deterministic outputs: stable sorting, explicit fields, no markdown
- Fast response targets: p50 < 500ms for cached micro-queries; p95 < 2s for uncached
- Pagination first: defaults page_size=20 with next_page tokens everywhere applicable
- Auth UX: rely on `gh auth status`; clear errors for missing scopes or auth

Functional requirements (initial surface):
- Core
  - `gh.ping`: health {ok, version}
  - `gh.whoami`: active host, user, available scopes
  - `gh.configure`: set defaults (page_size, host, mono vs multi)
- Repo and files
  - `gh.repo.resolve`: map path/url → owner/name, default branch, head sha
  - `gh.repo.branches.list`: names only with prefix filter
  - `gh.repo.refs.get`: ref → sha
  - `gh.file.tree`: list paths + blob sha (no content)
  - `gh.file.blob`: content by blob sha with {max_bytes, offset, length}
  - `gh.search.files`: grep results (path, line, col, excerpt)
- PRs and issues
  - `gh.pr.list`: IDs only, paged
  - `gh.pr.get`: meta only unless fields requested
  - `gh.pr.timeline`: minimal timeline entries (type, ids, actor, createdAt)
  - `gh.pr.expand`: explicit fields (full body, changed files summary, checks)
  - `gh.pr.comment`, `gh.pr.review`, `gh.pr.merge`
  - `issue.list`, `issue.get`, `issue.comment` mirroring micro patterns

Performance and reliability:
- Cache layer with TTL per category (lists 30s, meta 5m, blobs 1h)
- Conditional requests to GitHub (ETag/If-None-Match)
- Safe subprocess runner with timeouts and retries; redaction of secrets

Platform/Compatibility:
- Python 3.13+; `uvloop` optional (Linux only)
- Works headless via stdio; integrates with IDE agents
- Docker image with `git` and `gh` installed; Compose service provided

### 5) Shippable, Demo-able Milestones
Milestone 1: Scaffolding and Health (week 1)
- Ship: minimal server with `gh.ping`, `gh.whoami`, `gh.configure`; docs with quickstart
- Demo: run locally and via Docker; show registry size budget and quick responses

Milestone 2: Repo + File Surface (week 2)
- Ship: `gh.repo.resolve`, `.branches.list`, `.refs.get`, `file.tree`, `file.blob`, `search.files`
- Demo: navigate a public repo, fetch a blob slice, deterministic ordering, pagination

Milestone 3: PR Basics (week 3)
- Ship: `pr.list`, `pr.get`, `pr.timeline`; caching and ETag-enabled GraphQL/REST micro-queries
- Demo: triage PR IDs, expand a subset of fields, validate rate-limit friendliness

Milestone 4: PR Actions and Issues (week 4)
- Ship: `pr.expand`, `pr.files`, `pr.comment`, `pr.review`, `pr.merge`; `issue.list/get/comment`
- Demo: end-to-end PR review flow on a test repo, showing ids-first then expand-on-demand

Milestone 5: Hardening and Telemetry (week 5)
- Ship: context budget checks in CI, error envelopes with machine codes, basic metrics/logging toggle
- Demo: CI passing with budgets; structured JSON logs and deterministic outputs

### 6) Out of Scope (initial)
- Full UI; web dashboard
- Advanced analytics beyond simple metrics
- Organization-wide synchronization or mirror services

### 7) Risks and Mitigations
- Binary wheels not ready for Python 3.13 → build from source with `uv`; cache in CI
- `gh` not installed/authenticated in user env → actionable errors; container includes `gh`
- Rate limiting on large repos → defaults to ids-first, pagination, caching, conditional requests
- Agent variance in tool loading → provide mono-tool router mode to keep registry tiny

### 8) Success Metrics
- p50 latency of cached calls (< 500ms), p95 of uncached (< 2s)
- Tool registry JSON size ≤ 8KB by default
- ≥ 80% user satisfaction on early adopter feedback (qualitative)
- CI green: lint, typecheck, tests, and context-budget checks

### 9) References
- GitHub CLI: `https://cli.github.com/`
- `gh api` manual: `https://cli.github.com/manual/gh_api`
- GitHub REST best practices: `https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api`
- Conditional requests: `https://docs.github.com/en/rest/using-the-rest-api/conditional-requests`
- GraphQL docs: `https://docs.github.com/en/graphql`
- Discussions on tool/context bloat and determinism (representative):
  - OpenAI community: `https://community.openai.com/`
  - Anthropic community: `https://community.anthropic.com/`
  - LangChain issues (deterministic outputs, tool design themes): `https://github.com/langchain-ai/langchain/issues`

### Glossary
- Mono-tool router: single tool entrypoint with subcommand enum
- Expand: explicitly request heavy fields in a follow-up call
- IDs-first: list endpoints return identifiers before metadata
- Conditional request: ETag/If-None-Match gating to reduce bandwidth
- MLP: Minimal Lovable Product (experience-preserving MVP)
