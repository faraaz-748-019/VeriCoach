#!/usr/bin/env python3
"""Trend Chart Generator for VeriCoach Quality Engineering Platform.

Visualizes historical evaluation metrics (Faithfulness, Hallucination Rate,
Answer Relevancy, Prompt Injection ASR) and gate compliance over time.
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from typing import Any

# Ensure matplotlib writes to local writable directory
ROOT_DIR = Path(__file__).resolve().parent.parent
MPL_CACHE = ROOT_DIR / "results" / ".mpl_cache"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))

import matplotlib.pyplot as plt  # noqa: E402


def generate_trend_chart(
    history_csv: Path | str = "results/history.csv",
    output_png: Path | str = "results/trend_chart.png",
) -> Path | None:
    """Generate high-resolution trend chart from historical evaluation metrics CSV."""
    csv_path = Path(history_csv)
    png_path = Path(output_png)

    if not csv_path.is_file():
        sys.stderr.write(f"History CSV file not found at: {csv_path}\n")
        return None

    rows: list[dict[str, Any]] = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    if not rows:
        sys.stderr.write(f"No records found in {csv_path}\n")
        return None

    png_path.parent.mkdir(parents=True, exist_ok=True)

    # Extract sequences
    run_labels = [
        f"#{i + 1} ({r.get('run_id', '')[:7]})" if r.get("run_id") else f"#{i + 1}"
        for i, r in enumerate(rows)
    ]
    faithfulness = [float(r.get("faithfulness", 0.0)) for r in rows]
    hallucination_rate = [float(r.get("hallucination_rate", 0.0)) for r in rows]
    answer_relevancy = [float(r.get("answer_relevancy", 0.0)) for r in rows]
    prompt_injection_asr = [float(r.get("prompt_injection_asr", 0.0)) for r in rows]
    statuses = [r.get("gate_status", "PASS") for r in rows]

    x_indices = list(range(len(rows)))

    # Setup matplotlib figure
    plt.style.use(
        "seaborn-v0_8-whitegrid"
        if "seaborn-v0_8-whitegrid" in plt.style.available
        else "default"
    )
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(10, 8), sharex=True, gridspec_kw={"height_ratios": [2, 1.2]}
    )
    fig.patch.set_facecolor("#0f172a")

    for ax in (ax1, ax2):
        ax.set_facecolor("#1e293b")
        ax.grid(color="#334155", linestyle="--", linewidth=0.7, alpha=0.8)
        ax.tick_params(colors="#cbd5e1", labelsize=9)
        for spine in ax.spines.values():
            spine.set_color("#475569")

    # Plot 1: RAG Quality Metrics
    ax1.set_title(
        "VeriCoach Quality Gates — Evaluation & Safety Metrics Trend",
        fontsize=13,
        fontweight="bold",
        color="#f8fafc",
        pad=14,
    )

    ax1.plot(
        x_indices,
        faithfulness,
        marker="o",
        linewidth=2.4,
        color="#10b981",
        label="Faithfulness (Target ≥ 0.70)",
    )
    ax1.plot(
        x_indices,
        answer_relevancy,
        marker="s",
        linewidth=2.0,
        color="#38bdf8",
        label="Answer Relevancy (Target ≥ 0.70)",
    )
    ax1.plot(
        x_indices,
        hallucination_rate,
        marker="^",
        linewidth=2.2,
        color="#f43f5e",
        label="Hallucination Rate (Target ≤ 0.25)",
    )

    # Reference threshold lines
    ax1.axhline(0.70, color="#10b981", linestyle=":", linewidth=1.2, alpha=0.7)
    ax1.axhline(0.25, color="#f43f5e", linestyle=":", linewidth=1.2, alpha=0.7)

    ax1.set_ylabel("Score / Rate (0.0 - 1.0)", color="#e2e8f0", fontsize=10)
    ax1.set_ylim(-0.05, 1.08)
    ax1.legend(
        loc="upper left",
        facecolor="#0f172a",
        edgecolor="#334155",
        labelcolor="#e2e8f0",
        fontsize=9,
    )

    # Plot 2: Security Attack Success Rate (ASR)
    ax2.plot(
        x_indices,
        prompt_injection_asr,
        marker="d",
        linewidth=2.2,
        color="#fbbf24",
        label="Prompt Injection ASR (Target = 0.0)",
    )
    ax2.axhline(0.0, color="#fbbf24", linestyle=":", linewidth=1.2, alpha=0.7)
    ax2.set_ylabel("Injection ASR", color="#e2e8f0", fontsize=10)
    ax2.set_ylim(-0.05, 1.05)
    ax2.legend(
        loc="upper left",
        facecolor="#0f172a",
        edgecolor="#334155",
        labelcolor="#e2e8f0",
        fontsize=9,
    )

    # Annotate pass/fail outcome for each run
    for i, (idx, status) in enumerate(zip(x_indices, statuses, strict=False)):
        badge_color = "#10b981" if status == "PASS" else "#ef4444"
        ax1.scatter([idx], [faithfulness[i]], color=badge_color, s=55, zorder=5)
        ax2.text(
            idx,
            prompt_injection_asr[i] + 0.08,
            status,
            color=badge_color,
            fontsize=8,
            fontweight="bold",
            ha="center",
        )

    ax2.set_xticks(x_indices)
    ax2.set_xticklabels(run_labels, rotation=25, ha="right", color="#cbd5e1")
    ax2.set_xlabel("Evaluation Runs (Chronological)", color="#e2e8f0", fontsize=10)

    plt.tight_layout()
    fig.savefig(png_path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)

    sys.stdout.write(f"Trend chart successfully saved to: {png_path.resolve()}\n")
    return png_path


if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "results/history.csv"
    png_file = sys.argv[2] if len(sys.argv) > 2 else "results/trend_chart.png"
    generate_trend_chart(csv_file, png_file)
