"""Pytest configuration and fixtures for Mobile (Appium) automation."""

from __future__ import annotations

import base64
import logging
from collections.abc import Generator
from typing import Any

import pytest

from qa.framework.config import FrameworkSettings, get_settings
from qa.framework.drivers.mock_mobile import MockMobileDriver
from qa.framework.pages.mobile_chat_screen import MobileChatScreen
from qa.framework.reporting.allure_helper import (
    attach_screenshot,
    attach_video,
)

logger = logging.getLogger("vericoach.qa.mobile.conftest")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[Any]
) -> Generator[None, None, None]:
    """Capture test execution outcome for mobile failure artifact capture."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="session")
def mobile_settings() -> FrameworkSettings:
    """Retrieve framework settings with mobile capabilities."""
    return get_settings()


@pytest.fixture(scope="function")
def mobile_driver(
    mobile_settings: FrameworkSettings, request: pytest.FixtureRequest
) -> Generator[Any, None, None]:
    """Appium mobile driver with automatic recording and failure artifact capture."""
    driver: Any = None
    caps = mobile_settings.get_appium_capabilities()

    try:
        import httpx

        # Probe if live Appium server is reachable
        health_resp = httpx.get(
            f"{mobile_settings.mobile_server_url}/status", timeout=1.5
        )
        if health_resp.status_code == 200:
            from appium import webdriver
            from appium.options.android import UiAutomator2Options

            options = UiAutomator2Options().load_capabilities(caps)
            driver = webdriver.Remote(
                mobile_settings.mobile_server_url, options=options
            )
            logger.info("Connected to live Appium 2.x UiAutomator2 server.")
        else:
            raise ConnectionError(f"Appium status HTTP {health_resp.status_code}")
    except Exception as exc:
        logger.info(
            f"Appium server offline or unreachable ({exc}). Falling back to deterministic MockMobileDriver."
        )
        driver = MockMobileDriver(capabilities=caps)

    # Start screen recording before each test
    try:
        if hasattr(driver, "start_recording_screen"):
            driver.start_recording_screen()
    except Exception as exc:
        logger.debug(f"Unable to start screen recording: {exc}")

    try:
        yield driver
    finally:
        # Check if test failed
        test_failed = False
        rep_call = getattr(request.node, "rep_call", None)
        rep_setup = getattr(request.node, "rep_setup", None)
        if (rep_call and rep_call.failed) or (rep_setup and rep_setup.failed):
            test_failed = True

        # Capture failure screenshot and screen recording on failure
        if test_failed and driver is not None:
            try:
                # 1. Failure Screenshot
                screenshot_bytes = b""
                if hasattr(driver, "get_screenshot_as_png"):
                    screenshot_bytes = driver.get_screenshot_as_png()
                elif hasattr(driver, "get_screenshot_as_base64"):
                    screenshot_bytes = base64.b64decode(
                        driver.get_screenshot_as_base64()
                    )

                if screenshot_bytes:
                    attach_screenshot(
                        screenshot_bytes,
                        name=f"mobile_failure_{request.node.name}",
                    )
            except Exception as exc:
                logger.debug(f"Failed to capture failure screenshot: {exc}")

            try:
                # 2. Failure Screen Recording
                if hasattr(driver, "stop_recording_screen"):
                    b64_video = driver.stop_recording_screen()
                    if b64_video:
                        video_bytes = base64.b64decode(b64_video)
                        attach_video(
                            video_bytes,
                            name=f"mobile_failure_recording_{request.node.name}",
                        )
            except Exception as exc:
                logger.debug(f"Failed to capture failure video recording: {exc}")
        else:
            # Test passed: stop recording without attaching large video
            try:
                if hasattr(driver, "stop_recording_screen"):
                    driver.stop_recording_screen()
            except Exception:
                pass

        # Cleanup: restore orientation and network if altered
        if driver is not None:
            try:
                if (
                    hasattr(driver, "orientation")
                    and str(driver.orientation).upper() != "PORTRAIT"
                ):
                    driver.orientation = "PORTRAIT"
            except Exception:
                pass

            try:
                if (
                    hasattr(driver, "set_network_connection")
                    and getattr(driver, "network_connection", 6) != 6
                ):
                    driver.set_network_connection(6)  # ALL_NETWORK_ON
            except Exception:
                pass

            if hasattr(driver, "quit"):
                try:
                    driver.quit()
                except Exception:
                    pass


@pytest.fixture(scope="function")
def mobile_chat_screen(mobile_driver: Any) -> MobileChatScreen:
    """Pre-initialized MobileChatScreen object with readiness check."""
    screen = MobileChatScreen(driver=mobile_driver)
    assert screen.is_chat_ready(
        timeout_s=10.0
    ), "Mobile chat interface failed to initialize"
    return screen
