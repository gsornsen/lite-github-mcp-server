from pathlib import Path

from lite_github_mcp.services.git_cli import ensure_repo
from lite_github_mcp.tools.router import repo_refs_get, search_files


def test_refs_get_empty(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    r = repo_refs_get(str(repo.path), "HEAD")
    assert r.ref == "HEAD"
    # Unborn HEAD returns None
    assert r.sha is None or isinstance(r.sha, str)


def test_search_no_matches(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    res = search_files(str(repo.path), pattern="foobar")
    assert res.pattern == "foobar"
    assert res.matches == []
