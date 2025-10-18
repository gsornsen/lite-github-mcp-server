# Lite GitHub MCP Server

Minimal, context-efficient MCP server for GitHub with a CLI-first approach.

## Requirements
- Python 3.13+
- git, gh CLI installed (for later milestones)

## Quickstart

```bash
# Install uv (https://github.com/astral-sh/uv)
# Then setup dev env
just setup

# Run tests
just test

# Run server
just run

# Format and lint
just fmt && just lint
```

## Docker

```bash
just docker_build
just compose_up
# ... use it ...
just compose_down
```

## Notes
- Targets Python 3.13+; `uvloop` remains optional on Linux.
- `gh.ping` and `gh.whoami` are available; `whoami` returns a minimal auth status.
- For FastMCP concepts and up-to-date API details, see the MDX docs: https://github.com/jlowin/fastmcp/tree/main/docs

### Observability (optional)

- Structured JSON logging for tool calls (opt-in):

```bash
# Enable lightweight timing logs (one line per tool call)
LGMCP_LOG_JSON=1 just run
# or
LGMCP_LOG_JSON=1 uv run python -m lite_github_mcp.server
```

Emitted fields: `tool`, `arg_keys`, `duration_ms`, optional `error`.

- Caching and ETag:

```bash
# Disk-backed cache using `diskcache` under XDG cache dir
# ETag-based conditional requests are enabled for GitHub REST via gh api
# Cache TTLs: lists=30s, meta=5m, blobs=1h
```

- Context budget checks:
  - CI enforces budgets for the tool registry (bytes and token estimates)
  - Local live test (schema-aware):

```bash
# Run only the marked context test and print a brief report
just test_context
# Or with pytest directly
uv run pytest -q -m context_budget -s
```

You’ll see a short report like:

```
Context budget (tool registry):
  minimal bytes: 1084 / 8192 (13.2%)
  full bytes:    5628 / 32768 (17.2%)
  tokens:        1407 / 4000 (35.2%)
```

## CLI examples (paging and ranges)

```bash
# List tools
just cli_tools

# Trees (limit, cursor)
just cli_call gh.file.tree '{"repo_path": ".", "ref": "HEAD", "limit": 3}'
# Use the returned next_cursor to fetch next page
just cli_call gh.file.tree '{"repo_path": ".", "ref": "HEAD", "limit": 3, "cursor": "<next>"}'

# Search (limit, cursor)
just cli_call gh.search.files '{"repo_path": ".", "pattern": "FastMCP", "limit": 2}'
# Restrict search to paths
just cli_call gh.search.files '{"repo_path": ".", "pattern": "TODO", "paths": ["src/", "docs/"]}'

# Blob ranges (offset, max_bytes)
just cli_call gh.file.blob '{"repo_path": ".", "blob_sha": "<sha>", "max_bytes": 128, "offset": 0}'

# PRs (ids-first, meta, timeline)
just cli_call gh.pr.list '{"repo": "gsornsen/lite-github-mcp-server", "state": "open", "limit": 10}'
just cli_call gh.pr.get '{"repo": "gsornsen/lite-github-mcp-server", "number": 3}'
just cli_call gh.pr.timeline '{"repo": "gsornsen/lite-github-mcp-server", "number": 3, "limit": 5}'
```
