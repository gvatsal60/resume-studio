"""Shared pytest fixtures: a live FastAPI server and a Playwright browser."""

from __future__ import annotations

import httpx
import pytest
import subprocess
import pathlib
import time

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEST_PORT = 8011
LOG_FILE = ROOT / 'tests' / 'server.log'

BASE_URL = f"http://127.0.0.1:{TEST_PORT}"


def _wait_for_port_free(port: int, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with httpx.get(f"http://127.0.0.1:{port}/api/themes", timeout=0.5) as r:
                if r.status_code == 200:
                    time.sleep(0.2)
                    continue
        except Exception:
            return
        time.sleep(0.2)
    raise RuntimeError(f"Port {port} is already in use by another process.")


@pytest.fixture(scope='session')
def base_url():
    _wait_for_port_free(TEST_PORT)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log = LOG_FILE.open('w', encoding='utf-8')
    proc = subprocess.Popen(
        [
            'uv', 'run', 'uvicorn', 'backend.main:app',
            '--host', '127.0.0.1', f"--port={TEST_PORT}",
        ],
        cwd=str(ROOT),
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )

    ready = False
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            if httpx.get(f"{BASE_URL}/api/themes", timeout=2).status_code == 200:
                ready = True
                break
        except Exception:
            time.sleep(0.5)
    if not ready:
        proc.terminate()
        raise RuntimeError('Test server failed to start; see tests/server.log')

    yield BASE_URL

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        proc.kill()


@pytest.fixture(scope='session')
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=[
                '--no-sandbox',
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--disable-software-rasterizer',
                '--disable-extensions',
            ]
        )
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(accept_downloads=True)
    pg = context.new_page()
    yield pg
    context.close()


@pytest.fixture
def defaults(base_url):
    """Return the starter CV payload from the API."""
    return httpx.get(f"{base_url}/api/defaults").json()
