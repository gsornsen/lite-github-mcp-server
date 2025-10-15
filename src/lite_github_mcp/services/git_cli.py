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


def get_remote_origin_url(repo: GitRepo) -> str | None:
    result = run_command(["git", "remote", "get-url", "origin"], cwd=repo.path)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def current_branch(repo: GitRepo) -> str | None:
    # Returns current branch name or None if detached
    result = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo.path)
    if result.returncode != 0:
        return None
    name = result.stdout.strip()
    return name if name and name != "HEAD" else None


def default_branch(repo: GitRepo) -> str | None:
    # Try origin/HEAD -> refs/remotes/origin/HEAD -> origin/<branch>
    result = run_command(
        ["git", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"], cwd=repo.path
    )
    if result.returncode == 0:
        # Output like: refs/remotes/origin/main
        ref = result.stdout.strip()
        if ref.startswith("refs/remotes/origin/"):
            return ref.split("/")[-1]
    # Fallback: current local branch
    return current_branch(repo)


def parse_owner_repo_from_url(url: str) -> tuple[str | None, str | None]:
    # Supports ssh and https git URLs
    # ssh: git@github.com:owner/name.git
    # https: https://github.com/owner/name.git
    owner = None
    name = None
    if "://" in url:
        try:
            parts = url.split("//", 1)[1]
            host_and_path = parts.split("/", 1)[1]
            owner, name = host_and_path.split("/", 1)
        except Exception:
            return None, None
    else:
        # likely ssh
        try:
            host_and_path = url.split(":", 1)[1]
            owner, name = host_and_path.split("/", 1)
        except Exception:
            return None, None
    if name.endswith(".git"):
        name = name[:-4]
    return owner, name


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
    """Search for pattern in repo using ripgrep if available, else git grep.

    Returns list of (path, line, excerpt).
    """
    # Prefer ripgrep (rg) if available for speed
    try:
        rg_args: list[str] = ["rg", "-n", "--no-heading", "--color", "never", pattern]
        if paths:
            rg_args.extend(list(paths))
        else:
            rg_args.append(".")
        rg_result = run_command(rg_args, cwd=repo.path)
        if rg_result.returncode in (0, 1):  # 0=matches, 1=no matches
            matches: list[tuple[str, int, str]] = []
            for line in rg_result.stdout.splitlines():
                # rg format: file:line:col:excerpt
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    file_path, lineno, _col, excerpt = parts[0], parts[1], parts[2], parts[3]
                elif len(parts) >= 3:
                    file_path, lineno, excerpt = parts[0], parts[1], parts[2]
                else:
                    continue
                try:
                    matches.append((file_path, int(lineno), excerpt))
                except Exception:
                    continue
            return matches
        # If rg returns other error, fall back to git grep
    except FileNotFoundError:
        pass

    # Fallback: git grep
    gg_args = ["git", "grep", "-n", pattern]
    if paths:
        gg_args.extend(paths)
    gg_result = run_command(gg_args, cwd=repo.path)
    matches2: list[tuple[str, int, str]] = []
    for line in gg_result.stdout.splitlines():
        try:
            file_path, lineno, excerpt = line.split(":", 2)
            matches2.append((file_path, int(lineno), excerpt))
        except Exception:
            continue
    return matches2
