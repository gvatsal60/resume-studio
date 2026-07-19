# RenderCV Local

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/gvatsal60/rendercv-local/master.svg)](https://results.pre-commit.ci/latest/github/gvatsal60/rendercv-local/HEAD)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/412f34a844b148dfa277c16b2bec6316)](https://app.codacy.com/gh/gvatsal60/rendercv-local/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![CodeFactor](https://www.codefactor.io/repository/github/gvatsal60/rendercv-local/badge)](https://www.codefactor.io/repository/github/gvatsal60/rendercv-local)
![GitHub pull-requests](https://img.shields.io/github/issues-pr/gvatsal60/rendercv-local)
![GitHub Issues](https://img.shields.io/github/issues/gvatsal60/rendercv-local)
![GitHub forks](https://img.shields.io/github/forks/gvatsal60/rendercv-local)
![GitHub stars](https://img.shields.io/github/stars/gvatsal60/rendercv-local)

Generate professional, beautifully formatted CVs from **YAML** configuration files. Version control your resume, iterate with live preview, export to PDF and Markdown.

## ⚡ Quick Start

### 🐳 Using Dev Container (1 min setup)

```bash
git clone https://github.com/gvatsal60/rendercv-local.git
cd rendercv-local
code .
```

→ Click **"Reopen in Container"** when prompted → Done! ✅

### 📦 Local Setup

```bash
git clone https://github.com/gvatsal60/rendercv-local.git
cd rendercv-local
pip install -e .
```

## 🚀 Build Commands

```bash
just              # Clean, sync, and build (frontend + backend)
just build        # Render CV with frontend build
just watch        # Live preview (auto-reload on save)
just web          # Start production server with built frontend
just deploy       # Deploy to FastAPI Cloud
just --list       # See all commands
```

Output: **PDF** + **Markdown** files in current directory

## 🌐 Web App

A no-login web UI to fill in your résumé and download a polished PDF (powered by RenderCV).

### Local Development

```bash
uv sync                       # install deps (fastapi + rendercv)
cd src/frontend && npm ci     # install frontend deps
PYTHONPATH=src uv run uvicorn backend.main:app --reload --port 8000
```

Open <http://127.0.0.1:8000>. The form pre-fills from `src/backend/conf/*.yaml`. Pick a theme,
page size, and accent color, then **Update preview** to see the live PDF and
**Download PDF** to save it. No account required.

- `GET  /api/defaults` — starter `cv` / `design` / `locale` / `settings`
- `GET  /api/themes`  — available RenderCV themes
- `POST /api/preview` — returns a PDF for inline preview
- `POST /api/render`  — returns a PDF as a download

### Production Deployment (FastAPI Cloud)

This app is configured for deployment on [FastAPI Cloud](https://fastapicloud.com).

**Prerequisites:**
- FastAPI Cloud account
- Repository connected to GitHub

**Setup:**

1. Set the **Application Directory** to `src/backend` in the FastAPI Cloud dashboard
2. Configure environment variables:
   ```bash
   fastapi cloud env set APP_ENV "production"
   fastapi cloud env set LOG_LEVEL "warning"
   ```
3. Add GitHub secrets for CI/CD:
   - `FASTAPI_CLOUD_TOKEN` — your FastAPI Cloud deploy token
   - `FASTAPI_CLOUD_APP_ID` — your app ID from FastAPI Cloud

**Deploy:**

```bash
just deploy    # builds frontend and deploys to FastAPI Cloud
```

Or push to `main` — the GitHub Actions workflow will automatically build the frontend and deploy.

**Frontend Build:**

The frontend is built with Vite. The production build outputs to `dist/`, which is served by FastAPI in production. The `dist/` directory is git-ignored but un-ignored for deployment via `.fastapicloudignore`.

## 📁 File Structure

```text
src/
├── frontend/          # Web UI (HTML/CSS/JS)
└── backend/
    ├── main.py        # FastAPI app
    ├── rendercv_service.py  # RenderCV integration
    └── conf/
        ├── resume.yaml    # Your CV content
        ├── design.yaml    # Colors, fonts, margins, theme
        ├── locale.yaml    # Language & date formatting
        └── settings.yaml  # App configuration
```

## ✨ Features

- 📝 **YAML-based** - Easy to edit and version control
- 🎨 **Customizable themes** - Multiple professional designs
- 👀 **Live preview** - See changes as you type (`just watch`)
- 📄 **Multi-format export** - PDF + Markdown
- 🌍 **Localization** - Support for multiple languages
- 🐳 **Dev Container** - Pre-configured environment with all extensions

## 🔧 Dev Container Includes

Python 3.13 • RenderCV • PDF Preview • Python Extension • YAML Support • Ruff Linter • Spell Checker • Error Lens

## 📚 Configuration

**resume.yaml** - Personal info, experience, education, skills, projects
**design.yaml** - Theme, colors, typography, margins
**locale.yaml** - Language, date format, translations
**settings.yaml** - App settings

👉 [Full RenderCV docs](https://sinaatalay.github.io/rendercv/)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## 📄 License

Apache 2.0 - See [LICENSE](LICENSE)
