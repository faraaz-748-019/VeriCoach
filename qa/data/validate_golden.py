"""Golden Dataset Validator for VeriCoach QA Platform.

Validates:
1. Pydantic schema compliance for every golden dataset record.
2. Exact 40 items per language (en, hi, te) totaling 120 items.
3. Category distribution (answerable, unanswerable, advice_refusal, adversarial).
4. No duplicate question texts or duplicate record IDs.
5. Every reference_doc_id exists in the canonical documents corpus.
6. Refusal flag consistency (must_refuse matches category policy).
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Import canonical corpus document IDs
try:
    from backend.corpus.documents import DOCUMENTS_CORPUS

    CANONICAL_DOC_IDS = {doc.doc_id for doc in DOCUMENTS_CORPUS}
except ImportError:
    # Fallback to local import if backend not in sys.path
    repo_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(repo_root / "app"))
    from backend.corpus.documents import DOCUMENTS_CORPUS

    CANONICAL_DOC_IDS = {doc.doc_id for doc in DOCUMENTS_CORPUS}

LanguageCode = Literal["en", "hi", "te"]
CategoryType = Literal["answerable", "unanswerable", "advice_refusal", "adversarial"]


class GoldenDatasetItem(BaseModel):
    """Schema for an item in the golden evaluation dataset."""

    id: str = Field(..., min_length=1, description="Unique identifier for the item")
    language: LanguageCode = Field(
        ..., description="Language code: en (English), hi (Hindi), or te (Telugu)"
    )
    category: CategoryType = Field(
        ...,
        description="Evaluation category: answerable, unanswerable, advice_refusal, adversarial",
    )
    question: str = Field(
        ...,
        min_length=3,
        description="User question or prompt in the specified language",
    )
    reference_answer: str = Field(
        ..., min_length=5, description="Ground truth answer or expected refusal message"
    )
    reference_doc_ids: list[str] = Field(
        default_factory=list,
        description="IDs of corpus documents required to answer the question",
    )
    must_refuse: bool = Field(
        ..., description="Whether the assistant must refuse to answer this query"
    )
    notes: str = Field(
        default="", description="Contextual engineering notes or review status"
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("reference_doc_ids")
    @classmethod
    def validate_doc_ids(cls, v: list[str]) -> list[str]:
        for doc_id in v:
            if doc_id not in CANONICAL_DOC_IDS:
                raise ValueError(
                    f"Invalid reference_doc_id '{doc_id}'. Must exist in canonical corpus."
                )
        return v


def validate_golden_dataset(
    file_path: Path | str,
    expected_total: int = 120,
    expected_per_language: int = 40,
) -> dict[str, Any]:
    """Validate the golden dataset JSONL file against all quality rules.

    Returns a summary dictionary of dataset statistics.
    Raises ValueError on any schema or constraint violation.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Golden dataset file not found: {path}")

    items: list[GoldenDatasetItem] = []
    seen_ids: set[str] = set()
    seen_questions: set[str] = set()
    errors: list[str] = []

    with path.open("r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"Line {line_no}: Malformed JSON - {exc}")
                continue

            try:
                item = GoldenDatasetItem.model_validate(data)
            except Exception as exc:
                errors.append(
                    f"Line {line_no} [ID: {data.get('id', 'unknown')}]: Schema error - {exc}"
                )
                continue

            # Duplicate ID check
            if item.id in seen_ids:
                errors.append(f"Line {line_no}: Duplicate ID '{item.id}' detected.")
            seen_ids.add(item.id)

            # Duplicate question check (normalized)
            norm_q = item.question.strip().lower()
            if norm_q in seen_questions:
                errors.append(
                    f"Line {line_no} [ID: {item.id}]: Duplicate question detected: '{item.question}'."
                )
            seen_questions.add(norm_q)

            # Consistency check: must_refuse policy
            if item.category in ("advice_refusal", "adversarial"):
                if not item.must_refuse:
                    errors.append(
                        f"Line {line_no} [ID: {item.id}]: Category '{item.category}' must have must_refuse=True."
                    )
            elif item.category in ("answerable", "unanswerable"):
                if item.must_refuse:
                    errors.append(
                        f"Line {line_no} [ID: {item.id}]: Category '{item.category}' must have must_refuse=False."
                    )

            # Consistency check: reference_doc_ids for answerable
            if item.category == "answerable" and not item.reference_doc_ids:
                errors.append(
                    f"Line {line_no} [ID: {item.id}]: Answerable item must have at least one reference_doc_id."
                )
            elif item.category != "answerable" and item.reference_doc_ids:
                errors.append(
                    f"Line {line_no} [ID: {item.id}]: Category '{item.category}' should have empty reference_doc_ids."
                )

            items.append(item)

    if errors:
        error_summary = "\n  - " + "\n  - ".join(errors[:20])
        if len(errors) > 20:
            error_summary += f"\n  ... and {len(errors) - 20} more errors."
        raise ValueError(
            f"Golden dataset validation failed with {len(errors)} error(s):{error_summary}"
        )

    # Total count assertion
    if len(items) != expected_total:
        raise ValueError(
            f"Expected {expected_total} total items, found {len(items)} items."
        )

    # Language breakdown and balance assertion
    lang_counts: Counter[str] = Counter(item.language for item in items)
    for lang in ("en", "hi", "te"):
        count = lang_counts.get(lang, 0)
        if count != expected_per_language:
            raise ValueError(
                f"Language '{lang}' has {count} items; expected exactly {expected_per_language}."
            )

    # Category breakdown by language
    category_counts: Counter[str] = Counter(item.category for item in items)
    matrix: dict[str, Counter[str]] = {
        lang: Counter(item.category for item in items if item.language == lang)
        for lang in ("en", "hi", "te")
    }

    return {
        "total_items": len(items),
        "language_counts": dict(lang_counts),
        "category_counts": dict(category_counts),
        "matrix": {k: dict(v) for k, v in matrix.items()},
    }


def print_summary_table(stats: dict[str, Any]) -> None:
    """Print an ASCII summary table of dataset counts by language and category."""
    categories = ["answerable", "unanswerable", "advice_refusal", "adversarial"]

    print("\n" + "=" * 74)
    print(" " * 22 + "VERICOACH GOLDEN DATASET SUMMARY")
    print("=" * 74)
    print(
        f"{'Category':<20} | {'English (en)':<14} | {'Hindi (hi)':<12} | {'Telugu (te)':<13} | {'Total':<6}"
    )
    print("-" * 74)

    matrix = stats["matrix"]
    category_totals: dict[str, int] = {}
    for cat in categories:
        en_c = matrix.get("en", {}).get(cat, 0)
        hi_c = matrix.get("hi", {}).get(cat, 0)
        te_c = matrix.get("te", {}).get(cat, 0)
        tot = en_c + hi_c + te_c
        category_totals[cat] = tot
        pct = (tot / stats["total_items"]) * 100
        print(
            f"{cat:<20} | {en_c:<14} | {hi_c:<12} | {te_c:<13} | {tot:<3} ({pct:.0f}%)"
        )

    print("-" * 74)
    tot_en = stats["language_counts"].get("en", 0)
    tot_hi = stats["language_counts"].get("hi", 0)
    tot_te = stats["language_counts"].get("te", 0)
    print(
        f"{'Total':<20} | {tot_en:<14} | {tot_hi:<12} | {tot_te:<13} | {stats['total_items']:<6}"
    )
    print("=" * 74 + "\n")


def main() -> None:
    """CLI entrypoint for golden dataset validation."""
    default_path = Path(__file__).resolve().parent / "golden" / "golden_v1.jsonl"
    dataset_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path

    print(f"Validating golden dataset at: {dataset_path}")
    try:
        stats = validate_golden_dataset(dataset_path)
        print(
            "Dataset schema, language balance, uniqueness, and corpus doc_ids PASSED."
        )
        print_summary_table(stats)
    except Exception as exc:
        print(f"\nERROR: Validation failed!\n{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
