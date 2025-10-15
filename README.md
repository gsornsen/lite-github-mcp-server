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
