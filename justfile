src := "src"
build_dir := "build"

resume   := src / "resume.yaml"
design   := src / "design.yaml"
locale   := src / "locale.yaml"
settings := src / "settings.yaml"

# Default recipe (runs when you just type 'just')
all: clean sync build

# Sync dependencies using uv
sync:
    @uv sync --no-cache

watch:
    @uv run rendercv render --watch \
      --design {{design}} \
      --locale-catalog {{locale}} \
      --settings {{settings}} \
      --dont-generate-markdown \
      --dont-generate-html \
      --dont-generate-png \
      {{resume}}

build:
    @uv run rendercv render \
      --design {{design}} \
      --locale-catalog {{locale}} \
      --settings {{settings}} \
      --dont-generate-markdown \
      --dont-generate-html \
      --dont-generate-png \
      {{resume}}

clean:
    @uv clean
    @rm -rf __pycache__ .pytest_cache .mypy_cache .venv rendercv_output
