from __future__ import annotations

from pathlib import Path
from typing import Any

from lite_github_mcp.services.git_cli import GitRepo, default_branch
from lite_github_mcp.utils.subprocess import run_command


def _git(cwd: Path, *args: str) -> int:
    return run_command(["git", *args], cwd=cwd).returncode


def test_default_branch_uses_origin_head(tmp_path: Any) -> None:
    repo_path = Path(tmp_path)
    _git(repo_path, "init")
    _git(repo_path, "checkout", "-b", "dev")
    _git(repo_path, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    repo = GitRepo(path=repo_path)
    db = default_branch(repo)
    assert db == "main"
