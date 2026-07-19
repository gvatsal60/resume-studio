"""FastAPI application for the local resume builder."""

from __future__ import annotations

import pathlib

import fastapi
from fastapi import status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from backend import rendercv_service
from backend.config import settings

app = fastapi.FastAPI(title="Resume Studio", version="1.0.0")

DIST_DIR = pathlib.Path(__file__).resolve().parent.parent / "dist"
FRONTEND_DIR = pathlib.Path(__file__).resolve().parent.parent / "frontend"
CONF_DIR = pathlib.Path(__file__).resolve().parent / "conf"

if settings.frontend_dist:
    DIST_DIR = pathlib.Path(settings.frontend_dist)


def _frontend_dir() -> pathlib.Path:
    return DIST_DIR if DIST_DIR.is_dir() else FRONTEND_DIR


@app.get("/api/defaults")
def api_defaults() -> fastapi.responses.JSONResponse:
    """Return starting resume data, design, locale and settings."""
    return fastapi.responses.JSONResponse(rendercv_service.get_defaults())


@app.get("/api/themes")
def api_themes() -> fastapi.responses.JSONResponse:
    """Return the list of built-in RenderCV themes."""
    return fastapi.responses.JSONResponse({"themes": rendercv_service.get_themes()})


def _safe_name(name: str) -> str:
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in name).strip()
    return (safe_name or "Resume").replace(" ", "_")


def _render_pdf(data: dict) -> tuple[bytes, dict | None]:
    try:
        return rendercv_service.render_cv(data), None
    except rendercv_service.RenderError as exc:
        return None, {"detail": "Validation failed", "errors": exc.errors}
    except Exception as exc:
        return None, {"detail": "Render failed", "errors": [str(exc)]}


def _error_response(errors: list[str] | str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": detail, "errors": errors if isinstance(errors, list) else [errors]},
    )


async def _parse_request(request: fastapi.Request) -> dict | JSONResponse:
    try:
        data = await request.json()
    except Exception:
        return _error_response(["Request body must be valid JSON."], "Invalid JSON body")
    if not isinstance(data, dict):
        return _error_response(["Request body must be a JSON object."], "Invalid payload")
    return data


def _pdf_response(pdf_bytes: bytes, download: bool, data: dict) -> fastapi.responses.Response:
    headers = {"Content-Disposition": 'inline'} if not download else {
        "Content-Disposition": f'attachment; filename="{_safe_name((data.get("cv") or {}).get("name") or "Resume")}.pdf"'
    }
    return fastapi.responses.Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=headers,
    )


async def _render_endpoint(request: fastapi.Request, download: bool) -> fastapi.responses.Response:
    data = await _parse_request(request)
    if isinstance(data, JSONResponse):
        return data
    pdf_bytes, error_body = _render_pdf(data)
    if error_body:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_body,
        )
    return _pdf_response(pdf_bytes, download=download, data=data)


@app.post("/api/render")
async def api_render(request: fastapi.Request) -> fastapi.responses.Response:
    """Render resume data to a PDF and return it as a downloadable file."""
    return await _render_endpoint(request, download=True)


@app.post("/api/preview")
async def api_preview(request: fastapi.Request) -> fastapi.responses.Response:
    """Render resume data to a PDF for inline preview (no download)."""
    return await _render_endpoint(request, download=False)


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str) -> fastapi.responses.Response:
    """Serve the single-page frontend and its static assets."""
    base = _frontend_dir()
    requested = base / full_path
    if full_path and requested.is_file():
        return FileResponse(requested)

    index = base / "index.html"
    return HTMLResponse(index.read_text(encoding="utf-8"))
