from __future__ import annotations

from typing import Any

from lite_github_mcp.tools import router


def test_cursor_invalid_resets_tree(tmp_path: Any) -> None:
    # Compare behavior with and without invalid cursor; should be identical
    base = router.file_tree(repo_path=str(tmp_path), ref="HEAD", limit=1, cursor=None)
    bad = router.file_tree(repo_path=str(tmp_path), ref="HEAD", limit=1, cursor="not-base64")
    assert bad.count == base.count
    assert bad.entries == base.entries


def test_cursor_invalid_resets_search(tmp_path: Any) -> None:
    (tmp_path / "x.txt").write_text("hello\nworld\n")
    base = router.search_files(repo_path=str(tmp_path), pattern="hello", limit=1, cursor=None)
    bad = router.search_files(repo_path=str(tmp_path), pattern="hello", limit=1, cursor="bad")
    assert bad.count == base.count
    assert bad.matches == base.matches


def test_branch_list_determinism(tmp_path: Any) -> None:
    tree = router.repo_branches_list(repo_path=str(tmp_path), limit=10)
    names = tree.names
    assert names == sorted(names)
