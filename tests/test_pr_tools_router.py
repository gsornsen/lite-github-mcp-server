from typing import Any

from lite_github_mcp.services import gh_cli
from lite_github_mcp.tools.router import pr_get, pr_list, pr_timeline


def test_pr_list_paging_monkeypatched(monkeypatch: Any) -> None:
    sample = [
        {"number": 1, "state": "OPEN", "author": {"login": "a"}, "createdAt": "t1"},
        {"number": 2, "state": "OPEN", "author": {"login": "b"}, "createdAt": "t2"},
        {"number": 3, "state": "OPEN", "author": {"login": "c"}, "createdAt": "t3"},
    ]

    def fake_run_gh_json(args: list[str]) -> Any:  # noqa: ANN401
        return sample

    monkeypatch.setattr(gh_cli, "run_gh_json", fake_run_gh_json)

    out = pr_list("o/n", state="open", author=None, label=None, limit=2, cursor=None)
    assert out.ids == [1, 2]
    assert out.has_next is True and out.next_cursor

    out2 = pr_list("o/n", state="open", author=None, label=None, limit=2, cursor=out.next_cursor)
    assert out2.ids == [3]
    assert out2.has_next is False


def test_pr_get_monkeypatched(monkeypatch: Any) -> None:
    sample = {"number": 42, "state": "OPEN", "title": "T", "author": {"login": "me"}}

    def fake_run_gh_json(args: list[str]) -> Any:  # noqa: ANN401
        return sample

    monkeypatch.setattr(gh_cli, "run_gh_json", fake_run_gh_json)

    out = pr_get("o/n", number=42)
    assert out.number == 42 and out.state == "OPEN" and out.title == "T"


def test_pr_timeline_monkeypatched(monkeypatch: Any) -> None:
    rest_events = [
        {"event": "commented", "created_at": "t1", "actor": {"login": "a"}},
        {"event": "merged", "created_at": "t2", "actor": {"login": "b"}},
    ]

    def fake_run_gh_json(args: list[str]) -> Any:  # noqa: ANN401
        return rest_events

    monkeypatch.setattr(gh_cli, "run_gh_json", fake_run_gh_json)

    out = pr_timeline("o/n", number=7, limit=1)
    assert out.count == 1 and out.has_next is True and out.next_cursor
    out2 = pr_timeline("o/n", number=7, limit=1, cursor=out.next_cursor)
    assert out2.count == 1 and out2.has_next is False

    # With filter_nulls=True, events with any nulls should be excluded
    rest_events2 = [
        {"event": "committed", "created_at": None, "actor": {"login": None}},
        {"event": "merged", "created_at": "t", "actor": {"login": "ok"}},
    ]

    def fake_run_gh_json2(args: list[str]) -> Any:  # noqa: ANN401
        return rest_events2

    monkeypatch.setattr(gh_cli, "run_gh_json", fake_run_gh_json2)
    out3 = pr_timeline("o/n", number=8, limit=5, filter_nulls=True)
    assert out3.count == 1
