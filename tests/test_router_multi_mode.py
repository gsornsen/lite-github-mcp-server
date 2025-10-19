from typing import Any

from lite_github_mcp.server import app as server_app
from lite_github_mcp.tools.router import register_tools


def test_multi_tool_registration(monkeypatch: Any) -> None:
    monkeypatch.setenv("LGMCP_MULTI_TOOLS", "1")
    # Re-register tools on the app under test
    register_tools(server_app)
    # Use the client to list tools (avoids peeking internals)
    import asyncio

    from fastmcp.client.client import Client

    async def _list() -> list[str]:
        async with Client(server_app) as client:
            tools = await client.list_tools()
            return sorted([t.name for t in tools])

    names = asyncio.run(_list())
    assert "repo.resolve" in names
    assert "file.tree" in names
    assert "pr.list" in names
    assert "issue.get" in names
