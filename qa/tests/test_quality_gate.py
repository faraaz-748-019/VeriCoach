"""Unit and Integration Tests for VeriCoach Quality Gatekeeper.

Verifies:
1. All quality gates pass when metrics meet or exceed criteria.
2. Pipeline fails when faithfulness drops below threshold.
3. Pipeline fails when hallucination rate exceeds allowable threshold.
4. Pipeline fails when prompt injection attacks breach safety guardrails.
5. Pipeline fails when raw PII leaks are detected.
6. Pipeline fails when backwards-incompatible OpenAPI contract changes exist.
7. History logging and trend chart generation accurately record run data.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest  # noqa: E402

from scripts.quality_gate import QualityGateRunner  # noqa: E402


@pytest.fixture
def mock_results_dir(tmp_path: Path) -> Path:
    """Create a temporary sandbox directory with mock results files."""
    res_dir = tmp_path / "results"
    res_dir.mkdir(parents=True, exist_ok=True)

    # 1. DeepEval passing output
    deepeval_data = {
        "summary_metrics": {
            "faithfulness": 0.95,
            "hallucination": 0.98,
            "hallucination_rate": 0.02,
            "answer_relevancy": 0.92,
        }
    }
    (res_dir / "deepeval_mock.json").write_text(
        json.dumps(deepeval_data), encoding="utf-8"
    )

    # 2. Promptfoo passing output (all attacks defended)
    promptfoo_data = {
        "results": {
            "results": [
                {
                    "testCase": {
                        "metadata": {"category": "prompt_injection_jailbreak"}
                    },
                    "success": True,
                },
                {
                    "testCase": {"metadata": {"category": "prompt_injection_canary"}},
                    "success": True,
                },
                {
                    "testCase": {"metadata": {"category": "pii_leakage"}},
                    "success": True,
                },
            ]
        }
    }
    (res_dir / "promptfoo_mock.json").write_text(
        json.dumps(promptfoo_data), encoding="utf-8"
    )

    # 3. Gates YAML
    gates_data = {
        "thresholds": {
            "faithfulness": 0.70,
            "max_hallucination_rate": 0.25,
            "security": {
                "max_prompt_injection_success_rate": 0.0,
                "max_pii_leaks": 0,
            },
            "contract": {
                "max_breaking_changes": 0,
            },
        }
    }
    gates_file = tmp_path / "gates.yaml"
    import yaml

    gates_file.write_text(yaml.safe_dump(gates_data), encoding="utf-8")

    return tmp_path


def test_quality_gate_passes_healthy_suite(mock_results_dir: Path) -> None:
    """Ensure runner approves a healthy system meeting all quality and security gates."""
    runner = QualityGateRunner(
        gates_path=mock_results_dir / "gates.yaml",
        deepeval_path=mock_results_dir / "results" / "deepeval_mock.json",
        promptfoo_path=mock_results_dir / "results" / "promptfoo_mock.json",
        history_csv=mock_results_dir / "history.csv",
        trend_chart_png=mock_results_dir / "trend.png",
    )

    passed, results, summary = runner.evaluate()

    assert passed is True
    assert all(r.passed for r in results)
    assert summary["gate_status"] == "PASS"
    assert summary["faithfulness"] == 0.95
    assert summary["hallucination_rate"] == 0.02
    assert summary["prompt_injection_asr"] == 0.0
    assert summary["pii_leaks"] == 0


def test_quality_gate_fails_on_low_faithfulness(mock_results_dir: Path) -> None:
    """Ensure runner rejects a run when faithfulness drops below threshold."""
    # Degrade faithfulness in deepeval results
    low_eval = mock_results_dir / "results" / "deepeval_mock.json"
    data = json.loads(low_eval.read_text(encoding="utf-8"))
    data["summary_metrics"]["faithfulness"] = 0.55  # Below 0.70 target
    low_eval.write_text(json.dumps(data), encoding="utf-8")

    runner = QualityGateRunner(
        gates_path=mock_results_dir / "gates.yaml",
        deepeval_path=low_eval,
        promptfoo_path=mock_results_dir / "results" / "promptfoo_mock.json",
        history_csv=mock_results_dir / "history.csv",
        trend_chart_png=mock_results_dir / "trend.png",
    )

    passed, results, summary = runner.evaluate()

    assert passed is False
    assert summary["gate_status"] == "FAIL"
    faithfulness_gate = next(r for r in results if r.name == "Faithfulness")
    assert faithfulness_gate.passed is False
    assert faithfulness_gate.actual == 0.55


def test_quality_gate_fails_on_high_hallucination(mock_results_dir: Path) -> None:
    """Ensure runner rejects when hallucination rate exceeds the allowable threshold."""
    high_eval = mock_results_dir / "results" / "deepeval_mock.json"
    data = json.loads(high_eval.read_text(encoding="utf-8"))
    data["summary_metrics"]["hallucination_rate"] = 0.40  # Above 0.25 limit
    high_eval.write_text(json.dumps(data), encoding="utf-8")

    runner = QualityGateRunner(
        gates_path=mock_results_dir / "gates.yaml",
        deepeval_path=high_eval,
        promptfoo_path=mock_results_dir / "results" / "promptfoo_mock.json",
        history_csv=mock_results_dir / "history.csv",
        trend_chart_png=mock_results_dir / "trend.png",
    )

    passed, results, _ = runner.evaluate()

    assert passed is False
    hallucination_gate = next(r for r in results if r.name == "Hallucination Rate")
    assert hallucination_gate.passed is False
    assert hallucination_gate.actual == 0.40


def test_quality_gate_fails_on_prompt_injection_breach(
    mock_results_dir: Path,
) -> None:
    """Ensure runner rejects when a prompt injection test breaches safety defense."""
    breach_sec = mock_results_dir / "results" / "promptfoo_mock.json"
    data = json.loads(breach_sec.read_text(encoding="utf-8"))
    # Mark prompt injection test as breached (success: False means promptfoo assertion failed)
    data["results"]["results"][0]["success"] = False
    breach_sec.write_text(json.dumps(data), encoding="utf-8")

    runner = QualityGateRunner(
        gates_path=mock_results_dir / "gates.yaml",
        deepeval_path=mock_results_dir / "results" / "deepeval_mock.json",
        promptfoo_path=breach_sec,
        history_csv=mock_results_dir / "history.csv",
        trend_chart_png=mock_results_dir / "trend.png",
    )

    passed, results, summary = runner.evaluate()

    assert passed is False
    inj_gate = next(r for r in results if r.name == "Prompt Injection ASR")
    assert inj_gate.passed is False
    assert inj_gate.actual == 0.50  # 1 breach out of 2 prompt injection attacks
    assert summary["prompt_injection_asr"] == 0.50


def test_quality_gate_fails_on_pii_leak(mock_results_dir: Path) -> None:
    """Ensure runner rejects when any PII leak is detected."""
    pii_leak = mock_results_dir / "results" / "promptfoo_mock.json"
    data = json.loads(pii_leak.read_text(encoding="utf-8"))
    # PII leak assertion failed (leak detected)
    data["results"]["results"][2]["success"] = False
    pii_leak.write_text(json.dumps(data), encoding="utf-8")

    runner = QualityGateRunner(
        gates_path=mock_results_dir / "gates.yaml",
        deepeval_path=mock_results_dir / "results" / "deepeval_mock.json",
        promptfoo_path=pii_leak,
        history_csv=mock_results_dir / "history.csv",
        trend_chart_png=mock_results_dir / "trend.png",
    )

    passed, results, summary = runner.evaluate()

    assert passed is False
    pii_gate = next(r for r in results if r.name == "PII Leaks Found")
    assert pii_gate.passed is False
    assert pii_gate.actual == 1
    assert summary["pii_leaks"] == 1


def test_quality_gate_fails_on_openapi_breaking_changes(
    mock_results_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ensure runner rejects when backwards-incompatible OpenAPI breaking changes occur."""
    runner = QualityGateRunner(
        gates_path=mock_results_dir / "gates.yaml",
        deepeval_path=mock_results_dir / "results" / "deepeval_mock.json",
        promptfoo_path=mock_results_dir / "results" / "promptfoo_mock.json",
        history_csv=mock_results_dir / "history.csv",
        trend_chart_png=mock_results_dir / "trend.png",
    )

    # Simulate breaking change in OpenAPI
    monkeypatch.setattr(
        runner,
        "_check_contract_breaking_changes",
        lambda: ["Removed endpoint path: '/v1/chat'"],
    )

    passed, results, summary = runner.evaluate()

    assert passed is False
    contract_gate = next(r for r in results if r.name == "OpenAPI Breaking Changes")
    assert contract_gate.passed is False
    assert contract_gate.actual == 1
    assert summary["breaking_changes"] == 1


def test_quality_gate_records_history_and_renders_chart(
    mock_results_dir: Path,
) -> None:
    """Verify appending metrics to history CSV and chart generation."""
    history_file = mock_results_dir / "history.csv"
    chart_file = mock_results_dir / "trend.png"

    runner = QualityGateRunner(
        gates_path=mock_results_dir / "gates.yaml",
        deepeval_path=mock_results_dir / "results" / "deepeval_mock.json",
        promptfoo_path=mock_results_dir / "results" / "promptfoo_mock.json",
        history_csv=history_file,
        trend_chart_png=chart_file,
        run_id="test_run_123",
    )

    passed, _, summary = runner.evaluate()
    assert passed is True
    runner.record_history(summary)
    runner.generate_chart()

    assert history_file.is_file()
    assert chart_file.is_file()
    content = history_file.read_text(encoding="utf-8")
    assert "test_run_123" in content
    assert "0.9500" in content
    assert "PASS" in content
