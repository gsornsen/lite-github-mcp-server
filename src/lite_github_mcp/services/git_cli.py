from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from lite_github_mcp.utils.subprocess import run_command


@dataclass(frozen=True)
class GitRepo:
    path: Path


def ensure_repo(path: Path) -> GitRepo:
    path.mkdir(parents=True, exist_ok=True)
    # Initialize if not a git repo
    if not (path / ".git").exists():
        run_command(["git", "init"], cwd=path)
    return GitRepo(path=path)


def rev_parse(repo: GitRepo, ref: str = "HEAD") -> str | None:
    result = run_command(["git", "rev-parse", ref], cwd=repo.path)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def list_branches(repo: GitRepo, prefix: str | None = None) -> list[str]:
    result = run_command(
        ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads"], cwd=repo.path
    )
    if result.returncode != 0:
        return []
    names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if prefix:
        names = [n for n in names if n.startswith(prefix)]
    return sorted(names)


def ls_tree(repo: GitRepo, ref: str, path: str = "") -> list[tuple[str, str]]:
    args = ["git", "ls-tree", "-r", "--full-tree", ref]
    if path:
        args.append(path)
    result = run_command(args, cwd=repo.path)
    if result.returncode != 0:
        return []
    entries: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        # format: "<mode> <type> <object>\t<file>"
        try:
            meta, filename = line.split("\t", 1)
            _mode, _type, object_id = meta.split()
            entries.append((filename, object_id))
        except ValueError:
            continue
    entries.sort(key=lambda x: x[0])
    return entries


def show_blob(repo: GitRepo, blob_sha: str, max_bytes: int | None = None) -> bytes:
    result = run_command(["git", "cat-file", "-p", blob_sha], cwd=repo.path)
    data = result.stdout.encode()
    if max_bytes is not None and len(data) > max_bytes:
        return data[:max_bytes]
    return data


def grep(
    repo: GitRepo, pattern: str, paths: Iterable[str] | None = None
) -> list[tuple[str, int, str]]:
    args = ["git", "grep", "-n", pattern]
    if paths:
        args.extend(paths)
    result = run_command(args, cwd=repo.path)
    matches: list[tuple[str, int, str]] = []
    for line in result.stdout.splitlines():
        try:
            file_path, lineno, excerpt = line.split(":", 3)[0:3]
            matches.append((file_path, int(lineno), excerpt))
        except Exception:
            continue
    return matches
