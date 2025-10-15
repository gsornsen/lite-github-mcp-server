from pathlib import Path

from lite_github_mcp.services.git_cli import ensure_repo
from lite_github_mcp.tools.router import repo_resolve


def test_repo_resolve_empty_repo(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    r = repo_resolve(str(repo.path))
    assert r.repo_path == str(repo.path)
    assert r.owner is None
    assert r.name is None
    # In a freshly initialized repo, HEAD may be unborn; allow None
    assert r.head is None or isinstance(r.head, str)
