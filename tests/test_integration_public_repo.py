from pathlib import Path

import pytest

from lite_github_mcp.services.git_cli import ensure_repo, run_command
from lite_github_mcp.tools.router import file_tree, search_files

pytestmark = pytest.mark.integration


def test_public_repo_tree_and_search(tmp_path: Path) -> None:
    # Fixed small public repo for deterministic shallow clone
    url = "https://github.com/octocat/Spoon-Knife.git"
    # Shallow clone with partial options if possible
    dest = tmp_path / "repo"
    rc = run_command(["git", "clone", "--depth", "1", url, str(dest)])
    assert rc.returncode == 0, rc.stderr

    repo = ensure_repo(dest)

    tree = file_tree(str(repo.path), ref="HEAD", limit=5)
    assert tree.count <= 5

    search = search_files(str(repo.path), pattern="README", limit=5)
    assert search.count <= 5
