"""CLI interface for LangSmith tracing, dataset upload, and evaluation."""

from __future__ import annotations

import argparse
import sys

from qa.llm_eval.langsmith_eval.dataset_uploader import upload_golden_dataset
from qa.llm_eval.langsmith_eval.experiment_runner import run_langsmith_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="VeriCoach LangSmith Evaluation CLI")
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload the golden dataset to LangSmith",
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default="vericoach-golden-v1",
        help="Target LangSmith dataset name",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=15,
        help="Number of golden items to evaluate (0 for full dataset)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Force offline mock mode without remote network calls",
    )

    args = parser.parse_args()

    print(f"=== VeriCoach LangSmith Pipeline (mock={args.mock}) ===")
    if args.upload:
        print(f"Uploading dataset '{args.dataset_name}'...")
        res = upload_golden_dataset(dataset_name=args.dataset_name, mock=args.mock)
        print("Upload result:", res)

    print(f"Running evaluation experiment (sample size: {args.sample_size})...")
    exp_res = run_langsmith_experiment(
        dataset_name=args.dataset_name,
        sample_size=args.sample_size,
        mock=args.mock,
    )
    print("Experiment metrics:", exp_res.get("summary_metrics", {}))
    print("Results saved to results/langsmith_experiment_results.json")


if __name__ == "__main__":
    main()
