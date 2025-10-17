from __future__ import annotations

from collections.abc import Iterable

from rapidfuzz import fuzz

PERF_KEYWORDS = [
    "perf",
    "optimize",
    "optimization",
    "throughput",
    "latency",
    "benchmark",
    "speed",
    "alloc",
    "memory",
]
DX_KEYWORDS = [
    "devx",
    "developer experience",
    "tooling",
    "onboard",
    "onboarding",
    "lint",
    "pre-commit",
    "ci",
    "docs",
]
OPS_KEYWORDS = [
    "deploy",
    "rollback",
    "incident",
    "outage",
    "alert",
]


def _matches_any(text: str, keywords: Iterable[str], threshold: int = 80) -> bool:
    text_l = text.lower()
    for kw in keywords:
        if fuzz.partial_ratio(text_l, kw) >= threshold:
            return True
    return False


def compute_tags(*texts: str) -> list[str]:
    """Return lightweight tags inferred from provided texts using fuzzy matching.

    Tags: perf, dx, ops
    """
    combined = " ".join(t for t in texts if t).lower()
    tags: set[str] = set()
    if _matches_any(combined, PERF_KEYWORDS):
        tags.add("perf")
    if _matches_any(combined, DX_KEYWORDS):
        tags.add("dx")
    if _matches_any(combined, OPS_KEYWORDS):
        tags.add("ops")
    return sorted(tags)
