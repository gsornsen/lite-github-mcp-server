from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # mypy: avoid importing third-party lib without stubs
    _diskcache: Any = None
else:
    try:
        import diskcache as _diskcache
    except Exception as exc:  # pragma: no cover - import error surfaced at runtime
        raise RuntimeError(
            "diskcache is required for caching; add it to runtime dependencies"
        ) from exc


# TTLs by category (seconds)
_TTLS: dict[str, int] = {
    "lists": 30,
    "meta": 300,
    "blobs": 3600,
}


def ttl_for_category(category: str, default: int | None = None) -> int:
    if category in _TTLS:
        return _TTLS[category]
    if default is not None:
        return default
    return 300


def _default_cache_dir() -> Path:
    # Respect XDG on *nix; fallback to ~/.cache
    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg:
        base = Path(xdg)
    else:
        base = Path.home() / ".cache"
    return base / "lite_github_mcp"


@dataclass
class CacheStore:
    path: Path

    def __post_init__(self) -> None:
        # Annotate as Any to avoid missing type info
        self._cache: Any = _diskcache.Cache(str(self.path))

    # JSON helpers
    def get_json(self, key: str) -> Any | None:
        raw = self._cache.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        text = json.dumps(value, separators=(",", ":"))
        self._cache.set(key, text, expire=ttl_seconds)

    # ETag helpers
    def get_etag(self, etag_key: str) -> str | None:
        val = self._cache.get(etag_key)
        return str(val) if val else None

    def set_etag(self, etag_key: str, etag: str) -> None:
        # Do not expire ETag explicitly; content TTL governs freshness
        self._cache.set(etag_key, etag)

    # Invalidation helpers
    def invalidate_prefix(self, prefix: str) -> int:
        removed = 0
        # iterkeys yields live view; copy to list first
        for key in list(self._cache.iterkeys()):
            key_str = str(key)
            if key_str.startswith(prefix):
                try:
                    del self._cache[key]
                    removed += 1
                except Exception:
                    continue
        return removed


_GLOBAL_CACHE: CacheStore | None = None


def get_cache() -> CacheStore:
    global _GLOBAL_CACHE
    if _GLOBAL_CACHE is None:
        _GLOBAL_CACHE = CacheStore(path=_default_cache_dir())
    return _GLOBAL_CACHE
