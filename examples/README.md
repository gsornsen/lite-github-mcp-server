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
