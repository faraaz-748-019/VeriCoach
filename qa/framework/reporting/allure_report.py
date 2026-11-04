"""Allure HTML Report Generator script supporting local, CI, and Docker workflows."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def generate_allure_report(
    results_dir: str | Path = "qa/allure-results",
    output_dir: str | Path = "qa/allure-report",
) -> int:
    """Generate HTML Allure report from test run raw artifacts."""
    results_path = Path(results_dir)
    output_path = Path(output_dir)

    if not results_path.exists():
        sys.stderr.write(
            f"Results directory '{results_path}' does not exist. Run tests first.\n"
        )
        return 1

    # Check for native allure binary
    allure_bin = shutil.which("allure")
    if allure_bin:
        cmd = [
            allure_bin,
            "generate",
            str(results_path),
            "-o",
            str(output_path),
            "--clean",
        ]
    else:
        # Fallback to npx allure-commandline (bundled with Node)
        npx_bin = shutil.which("npx") or shutil.which("npx.cmd")
        if npx_bin:
            cmd = [
                npx_bin,
                "allure-commandline",
                "generate",
                str(results_path),
                "-o",
                str(output_path),
                "--clean",
            ]
        else:
            sys.stderr.write("Neither 'allure' nor 'npx' command found in PATH.\n")
            return 1

    sys.stdout.write(f"Generating Allure report: {' '.join(cmd)}\n")
    proc = subprocess.run(cmd, check=False)
    if proc.returncode == 0:
        sys.stdout.write(
            f"Allure report successfully compiled to: {output_path.resolve()}\n"
        )
    return proc.returncode


if __name__ == "__main__":
    res_dir = sys.argv[1] if len(sys.argv) > 1 else "qa/allure-results"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "qa/allure-report"
    sys.exit(generate_allure_report(res_dir, out_dir))
