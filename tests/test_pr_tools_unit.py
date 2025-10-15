from lite_github_mcp.schemas.pr import PRGet, PRList, PRTimeline


def test_pr_schemas_construction() -> None:
    pr_list = PRList(repo="o/n", filters={"state": "open"}, ids=[1, 2], count=2, has_next=False)
    assert pr_list.ids == [1, 2]
    pr_get = PRGet(repo="o/n", number=1, state="OPEN", title="t", author={"login": "me"})
    assert pr_get.number == 1
    pr_timeline = PRTimeline(repo="o/n", number=1, events=[{"type": "X"}], count=1, has_next=False)
    assert pr_timeline.count == 1
