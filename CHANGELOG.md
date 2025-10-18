## v0.2.0 (2025-10-18)

### Feat

- **timeline,tests**: add filter_nulls for PR timeline; test ETag+invalidation
- **cache+errors**: add diskcache-backed cache with ETag and error envelopes
- **analytics**: add context tokage usage and gates
- **m4**: standardize gh error envelopes; tests updated
- **m4**: invalid regex returns 0 matches; update checklist state
- **m4**: add PR files/actions and Issues list/get/comment; wire fuzzy tags
- **analytics**: add rapidfuzz for lightweight fuzzy matching
- **m3**: add gh_cli service and PR schemas; expose pr.list/get/timeline
- **paging**: add has_next/next_cursor to list endpoints; blob next_offset
- **files/search**: add limit and base_path validation; tests
- **cli**: add local CLI to exercise MCP tools
- **m2**: add git_cli service and repo/file tools
- **scaffold**: milestone 1 scaffolding, health tools, CI, Docker, tests

### Fix

- **m4**: robust tree parsing; blob not_found; search validation
- **m4**: PR timeline not_found; whoami auth shape; enforce file_tree limit>=1
- **pr.get**: return not_found=true for missing PR numbers; avoid exceptions
- **pr/issues**: normalize invalid states to 'all'; return empty on gh errors; reduce stderr noise
- **pr.timeline**: use query param for per_page and add preview header; fallback to issue events
- **tests**: update timeline test to match REST shape
- **cli**: register tools at import-time for embedded client
- **cli**: add typer to runtime dependencies
- **tests**: handle unborn HEAD case in repo_resolve test

### Refactor

- **tests**: consolidate m4_polish tests into existing suites

### Perf

- **search**: prefer ripgrep when available, fallback to git grep
