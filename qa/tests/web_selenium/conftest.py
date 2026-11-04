"""Pytest configuration and fixtures for Selenium cross-browser smoke tests."""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Generator
from pathlib import Path

import httpx
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

# Zero-network LLM configuration for deterministic CI tests
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "mock"

from qa.framework.reporting.allure_helper import attach_screenshot


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
    """Session fixture ensuring web server is alive."""
    port = int(os.environ.get("VERICOACH_TEST_PORT", "8000"))
    base_url = f"http://127.0.0.1:{port}"

    if _wait_for_server(base_url, timeout=1.5):
        return base_url

    from filelock import FileLock

    lock_file = Path("qa/.web_server.lock")
    with FileLock(str(lock_file), timeout=30):
        if _wait_for_server(base_url, timeout=1.0):
            return base_url

        import uvicorn
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
            raise RuntimeError(f"Server failed to start at {base_url}")

    return base_url


def _find_firefox_binary() -> str | None:
    """Locate Firefox executable from system PATH or Playwright cache."""
    candidates = [
        Path(os.environ.get("FIREFOX_BIN", "")),
        Path(
            r"C:\Users\Acer\AppData\Local\ms-playwright\firefox-1555\firefox\firefox.exe"
        ),
        Path(r"C:\Program Files\Mozilla Firefox\firefox.exe"),
        Path(r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"),
    ]
    for p in candidates:
        if p and p.exists():
            return str(p)
    # Search AppData ms-playwright dynamically
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        pw_dir = Path(local_appdata) / "ms-playwright"
        if pw_dir.exists():
            matches = list(pw_dir.glob("firefox-*/firefox/firefox.exe"))
            if matches:
                return str(matches[0])
    return None


@pytest.fixture(params=["chrome", "firefox"], scope="function")
def driver(request: pytest.FixtureRequest) -> Generator[webdriver.Remote, None, None]:
    """Cross-browser WebDriver fixture supporting Chrome and Firefox headless."""
    browser_name = request.param
    drv: webdriver.Remote | None = None

    if browser_name == "chrome":
        options = ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280,800")
        drv = webdriver.Chrome(options=options)

    elif browser_name == "firefox":
        options = FirefoxOptions()
        options.add_argument("-headless")
        options.add_argument("--width=1280")
        options.add_argument("--height=800")
        ff_bin = _find_firefox_binary()
        if ff_bin:
            options.binary_location = ff_bin
        drv = webdriver.Firefox(options=options)

    else:
        raise ValueError(f"Unsupported browser: {browser_name}")

    # Set script timeout and zero implicit wait to strictly enforce explicit waits
    drv.set_page_load_timeout(20.0)
    drv.implicitly_wait(0.0)

    try:
        yield drv
    finally:
        if drv:
            try:
                # Capture screenshot on failure for Allure
                screenshot = drv.get_screenshot_as_png()
                attach_screenshot(screenshot, name=f"selenium_{browser_name}_teardown")
            except Exception:
                pass
            drv.quit()
