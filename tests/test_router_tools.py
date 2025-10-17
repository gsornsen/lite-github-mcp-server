from pathlib import Path

from lite_github_mcp.services.git_cli import ensure_repo
from lite_github_mcp.tools.router import file_blob, repo_branches_list


def test_branches_list_paging(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    # No branches yet
    res = repo_branches_list(str(repo.path), limit=2)
    assert res.count == 0 and res.has_next is False


def test_blob_paging_empty(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    # For empty repo blob won't exist; just exercise paging on empty data
    out = file_blob(str(repo.path), blob_sha="deadbeef", max_bytes=16, offset=0)
    # Will return empty; size=fetched=0
    assert out.fetched == 0


def test_branch_paging_union(tmp_path: Path) -> None:
    repo = ensure_repo(tmp_path / "repo")
    # Create initial commit to allow branch creation
    from lite_github_mcp.utils.subprocess import run_command

    run_command(["git", "init"], cwd=repo.path)
    run_command(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "--allow-empty",
            "-m",
            "init",
        ],
        cwd=repo.path,
    )
    for name in ["b1", "b2", "b3", "b4"]:
        run_command(["git", "branch", name], cwd=repo.path)
    full = repo_branches_list(str(repo.path), limit=100)
    p1 = repo_branches_list(str(repo.path), limit=2)
    names = list(p1.names)
    if p1.has_next and p1.next_cursor:
        p2 = repo_branches_list(str(repo.path), limit=2, cursor=p1.next_cursor)
        names.extend(p2.names)
        if p2.has_next and p2.next_cursor:
            p3 = repo_branches_list(str(repo.path), limit=2, cursor=p2.next_cursor)
            names.extend(p3.names)
    assert sorted(names) == sorted(full.names)
