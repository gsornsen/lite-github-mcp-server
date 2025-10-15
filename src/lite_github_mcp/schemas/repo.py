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
