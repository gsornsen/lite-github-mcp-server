set shell := ["bash", "-lc"]

PY := "uv run"

# Bootstrap
default: build

setup:
	uv sync --dev
	uv run pre-commit install --install-hooks

fmt:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff check .

typecheck:
	uv run mypy src tests

test:
	uv run pytest -q

# Affected tests using testmon cache
test_changed:
	uv run pytest --testmon -q

run:
	uv run python -m lite_github_mcp.server

build:
	uv build

precommit:
	uv run pre-commit run --all-files

ci:
	just fmt lint typecheck test

release:
	uv run cz bump --changelog

whoami:
	gh auth status || true

# Docker
docker_build:
	docker build -t lite-github-mcp:dev -f docker/Dockerfile .

compose_up:
	docker compose up --build -d

compose_down:
	docker compose down
