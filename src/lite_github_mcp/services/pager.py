from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any

CURSOR_VERSION = "v1"


@dataclass(frozen=True)
class PageCursor:
    index: int
    filters: dict[str, Any]
    version: str = CURSOR_VERSION


def encode_cursor(index: int, *, filters: dict[str, Any] | None = None) -> str:
    payload = {
        "index": int(index),
        "filters": filters or {},
        "version": CURSOR_VERSION,
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def decode_cursor(cursor: str | None) -> PageCursor:
    if not cursor:
        return PageCursor(index=0, filters={})
    try:
        raw = base64.b64decode(cursor.encode("ascii"))
        obj = json.loads(raw)
        return PageCursor(index=int(obj.get("index", 0)), filters=dict(obj.get("filters", {})))
    except Exception:
        return PageCursor(index=0, filters={})
