src := "src"
backend := src / "backend"
frontend := src / "frontend"
conf := backend / "conf"

resume   := conf / "resume.yaml"
design   := conf / "design.yaml"
locale   := conf / "locale.yaml"
settings := conf / "settings.yaml"

# Default recipe (runs when you just type 'just')
all: clean sync build test

# Sync dependencies using uv
sync:
    @uv sync --no-cache

# Install frontend dependencies
frontend-sync:
    @cd {{frontend}} && npm ci || echo "npm not found, skipping frontend sync"

# Build frontend for production
frontend-build: frontend-sync
    @cd {{frontend}} && npm run build || echo "npm not found, skipping frontend build"

watch: sync
    @uv run rendercv render --watch \
      --design {{design}} \
      --locale-catalog {{locale}} \
      --settings {{settings}} \
      --dont-generate-markdown \
      --dont-generate-html \
      --dont-generate-png \
      {{resume}}

build: sync frontend-build
    @uv run rendercv render \
      --design {{design}} \
      --locale-catalog {{locale}} \
      --settings {{settings}} \
      --dont-generate-markdown \
      --dont-generate-html \
      --dont-generate-png \
      {{resume}}

web-debug: sync
    @PYTHONPATH=src uv run uvicorn backend.main:app --reload --port 8001

web: sync
    @PYTHONPATH=src uv run uvicorn backend.main:app --port 50000

deploy: sync frontend-build
    @uv run fastapi deploy

test:
    @uv run pytest tests

clean:
    @uv clean
    @rm -rf __pycache__ .pytest_cache .mypy_cache .venv rendercv_output dist
