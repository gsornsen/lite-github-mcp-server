from pathlib import Path
from typing import Any

from fastmcp.tools.tool import Tool

from lite_github_mcp.schemas.repo import (
    BlobResult,
    BranchList,
    RefResolve,
    RepoResolve,
    SearchMatch,
    SearchResult,
    TreeEntry,
    TreeList,
)
from lite_github_mcp.services.git_cli import (
    default_branch,
    ensure_repo,
    get_remote_origin_url,
    grep,
    list_branches,
    ls_tree,
    parse_owner_repo_from_url,
    rev_parse,
    show_blob,
)
from lite_github_mcp.services.pager import decode_cursor, encode_cursor


def ping() -> dict[str, Any]:
    return {"ok": True, "version": "0.1.0"}


def whoami() -> dict[str, Any]:
    # Placeholder; real impl will shell out to `gh auth status --show-token-scopes`
    return {"ok": True, "user": None, "scopes": []}


def register_tools(app: Any) -> None:
    app.add_tool(Tool.from_function(ping, name="gh.ping", description="Health check"))
    app.add_tool(Tool.from_function(whoami, name="gh.whoami", description="gh auth status"))
    app.add_tool(
        Tool.from_function(
            repo_branches_list, name="gh.repo.branches.list", description="List branch names"
        )
    )
    app.add_tool(
        Tool.from_function(file_tree, name="gh.file.tree", description="List files at ref")
    )
    app.add_tool(
        Tool.from_function(file_blob, name="gh.file.blob", description="Get file blob by sha")
    )
    app.add_tool(
        Tool.from_function(
            search_files, name="gh.search.files", description="Search files via git grep"
        )
    )
    app.add_tool(
        Tool.from_function(repo_resolve, name="gh.repo.resolve", description="Resolve repo info")
    )
    app.add_tool(
        Tool.from_function(repo_refs_get, name="gh.repo.refs.get", description="Resolve ref to sha")
    )


def repo_branches_list(
    repo_path: str, prefix: str | None = None, limit: int | None = None, cursor: str | None = None
) -> BranchList:
    repo = ensure_repo(Path(repo_path))
    names = list_branches(repo, prefix=prefix)
    start = decode_cursor(cursor).index
    if start < 0:
        start = 0
    end = start + (limit or len(names))
    page = names[start:end]
    has_next = end < len(names)
    next_cur = encode_cursor(end) if has_next else None
    return BranchList(
        repo=str(repo.path),
        prefix=prefix,
        names=page,
        count=len(page),
        has_next=has_next,
        next_cursor=next_cur,
    )


def file_tree(
    repo_path: str,
    ref: str,
    base_path: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> TreeList:
    repo = ensure_repo(Path(repo_path))
    # Basic base_path validation to avoid invalid path specs
    if base_path:
        p = Path(base_path)
        if p.is_absolute() or ".." in p.parts:
            raise ValueError("Invalid base_path")
    all_entries = [
        TreeEntry(path=p, blob_sha=sha) for p, sha in ls_tree(repo, ref=ref, path=base_path or "")
    ]
    start = decode_cursor(cursor).index
    if start < 0:
        start = 0
    end = start + (limit or len(all_entries))
    page = all_entries[start:end]
    has_next = end < len(all_entries)
    next_cur = encode_cursor(end) if has_next else None
    return TreeList(
        repo=str(repo.path),
        ref=ref,
        base_path=base_path,
        entries=page,
        count=len(page),
        has_next=has_next,
        next_cursor=next_cur,
    )


def file_blob(repo_path: str, blob_sha: str, max_bytes: int = 32768, offset: int = 0) -> BlobResult:
    import base64

    repo = ensure_repo(Path(repo_path))
    data = show_blob(repo, blob_sha=blob_sha, max_bytes=max_bytes, offset=offset)
    total = len(show_blob(repo, blob_sha=blob_sha))
    next_off = offset + len(data)
    has_next = next_off < total
    return BlobResult(
        blob_sha=blob_sha,
        size=len(data),
        content_b64=base64.b64encode(data).decode("ascii"),
        offset=offset,
        fetched=len(data),
        total_size=total,
        has_next=has_next,
        next_offset=next_off if has_next else None,
    )


def search_files(
    repo_path: str,
    pattern: str,
    paths: list[str] | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> SearchResult:
    repo = ensure_repo(Path(repo_path))
    matches = grep(repo, pattern=pattern, paths=paths or [])
    converted = [SearchMatch(path=p, line=ln, excerpt=ex) for (p, ln, ex) in matches]
    start = decode_cursor(cursor).index
    if start < 0:
        start = 0
    end = start + (limit or len(converted))
    page = converted[start:end]
    has_next = end < len(converted)
    next_cur = encode_cursor(end) if has_next else None
    return SearchResult(
        repo=str(repo.path),
        pattern=pattern,
        matches=page,
        count=len(page),
        has_next=has_next,
        next_cursor=next_cur,
    )


def repo_resolve(repo_path: str) -> RepoResolve:
    repo = ensure_repo(Path(repo_path))
    origin = get_remote_origin_url(repo)
    owner: str | None
    name: str | None
    owner, name = (None, None)
    if origin:
        owner, name = parse_owner_repo_from_url(origin)
    head = rev_parse(repo, "HEAD")
    return RepoResolve(
        repo_path=str(repo.path),
        origin_url=origin,
        owner=owner,
        name=name,
        default_branch=default_branch(repo),
        head=head,
    )


def repo_refs_get(repo_path: str, ref: str) -> RefResolve:
    repo = ensure_repo(Path(repo_path))
    sha = rev_parse(repo, ref)
    return RefResolve(repo_path=str(repo.path), ref=ref, sha=sha)
