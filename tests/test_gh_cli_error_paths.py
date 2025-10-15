import pytest
from _pytest.monkeypatch import MonkeyPatch

from lite_github_mcp.services import gh_cli
from lite_github_mcp.utils.subprocess import CommandResult


def test_run_gh_json_raises_on_nonzero(monkeypatch: MonkeyPatch) -> None:
    def fake_run(args: list[str]) -> CommandResult:
        return CommandResult(args=tuple(args), returncode=1, stdout="", stderr="boom")

    monkeypatch.setattr(gh_cli, "_run_gh", fake_run)

    with pytest.raises(RuntimeError) as exc:
        gh_cli.run_gh_json(["pr", "list"])
    assert "boom" in str(exc.value)


def test_run_gh_json_none_on_empty_stdout(monkeypatch: MonkeyPatch) -> None:
    def fake_run(args: list[str]) -> CommandResult:
        return CommandResult(args=tuple(args), returncode=0, stdout="", stderr="")

    monkeypatch.setattr(gh_cli, "_run_gh", fake_run)

    out = gh_cli.run_gh_json(["auth", "status"])
    assert out is None
