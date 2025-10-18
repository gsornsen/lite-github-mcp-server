from __future__ import annotations

import json
from typing import Any

from lite_github_mcp.services.analytics import compute_tags
from lite_github_mcp.services.cache import get_cache, ttl_for_category
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


# --- Cached GitHub REST helpers (via `gh api`) ---


def _split_headers_body(text: str) -> tuple[dict[str, str], str]:
    # gh api -i prefixes response headers; split once at last blank line
    sep = "\r\n\r\n"
    if sep in text:
        head, body = text.rsplit(sep, 1)
    else:
        head, body = text.rsplit("\n\n", 1) if "\n\n" in text else ("", text)
    headers: dict[str, str] = {}
    if head:
        lines = [ln for ln in head.splitlines() if ln.strip()]
        # Only keep the last header block if multiple HTTP status lines exist
        # Find last index of a line starting with HTTP/
        status_idx = max((i for i, ln in enumerate(lines) if ln.startswith("HTTP/")), default=-1)
        if status_idx >= 0:
            lines = lines[status_idx:]
        for ln in lines[1:]:
            if ":" in ln:
                k, v = ln.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        # Store status code for convenience
        if lines:
            parts = lines[0].split()
            if len(parts) >= 2 and parts[1].isdigit():
                headers[":status"] = parts[1]
    return headers, body


def _api_get_json_cached(path: str, extra_headers: list[str] | None, category: str) -> Any:
    cache = get_cache()
    data_key = f"api:{path}"
    etag_key = f"etag:{path}"
    headers_args: list[str] = [
        "-H",
        "Accept: application/vnd.github+json",
    ]
    # Add If-None-Match when we have a stored etag
    etag = cache.get_etag(etag_key)
    if etag:
        headers_args += ["-H", f"If-None-Match: {etag}"]
    if extra_headers:
        for h in extra_headers:
            headers_args += ["-H", h]

    # Use -i/--include to capture response headers for ETag/304
    res = _run_gh(["api", path, "-i", *headers_args])
    if res.returncode != 0:
        msg = res.stderr.strip() or "gh api error"
        raise RuntimeError(msg)
    hdrs, body_text = _split_headers_body(res.stdout)
    status = int(hdrs.get(":status", "200"))
    if status == 304:
        cached = cache.get_json(data_key)
        return cached if cached is not None else []
    # Parse and cache
    obj = json.loads(body_text) if body_text.strip() else None
    # Capture ETag if available
    etag_value = hdrs.get("etag")
    if etag_value:
        cache.set_etag(etag_key, etag_value)
    cache.set_json(data_key, obj, ttl_for_category(category))
    return obj


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
    path = f"repos/{owner}/{name}/pulls/{number}/files?per_page=100"
    try:
        data = _api_get_json_cached(path, extra_headers=None, category="lists") or []
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
    if ok:
        # Invalidate PR issue timeline endpoints and PR files
        cache = get_cache()
        prefix = f"api:repos/{owner}/{name}/issues/{number}/"
        cache.invalidate_prefix(prefix)
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
    ok = res.returncode == 0
    if ok:
        cache = get_cache()
        cache.invalidate_prefix(f"api:repos/{owner}/{name}/issues/{number}/")
        cache.invalidate_prefix(f"api:repos/{owner}/{name}/pulls/{number}/")
    return {"ok": ok}


def pr_merge(owner: str, name: str, number: int, method: str = "merge") -> dict[str, Any]:
    # method: merge|squash|rebase
    args = ["pr", "merge", str(number), "--repo", f"{owner}/{name}"]
    if method in {"merge", "squash", "rebase"}:
        args += [f"--{method}"]
    res = _run_gh(args)
    ok = res.returncode == 0
    if ok:
        cache = get_cache()
        cache.invalidate_prefix(f"api:repos/{owner}/{name}/issues/{number}/")
        cache.invalidate_prefix(f"api:repos/{owner}/{name}/pulls/{number}/")
    return {"ok": ok}


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
    ok = res.returncode == 0
    if ok:
        cache = get_cache()
        cache.invalidate_prefix(f"api:repos/{owner}/{name}/issues/{number}/")
    return {"ok": ok, "stderr": res.stderr.strip() or None}


def repo_ref_get_remote(owner: str, name: str, ref: str) -> dict[str, Any]:
    # Resolve arbitrary ref for a remote repo via gh api/git ref resolution
    # Try git ref endpoint: /repos/{owner}/{repo}/git/ref/{ref}
    # ref can be heads/main or tags/v1.0 etc. For shorthand, try as heads/ first.
    candidates = [ref]
    if not ref.startswith("heads/") and not ref.startswith("tags/") and ref not in {"HEAD"}:
        candidates = [f"heads/{ref}", f"tags/{ref}", ref]
    for c in candidates:
        try:
            data = _api_get_json_cached(
                f"repos/{owner}/{name}/git/ref/{c}", extra_headers=None, category="meta"
            )
            if isinstance(data, dict):
                obj = data.get("object") or {}
                return {"ref": ref, "sha": obj.get("sha")}
        except RuntimeError:
            continue
    # Fallback: try branches endpoint for HEAD-like resolution
    try:
        if ref in {"HEAD", "head", "default"}:
            repo_meta = (
                _api_get_json_cached(f"repos/{owner}/{name}", extra_headers=None, category="meta")
                or {}
            )
            default_branch = repo_meta.get("default_branch")
            if default_branch:
                br = (
                    _api_get_json_cached(
                        f"repos/{owner}/{name}/branches/{default_branch}",
                        extra_headers=None,
                        category="meta",
                    )
                    or {}
                )
                commit = br.get("commit") or {}
                return {"ref": ref, "sha": (commit.get("sha"))}
    except RuntimeError:
        pass
    return {"ref": ref, "sha": None}


def pr_timeline(
    owner: str,
    name: str,
    number: int,
    limit: int | None,
    cursor: str | None,
    *,
    filter_nulls: bool = False,
) -> dict[str, Any]:
    # Use REST timeline for broad compatibility
    not_found = False
    args = [
        "api",
        f"repos/{owner}/{name}/issues/{number}/timeline?per_page=100",
        "-H",
        "Accept: application/vnd.github+json",
        "-H",
        "Accept: application/vnd.github.mockingbird-preview+json",
    ]
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
    if filter_nulls:
        events = [e for e in events if all(v is not None for v in e.values())]
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
