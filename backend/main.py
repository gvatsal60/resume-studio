"""FastAPI application for the local resume builder."""

from __future__ import annotations

import logging
import pathlib

import fastapi
from fastapi import status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from backend import rendercv_service

app = fastapi.FastAPI(title='Resume Builder', version='1.0.0')

FRONTEND_DIR = pathlib.Path(__file__).resolve().parent.parent / 'frontend'
RENDER_FAILED = 'Render failed'


def _json_error(status_code: int, detail: str, errors: list[str]) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={'detail': detail, 'errors': errors},
    )


async def _parse_json_body(request: fastapi.Request) -> tuple[dict | None, JSONResponse | None]:
    try:
        data = await request.json()
    except Exception:
        return None, _json_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            'Invalid JSON body',
            ['Request body must be valid JSON.'],
        )
    if not isinstance(data, dict):
        return None, _json_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            'Invalid payload',
            ['Request body must be a JSON object.'],
        )
    return data, None


def _render_pdf(data: dict) -> tuple[bytes | None, JSONResponse | None]:
    try:
        return rendercv_service.render_cv(data), None
    except rendercv_service.RenderError as exc:
        return None, _json_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            'Validation failed',
            exc.errors,
        )
    except Exception:
        logging.exception(RENDER_FAILED)
        return None, _json_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            RENDER_FAILED,
            ['An unexpected error occurred.'],
        )


@app.get('/api/defaults')
def api_defaults() -> fastapi.responses.JSONResponse:
    """Return starting resume data, design, locale and settings."""
    return fastapi.responses.JSONResponse(rendercv_service.get_defaults())


@app.get('/api/themes')
def api_themes() -> fastapi.responses.JSONResponse:
    """Return the list of built-in RenderCV themes."""
    return fastapi.responses.JSONResponse({'themes': rendercv_service.get_themes()})


async def _render_from_request(request: fastapi.Request) -> tuple[dict, bytes] | JSONResponse:
    data, err = await _parse_json_body(request)
    if err:
        return err
    if data is None:
        return _json_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            RENDER_FAILED,
            ['Unexpected null data.'],
        )
    pdf_bytes, err = _render_pdf(data)
    if err:
        return err
    return data, pdf_bytes


@app.post('/api/render')
async def api_render(request: fastapi.Request) -> fastapi.responses.Response:
    """Render resume data to a PDF and return it as a downloadable file."""
    result = await _render_from_request(request)
    if isinstance(result, JSONResponse):
        return result
    data, pdf_bytes = result
    name = (data.get('cv') or {}).get('name') or 'Resume'
    safe_name = ''.join(c if c.isalnum() or c in ' -_' else '_' for c in name).strip()
    filename = f"{safe_name or 'Resume'}.pdf".replace(' ', '_')

    return fastapi.responses.Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@app.post('/api/preview')
async def api_preview(request: fastapi.Request) -> fastapi.responses.Response:
    """Render resume data to a PDF for inline preview (no download)."""
    result = await _render_from_request(request)
    if isinstance(result, JSONResponse):
        return result
    _, pdf_bytes = result
    return fastapi.responses.Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': 'inline'},
    )


@app.get('/{full_path:path}')
async def serve_frontend(full_path: str) -> fastapi.responses.Response:
    """Serve the single-page frontend and its static assets."""
    normalized_path = pathlib.PurePosixPath(full_path)
    if normalized_path.is_absolute() or '..' in normalized_path.parts:
        index = FRONTEND_DIR / 'index.html'
        return HTMLResponse(index.read_text(encoding='utf-8'))
    requested = (FRONTEND_DIR / pathlib.Path(*normalized_path.parts)).resolve()
    if (
        full_path
        and requested.is_file()
        and (requested == FRONTEND_DIR or FRONTEND_DIR in requested.parents)
    ):
        return FileResponse(requested)

    index = FRONTEND_DIR / 'index.html'
    return HTMLResponse(index.read_text(encoding='utf-8'))
