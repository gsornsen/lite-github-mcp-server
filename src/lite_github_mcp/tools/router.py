from fastmcp import tool


@tool(name="gh.ping", desc="Health check")
def ping() -> dict:
    return {"ok": True, "version": "0.1.0"}


@tool(name="gh.whoami", desc="gh auth status")
def whoami() -> dict:
    # Minimal placeholder; real impl will shell out to `gh auth status --show-token-scopes`
    # For Milestone 1, keep it lightweight and non-failing.
    return {"ok": True, "user": None, "scopes": []}


def register_tools(app) -> None:
    app.register(ping)
    app.register(whoami)
