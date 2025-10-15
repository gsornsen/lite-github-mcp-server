from pathlib import Path

from lite_github_mcp.services.git_cli import ensure_repo
from lite_github_mcp.tools.router import file_blob, repo_branches_list


def test_branches_list_paging(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    # No branches yet
    res = repo_branches_list(str(repo.path), limit=2)
    assert res.count == 0 and res.has_next is False


def test_blob_paging_empty(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    # For empty repo blob won't exist; just exercise paging on empty data
    out = file_blob(str(repo.path), blob_sha="deadbeef", max_bytes=16, offset=0)
    # Will return empty; size=fetched=0
    assert out.fetched == 0
