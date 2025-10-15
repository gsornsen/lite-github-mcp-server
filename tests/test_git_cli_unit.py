import shutil
from pathlib import Path

from lite_github_mcp.services.git_cli import (
    GitRepo,
    current_branch,
    default_branch,
    get_remote_origin_url,
    parse_owner_repo_from_url,
    rev_parse,
)
from lite_github_mcp.services.git_cli import grep as git_grep
from lite_github_mcp.utils.subprocess import run_command


def test_parse_owner_repo_from_url_variants() -> None:
    ssh = "git@github.com:owner/name.git"
    https = "https://github.com/owner/name.git"
    owner, name = parse_owner_repo_from_url(ssh)
    assert owner == "owner" and name == "name"
    owner2, name2 = parse_owner_repo_from_url(https)
    assert owner2 == "owner" and name2 == "name"


def test_origin_and_branch_empty_repo(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    # init
    rc = run_command(["git", "init"], cwd=repo_path)
    assert rc.returncode == 0

    repo = GitRepo(path=repo_path)
    assert get_remote_origin_url(repo) is None
    assert current_branch(repo) is None
    assert default_branch(repo) is None
    assert rev_parse(repo, "HEAD") is None


def test_grep_git_fallback_no_rg(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # Force shutil.which('rg') to return None so fallback path is taken
    orig_which = shutil.which
    monkeypatch.setattr(shutil, "which", lambda name: None if name == "rg" else orig_which(name))

    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    rc = run_command(["git", "init"], cwd=repo_path)
    assert rc.returncode == 0
    # create file
    f = repo_path / "readme.txt"
    f.write_text("hello world\nfoo bar\n")

    matches = git_grep(GitRepo(repo_path), pattern="hello", paths=None)
    assert matches and matches[0][0].endswith("readme.txt")
