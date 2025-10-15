from pathlib import Path

from lite_github_mcp.services.git_cli import ensure_repo
from lite_github_mcp.tools.router import file_tree, search_files


def test_tree_limit_and_basepath_validation(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    # No entries, still returns with empty list
    tl = file_tree(str(repo.path), ref="HEAD", base_path=None, limit=1)
    assert tl.entries == []


def test_search_limit(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    res = search_files(str(repo.path), pattern="nothing", limit=1)
    assert res.matches == []
