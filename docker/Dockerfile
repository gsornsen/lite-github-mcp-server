# syntax=docker/dockerfile:1.6
FROM ghcr.io/astral-sh/uv:python3.13-bookworm AS base

# OS deps + git + gh CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates && \
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | \
      dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
    chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list && \
    apt-get update && apt-get install -y gh && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md /app/
# Install deps only (no dev) to keep image lean
RUN uv sync --no-dev --frozen || true

# Copy source
COPY src /app/src

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_SYSTEM_PYTHON=1

CMD ["uv", "run", "python", "-m", "lite_github_mcp.server"]
