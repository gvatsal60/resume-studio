top_dir := `git rev-parse --show-toplevel`
src     := top_dir / "src"
target  := top_dir / "target"

resume   := src / "resume.yaml"
design   := src / "design.yaml"
locale   := src / "locale.yaml"
settings := src / "settings.yaml"

# Default recipe
default: clean sync build

# Sync dependencies using uv
sync:
    @uv sync --no-cache

watch:
    @uv run rendercv render --watch \
        --design {{design}} \
        --locale-catalog {{locale}} \
        --settings {{settings}} \
        --output-folder "{{target}}" \
        --dont-generate-html \
        --dont-generate-markdown \
        --dont-generate-png \
        {{resume}}

build:
    @uv run rendercv render \
        --design "{{design}}" \
        --locale-catalog "{{locale}}" \
        --settings "{{settings}}" \
        --output-folder "{{target}}" \
        --dont-generate-html \
        --dont-generate-markdown \
        --dont-generate-png \
        "{{resume}}"

web:
    @uv run fastapi dev

deploy:
    @uv run fastapi deploy

test:
    @uv run pytest tests

coverage:
    @uv run pytest tests --cov=backend --cov-report=term-missing --cov-report=html
    @echo "HTML report: file://$(pwd)/htmlcov/index.html"

clean:
    @uv clean
    @rm -rf target/ __pycache__ .pytest_cache .mypy_cache .venv rendercv_output htmlcov
