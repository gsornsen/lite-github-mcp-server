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


def repo_branches_list(repo_path: str, prefix: str | None = None) -> BranchList:
    repo = ensure_repo(Path(repo_path))
    names = list_branches(repo, prefix=prefix)
    return BranchList(repo=str(repo.path), prefix=prefix, names=names)


def file_tree(repo_path: str, ref: str, base_path: str | None = None) -> TreeList:
    repo = ensure_repo(Path(repo_path))
    entries = [
        TreeEntry(path=p, blob_sha=sha) for p, sha in ls_tree(repo, ref=ref, path=base_path or "")
    ]
    return TreeList(repo=str(repo.path), ref=ref, base_path=base_path, entries=entries)


def file_blob(repo_path: str, blob_sha: str, max_bytes: int = 32768) -> BlobResult:
    import base64

    repo = ensure_repo(Path(repo_path))
    data = show_blob(repo, blob_sha=blob_sha, max_bytes=max_bytes)
    return BlobResult(
        blob_sha=blob_sha, size=len(data), content_b64=base64.b64encode(data).decode("ascii")
    )


def search_files(repo_path: str, pattern: str, paths: list[str] | None = None) -> SearchResult:
    repo = ensure_repo(Path(repo_path))
    matches = grep(repo, pattern=pattern, paths=paths or [])
    converted = [SearchMatch(path=p, line=ln, excerpt=ex) for (p, ln, ex) in matches]
    return SearchResult(repo=str(repo.path), pattern=pattern, matches=converted)


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
