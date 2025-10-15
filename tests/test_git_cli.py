from pathlib import Path

from lite_github_mcp.services.git_cli import ensure_repo, list_branches


def test_ensure_repo_initializes(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    assert (repo.path / ".git").exists()


def test_list_branches_empty(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    branches = list_branches(repo)
    assert branches == []
