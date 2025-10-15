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
	# Prefer Procfile-based orchestration for clean start/stop
	uv run honcho start -f Procfile

cli:
	uv run lite-github-mcp-cli --help


cli_tools:
	uv run lite-github-mcp-cli tools


cli_call name args:
	# Example: just cli-call gh.ping '{}'
	uv run lite-github-mcp-cli call {{name}} --args '{{args}}'

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
