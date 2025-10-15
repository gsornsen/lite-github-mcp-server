from typing import Any

from fastmcp.tools.tool import Tool


def ping() -> dict[str, Any]:
    return {"ok": True, "version": "0.1.0"}


def whoami() -> dict[str, Any]:
    # Placeholder; real impl will shell out to `gh auth status --show-token-scopes`
    return {"ok": True, "user": None, "scopes": []}


def register_tools(app: Any) -> None:
    app.add_tool(Tool.from_function(ping, name="gh.ping", description="Health check"))
    app.add_tool(Tool.from_function(whoami, name="gh.whoami", description="gh auth status"))
