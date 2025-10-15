from __future__ import annotations

from pydantic import BaseModel


class IssueList(BaseModel):
    repo: str
    filters: dict[str, str | None]
    ids: list[int]
    count: int
    has_next: bool = False
    next_cursor: str | None = None


class IssueGet(BaseModel):
    repo: str
    number: int | None
    state: str | None
    title: str | None
    author: dict[str, object] | None


class CommentResult(BaseModel):
    ok: bool
    url: str | None = None
