import json
import os
import time
from pathlib import Path
from typing import Any

from fastmcp.tools.tool import Tool

from lite_github_mcp.schemas.issue import CommentResult, IssueGet, IssueList
from lite_github_mcp.schemas.pr import PRGet, PRList, PRTimeline
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
from lite_github_mcp.services.gh_cli import (
    issue_comment as gh_issue_comment,
)
from lite_github_mcp.services.gh_cli import (
    issue_get as gh_issue_get,
)
from lite_github_mcp.services.gh_cli import (
    issue_list as gh_issue_list,
)
from lite_github_mcp.services.gh_cli import (
    pr_comment as gh_pr_comment,
)
from lite_github_mcp.services.gh_cli import (
    pr_files as gh_pr_files,
)
from lite_github_mcp.services.gh_cli import (
    pr_get as gh_pr_get,
)
from lite_github_mcp.services.gh_cli import (
    pr_list as gh_pr_list,
)
from lite_github_mcp.services.gh_cli import (
    pr_merge as gh_pr_merge,
)
from lite_github_mcp.services.gh_cli import (
    pr_review as gh_pr_review,
)
from lite_github_mcp.services.gh_cli import (
    pr_timeline as gh_pr_timeline,
)
from lite_github_mcp.services.gh_cli import repo_ref_get_remote
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
from lite_github_mcp.utils.errors import GH_ERROR, ErrorEnvelope


def ping() -> dict[str, Any]:
    return {"ok": True, "version": "0.1.0"}


def whoami() -> dict[str, Any]:
    from lite_github_mcp.services.gh_cli import gh_auth_status

    status = gh_auth_status()
    if not status.get("ok"):
        return ErrorEnvelope(
            code=status.get("code") or GH_ERROR,
            message=status.get("error") or "gh error",
            details={},
        ).to_dict()
    return {
        "ok": True,
        "authed": True,
        "user": status.get("user"),
        "scopes": status.get("scopes") or [],
        "host": status.get("host"),
    }


def _should_log() -> bool:
    return os.environ.get("LGMCP_LOG_JSON") in {"1", "true", "TRUE", "yes"}


def _log_event(event: dict[str, Any]) -> None:
    try:
        print(json.dumps(event, separators=(",", ":")))
    except Exception:
        # Do not fail server if logging fails
        pass


def _instrument_tool(func: Any, tool_name: str) -> Any:
    if not _should_log():
        return func

    def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        start = time.perf_counter()
        error: str | None = None
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            # Keep args minimal to avoid leaking content; only log keys
            arg_keys = list(kwargs.keys())
            event = {
                "type": "tool_call",
                "tool": tool_name,
                "duration_ms": round(duration_ms, 2),
                "arg_keys": arg_keys,
            }
            if error is not None:
                event["error"] = error
            _log_event(event)

    return wrapper


def register_tools(app: Any) -> None:
    app.add_tool(
        Tool.from_function(
            _instrument_tool(ping, "gh.ping"), name="gh.ping", description="Health check"
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(whoami, "gh.whoami"), name="gh.whoami", description="gh auth status"
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(repo_branches_list, "gh.repo.branches.list"),
            name="gh.repo.branches.list",
            description="List branch names",
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(file_tree, "gh.file.tree"),
            name="gh.file.tree",
            description="List files at ref",
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(file_blob, "gh.file.blob"),
            name="gh.file.blob",
            description="Get file blob by sha",
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(search_files, "gh.search.files"),
            name="gh.search.files",
            description="Search files via git grep",
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(repo_resolve, "gh.repo.resolve"),
            name="gh.repo.resolve",
            description="Resolve repo info",
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(repo_refs_get, "gh.repo.refs.get"),
            name="gh.repo.refs.get",
            description="Resolve ref to sha",
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(pr_list, "gh.pr.list"), name="gh.pr.list", description="List PR ids"
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(pr_get, "gh.pr.get"), name="gh.pr.get", description="Get PR meta"
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(pr_timeline, "gh.pr.timeline"),
            name="gh.pr.timeline",
            description="PR timeline events",
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(pr_files, "gh.pr.files"),
            name="gh.pr.files",
            description="PR changed files",
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(pr_comment, "gh.pr.comment"),
            name="gh.pr.comment",
            description="Comment on PR",
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(pr_review, "gh.pr.review"),
            name="gh.pr.review",
            description="Review PR",
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(pr_merge, "gh.pr.merge"), name="gh.pr.merge", description="Merge PR"
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(issue_list, "gh.issue.list"),
            name="gh.issue.list",
            description="List issues",
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(issue_get, "gh.issue.get"),
            name="gh.issue.get",
            description="Get issue",
        )
    )
    app.add_tool(
        Tool.from_function(
            _instrument_tool(issue_comment, "gh.issue.comment"),
            name="gh.issue.comment",
            description="Comment on issue",
        )
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
    # Enforce limit semantics
    if limit is not None and limit < 1:
        raise ValueError("Invalid limit: must be >= 1")
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
    not_found = total == 0 and len(data) == 0
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
        not_found=not_found,
    )


def search_files(
    repo_path: str,
    pattern: str,
    paths: list[str] | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> SearchResult:
    repo = ensure_repo(Path(repo_path))
    if not pattern:
        raise ValueError("Invalid pattern: must be non-empty")
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


def repo_refs_get(
    repo_path: str | None = None, ref: str = "HEAD", repo: str | None = None
) -> RefResolve:
    # Input shape: either local repo_path or owner/name repo, but not both
    if (repo_path and repo) or (not repo_path and not repo):
        raise ValueError("Specify exactly one of repo_path or repo")
    if repo is not None:
        owner, name = repo.split("/", 1)
        remote = repo_ref_get_remote(owner, name, ref)
        return RefResolve(repo_path=repo, ref=ref, sha=remote.get("sha"))
    assert repo_path is not None
    repo_obj = ensure_repo(Path(repo_path))
    sha = rev_parse(repo_obj, ref)
    return RefResolve(repo_path=str(repo_obj.path), ref=ref, sha=sha)


def pr_list(
    repo: str,
    state: str | None = None,
    author: str | None = None,
    label: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> PRList:
    owner, name = repo.split("/", 1)
    data = gh_pr_list(owner, name, state, author, label, limit, cursor)
    return PRList(**data)


def pr_get(repo: str, number: int) -> PRGet:
    owner, name = repo.split("/", 1)
    data = gh_pr_get(owner, name, number)
    if not data:
        return PRGet(repo=repo, number=number, state=None, title=None, author=None, not_found=True)
    return PRGet(**data)


def pr_timeline(
    repo: str, number: int, limit: int | None = None, cursor: str | None = None
) -> PRTimeline:
    owner, name = repo.split("/", 1)
    data = gh_pr_timeline(owner, name, number, limit, cursor)
    return PRTimeline(**data)


def pr_files(
    repo: str, number: int, limit: int | None = None, cursor: str | None = None
) -> dict[str, Any]:
    owner, name = repo.split("/", 1)
    return gh_pr_files(owner, name, number, limit, cursor)


def pr_comment(repo: str, number: int, body: str) -> CommentResult:
    owner, name = repo.split("/", 1)
    data = gh_pr_comment(owner, name, number, body)
    return CommentResult(ok=bool(data.get("ok")), url=None)


def pr_review(repo: str, number: int, event: str, body: str | None = None) -> CommentResult:
    owner, name = repo.split("/", 1)
    data = gh_pr_review(owner, name, number, event, body)
    return CommentResult(ok=bool(data.get("ok")), url=None)


def pr_merge(repo: str, number: int, method: str = "merge") -> CommentResult:
    owner, name = repo.split("/", 1)
    data = gh_pr_merge(owner, name, number, method)
    return CommentResult(ok=bool(data.get("ok")), url=None)


def issue_list(
    repo: str,
    state: str | None = None,
    author: str | None = None,
    label: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> IssueList:
    owner, name = repo.split("/", 1)
    return IssueList(**gh_issue_list(owner, name, state, author, label, limit, cursor))


def issue_get(repo: str, number: int) -> IssueGet:
    owner, name = repo.split("/", 1)
    data = gh_issue_get(owner, name, number)
    if not data:
        return IssueGet(
            repo=repo, number=number, state=None, title=None, author=None, not_found=True
        )
    return IssueGet(**data)


def issue_comment(repo: str, number: int, body: str) -> CommentResult:
    owner, name = repo.split("/", 1)
    data = gh_issue_comment(owner, name, number, body)
    return CommentResult(ok=bool(data.get("ok")), url=None)
