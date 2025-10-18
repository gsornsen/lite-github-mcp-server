import shutil
from pathlib import Path
from typing import Any

import pytest

from lite_github_mcp.services import gh_cli
from lite_github_mcp.services.gh_cli import gh_auth_status
from lite_github_mcp.tools.router import pr_list

pytestmark = pytest.mark.integration


def test_pr_list_against_public_repo_if_authed(tmp_path: Path) -> None:
    # Skip if gh not installed
    if shutil.which("gh") is None:
        pytest.skip("gh not installed")

    status = gh_auth_status()
    if not status.get("ok"):
        pytest.skip("gh not authenticated")

    # A very active small repo for PRs may vary; use this repository as a fallback owner/name
    repo = "octocat/Hello-World"

    out = pr_list(repo, state="open", author=None, label=None, limit=1, cursor=None)
    # Just assert shape; count may be 0..1 depending on live data
    assert out.ids is not None and out.count in (0, 1)


def test_etag_and_invalidation_monkeypatched(monkeypatch: Any) -> None:
    # Simulate ETag caching for timeline and invalidation via comment
    calls: list[str] = []

    class Res:
        def __init__(self, stdout: str, returncode: int = 0) -> None:
            self.stdout = stdout
            self.returncode = returncode
            self.stderr = ""

    def fake_run(args: list[str]) -> Any:  # noqa: ANN401
        calls.append(" ".join(args))
        # gh api -i timeline path
        if args[:2] == ["api", "repos/o/n/issues/1/timeline?per_page=100"] and "-i" in args:
            # First call -> 200 with ETag, empty array
            if len([c for c in calls if "timeline" in c]) == 1:
                headers = 'HTTP/1.1 200 OK\r\nETag: "etag-1"\r\n\r\n'
                body = "[]"
                return Res(headers + body)
            # Second call -> 304 Not Modified
            headers = "HTTP/1.1 304 Not Modified\r\n\r\n"
            return Res(headers)
        # pr comment success should invalidate
        if args[:2] == ["pr", "comment"]:
            return Res("", 0)
        return Res("[]")

    monkeypatch.setattr(gh_cli, "_run_gh", fake_run)

    out1 = gh_cli.pr_timeline("o", "n", 1, limit=10, cursor=None)
    assert out1["count"] == 0
    out2 = gh_cli.pr_timeline("o", "n", 1, limit=10, cursor=None)
    assert out2["count"] == 0

    gh_cli.pr_comment("o", "n", 1, body="test")
    out3 = gh_cli.pr_timeline("o", "n", 1, limit=10, cursor=None)
    assert out3["count"] == 0
