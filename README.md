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
- `gh.ping` and `gh.whoami` are available; `whoami` is a placeholder until auth wiring.
- For FastMCP concepts and up-to-date API details, see the MDX docs: https://github.com/jlowin/fastmcp/tree/main/docs

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
