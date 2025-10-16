from __future__ import annotations

import json
from typing import Any

from lite_github_mcp.services.analytics import compute_tags
from lite_github_mcp.services.pager import decode_cursor, encode_cursor
from lite_github_mcp.utils.subprocess import CommandResult, run_command


def gh_installed() -> bool:
    result = run_command(["gh", "--version"])
    return result.returncode == 0


def gh_auth_status() -> dict[str, Any]:
    # First check if gh is installed
    try:
        ver = run_command(["gh", "--version"])
    except Exception:
        ver = CommandResult(args=("gh", "--version"), returncode=127, stdout="", stderr="")
    if ver.returncode != 0:
        return {"ok": False, "error": "gh CLI not installed", "code": "GH_NOT_INSTALLED"}

    res = run_command(["gh", "auth", "status"])
    ok = res.returncode == 0
    # Try to get user and scopes when authed; host is inferred from env or gh config
    user = None
    scopes: list[str] = []
    host = None
    if ok:
        # gh api to check current user and token scopes (best-effort)
        try:
            me = run_gh_json(["api", "user"])
            if me and isinstance(me, dict):
                user = {"login": me.get("login"), "name": me.get("name")}
        except Exception:
            user = None
        # scopes are not directly exposed; leave empty unless GH_TOKEN env exposes it elsewhere
    payload: dict[str, Any] = {"ok": ok, "user": user, "scopes": scopes, "host": host}
    if not ok:
        payload.update(
            {
                "error": (res.stderr.strip() or "gh not authenticated"),
                "code": "GH_NOT_AUTHED",
            }
        )
    return payload


def _run_gh(args: list[str]) -> CommandResult:
    return run_command(["gh", *args])


def run_gh_json(args: list[str]) -> Any:
    res = _run_gh(args)
    if res.returncode != 0:
        # Normalize gh errors into a standard exception with minimal message
        msg = res.stderr.strip() or "gh error"
        raise RuntimeError(msg)
    text = res.stdout.strip()
    if not text:
        return None
    return json.loads(text)


def pr_list(
    owner: str,
    name: str,
    state: str | None,
    author: str | None,
    label: str | None,
    limit: int | None,
    cursor: str | None,
) -> dict[str, Any]:
    fields = ["number", "state", "author", "createdAt"]
    # Normalize state for gh; map "any"/unknown -> "all"
    normalized_state: str | None = None
    if state:
        s = state.lower()
        if s == "any":
            normalized_state = "all"
        elif s in {"open", "closed", "merged", "all"}:
            normalized_state = s
        else:
            normalized_state = "all"

    args = [
        "pr",
        "list",
        "--repo",
        f"{owner}/{name}",
        "--json",
        ",".join(fields),
        "--limit",
        "100",
    ]
    if normalized_state:
        args += ["--state", normalized_state]
    if author:
        args += ["--author", author]
    if label:
        args += ["--label", label]

    try:
        data = run_gh_json(args) or []
    except RuntimeError:
        # Return empty list on invalid filter to avoid noisy errors
        data = []
    items = [int(item.get("number")) for item in data if "number" in item]
    start = decode_cursor(cursor).index
    if start < 0:
        start = 0
    end = start + (limit or len(items))
    page = items[start:end]
    has_next = end < len(items)
    next_cur = encode_cursor(end) if has_next else None
    return {
        "repo": f"{owner}/{name}",
        "filters": {"state": normalized_state or state, "author": author, "label": label},
        "ids": page,
        "count": len(page),
        "has_next": has_next,
        "next_cursor": next_cur,
    }


def pr_get(owner: str, name: str, number: int) -> dict[str, Any]:
    fields = [
        "number",
        "state",
        "title",
        "author",
        "additions",
        "deletions",
        "createdAt",
        "mergedAt",
    ]
    args = [
        "pr",
        "view",
        str(number),
        "--repo",
        f"{owner}/{name}",
        "--json",
        ",".join(fields),
    ]
    try:
        data = run_gh_json(args) or {}
    except RuntimeError:
        return {}
    meta = {
        "repo": f"{owner}/{name}",
        "number": data.get("number"),
        "state": data.get("state"),
        "title": data.get("title"),
        "author": data.get("author"),
        "additions": data.get("additions"),
        "deletions": data.get("deletions"),
        "createdAt": data.get("createdAt"),
        "mergedAt": data.get("mergedAt"),
    }
    meta["tags"] = compute_tags(str(meta.get("title") or ""))
    return meta


def pr_files(
    owner: str, name: str, number: int, limit: int | None, cursor: str | None
) -> dict[str, Any]:
    args = [
        "api",
        f"repos/{owner}/{name}/pulls/{number}/files?per_page=100",
        "-H",
        "Accept: application/vnd.github+json",
    ]
    try:
        data = run_gh_json(args) or []
    except RuntimeError:
        data = []
    files = [
        {
            "path": f.get("filename"),
            "status": f.get("status"),
            "additions": f.get("additions"),
            "deletions": f.get("deletions"),
        }
        for f in data
    ]
    start = decode_cursor(cursor).index
    if start < 0:
        start = 0
    end = start + (limit or len(files))
    page = files[start:end]
    has_next = end < len(files)
    next_cur = encode_cursor(end) if has_next else None
    return {
        "repo": f"{owner}/{name}",
        "number": number,
        "files": page,
        "count": len(page),
        "has_next": has_next,
        "next_cursor": next_cur,
    }


def pr_comment(owner: str, name: str, number: int, body: str) -> dict[str, Any]:
    args = ["pr", "comment", str(number), "--repo", f"{owner}/{name}", "--body", body]
    res = _run_gh(args)
    ok = res.returncode == 0
    return {"ok": ok}


def pr_review(owner: str, name: str, number: int, event: str, body: str | None) -> dict[str, Any]:
    # event: APPROVE | REQUEST_CHANGES | COMMENT
    args = ["pr", "review", str(number), "--repo", f"{owner}/{name}"]
    if event.lower() == "approve":
        args += ["--approve"]
    elif event.lower() in ("request_changes", "request-changes"):
        args += ["--request-changes"]
    else:
        args += ["--comment"]
    if body:
        args += ["--body", body]
    res = _run_gh(args)
    return {"ok": res.returncode == 0}


def pr_merge(owner: str, name: str, number: int, method: str = "merge") -> dict[str, Any]:
    # method: merge|squash|rebase
    args = ["pr", "merge", str(number), "--repo", f"{owner}/{name}"]
    if method in {"merge", "squash", "rebase"}:
        args += [f"--{method}"]
    res = _run_gh(args)
    return {"ok": res.returncode == 0}


def issue_list(
    owner: str,
    name: str,
    state: str | None,
    author: str | None,
    label: str | None,
    limit: int | None,
    cursor: str | None,
) -> dict[str, Any]:
    args = [
        "issue",
        "list",
        "--repo",
        f"{owner}/{name}",
        "--json",
        "number,state,author,title",
        "--limit",
        "100",
    ]
    if state:
        args += ["--state", state]
    if author:
        args += ["--author", author]
    if label:
        args += ["--label", label]
    data = run_gh_json(args) or []
    items = [int(item.get("number")) for item in data if "number" in item]
    start = decode_cursor(cursor).index
    if start < 0:
        start = 0
    end = start + (limit or len(items))
    page = items[start:end]
    has_next = end < len(items)
    next_cur = encode_cursor(end) if has_next else None
    return {
        "repo": f"{owner}/{name}",
        "filters": {"state": state, "author": author, "label": label},
        "ids": page,
        "count": len(page),
        "has_next": has_next,
        "next_cursor": next_cur,
    }


def issue_get(owner: str, name: str, number: int) -> dict[str, Any]:
    args = [
        "issue",
        "view",
        str(number),
        "--repo",
        f"{owner}/{name}",
        "--json",
        "number,state,title,author,body",
    ]
    try:
        data = run_gh_json(args) or {}
    except RuntimeError:
        return {}
    meta = {
        "repo": f"{owner}/{name}",
        "number": data.get("number"),
        "state": data.get("state"),
        "title": data.get("title"),
        "author": data.get("author"),
    }
    meta["tags"] = compute_tags(str(meta.get("title") or ""), str((data.get("body") or "")[:400]))
    return meta


def issue_comment(owner: str, name: str, number: int, body: str) -> dict[str, Any]:
    args = ["issue", "comment", str(number), "--repo", f"{owner}/{name}", "--body", body]
    res = _run_gh(args)
    return {"ok": res.returncode == 0, "stderr": res.stderr.strip() or None}


def pr_timeline(
    owner: str, name: str, number: int, limit: int | None, cursor: str | None
) -> dict[str, Any]:
    # Use REST timeline for broad compatibility
    args = [
        "api",
        f"repos/{owner}/{name}/issues/{number}/timeline?per_page=100",
        "-H",
        "Accept: application/vnd.github+json",
        "-H",
        "Accept: application/vnd.github.mockingbird-preview+json",
    ]
    not_found = False
    try:
        data = run_gh_json(args) or []
    except RuntimeError:
        # Fallback to issue events if timeline preview not available
        events_args = [
            "api",
            f"repos/{owner}/{name}/issues/{number}/events?per_page=100",
            "-H",
            "Accept: application/vnd.github+json",
        ]
        try:
            data = run_gh_json(events_args) or []
        except RuntimeError:
            # Treat missing issue/PR as not_found
            data = []
            not_found = True
    events: list[dict[str, Any]] = []
    for n in data:
        events.append(
            {
                "type": n.get("event"),
                "actor": (n.get("actor") or {}).get("login"),
                "createdAt": n.get("created_at") or n.get("createdAt"),
            }
        )
    start = decode_cursor(cursor).index
    if start < 0:
        start = 0
    end = start + (limit or len(events))
    page = events[start:end]
    has_next = end < len(events)
    next_cur = encode_cursor(end) if has_next else None
    return {
        "repo": f"{owner}/{name}",
        "number": number,
        "events": page,
        "count": len(page),
        "has_next": has_next,
        "next_cursor": next_cur,
        "not_found": not_found,
    }
