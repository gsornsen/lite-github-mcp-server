from __future__ import annotations

import subprocess
from typing import Any

from lite_github_mcp.tools import router


def _git(cwd: str, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True)


def test_branch_paging_union_equals_full(tmp_path: Any) -> None:
    _git(str(tmp_path), "init")
    _git(
        str(tmp_path),
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "--allow-empty",
        "-m",
        "init",
    )
    for name in ["b1", "b2", "b3", "b4"]:
        _git(str(tmp_path), "branch", name)

    full = router.repo_branches_list(repo_path=str(tmp_path), limit=100)
    p1 = router.repo_branches_list(repo_path=str(tmp_path), limit=2)
    names = list(p1.names)
    if p1.has_next and p1.next_cursor:
        p2 = router.repo_branches_list(repo_path=str(tmp_path), limit=2, cursor=p1.next_cursor)
        names.extend(p2.names)
        if p2.has_next and p2.next_cursor:
            p3 = router.repo_branches_list(repo_path=str(tmp_path), limit=2, cursor=p2.next_cursor)
            names.extend(p3.names)
    assert sorted(names) == sorted(full.names)
