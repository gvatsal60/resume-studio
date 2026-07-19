# Résumé Studio

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/gvatsal60/rendercv-local/master.svg)](https://results.pre-commit.ci/latest/github/gvatsal60/rendercv-local/HEAD)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/412f34a844b148dfa277c16b2bec6316)](https://app.codacy.com/gh/gvatsal60/rendercv-local/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![Quality gate status](https://sonarcloud.io/api/project_badges/measure?project=gvatsal60_resume-studio&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=gvatsal60_resume-studio)
![GitHub pull-requests](https://img.shields.io/github/issues-pr/gvatsal60/rendercv-local)
![GitHub Issues](https://img.shields.io/github/issues/gvatsal60/rendercv-local)
![GitHub forks](https://img.shields.io/github/forks/gvatsal60/rendercv-local)
![GitHub stars](https://img.shields.io/github/stars/gvatsal60/rendercv-local)

Generate professional, beautifully formatted CVs from **YAML** configuration files. Version control your resume, iterate with live preview, and export to PDF.

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
uv sync
```

## 🚀 Build Commands

```bash
just           # Clean, sync, and build
just build     # Render your CV (PDF only)
just watch     # Live preview (auto-reload on save)
just web       # Start the web UI
just --list    # See all commands
```

Output: **PDF** in `rendercv_output/`

## 🌐 Web App

A no-login web UI to fill in your résumé and download a polished PDF (powered by RenderCV).

```bash
just web       # Start the web UI (FastAPI dev server)
```

Open <http://127.0.0.1:8000>. The form pre-fills from `src/*.yaml`. Pick a theme
and accent color, then **Update preview** to see the live PDF and
**Download PDF** to save it. No account required.

- `GET  /api/defaults` — starter `cv` / `design` / `locale` / `settings`
- `GET  /api/themes`  — available RenderCV themes
- `POST /api/preview` — returns a PDF for inline preview
- `POST /api/render`  — returns a PDF as a download

## 📁 File Structure

```text
.
├── backend/
│   ├── main.py            # FastAPI app & API routes
│   └── rendercv_service.py # RenderCV rendering logic
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── src/
│   ├── resume.yaml        # Your CV content
│   ├── design.yaml        # Colors, fonts, margins, theme
│   ├── locale.yaml        # Language & date formatting
│   └── settings.yaml      # App configuration
├── tests/
│   ├── api_test.py
│   ├── frontend_test.py
│   └── conftest.py
├── justfile               # Command runner recipes
├── pyproject.toml
└── README.md
```

## ✨ Features

- 📝 **YAML-based** - Easy to edit and version control
- 🎨 **Customizable themes** - Multiple professional designs
- 👀 **Live preview** - See changes as you type (`just watch`)
- 📄 **PDF export** - Polished output via RenderCV
- 🌍 **Localization** - Support for multiple languages
- 🐳 **Dev Container** - Pre-configured environment with all extensions

## 🔧 Dev Container Includes

Python 3.13 • RenderCV • PDF Preview • Ty • Python Extension • YAML Support • Ruff Linter • Spell Checker • Error Lens

## 📚 Configuration

**resume.yaml** - Personal info, experience, education, skills, projects
**design.yaml** - Theme, colors, typography, margins
**locale.yaml** - Language, date format, translations
**settings.yaml** - App settings

👉 [Full RenderCV docs](https://sinaatalay.github.io/rendercv/)

## 🙏 Special Thanks

This project is built on top of **[RenderCV](https://github.com/sinaatalay/rendercv)**, created by **Sina Atalay**.

RenderCV is released under the **[MIT License](https://github.com/sinaatalay/rendercv/blob/main/LICENSE)**.
Copyright (c) 2023 to present Sina Atalay and individual contributors.

We are grateful for the excellent tooling and themes RenderCV provides.

## 🤝 Contributing

Open an issue or pull request on GitHub.

## 📄 License

Apache 2.0 - See [LICENSE](LICENSE)
