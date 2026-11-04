"""Configuration management with profile support for VeriCoach QA Framework."""

from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Profile(str, Enum):
    """Execution profile environment."""

    LOCAL = "local"
    CI = "ci"


class FrameworkSettings(BaseSettings):
    """Framework configuration loaded from environment variables and profiles."""

    profile: Profile = Field(
        default=Profile.LOCAL, description="Execution profile (local or ci)"
    )

    # Web & Application Targets
    base_url: str = Field(
        default="http://localhost:8000", description="Base URL under test"
    )
    browser_type: str = Field(
        default="chromium", description="Playwright browser: chromium, firefox, webkit"
    )
    headless: bool = Field(default=True, description="Run browser in headless mode")
    browser_timeout_ms: int = Field(
        default=15000, description="Default timeout for browser actions in ms"
    )

    # Mobile Targets
    mobile_server_url: str = Field(
        default="http://127.0.0.1:4723", description="Appium server endpoint"
    )
    mobile_platform_name: str = Field(
        default="Android", description="Mobile OS platform"
    )
    mobile_platform_version: str = Field(
        default="14.0", description="Android OS version (API 34)"
    )
    mobile_device_name: str = Field(
        default="Pixel 7", description="Device or emulator name"
    )
    mobile_avd_name: str = Field(
        default="Pixel_7_API_34", description="Android virtual device name"
    )
    mobile_app_package: str = Field(
        default="com.vericoach.app", description="Android package name"
    )
    mobile_app_activity: str = Field(
        default="com.vericoach.app.MainActivity", description="Launch activity"
    )
    mobile_app_path: str = Field(
        default="", description="Path to .apk file for automated install"
    )
    mobile_automation_name: str = Field(
        default="UiAutomator2", description="Appium driver engine"
    )
    mobile_auto_grant_permissions: bool = Field(
        default=True, description="Automatically grant Android runtime permissions"
    )
    mobile_no_reset: bool = Field(
        default=True, description="Preserve app state between sessions"
    )
    mobile_new_command_timeout: int = Field(
        default=120, description="Appium command timeout in seconds"
    )

    # Execution & Flakiness Management
    retry_count: int = Field(
        default=1, description="Number of retries for flaky failures"
    )
    retry_delay_seconds: int = Field(
        default=1, description="Backoff delay between retries"
    )
    parallel_workers: str = Field(
        default="auto", description="pytest-xdist workers count or 'auto'"
    )

    # Reporting & Artifacts
    allure_results_dir: Path = Field(
        default=Path("qa/allure-results"),
        description="Path to store Allure raw results",
    )
    triage_output_path: Path = Field(
        default=Path("qa/triage.json"),
        description="Path for failure classification triage JSON",
    )

    # LLM & Synthetic Data Settings
    llm_provider: str = Field(
        default="mock", description="LLM provider: mock, gemini, ollama"
    )
    synthetic_locale: str = Field(
        default="en_IN", description="Default Faker locale for test data"
    )

    model_config = SettingsConfigDict(
        env_prefix="TEST_",
        env_file=(".env", "qa/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("profile", mode="before")
    @classmethod
    def parse_profile(cls, value: Any) -> Profile:
        if isinstance(value, Profile):
            return value
        if isinstance(value, str):
            clean = value.strip().lower()
            if clean in ("ci", "continuous_integration"):
                return Profile.CI
            return Profile.LOCAL
        return Profile.LOCAL

    def model_post_init(self, __context: Any) -> None:
        """Apply profile-specific overrides."""
        if self.profile == Profile.CI:
            # CI profile guarantees headless and robust retry counts
            object.__setattr__(self, "headless", True)
            if self.retry_count < 2:
                object.__setattr__(self, "retry_count", 2)
            # Ensure LLM provider defaults to mock in CI to prevent network access
            if not os.getenv("LLM_PROVIDER"):
                object.__setattr__(self, "llm_provider", "mock")

    def get_appium_capabilities(self) -> dict[str, Any]:
        """Produce W3C Appium capabilities for mobile testing."""
        caps: dict[str, Any] = {
            "platformName": self.mobile_platform_name,
            "appium:automationName": self.mobile_automation_name,
            "appium:deviceName": self.mobile_device_name,
            "appium:appPackage": self.mobile_app_package,
            "appium:appActivity": self.mobile_app_activity,
            "appium:platformVersion": self.mobile_platform_version,
            "appium:autoGrantPermissions": self.mobile_auto_grant_permissions,
            "appium:noReset": self.mobile_no_reset,
            "appium:newCommandTimeout": self.mobile_new_command_timeout,
        }
        if self.mobile_app_path:
            caps["appium:app"] = self.mobile_app_path
        return caps


@lru_cache(maxsize=1)
def get_settings() -> FrameworkSettings:
    """Retrieve singleton framework settings instance."""
    profile_override = os.getenv("TEST_PROFILE", os.getenv("PROFILE", "local")).lower()
    return FrameworkSettings(
        profile=Profile.CI if profile_override == "ci" else Profile.LOCAL
    )


def reset_settings() -> None:
    """Clear cached settings (useful for test profile switches)."""
    get_settings.cache_clear()
