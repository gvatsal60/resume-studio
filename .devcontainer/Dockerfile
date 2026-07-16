FROM mcr.microsoft.com/devcontainers/python:latest

ENV ANONYMIZED_TELEMETRY=false \
  DEBIAN_FRONTEND=noninteractive \
  PIP_NO_CACHE_DIR=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  STREAMLIT_BROWSER_GATHERUSAGESTATS=false \
  UV_LINK_MODE=copy

USER vscode

RUN pip install --no-cache-dir \
  playwright \
  python-dateutil \
  just \
  uv && \
  python -m playwright install chromium && \
  python -m playwright install-deps chromium && \
  sudo apt-get autoremove -y && \
  sudo apt-get clean -y && \
  sudo rm -rf /var/lib/apt/lists/* /tmp/*
