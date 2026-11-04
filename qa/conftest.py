"""Root pytest configuration and lifecycle hooks for the VeriCoach QA Platform.

Implements:
1. Reusable fixtures registration (api_client, browser_page, mobile_driver, synthetic data)
2. Retry policy logging (intercepts pytest-rerunfailures and logs the failure reason for each retry)
3. Automated failure triage engine (classifies failures into assertion, timeout, network,
   element-not-found, environment and dumps triage.json at session end)
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import pytest

# Ensure mock provider is used for zero-network execution during test runs
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("EMBEDDING_PROVIDER", "mock")
os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")

from qa.framework.config import get_settings
from qa.framework.fixtures import *  # noqa: F403
from qa.framework.reporting.allure_helper import attach_text
from qa.framework.reporting.triager import FailureClassifier, TriageReport

logger = logging.getLogger("vericoach.qa.conftest")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# Global session triage accumulator
_SESSION_TRIAGE = TriageReport()


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add framework command-line arguments to pytest."""
    group = parser.getgroup("vericoach", "VeriCoach QA Framework Options")
    group.addoption(
        "--profile",
        action="store",
        default="local",
        help="Test execution profile: local, ci",
    )
    group.addoption(
        "--triage-file",
        action="store",
        default="triage.json",
        help="Target output file path for failure triage JSON",
    )
    group.addoption(
        "--subset",
        action="store",
        nargs="?",
        const="6",
        default=None,
        help="Fast CI evaluation subset: run only N samples (default 6 when flagged)",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Configure markers and environment before test execution."""
    profile_arg = config.getoption("--profile", default="local")
    os.environ["TEST_PROFILE"] = profile_arg

    # Register custom markers to avoid warnings
    markers = [
        "smoke: Critical smoke tests",
        "regression: Full regression test cases",
        "api: REST API endpoint tests",
        "web: Playwright web UI tests",
        "mobile: Appium mobile automation tests",
        "llm: LLM evaluation and prompt tests",
        "security: Security and PII compliance tests",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Intercept test execution reports for retry policy logging and failure triage."""
    # 1. Rerun Logging Policy (pytest-rerunfailures integration)
    if hasattr(report, "outcome") and report.outcome == "rerun":
        rerun_idx = getattr(report, "rerun", 1)
        reason = "Unknown failure during attempt"
        if report.longrepr:
            reason = str(report.longrepr).splitlines()[-1]

        retry_msg = (
            f"\n🔄 [RETRY POLICY] Test '{report.nodeid}' failed on attempt #{rerun_idx}."
            f"\n   Reason: {reason}"
            f"\n   Action: Rerunning test according to flakiness policy...\n"
        )
        sys.stderr.write(retry_msg)
        logger.warning(retry_msg)
        attach_text(retry_msg, name=f"Retry #{rerun_idx} - {report.nodeid}")

    # 2. Failure Triage Collection
    # Collect only final failures (when test actually failed after all retries)
    if report.failed and report.when in ("call", "setup"):
        # If pytest-rerunfailures is active, check if this is a final failure or intermediate
        exc_type = None
        message = ""
        traceback_str = ""

        if report.longrepr:
            longrepr_str = str(report.longrepr)
            traceback_str = longrepr_str
            lines = longrepr_str.strip().splitlines()
            if lines:
                message = lines[-1]
                # Try to extract exception type e.g. "AssertionError: ..."
                if ":" in message:
                    exc_type = message.split(":")[0].strip()

        rerun_count = getattr(report, "rerun", 0)

        record = FailureClassifier.classify(
            nodeid=report.nodeid,
            exc_type=exc_type,
            message=message,
            traceback=traceback_str,
            reruns=rerun_count,
        )
        _SESSION_TRIAGE.add_failure(record)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Generate triage.json report upon test session completion."""
    # In pytest-xdist runs, only write on the master process
    if hasattr(session.config, "workerinput"):
        return

    settings = get_settings()
    triage_file = session.config.getoption("--triage-file", default=None)
    output_path = (
        Path(triage_file) if triage_file else Path(settings.triage_output_path)
    )

    # Persist the failure triage JSON
    written_path = _SESSION_TRIAGE.write_json(output_path)

    # Output clean console summary
    summary = _SESSION_TRIAGE.to_dict()["summary"]
    total = summary["total_failures"]
    cats = summary["by_category"]

    summary_banner = (
        f"\n=========================== TRIAGE REPORT ===========================\n"
        f"Total Failures: {total}\n"
        f"  • Assertion:         {cats.get('assertion', 0)}\n"
        f"  • Timeout:           {cats.get('timeout', 0)}\n"
        f"  • Network:           {cats.get('network', 0)}\n"
        f"  • Element Not Found: {cats.get('element-not-found', 0)}\n"
        f"  • Environment:       {cats.get('environment', 0)}\n"
        f"Report Written To: {written_path.resolve()}\n"
        f"=====================================================================\n"
    )
    sys.stdout.write(summary_banner)
    logger.info(f"Triage report written to {written_path.resolve()}")
