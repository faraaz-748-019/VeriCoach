"""Command-line interface for running VeriCoach Ragas evaluation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Ensure Windows terminal standard out uses utf-8
if sys.platform.startswith("win"):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table

from qa.llm_eval.ragas_eval.config import get_eval_settings
from qa.llm_eval.ragas_eval.evaluator import RagasEvaluator
from qa.llm_eval.ragas_eval.pipeline_collector import RAGPipelineCollector

console = Console(highlight=False)


def _safe_text(text: str) -> str:
    """Sanitize strings for terminal display across different platform charmaps."""
    encoding = getattr(sys.stdout, "encoding", "utf-8") or "utf-8"
    try:
        text.encode(encoding)
        return text
    except UnicodeEncodeError:
        return text.encode(encoding, errors="replace").decode(encoding)


def print_score_table(title: str, scores_dict: dict[str, Any]) -> None:
    """Render a clean rich table for metric summaries."""
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("Segment", style="dim")
    table.add_column("Count", justify="right")
    table.add_column("Context Precision", justify="right")
    table.add_column("Context Recall", justify="right")
    table.add_column("Faithfulness", justify="right")
    table.add_column("Answer Relevancy", justify="right")
    table.add_column("Composite Score", justify="right", style="bold green")

    for segment, metrics in scores_dict.items():
        count_val = str(metrics.get("count", "-"))
        table.add_row(
            str(segment),
            count_val,
            f"{metrics['context_precision']:.4f}",
            f"{metrics['context_recall']:.4f}",
            f"{metrics['faithfulness']:.4f}",
            f"{metrics['answer_relevancy']:.4f}",
            f"{metrics['composite_score']:.4f}",
        )
    console.print(table)


def print_worst_items_table(worst_items: list[dict[str, Any]]) -> None:
    """Render top 10 worst items for quality engineer manual review."""
    table = Table(
        title="Top 10 Worst Items for Manual Review (Lowest Composite Score)",
        show_header=True,
        header_style="bold red",
    )
    table.add_column("ID", style="bold yellow", width=12)
    table.add_column("Lang", width=5)
    table.add_column("Category", width=12)
    table.add_column("Question", width=30)
    table.add_column("Response Snippet", width=30)
    table.add_column("Contexts Count", justify="right", width=8)
    table.add_column("Prec", justify="right", width=6)
    table.add_column("Rec", justify="right", width=6)
    table.add_column("Faith", justify="right", width=6)
    table.add_column("Relev", justify="right", width=6)
    table.add_column("Composite", justify="right", style="bold red", width=9)

    for item in worst_items:
        q_raw = item["question"][:28] + ("..." if len(item["question"]) > 28 else "")
        r_raw = item["response"][:28] + ("..." if len(item["response"]) > 28 else "")
        q_disp = _safe_text(q_raw)
        r_disp = _safe_text(r_raw)
        ctx_cnt = str(len(item.get("retrieved_contexts", [])))
        table.add_row(
            _safe_text(item["id"]),
            _safe_text(item["language"]),
            _safe_text(item["category"]),
            q_disp,
            r_disp,
            ctx_cnt,
            f"{item['context_precision']:.2f}",
            f"{item['context_recall']:.2f}",
            f"{item['faithfulness']:.2f}",
            f"{item['answer_relevancy']:.2f}",
            f"{item['composite_score']:.4f}",
        )
    console.print(table)


def run_evaluation(
    golden_path: Path | str | None = None,
    limit: int | None = None,
    provider: str | None = None,
    cache_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Execute pipeline collection and Ragas evaluation."""
    settings = get_eval_settings()

    if golden_path:
        settings.golden_path = Path(golden_path)
    if limit is not None:
        settings.default_sample_limit = limit
    if provider:
        settings.provider = provider
    if cache_dir:
        settings.cache_dir = Path(cache_dir)
    if output_dir:
        settings.output_dir = Path(output_dir)

    console.print(
        f"[bold blue]Starting Ragas Evaluation[/bold blue] "
        f"(Provider: [green]{settings.provider}[/green], "
        f"Limit: [green]{settings.default_sample_limit}[/green], "
        f"Cache: [yellow]{settings.cache_dir}[/yellow])"
    )

    collector = RAGPipelineCollector(settings)
    items = collector.collect_dataset(
        golden_path=settings.golden_path,
        limit=settings.default_sample_limit,
    )

    evaluator = RagasEvaluator(settings)
    report = evaluator.evaluate_dataset(items)

    # 1. Print Overall Summary
    overall_wrapper = {
        "Overall": {**report["overall_scores"], "count": report["total_items"]}
    }
    print_score_table("Overall Evaluation Scores", overall_wrapper)

    # 2. Print Per-Language Breakdown
    print_score_table("Evaluation Scores by Language", report["scores_by_language"])

    # 3. Print Per-Category Breakdown
    print_score_table("Evaluation Scores by Category", report["scores_by_category"])

    # 4. Print 10 Worst Items Table
    print_worst_items_table(report["worst_10_items"])

    # 5. Print Cache Stats
    cache_stats = report["cache_stats"]
    console.print(
        f"\n[bold magenta]Disk Cache Statistics:[/bold magenta] "
        f"Hits: [green]{cache_stats['hits']}[/green] | "
        f"Misses: [yellow]{cache_stats['misses']}[/yellow] | "
        f"Total: {cache_stats['total']} | "
        f"Hit Ratio: [bold]{cache_stats['hit_ratio'] * 100:.1f}%[/bold]"
    )

    date_str = report["run_date"]
    console.print(
        f"\n[bold green]Report exported successfully:[/bold green]\n"
        f" - JSON: {settings.output_dir / f'ragas_{date_str}.json'}\n"
        f" - CSV:  {settings.output_dir / f'ragas_{date_str}.csv'}\n"
    )

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="VeriCoach Ragas Evaluation Runner")
    parser.add_argument(
        "--golden-path",
        type=Path,
        default=None,
        help="Path to golden_v1.jsonl dataset",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
        help="Number of golden items to evaluate (default: 30)",
    )
    parser.add_argument(
        "--provider",
        choices=["gemini", "mock", "ollama"],
        default="mock",
        help="LLM & evaluation judge provider (default: mock)",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Custom disk cache directory path",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to save JSON & CSV outputs",
    )

    args = parser.parse_args()

    run_evaluation(
        golden_path=args.golden_path,
        limit=args.limit,
        provider=args.provider,
        cache_dir=args.cache_dir,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
