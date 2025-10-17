from typing import Any

import lite_github_mcp.tools.router as router_mod
from lite_github_mcp.tools.router import issue_comment, issue_get, issue_list


def test_issue_list_paging(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        router_mod,
        "gh_issue_list",
        lambda owner, name, state, author, label, limit, cursor: {
            "repo": f"{owner}/{name}",
            "filters": {"state": state},
            "ids": [10, 11],
            "count": 2,
            "has_next": False,
            "next_cursor": None,
        },
    )

    out = issue_list("o/n", state="open", limit=2)
    assert out.count == 2 and out.ids == [10, 11]


ess = {"repo": "o/n", "number": 10, "state": "open", "title": "T", "author": {"login": "me"}}


def test_issue_get(monkeypatch: Any) -> None:
    monkeypatch.setattr(router_mod, "gh_issue_get", lambda owner, name, number: ess)
    out = issue_get("o/n", 10)
    assert out.number == 10 and out.title == "T"


def test_issue_comment(monkeypatch: Any) -> None:
    monkeypatch.setattr(router_mod, "gh_issue_comment", lambda *a, **k: {"ok": True})
    res = issue_comment("o/n", 10, body="Thanks")
    assert res.ok
