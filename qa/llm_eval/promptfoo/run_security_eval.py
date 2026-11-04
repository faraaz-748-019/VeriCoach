"""Security Evaluation Runner for VeriCoach using Promptfoo.

Executes adversarial security test suite covering:
1. Direct prompt injection
2. Jailbreaks
3. PII extraction & leakage
4. Hijacking (off-topic queries)
5. Harmful financial advice
6. Hallucination & guaranteed returns claims

Generates:
- results/promptfoo_security_report.html
- results/promptfoo_security_results.json
- Console table of Attack Success Rate (ASR) by category
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("promptfoo_security_eval")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "qa" / "llm_eval" / "promptfoo" / "promptfooconfig.yaml"
ENTRYPOINT_PATH = (
    PROJECT_ROOT
    / "qa"
    / "node_modules"
    / "promptfoo"
    / "dist"
    / "src"
    / "entrypoint.js"
)
RESULTS_DIR = PROJECT_ROOT / "results"
JSON_OUTPUT = RESULTS_DIR / "promptfoo_security_results.json"
HTML_OUTPUT = RESULTS_DIR / "promptfoo_security_report.html"

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
HEALTH_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}/v1/health"


def is_server_healthy() -> bool:
    """Check if the backend server is responding to health requests."""
    try:
        req = urllib.request.Request(HEALTH_URL, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            return resp.status == 200
    except Exception:
        return False


def wait_for_server(timeout_sec: float = 20.0) -> bool:
    """Poll health endpoint until server is ready or timeout expires."""
    start = time.time()
    while time.time() - start < timeout_sec:
        if is_server_healthy():
            return True
        time.sleep(0.5)
    return False


def run_promptfoo_eval() -> int:
    """Run promptfoo CLI via Node.js with local sandbox environment."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["PROMPTFOO_DISABLE_TELEMETRY"] = "true"
    env["PROMPTFOO_CONFIG_DIR"] = str(PROJECT_ROOT / "qa" / ".promptfoo")
    env["PROMPTFOO_CACHE_DIR"] = str(PROJECT_ROOT / "qa" / ".promptfoo" / "cache")
    env["PYTHONPATH"] = str(PROJECT_ROOT / "app")

    (PROJECT_ROOT / "qa" / ".promptfoo" / "cache").mkdir(parents=True, exist_ok=True)

    cmd = [
        "node",
        str(ENTRYPOINT_PATH),
        "eval",
        "-c",
        str(CONFIG_PATH),
        "-o",
        str(JSON_OUTPUT),
        "-o",
        str(HTML_OUTPUT),
        "--no-cache",
    ]

    logger.info("Executing promptfoo security eval...")
    proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env, capture_output=False)
    return proc.returncode


def generate_asr_summary_table() -> dict[str, Any]:
    """Parse promptfoo JSON results and compute Attack Success Rate (ASR) by threat category."""
    if not JSON_OUTPUT.is_file():
        logger.error(f"Results file not found: {JSON_OUTPUT}")
        return {}

    with open(JSON_OUTPUT, encoding="utf-8") as f:
        data = json.load(f)

    # Parse results list from promptfoo results JSON
    raw_results = data.get("results", {})
    test_results = raw_results.get("results", [])
    if not test_results and isinstance(raw_results, list):
        test_results = raw_results

    category_stats: dict[str, dict[str, int]] = {}

    for item in test_results:
        test_case = item.get("testCase", {})
        metadata = test_case.get("metadata", {}) or item.get("metadata", {}) or {}
        category = metadata.get("category", "unclassified")

        if category not in category_stats:
            category_stats[category] = {
                "total": 0,
                "defended": 0,
                "successful_attack": 0,
            }

        category_stats[category]["total"] += 1
        success = bool(item.get("success", False))

        if success:
            category_stats[category]["defended"] += 1
        else:
            category_stats[category]["successful_attack"] += 1

    # Print Formatted Table
    print("\n" + "=" * 80)
    print("VERICOACH AI SECURITY EVALUATION — ATTACK SUCCESS RATE (ASR) BY CATEGORY")
    print("=" * 80)
    print(
        f"{'Category':<28} | {'Total Attacks':<13} | {'Defended':<10} | {'Breached':<10} | {'ASR (%)':<8}"
    )
    print("-" * 80)

    total_attacks = 0
    total_breaches = 0

    for cat, stats in sorted(category_stats.items()):
        total = stats["total"]
        defended = stats["defended"]
        breaches = stats["successful_attack"]
        asr = (breaches / total * 100.0) if total > 0 else 0.0
        total_attacks += total
        total_breaches += breaches
        print(
            f"{cat:<28} | {total:<13} | {defended:<10} | {breaches:<10} | {asr:>6.1f}%"
        )

    print("-" * 80)
    overall_asr = (total_breaches / total_attacks * 100.0) if total_attacks > 0 else 0.0
    print(
        f"{'OVERALL':<28} | {total_attacks:<13} | {total_attacks - total_breaches:<10} | {total_breaches:<10} | {overall_asr:>6.1f}%"
    )
    print("=" * 80)
    print(f"HTML Report generated at: {HTML_OUTPUT}")
    print(f"JSON Results generated at: {JSON_OUTPUT}\n")

    return {
        "categories": category_stats,
        "total_attacks": total_attacks,
        "total_breaches": total_breaches,
        "overall_asr": overall_asr,
    }


def main() -> None:
    server_process: subprocess.Popen[bytes] | None = None
    started_server = False

    try:
        if not is_server_healthy():
            logger.info(
                "Backend server not running. Starting uvicorn instance on port 8000..."
            )
            backend_env = os.environ.copy()
            backend_env["LLM_PROVIDER"] = "mock"
            backend_env["REQUIRE_API_KEY"] = "false"
            backend_env["PYTHONPATH"] = str(PROJECT_ROOT / "app")

            server_cmd = [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.main:app",
                "--host",
                BACKEND_HOST,
                "--port",
                str(BACKEND_PORT),
                "--log-level",
                "warning",
            ]
            server_process = subprocess.Popen(
                server_cmd,
                cwd=str(PROJECT_ROOT / "app"),
                env=backend_env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            started_server = True

            if not wait_for_server(timeout_sec=15.0):
                logger.error("Failed to start backend server within 15 seconds.")
                sys.exit(1)
            logger.info("Backend server started successfully.")
        else:
            logger.info("Backend server is already running and healthy.")

        run_promptfoo_eval()
        generate_asr_summary_table()

    finally:
        if started_server and server_process is not None:
            logger.info("Shutting down background backend server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                server_process.kill()


if __name__ == "__main__":
    main()
