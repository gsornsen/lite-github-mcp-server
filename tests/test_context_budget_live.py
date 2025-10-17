from __future__ import annotations

import json
from typing import Any

import pytest
from fastmcp.client.client import Client

from lite_github_mcp.server import app as server_app


def estimate_tokens(text: str) -> int:
    try:
        import importlib

        tiktoken = importlib.import_module("tiktoken")
        get_encoding = tiktoken.get_encoding
        try:
            enc = get_encoding("cl100k_base")
        except Exception:
            enc = get_encoding("o200k_base")
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 4)


async def _fetch_registry() -> tuple[int, int, int]:
    async with Client(server_app) as client:
        tools = await client.list_tools()
        minimal = json.dumps([{"name": t.name, "description": t.description} for t in tools])
        # Best-effort input schema capture
        full_items: list[dict[str, Any]] = []
        for t in tools:
            item: dict[str, Any] = {"name": t.name, "description": t.description}
            schema = getattr(t, "inputSchema", None) or getattr(t, "input_schema", None)
            if schema is not None:
                item["input_schema"] = schema
            full_items.append(item)
        full = json.dumps(full_items)
        return (
            len(minimal.encode("utf-8")),
            len(full.encode("utf-8")),
            estimate_tokens(full),
        )


@pytest.mark.context_budget
def test_live_registry_context_budget(anyio_backend: Any) -> None:  # noqa: ANN001
    import anyio

    result = anyio.run(_fetch_registry)
    size_min, size_full, tokens = result

    budget_bytes_min = 8192
    budget_bytes_full = 32768
    budget_tokens = 4000

    # Human-readable report for local and CI logs (use -s to see stdout)
    print("\nContext budget (tool registry):")
    print(f"  minimal bytes: {size_min} / {budget_bytes_min} ({size_min / budget_bytes_min:.1%})")
    pct_full = size_full / budget_bytes_full
    print(f"  full bytes:    {size_full} / {budget_bytes_full} ({pct_full:.1%})")
    print(f"  tokens:        {tokens} / {budget_tokens} ({tokens / budget_tokens:.1%})\n")

    assert size_min <= budget_bytes_min
    assert size_full <= budget_bytes_full
    assert tokens <= budget_tokens
