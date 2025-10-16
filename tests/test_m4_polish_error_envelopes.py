from __future__ import annotations

from typing import Any

import pytest

from lite_github_mcp.tools import router


def test_base_path_validation_error(tmp_path: Any) -> None:
    with pytest.raises(ValueError):
        router.file_tree(repo_path=str(tmp_path), ref="HEAD", base_path="/etc", limit=1)


def test_limit_validation_error(tmp_path: Any) -> None:
    with pytest.raises(ValueError):
        router.file_tree(repo_path=str(tmp_path), ref="HEAD", limit=0)
