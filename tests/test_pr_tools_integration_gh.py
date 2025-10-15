import shutil
from pathlib import Path

import pytest

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
