# ADR 0001: Mono-tool Router Default

## Status
Accepted

## Context
Agent platforms often preload the full tool registry. Large numbers of tools with verbose descriptions bloat context and increase latency.

## Decision
Adopt a mono-tool router (tool name `gh`) with a subcommand enum as the default. Provide a multi-tool mode (`repo.*`, `pr.*`, `issue.*`, `file.*`) as an opt-in alternative.

## Consequences
- Smaller registry JSON, faster startup for agents
- Centralized routing; consistent parameter patterns
- Clear mapping to grouped tools if needed

## Alternatives considered
- Multi-tool by default: rejected due to context budget concerns.
