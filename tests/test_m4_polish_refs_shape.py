from __future__ import annotations

import pytest

from lite_github_mcp.tools import router


def test_repo_refs_requires_exactly_one_selector(tmp_path):  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError):
        router.repo_refs_get(ref="HEAD")  # neither provided
    with pytest.raises(ValueError):
        router.repo_refs_get(repo_path=str(tmp_path), ref="HEAD", repo="o/n")  # both provided


def test_repo_refs_owner_name_supported(monkeypatch):  # type: ignore[no-untyped-def]
    # Mock remote resolution
    def fake_repo_ref_get_remote(owner: str, name: str, ref: str) -> dict[str, str | None]:
        assert (owner, name, ref) == ("o", "n", "main")
        return {"ref": ref, "sha": "abc123"}

    monkeypatch.setattr(router, "repo_ref_get_remote", fake_repo_ref_get_remote)
    out = router.repo_refs_get(ref="main", repo="o/n")
    assert out.ref == "main"
    assert out.sha == "abc123"


def test_repo_refs_repo_path_ok(tmp_path):  # type: ignore[no-untyped-def]
    out = router.repo_refs_get(repo_path=str(tmp_path), ref="HEAD")
    assert out.ref == "HEAD"
