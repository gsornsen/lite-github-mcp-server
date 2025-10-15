# Examples

Copyable CLI examples for testing the MCP server.

- Tools listing
  - `just cli_tools`

- File tree paging
  - `just cli_call gh.file.tree '{"repo_path": ".", "ref": "HEAD", "limit": 3}'`
  - `just cli_call gh.file.tree '{"repo_path": ".", "ref": "HEAD", "limit": 3, "cursor": "<next>"}'`

- Search paging
  - `just cli_call gh.search.files '{"repo_path": ".", "pattern": "FastMCP", "limit": 2}'`

- Blob ranges
  - `just cli_call gh.file.blob '{"repo_path": ".", "blob_sha": "<sha>", "max_bytes": 128, "offset": 0}'`

- PRs
  - `just cli_call gh.pr.list '{"repo": "gsornsen/lite-github-mcp-server", "state": "open", "limit": 10}'`
  - `just cli_call gh.pr.get '{"repo": "gsornsen/lite-github-mcp-server", "number": 3}'`
  - `just cli_call gh.pr.timeline '{"repo": "gsornsen/lite-github-mcp-server", "number": 3, "limit": 5}'`
  - `just cli_call gh.pr.files '{"repo": "gsornsen/lite-github-mcp-server", "number": 3, "limit": 10}'`
  - `just cli_call gh.pr.comment '{"repo": "gsornsen/lite-github-mcp-server", "number": 3, "body": "Thanks!"}'`
  - `just cli_call gh.pr.review '{"repo": "gsornsen/lite-github-mcp-server", "number": 3, "event": "approve", "body": "LGTM"}'`
  - `just cli_call gh.pr.merge '{"repo": "gsornsen/lite-github-mcp-server", "number": 3, "method": "squash"}'`

- Issues
  - `just cli_call gh.issue.list '{"repo": "gsornsen/lite-github-mcp-server", "state": "open", "limit": 10}'`
  - `just cli_call gh.issue.get '{"repo": "gsornsen/lite-github-mcp-server", "number": 3}'`
  - `just cli_call gh.issue.comment '{"repo": "gsornsen/lite-github-mcp-server", "number": 3, "body": "Following up"}'`
