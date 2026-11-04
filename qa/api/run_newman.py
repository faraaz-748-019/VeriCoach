"""Runner script to execute Newman against live FastAPI backend with htmlextra reporter."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
QA_DIR = ROOT_DIR / "qa"
REPORT_DIR = QA_DIR / "newman-reports"
REPORT_FILE = REPORT_DIR / "newman_report.html"
COLLECTION_FILE = QA_DIR / "api" / "vericoach.postman_collection.json"
ENV_FILE = QA_DIR / "api" / "vericoach_ci.postman_environment.json"


def wait_for_server(
    url: str = "http://127.0.0.1:8000/v1/health", timeout: float = 15.0
) -> bool:
    """Poll health endpoint until server is ready or timeout expires."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = httpx.get(url, timeout=1.0)
            if resp.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def run_newman(env_path: Path | None = None, port: int = 8000) -> int:
    """Launch uvicorn server, execute Newman suite, and generate htmlextra report."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    env_file = env_path or ENV_FILE

    server_env = os.environ.copy()
    server_env["LLM_PROVIDER"] = "mock"
    server_env["REQUIRE_API_KEY"] = "true"
    server_env["PYTHONPATH"] = str(ROOT_DIR / "app")

    python_exe = sys.executable

    print(f"Starting VeriCoach backend on 127.0.0.1:{port}...")
    server_proc = subprocess.Popen(
        [
            python_exe,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=str(ROOT_DIR / "app"),
        env=server_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        health_url = f"http://127.0.0.1:{port}/v1/health"
        if not wait_for_server(health_url, timeout=15.0):
            print("ERROR: Backend server failed to start within timeout.")
            if server_proc.poll() is not None:
                _, stderr = server_proc.communicate()
                print("Server output:", stderr.decode("utf-8", errors="replace"))
            return 1

        print("Backend server is healthy. Executing Newman suite...")

        newman_cmd = [
            "npx",
            "--prefix",
            str(QA_DIR),
            "newman",
            "run",
            str(COLLECTION_FILE),
            "-e",
            str(env_file),
            "--env-var",
            f"baseUrl=http://127.0.0.1:{port}",
            "-r",
            "cli,htmlextra",
            "--reporter-htmlextra-export",
            str(REPORT_FILE),
        ]

        # Use shell=True on Windows to find npx.cmd
        newman_res = subprocess.run(
            newman_cmd,
            shell=sys.platform == "win32",
            cwd=str(QA_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        print(newman_res.stdout)
        if newman_res.stderr:
            print("Newman stderr:", newman_res.stderr)

        if REPORT_FILE.exists():
            print(f"Newman htmlextra report generated at: {REPORT_FILE}")

        return newman_res.returncode
    finally:
        print("Shutting down backend server...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            server_proc.kill()


if __name__ == "__main__":
    code = run_newman()
    sys.exit(code)
