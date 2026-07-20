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


@app.get('/api/defaults')
def api_defaults() -> fastapi.responses.JSONResponse:
    """Return starting resume data, design, locale and settings."""
    return fastapi.responses.JSONResponse(rendercv_service.get_defaults())


@app.get('/api/themes')
def api_themes() -> fastapi.responses.JSONResponse:
    """Return the list of built-in RenderCV themes."""
    return fastapi.responses.JSONResponse({'themes': rendercv_service.get_themes()})


@app.post('/api/render')
async def api_render(request: fastapi.Request) -> fastapi.responses.Response:
    """Render resume data to a PDF and return it as a downloadable file."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={'detail': 'Invalid JSON body', 'errors': ['Request body must be valid JSON.']},
        )
    if not isinstance(data, dict):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={'detail': 'Invalid payload', 'errors': ['Request body must be a JSON object.']},
        )
    try:
        pdf_bytes = rendercv_service.render_cv(data)
    except rendercv_service.RenderError as exc:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={'detail': 'Validation failed', 'errors': exc.errors},
        )
    except Exception as exc:
        logging.exception(RENDER_FAILED)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'detail': RENDER_FAILED, 'errors': ['An unexpected error occurred.']},
        )

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
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={'detail': 'Invalid JSON body', 'errors': ['Request body must be valid JSON.']},
        )
    if not isinstance(data, dict):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={'detail': 'Invalid payload', 'errors': ['Request body must be a JSON object.']},
        )
    try:
        pdf_bytes = rendercv_service.render_cv(data)
    except rendercv_service.RenderError as exc:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={'detail': 'Validation failed', 'errors': exc.errors},
        )
    except Exception as exc:
        logging.exception('Preview render failed')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'detail': RENDER_FAILED, 'errors': ['An unexpected error occurred.']},
        )
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
