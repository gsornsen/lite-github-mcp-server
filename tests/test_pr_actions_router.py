from typing import Any

import lite_github_mcp.tools.router as router_mod
from lite_github_mcp.tools.router import (
    pr_comment,
    pr_files,
    pr_merge,
    pr_review,
)


def test_pr_files_paging(monkeypatch: Any) -> None:
    def fake(
        owner: str, name: str, number: int, limit: int | None, cursor: str | None
    ) -> dict[str, Any]:
        return {
            "repo": f"{owner}/{name}",
            "number": number,
            "files": [
                {"path": "a.py", "status": "modified", "additions": 10, "deletions": 2},
                {"path": "b.py", "status": "added", "additions": 5, "deletions": 0},
            ],
            "count": 2,
            "has_next": False,
            "next_cursor": None,
        }

    monkeypatch.setattr(router_mod, "gh_pr_files", fake)

    out = pr_files("o/n", number=1, limit=2)
    assert out["count"] == 2 and out["files"][0]["path"] == "a.py"


def test_pr_comment_and_review_and_merge(monkeypatch: Any) -> None:
    monkeypatch.setattr(router_mod, "gh_pr_comment", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(router_mod, "gh_pr_review", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(router_mod, "gh_pr_merge", lambda *a, **k: {"ok": True})

    c = pr_comment("o/n", number=1, body="Thanks!")
    r = pr_review("o/n", number=1, event="approve", body="LGTM")
    m = pr_merge("o/n", number=1, method="squash")

    assert c.ok and r.ok and m.ok
