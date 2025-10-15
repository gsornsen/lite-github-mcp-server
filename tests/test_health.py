from lite_github_mcp.tools.router import ping


def test_ping_ok() -> None:
    result = ping()
    assert result["ok"] is True
    assert result["version"] == "0.1.0"
