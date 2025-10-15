from lite_github_mcp.services.pager import decode_cursor, encode_cursor


def test_pager_encode_decode_basic() -> None:
    cur = encode_cursor(5, filters={"k": "v"})
    decoded = decode_cursor(cur)
    assert decoded.index == 5
    assert decoded.filters == {"k": "v"}


def test_pager_invalid_cursor_returns_zero() -> None:
    decoded = decode_cursor("not-base64!!")
    assert decoded.index == 0
    assert decoded.filters == {}


def test_pager_start_beyond_length_is_ok() -> None:
    cur = encode_cursor(10)
    decoded = decode_cursor(cur)
    assert decoded.index == 10
