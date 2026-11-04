"""Pytest configuration and fixtures for Playwright Web UI testing."""

from __future__ import annotations

import os
import socket
import threading
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import httpx
import pytest
import uvicorn
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

# Zero-network LLM configuration for deterministic CI tests
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "mock"

from qa.framework.config import FrameworkSettings
from qa.framework.pages.web_chat_page import WebChatPage
from qa.framework.reporting.allure_helper import (
    attach_playwright_trace,
)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[Any]
) -> Generator[None, None, None]:
    """Hook capturing test execution outcome for failure trace retention."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


def _is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def _wait_for_server(url: str, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = httpx.get(f"{url}/v1/health", timeout=1.0)
            if resp.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


@pytest.fixture(scope="session")
def web_server_url() -> str:
    """Session fixture ensuring backend and frontend web server is alive."""
    port = int(os.environ.get("VERICOACH_TEST_PORT", "8000"))
    base_url = f"http://127.0.0.1:{port}"

    if _is_port_in_use(port) or _wait_for_server(base_url, timeout=1.0):
        if _wait_for_server(base_url, timeout=15.0):
            return base_url

    # In parallel pytest-xdist runs, synchronize server startup with a file lock
    from filelock import FileLock

    lock_file = Path("qa/.web_server.lock")
    with FileLock(str(lock_file), timeout=30):
        if _wait_for_server(base_url, timeout=1.0):
            return base_url

        from backend.main import app as fastapi_app

        config = uvicorn.Config(
            app=fastapi_app,
            host="127.0.0.1",
            port=port,
            log_level="warning",
            loop="asyncio",
        )
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()

        if not _wait_for_server(base_url, timeout=20.0):
            raise RuntimeError(f"FastAPI/Frontend server failed to start at {base_url}")

    return base_url


@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Any, None, None]:
    """Session-scoped Playwright runtime."""
    with sync_playwright() as pw:
        yield pw


@pytest.fixture(scope="session")
def browser(
    playwright_instance: Any, framework_settings: FrameworkSettings
) -> Generator[Browser, None, None]:
    """Session-scoped headless Chromium browser instance."""
    browser_instance = playwright_instance.chromium.launch(
        headless=framework_settings.headless,
        timeout=framework_settings.browser_timeout_ms,
    )
    yield browser_instance
    browser_instance.close()


@pytest.fixture(scope="function")
def context(
    browser: Browser,
    request: pytest.FixtureRequest,
    tmp_path: Path,
) -> Generator[BrowserContext, None, None]:
    """Browser context with active tracing; retains traces strictly on failure."""
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 800},
        locale="en-US",
    )
    # Start tracing with screenshots, snapshots, and sources
    ctx.tracing.start(screenshots=True, snapshots=True, sources=True)

    yield ctx

    # Determine if test failed
    test_failed = False
    rep_call = getattr(request.node, "rep_call", None)
    if rep_call and rep_call.failed:
        test_failed = True

    traces_dir = Path("qa/traces")
    traces_dir.mkdir(parents=True, exist_ok=True)
    trace_path = traces_dir / f"trace_{request.node.name}.zip"

    if test_failed:
        try:
            ctx.tracing.stop(path=str(trace_path))
            if trace_path.exists():
                attach_playwright_trace(trace_path, name=f"trace-{request.node.name}")
        except Exception:
            pass
    else:
        # Discard trace without writing to disk if passed
        try:
            ctx.tracing.stop()
        except Exception:
            pass

    ctx.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """Function-scoped Playwright page."""
    pg = context.new_page()
    yield pg
    pg.close()


@pytest.fixture(scope="function")
def chat_page(page: Page, web_server_url: str) -> WebChatPage:
    """Pre-initialized WebChatPage object pointing to test web server."""
    return WebChatPage(page=page, base_url=web_server_url)
