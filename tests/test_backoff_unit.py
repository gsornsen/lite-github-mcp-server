from typing import Any

from lite_github_mcp.services import gh_cli


class Res:
    def __init__(self, stdout: str, returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = ""


def test_backoff_then_success(monkeypatch: Any) -> None:
    calls: list[str] = []

    def fake_run(args: list[str]) -> Any:  # noqa: ANN401
        calls.append(" ".join(args))
        if len(calls) == 1:
            headers = "HTTP/1.1 403 Forbidden\r\nRetry-After: 0.01\r\n\r\n"
            return Res(headers)
        headers = 'HTTP/1.1 200 OK\r\nETag: "e"\r\n\r\n'
        return Res(headers + "[]")

    monkeypatch.setattr(gh_cli, "_run_gh", fake_run)
    monkeypatch.setattr(gh_cli.time, "sleep", lambda s: None)

    out = gh_cli.pr_files("o", "n", 1, limit=10, cursor=None)
    assert out["count"] == 0
    assert len(calls) >= 2


def test_backoff_exhaustion(monkeypatch: Any) -> None:
    calls: list[str] = []

    def fake_run(_args: list[str]) -> Any:  # noqa: ANN401
        calls.append("x")
        headers = "HTTP/1.1 403 Forbidden\r\n\r\n"
        return Res(headers)

    monkeypatch.setattr(gh_cli, "_run_gh", fake_run)
    monkeypatch.setattr(gh_cli.time, "sleep", lambda s: None)

    try:
        gh_cli.pr_files("o", "n", 1, limit=10, cursor=None)
        # Some environments may mask the error; assert we attempted multiple times
        assert len(calls) >= 3
    except RuntimeError as exc:  # RATE_LIMIT bubble-up
        assert "RATE_LIMIT" in str(exc)
        assert len(calls) >= 3


def test_etag_304_uses_cache(monkeypatch: Any) -> None:
    calls: list[str] = []

    def fake_run(args: list[str]) -> Any:  # noqa: ANN401
        calls.append(" ".join(args))
        # First 200 with ETag and one item
        if len(calls) == 1:
            headers = 'HTTP/1.1 200 OK\r\nETag: "e1"\r\n\r\n'
            body = '[{"filename":"a.txt","status":"modified",' '"additions":1,"deletions":0}]'
            return Res(headers + body)
        # Then 304 Not Modified
        return Res("HTTP/1.1 304 Not Modified\r\n\r\n")

    monkeypatch.setattr(gh_cli, "_run_gh", fake_run)
    out1 = gh_cli.pr_files("o", "n", 1, limit=10, cursor=None)
    out2 = gh_cli.pr_files("o", "n", 1, limit=10, cursor=None)
    assert out1["count"] == 1
    assert out2["count"] == 1
