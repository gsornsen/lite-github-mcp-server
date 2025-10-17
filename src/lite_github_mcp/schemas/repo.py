from __future__ import annotations

from pydantic import BaseModel


class BranchList(BaseModel):
    repo: str
    prefix: str | None = None
    names: list[str]
    count: int
    has_next: bool = False
    next_cursor: str | None = None


class TreeEntry(BaseModel):
    path: str
    blob_sha: str


class TreeList(BaseModel):
    repo: str
    ref: str
    base_path: str | None = None
    entries: list[TreeEntry]
    count: int
    has_next: bool = False
    next_cursor: str | None = None


class BlobResult(BaseModel):
    blob_sha: str
    size: int  # number of bytes returned (fetched)
    encoding: str = "base64"
    content_b64: str
    offset: int = 0
    fetched: int
    total_size: int
    has_next: bool = False
    next_offset: int | None = None
    not_found: bool = False


class RepoResolve(BaseModel):
    repo_path: str
    origin_url: str | None
    owner: str | None
    name: str | None
    default_branch: str | None
    head: str | None


class RefResolve(BaseModel):
    repo_path: str
    ref: str
    sha: str | None


class SearchMatch(BaseModel):
    path: str
    line: int
    excerpt: str


class SearchResult(BaseModel):
    repo: str
    pattern: str
    matches: list[SearchMatch]
    count: int
    has_next: bool = False
    next_cursor: str | None = None
