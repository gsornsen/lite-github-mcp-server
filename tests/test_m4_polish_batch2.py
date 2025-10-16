from __future__ import annotations

from typing import Any

import pytest

from lite_github_mcp.services import gh_cli
from lite_github_mcp.tools import router


def test_search_empty_pattern_validation(tmp_path: Any) -> None:
    # Validates before IO
    with pytest.raises(ValueError):
        router.search_files(repo_path=str(tmp_path), pattern="")


def test_blob_invalid_sha_not_found(tmp_path: Any) -> None:
    # Initialize empty git repo implicitly; invalid sha should yield not_found
    result = router.file_blob(repo_path=str(tmp_path), blob_sha="deadbeef", max_bytes=16, offset=0)
    assert result.not_found is True
    assert result.size == 0
    assert result.fetched == 0
    assert result.total_size == 0
    assert result.has_next is False


def test_pr_list_state_any_normalizes(monkeypatch: Any) -> None:
    def fake_run_gh_json(args: list[str]) -> Any:  # noqa: ANN401
        return [{"number": 1, "state": "OPEN"}]

    monkeypatch.setattr(gh_cli, "run_gh_json", fake_run_gh_json)
    data = gh_cli.pr_list(
        "owner", "name", state="any", author=None, label=None, limit=10, cursor=None
    )
    assert data["filters"]["state"] == "all"
    assert data["ids"] == [1]


def test_pr_timeline_not_found_sets_flag(monkeypatch: Any) -> None:
    def fake_run_gh_json_raises(args: list[str]) -> Any:  # noqa: ANN401
        raise RuntimeError("gh: Not Found (HTTP 404)")

    monkeypatch.setattr(gh_cli, "run_gh_json", fake_run_gh_json_raises)
    data = gh_cli.pr_timeline("owner", "name", number=999999, limit=2, cursor=None)
    assert data["not_found"] is True
    assert data["events"] == []
    assert data["count"] == 0
