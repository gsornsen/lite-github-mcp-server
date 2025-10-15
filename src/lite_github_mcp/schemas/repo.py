from __future__ import annotations

from pydantic import BaseModel


class BranchList(BaseModel):
    repo: str
    prefix: str | None = None
    names: list[str]


class TreeEntry(BaseModel):
    path: str
    blob_sha: str


class TreeList(BaseModel):
    repo: str
    ref: str
    base_path: str | None = None
    entries: list[TreeEntry]


class BlobResult(BaseModel):
    blob_sha: str
    size: int
    encoding: str = "base64"
    content_b64: str
    offset: int = 0
    fetched: int


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
