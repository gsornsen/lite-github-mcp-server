from __future__ import annotations

import json
from typing import Any

from lite_github_mcp.services.pager import decode_cursor, encode_cursor
from lite_github_mcp.utils.subprocess import CommandResult, run_command


def gh_installed() -> bool:
    result = run_command(["gh", "--version"])
    return result.returncode == 0


def gh_auth_status() -> dict[str, Any]:
    res = run_command(["gh", "auth", "status"])
    return {"ok": res.returncode == 0, "stderr": res.stderr.strip()}


def _run_gh(args: list[str]) -> CommandResult:
    return run_command(["gh", *args])


def run_gh_json(args: list[str]) -> Any:
    res = _run_gh(args)
    if res.returncode != 0:
        raise RuntimeError(f"gh failed: {' '.join(args)}\n{res.stderr}")
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


def pr_get(owner: str, name: str, number: int) -> dict[str, Any]:
    fields = ["number", "state", "title", "author"]
    args = [
        "pr",
        "view",
        str(number),
        "--repo",
        f"{owner}/{name}",
        "--json",
        ",".join(fields),
    ]
    data = run_gh_json(args) or {}
    return {
        "repo": f"{owner}/{name}",
        "number": data.get("number"),
        "state": data.get("state"),
        "title": data.get("title"),
        "author": data.get("author"),
    }


def pr_timeline(
    owner: str, name: str, number: int, limit: int | None, cursor: str | None
) -> dict[str, Any]:
    query = (
        "query($owner:String!,$name:String!,$number:Int!){"
        "repository(owner:$owner,name:$name){"
        "pullRequest(number:$number){"
        "timelineItems(first:100){nodes{__typename createdAt actor{login}}}"
        "}}}"
    )
    args = [
        "api",
        "graphql",
        "-F",
        f"owner={owner}",
        "-F",
        f"name={name}",
        "-F",
        f"number={number}",
        "-f",
        f"query={query}",
    ]
    data = run_gh_json(args) or {}
    nodes = (
        data.get("data", {})
        .get("repository", {})
        .get("pullRequest", {})
        .get("timelineItems", {})
        .get("nodes", [])
    )
    events: list[dict[str, Any]] = []
    for n in nodes:
        events.append(
            {
                "type": n.get("__typename"),
                "actor": (n.get("actor") or {}).get("login"),
                "createdAt": n.get("createdAt"),
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
    }
