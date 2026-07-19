"""Backend API tests (no browser required)."""
# codeql[python/assert-used]

from __future__ import annotations

import httpx


def _render(base_url: str, payload: dict) -> httpx.Response:
    return httpx.post(f"{base_url}/api/render", json=payload, timeout=30)


def _preview(base_url: str, payload: dict) -> httpx.Response:
    return httpx.post(f"{base_url}/api/preview", json=payload, timeout=30)


def test_themes_endpoint(base_url: str):
    r = httpx.get(f"{base_url}/api/themes")
    assert r.status_code == 200
    themes = r.json()['themes']
    assert isinstance(themes, list) and len(themes) >= 5
    assert 'engineeringresumes' in themes
    assert 'classic' in themes


def test_defaults_shape(base_url: str):
    r = httpx.get(f"{base_url}/api/defaults")
    assert r.status_code == 200
    data = r.json()
    for key in ('cv', 'design', 'locale', 'settings'):
        assert key in data
    assert 'sections' in data['cv']


def test_render_defaults(base_url: str, defaults: dict):
    r = _render(base_url, defaults)
    assert r.status_code == 200
    assert r.headers['content-type'] == 'application/pdf'
    assert r.content[:4] == b'%PDF'
    assert len(r.content) > 1000


def test_preview_defaults(base_url: str, defaults: dict):
    r = _preview(base_url, defaults)
    assert r.status_code == 200
    assert r.content[:4] == b'%PDF'


def test_render_invalid_email(base_url: str, defaults: dict):
    payload = defaults
    payload['cv']['email'] = 'not-an-email'
    r = _render(base_url, payload)
    assert r.status_code == 422
    body = r.json()
    assert 'errors' in body
    assert any('email' in e.lower() for e in body['errors'])


def test_render_invalid_phone(base_url: str, defaults: dict):
    payload = defaults
    payload['cv']['phone'] = '123'  # not a valid phone number
    r = _render(base_url, payload)
    assert r.status_code == 422
    assert any('phone' in e.lower() for e in r.json()['errors'])


def test_render_theme_override(base_url: str, defaults: dict):
    payload = defaults
    payload['design'] = {
        'theme': 'moderncv',
        'page': {'size': 'a4', 'show_footer': False, 'show_top_note': False},
        'colors': {
            'section_titles': '#e11d48',
            'links': '#e11d48',
            'connections': '#e11d48',
        },
    }
    r = _render(base_url, payload)
    assert r.status_code == 200
    assert r.content[:4] == b'%PDF'


def test_render_a4_page(base_url: str, defaults: dict):
    payload = defaults
    payload['design']['page']['size'] = 'a4'
    r = _render(base_url, payload)
    assert r.status_code == 200


def test_render_empty_cv(base_url: str):
    payload = {
        'cv': {'name': None, 'email': None, 'social_networks': [], 'sections': {}},
        'design': {
            'theme': 'classic',
            'page': {'size': 'a4', 'show_footer': False, 'show_top_note': False},
            'colors': {
                'section_titles': '#4f46e5',
                'links': '#4f46e5',
                'connections': '#4f46e5',
            },
        },
        'locale': {'language': 'english'},
        'settings': {},
    }
    r = _render(base_url, payload)
    assert r.status_code == 200


def test_render_long_skills_details_wraps(base_url: str):
    long_details = 'Python, Go, Rust, TypeScript, Kubernetes, Docker, Terraform, ' * 8
    payload = {
        'cv': {
            'name': 'Wrap Test',
            'email': 'a@b.com',
            'sections': {'Skills': [{'label': 'Programming', 'details': long_details}]},
        },
        'design': {
            'theme': 'engineeringresumes',
            'page': {'size': 'a4', 'show_footer': False, 'show_top_note': False},
            'colors': {
                'section_titles': '#4f46e5',
                'links': '#4f46e5',
                'connections': '#4f46e5',
            },
        },
        'locale': {'language': 'english'},
        'settings': {},
    }
    r = _render(base_url, payload)
    assert r.status_code == 200
    assert r.content[:4] == b'%PDF'


def test_static_assets(base_url: str):
    for path in ('/', '/app.js', '/styles.css'):
        r = httpx.get(f"{base_url}{path}")
        assert r.status_code == 200, path
    assert 'Resume Studio' in httpx.get(f"{base_url}/").text


def test_header_pill_controls(base_url: str):
    html = httpx.get(f"{base_url}/").text
    assert html.count('<label class="pill">') == 2
    assert '<div class="pill">' in html
    assert 'Format</span>' in html
    assert 'Theme</span>' in html
    assert 'Accent</span>' in html
    assert '<label class="toggle">' in html
    assert 'id="preview-btn"' in html
    assert 'id="download-btn"' in html


def test_render_missing_cv(base_url: str, defaults: dict):
    payload = defaults
    payload.pop('cv', None)
    r = _render(base_url, payload)
    assert r.status_code == 200
    assert r.content[:4] == b'%PDF'


def test_render_missing_design(base_url: str, defaults: dict):
    payload = defaults
    payload.pop('design', None)
    r = _render(base_url, payload)
    assert r.status_code == 422
    assert 'errors' in r.json()


def test_render_invalid_theme_name(base_url: str, defaults: dict):
    payload = defaults
    payload['design'] = {
        'theme': 'does_not_exist',
        'page': {'size': 'a4', 'show_footer': False, 'show_top_note': False},
        'colors': {
            'section_titles': '#4f46e5',
            'links': '#4f46e5',
            'connections': '#4f46e5',
        },
    }
    r = _render(base_url, payload)
    assert r.status_code == 422
    assert 'errors' in r.json()


def test_render_invalid_page_size(base_url: str, defaults: dict):
    payload = defaults
    payload['design']['page']['size'] = 'tabloid'
    r = _render(base_url, payload)
    assert r.status_code == 422
    assert 'errors' in r.json()


def test_render_invalid_color_format(base_url: str, defaults: dict):
    payload = defaults
    payload['design']['colors']['section_titles'] = 'not-a-color'
    r = _render(base_url, payload)
    assert r.status_code == 422
    assert 'errors' in r.json()


def test_render_empty_sections(base_url: str, defaults: dict):
    payload = defaults
    payload['cv']['sections'] = {}
    r = _render(base_url, payload)
    assert r.status_code == 200
    assert r.content[:4] == b'%PDF'


def test_render_null_required_fields(base_url: str):
    payload = {
        'cv': {'name': None, 'email': None, 'phone': None, 'social_networks': [], 'sections': {}},
        'design': {
            'theme': 'classic',
            'page': {'size': 'a4', 'show_footer': False, 'show_top_note': False},
            'colors': {
                'section_titles': '#4f46e5',
                'links': '#4f46e5',
                'connections': '#4f46e5',
            },
        },
        'locale': {'language': 'english'},
        'settings': {},
    }
    r = _render(base_url, payload)
    assert r.status_code == 200


def test_preview_missing_payload(base_url: str):
    r = httpx.post(f"{base_url}/api/preview", json={}, timeout=30)
    assert r.status_code == 422


def test_render_malformed_json(base_url: str):
    r = httpx.post(
        f"{base_url}/api/render",
        content='{bad json',
        headers={'Content-Type': 'application/json'},
        timeout=30,
    )
    assert r.status_code == 422


def test_defaults_endpoint_has_required_keys(base_url: str):
    r = httpx.get(f"{base_url}/api/defaults")
    assert r.status_code == 200
    data = r.json()
    cv = data['cv']
    for key in ('name', 'email', 'phone', 'social_networks', 'sections'):
        assert key in cv, f"missing cv.{key}"
    design = data['design']
    for key in ('theme', 'page', 'colors'):
        assert key in design, f"missing design.{key}"
    assert 'language' in data['locale']


def test_render_with_extremely_long_field(base_url: str, defaults: dict):
    payload = defaults
    payload['cv']['name'] = 'X' * 10000
    r = _render(base_url, payload)
    assert r.status_code == 422
    body = r.json()
    assert 'errors' in body
