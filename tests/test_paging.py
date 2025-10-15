from pathlib import Path

from lite_github_mcp.services.git_cli import ensure_repo
from lite_github_mcp.tools.router import file_tree, search_files


def test_tree_invalid_basepath(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    try:
        file_tree(str(repo.path), ref="HEAD", base_path="/abs")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for absolute base_path")


def test_search_paging_cursor_roundtrip(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    # No matches, paging is stable
    res1 = search_files(str(repo.path), pattern="nothing", limit=2)
    assert res1.count == 0 and res1.has_next is False and res1.next_cursor is None
    res2 = search_files(str(repo.path), pattern="nothing", limit=2, cursor=res1.next_cursor)
    assert res2.count == 0 and res2.has_next is False and res2.next_cursor is None
