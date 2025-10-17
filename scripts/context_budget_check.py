import json
from math import ceil
from typing import Any

from lite_github_mcp.server import app

THRESHOLDS = {
    "tool_registry_bytes": 8192,  # 8KB budget for tool list JSON
    "tool_registry_tokens": 2000,  # Approx token budget for registry load
}


def serialize_tools(include_schemas: bool = True) -> bytes:
    # FastMCP exposes tools via app._tool_manager._tools (internal)
    registry: list[dict[str, Any]] = []
    tools = getattr(getattr(app, "_tool_manager", None), "_tools", []) or []
    for t in tools:
        item: dict[str, Any] = {
            "name": getattr(t, "name", None),
            "description": getattr(t, "description", None),
        }
        if include_schemas:
            schema: Any = None
            inp = getattr(t, "input_model", None)
            try:
                if inp is not None and hasattr(inp, "model_json_schema"):
                    schema = inp.model_json_schema()
                if hasattr(t, "input_schema"):
                    schema = t.input_schema
            except Exception:
                schema = None
            if schema is not None:
                item["input_schema"] = schema
        registry.append(item)
    return json.dumps(registry, separators=(",", ":")).encode("utf-8")


def main() -> None:
    # Minimal (name+description) and full (including schema) measurements
    reg_min = serialize_tools(include_schemas=False)
    reg = serialize_tools(include_schemas=True)
    size = len(reg)
    size_min = len(reg_min)

    # Estimate token count (best-effort)
    text = reg.decode("utf-8", errors="ignore")
    tokens = None
    try:
        import tiktoken

        try:
            enc = tiktoken.get_encoding("cl100k_base")
        except Exception:
            enc = tiktoken.get_encoding("o200k_base")  # fallback if available
        tokens = len(enc.encode(text))
    except Exception:
        # Heuristic: ~4 chars per token for English-ish JSON
        tokens = ceil(len(text) / 4)

    if size > THRESHOLDS["tool_registry_bytes"] or tokens > THRESHOLDS["tool_registry_tokens"]:
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "code": "CONTEXT_BUDGET_EXCEEDED",
                    "metrics": {
                        "tool_registry_bytes_min": {
                            "value": size_min,
                            "budget": THRESHOLDS["tool_registry_bytes"],
                        },
                        "tool_registry_bytes": {
                            "value": size,
                            "budget": THRESHOLDS["tool_registry_bytes"],
                        },
                        "tool_registry_tokens": {
                            "value": tokens,
                            "budget": THRESHOLDS["tool_registry_tokens"],
                        },
                    },
                }
            )
        )
    print(
        json.dumps(
            {
                "ok": True,
                "tool_registry_bytes_min": size_min,
                "tool_registry_bytes": size,
                "tool_registry_tokens": tokens,
            }
        )
    )


if __name__ == "__main__":
    main()
