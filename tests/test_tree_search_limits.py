from pathlib import Path

from lite_github_mcp.services.git_cli import ensure_repo
from lite_github_mcp.tools.router import file_tree, search_files


def test_tree_limit_and_basepath_validation(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    # No entries, still returns with empty list
    tl = file_tree(str(repo.path), ref="HEAD", base_path=None, limit=1)
    assert tl.entries == []


def test_tree_invalid_basepath_and_limit_errors(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    # Absolute base_path should raise
    try:
        file_tree(str(repo.path), ref="HEAD", base_path="/abs", limit=1)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for absolute base_path")
    # Invalid limit should raise
    try:
        file_tree(str(repo.path), ref="HEAD", base_path=None, limit=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for invalid limit")


def test_search_limit(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    res = search_files(str(repo.path), pattern="nothing", limit=1)
    assert res.matches == []


def test_search_empty_pattern_and_invalid_regex(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    # Empty pattern -> validation error
    raised = False
    try:
        search_files(str(repo.path), pattern="", limit=1)
    except ValueError:
        raised = True
    assert raised is True
    # Invalid regex should not crash; returns 0 matches
    res = search_files(str(repo.path), pattern="(")
    assert res.count == 0
