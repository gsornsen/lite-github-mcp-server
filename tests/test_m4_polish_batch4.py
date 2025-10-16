from __future__ import annotations

import subprocess
from typing import Any

from lite_github_mcp.services import gh_cli
from lite_github_mcp.tools import router
from lite_github_mcp.utils.subprocess import CommandResult


def _git(cwd: str, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True)


def test_blob_large_offset_after_commit(tmp_path: Any) -> None:
    # Initialize repo and make a commit
    _git(str(tmp_path), "init")
    (tmp_path / "f.txt").write_text("hello world\n")
    _git(str(tmp_path), "add", ".")
    _git(
        str(tmp_path),
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-m",
        "init",
    )
    tree = router.file_tree(repo_path=str(tmp_path), ref="HEAD", limit=10)
    assert tree.count >= 1
    blob_sha = tree.entries[0].blob_sha
    # Use an offset way beyond the file size
    res = router.file_blob(
        repo_path=str(tmp_path), blob_sha=blob_sha, max_bytes=32, offset=10_000_000
    )
    assert res.fetched == 0
    assert res.has_next is False


def test_pr_files_not_found_returns_empty(monkeypatch: Any) -> None:
    def fake_run_gh_json(args: list[str]) -> Any:  # noqa: ANN401
        raise RuntimeError("gh: Not Found (HTTP 404)")

    monkeypatch.setattr(gh_cli, "run_gh_json", fake_run_gh_json)
    data = gh_cli.pr_files("o", "n", number=999, limit=5, cursor=None)
    assert data["files"] == []
    assert data["count"] == 0


def test_whoami_unauth(monkeypatch: Any) -> None:
    def fake_run_command(args: list[str], **kwargs: Any) -> CommandResult:  # noqa: ANN401
        # Simulate gh auth status failure
        return CommandResult(args=tuple(args), returncode=1, stdout="", stderr="not authed")

    monkeypatch.setattr(gh_cli, "run_command", fake_run_command)
    out = router.whoami()
    assert out["authed"] is False
    assert out["user"] is None
