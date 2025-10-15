from __future__ import annotations

import asyncio
import json
from typing import Any

import typer
from fastmcp.client.client import Client

from lite_github_mcp.server import app as server_app

cli = typer.Typer(help="CLI for exercising the Lite GitHub MCP Server tools")


async def _list_tools_async() -> None:
    async with Client(server_app) as client:
        tools = await client.list_tools()
        names = sorted([t.name for t in tools])
        typer.echo(json.dumps({"tools": names}, indent=2))


@cli.command("tools")
def list_tools() -> None:
    asyncio.run(_list_tools_async())


async def _call_tool_async(name: str, args: dict[str, Any]) -> None:
    async with Client(server_app) as client:
        result = await client.call_tool(name, args)
        # Prefer structured content when available; fall back to text
        structured = getattr(result, "structuredContent", None) or getattr(
            result, "structured_content", None
        )
        if structured is not None:
            typer.echo(json.dumps(structured, indent=2, default=str))
            return
        content = getattr(result, "content", None)
        if content and isinstance(content, list) and content:
            first = content[0]
            text = getattr(first, "text", None) or getattr(first, "content", None)
            if isinstance(text, str):
                typer.echo(text)
                return
        typer.echo(json.dumps({"result": str(result)}, indent=2))


@cli.command("call")
def call_tool(
    name: str = typer.Argument(..., help="Tool name, e.g., gh.ping"),
    args_json: str | None = typer.Option(
        None,
        "--args",
        help="JSON dict of arguments to pass to the tool",
    ),
) -> None:
    args: dict[str, Any] = {}
    if args_json:
        try:
            parsed = json.loads(args_json)
            if not isinstance(parsed, dict):
                raise ValueError("--args must be a JSON object")
            args = parsed
        except Exception as exc:
            raise typer.BadParameter(f"Invalid JSON for --args: {exc}") from exc
    asyncio.run(_call_tool_async(name, args))


def app() -> None:
    cli()


if __name__ == "__main__":
    app()
