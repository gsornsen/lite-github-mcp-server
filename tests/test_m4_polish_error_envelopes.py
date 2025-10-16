from __future__ import annotations

from typing import Any

import pytest

from lite_github_mcp.services import gh_cli
from lite_github_mcp.tools import router


def test_base_path_validation_error(tmp_path: Any) -> None:
    with pytest.raises(ValueError):
        router.file_tree(repo_path=str(tmp_path), ref="HEAD", base_path="/etc", limit=1)


def test_limit_validation_error(tmp_path: Any) -> None:
    with pytest.raises(ValueError):
        router.file_tree(repo_path=str(tmp_path), ref="HEAD", limit=0)


def test_whoami_error_when_gh_missing(monkeypatch: Any) -> None:
    # Simulate gh not installed
    def fake_run_command(args: list[str], **kwargs: Any):  # type: ignore[no-untyped-def]
        if args[:2] == ["gh", "--version"]:
            return gh_cli.CommandResult(args=tuple(args), returncode=127, stdout="", stderr="")
        return gh_cli.CommandResult(args=tuple(args), returncode=1, stdout="", stderr="not authed")

    monkeypatch.setattr(gh_cli, "run_command", fake_run_command)
    out = router.whoami()
    assert out["ok"] is False
    assert out["code"] in {"GH_NOT_INSTALLED", "GH_NOT_AUTHED"}
    assert "error" in out
