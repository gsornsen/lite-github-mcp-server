from __future__ import annotations

from pydantic import BaseModel


class PRList(BaseModel):
    repo: str
    filters: dict[str, str | None]
    ids: list[int]
    count: int
    has_next: bool = False
    next_cursor: str | None = None


class PRGet(BaseModel):
    repo: str
    number: int | None
    state: str | None
    title: str | None
    author: dict[str, object] | None


class PRTimeline(BaseModel):
    repo: str
    number: int
    events: list[dict[str, object]]
    count: int
    has_next: bool = False
    next_cursor: str | None = None
