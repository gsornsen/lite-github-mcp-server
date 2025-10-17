import json
from typing import Any

from lite_github_mcp.server import app

THRESHOLDS = {
    "tool_registry_bytes": 8192,  # 8KB budget for tool list JSON
}


def serialize_tools() -> bytes:
    # FastMCP exposes tools via app._tool_manager._tools (internal)
    registry: list[dict[str, Any]] = []
    tools = getattr(getattr(app, "_tool_manager", None), "_tools", []) or []
    for t in tools:
        registry.append(
            {
                "name": getattr(t, "name", None),
                "description": getattr(t, "description", None),
            }
        )
    return json.dumps(registry, separators=(",", ":")).encode("utf-8")


def main() -> None:
    reg = serialize_tools()
    size = len(reg)
    if size > THRESHOLDS["tool_registry_bytes"]:
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "code": "CONTEXT_BUDGET_EXCEEDED",
                    "metric": "tool_registry_bytes",
                    "value": size,
                    "budget": THRESHOLDS["tool_registry_bytes"],
                }
            )
        )
    print(json.dumps({"ok": True, "tool_registry_bytes": size}))


if __name__ == "__main__":
    main()
