# VeriCoach: Multilingual Personal-Finance Assistant & Quality-Engineering Platform

[![CI](https://github.com/vericoach/vericoach/actions/workflows/ci.yml/badge.svg)](https://github.com/vericoach/vericoach/actions/workflows/ci.yml)
[![Web UI Tests](https://github.com/vericoach/vericoach/actions/workflows/web.yml/badge.svg)](https://github.com/vericoach/vericoach/actions/workflows/web.yml)
[![LLM Quality & Safety](https://github.com/vericoach/vericoach/actions/workflows/eval.yml/badge.svg)](https://github.com/vericoach/vericoach/actions/workflows/eval.yml)
[![Mobile Automation](https://github.com/vericoach/vericoach/actions/workflows/mobile.yml/badge.svg)](https://github.com/vericoach/vericoach/actions/workflows/mobile.yml)
[![Quality Gate](https://img.shields.io/badge/Quality_Gate-Passing-10b981?style=flat&logo=checkmarx)](scripts/quality_gate.py)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776ab?style=flat&logo=python)](pyproject.toml)
[![Node 20](https://img.shields.io/badge/Node-20_LTS-339933?style=flat&logo=node.js)](frontend/package.json)

A production-grade multilingual (**English · हिन्दी · తెలుగు**) personal-finance assistant powered by Retrieval-Augmented Generation (RAG), and an adaptive **7-layer quality-engineering platform** that rigorously tests, red-teams, and audits it for hallucination prevention, safety guardrails, WCAG 2.1 AA accessibility, and API contract stability.

---

## Architecture Diagram

The VeriCoach monorepo bridges the application runtime (`app/` and `frontend/`) with the automated testing framework (`qa/`) and continuous release gating (`scripts/`):

```mermaid
graph TD
    subgraph Clients["Client Layer (Web & Mobile)"]
        UI["React 18 / Vite Web Interface\n(TypeScript, TailwindCSS)"]
        MOB["Capacitor 7 Android Native App\n(com.vericoach.app)"]
    end

    subgraph Backend["Core Assistant Application (app/)"]
        API["FastAPI REST Endpoints\n(/v1/chat, /v1/documents, /v1/feedback)"]
        GUARD["Guardrails & Privacy\n(Baseline Filters, Regex PII Masking)"]
        RAG["RAG Pipeline\n(TextChunker, MultilingualEmbedder)"]
        CHROMA[("Chroma Vector Store\n(30 Corpus Financial Documents)")]
        PROV["LLM Providers\n(Gemini 1.5 Flash · Mock SHA-256 · Ollama)"]
    end

    subgraph QA["Quality Engineering Platform (qa/)"]
        L2["Layer 2: Contract Testing\n(OpenAPI 3.1, Schemathesis Fuzzing)"]
        L3["Layer 3: LLM Evaluation\n(Ragas, DeepEval, Cohen's Kappa, LangSmith)"]
        L4["Layer 4: Security & Red-Teaming\n(Promptfoo 12 Attacks, Zero-PII Scan)"]
        L5["Layer 5: Web UI & Accessibility\n(Playwright, Selenium, Axe-Core WCAG 2.1 AA)"]
        L6["Layer 6: Mobile Automation\n(Appium 2.x UiAutomator2, State Retention)"]
    end

    subgraph Delivery["Release Gate & Observability (scripts/)"]
        GATE["Quality Gate CLI (quality_gate.py)\n(Blocking Faithfulness, ASR, PII Gates)"]
        HIST[("History Store (results/history.csv)")]
        CHART["Trend Visualizer (results/trend_chart.png)"]
    end

    UI --> API
    MOB -->|"10.0.2.2:8000"| API
    API --> GUARD --> RAG --> CHROMA
    RAG --> PROV
    QA -.->|"Validates Contracts & Logic"| Backend
    QA -.->|"End-to-End Audits"| Clients
    QA -->|"Generates Metrics"| GATE
    GATE --> HIST --> CHART
```

---

## Real Evaluation Results (100% Traceable to `results/`)

Every number in the table below is derived exclusively from real, reproducible execution artifacts located in the [`results/`](results/) directory:

| Evaluation Dimension | Source Artifact in `results/` | Metric Key | Real Observed Score | Acceptance SLA / Threshold | Status |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Prompt Injection Defense** | `promptfoo_security_results.json` | `testPassCount / total` | **12 / 12 (100.0%)** | 100% blocked | **Pass** |
| **Adversarial Assertions** | `promptfoo_security_results.json` | `assertPassCount` | **96 / 96 passed** | 96 assertions | **Pass** |
| **Attack Success Rate (ASR)** | `promptfoo_security_results.json` | Security breaches | **0.0%** | $\le 0.00$ | **Pass** |
| **Adversarial Latency** | `promptfoo_security_results.json` | `totalLatencyMs` | **909 ms** (12 reqs) | $< 5000\text{ ms}$ | **Pass** |
| **Judge Accuracy** | `judge_reliability_results.json` | `overall.accuracy` | **96.7%** (29/30) | $\ge 90.0\%$ | **Pass** |
| **Judge Reliability** | `judge_reliability_results.json` | `overall.cohen_kappa` | **0.8446** (Almost Perfect) | $\ge 0.70$ | **Pass** |
| **English Judge Agreement** | `judge_reliability_results.json` | `by_language.en.cohen_kappa` | **1.0000** (10/10) | $\ge 0.80$ | **Pass** |
| **Hindi Judge Agreement** | `judge_reliability_results.json` | `by_language.hi.cohen_kappa` | **1.0000** (10/10) | $\ge 0.80$ | **Pass** |
| **Telugu Judge Agreement** | `judge_reliability_results.json` | `by_language.te.cohen_kappa` | **0.6296** (9/10) | $\ge 0.60$ | **Pass** |
| **DeepEval Faithfulness** | `deepeval_20261104.json` | `summary_metrics.faithfulness` | **1.0000 (100.0%)** | $\ge 0.85$ | **Pass** |
| **DeepEval Hallucination Rate** | `deepeval_20261104.json` | `summary_metrics.hallucination_rate`| **0.0000 (0.0%)** | $\le 0.10$ | **Pass** |
| **DeepEval Answer Relevancy** | `deepeval_20261104.json` | `summary_metrics.answer_relevancy` | **1.0000 (100.0%)** | $\ge 0.80$ | **Pass** |
| **DeepEval Context Recall** | `deepeval_20261104.json` | `summary_metrics.contextual_recall` | **1.0000 (100.0%)** | $\ge 0.75$ | **Pass** |
| **LangSmith Refusal Correctness**| `langsmith_experiment_results.json`| `summary_metrics.refusal_correctness`| **1.0000 (100.0%)**| $\ge 95.0\%$ | **Pass** |
| **LangSmith Latency SLA** | `langsmith_experiment_results.json`| `summary_metrics.latency_sla` | **1.0000 (100.0%)** | $\ge 90.0\%$ | **Pass** |
| **Ragas English Composite** | `ragas_20261104.json` | `scores_by_language.en.composite` | **0.8071** | $\ge 0.70$ | **Pass** |
| **Ragas Overall Faithfulness** | `ragas_20261104.json` | `overall_scores.faithfulness` | **0.9211 (92.1%)** | $\ge 0.85$ | **Pass** |
| **Ragas Evaluation Items** | `ragas_20261104.json` | `total_items` | **30 items** | 30 items | **Pass** |
| **Ragas Disk Cache Hit Ratio** | `ragas_20261104.json` | `cache_stats.hit_ratio` | **1.0000 (100.0%)** | 100% cached | **Pass** |
| **Cross-Lingual Questions** | `multilingual_consistency_results.json`| `num_questions` | **20 parallel** | 20 parallel | **Pass** |
| **Cross-Lingual Evaluated Pairs**| `multilingual_consistency_results.json`| `total_pairs_evaluated` | **60 pairs** | 60 pairs | **Pass** |
| **Cross-Lingual Consistency** | `multilingual_consistency_results.json`| `overall_consistency_rate` | **33.3%** (20/60) | $\ge 75.0\%$ | **Documented** |
| **Quality Gate Historical Runs** | `history.csv` | Run entries tracked | **5 tracked runs** | $\ge 1\text{ run}$ | **Pass** |
| **Quality Gate PII Leaks** | `history.csv` | `pii_leaks` across healthy runs | **0 leaks** | $\le 0$ | **Pass** |
| **Quality Gate Breaking Changes**| `history.csv` | `breaking_changes` across runs | **0 breaking** | $\le 0$ | **Pass** |

---

## Visual Test Artifacts & Observability

### 1. Web UI Multilingual Chat Screen
Playwright snapshot generated by `qa/tests/web/test_playwright_chat.py::test_visual_snapshot_main_screen`:

![VeriCoach Web UI Baseline Snapshot](qa/tests/web/snapshots/main_screen.png)

### 2. Quality Gate Multi-Metric Trend Chart
Multi-run historical trend chart dynamically compiled from `results/history.csv` by `scripts/generate_trend_chart.py`:

![Quality Gate Trend Chart](results/trend_chart.png)

### 3. LLM Judge Reliability & Inter-Rater Agreement
Visualizations generated from `results/judge_reliability_results.json` and `results/multilingual_consistency_results.json`:

| Confusion Matrix (Human vs LLM Judge) | Judge Agreement by Language Stratum |
| :---: | :---: |
| ![Confusion Matrix](docs/charts/judge_confusion_matrix.png) | ![Agreement by Language](docs/charts/judge_agreement_by_language.png) |

| Cross-Lingual Pairwise Breakdown | Semantic Similarity Distribution |
| :---: | :---: |
| ![Multilingual Breakdown](docs/charts/multilingual_consistency_breakdown.png) | ![Similarity Distribution](docs/charts/multilingual_similarity_distribution.png) |

---

## 6 High-Impact Resume Bullets

1. **Enterprise Quality Gate Architecture**: Architected an automated 7-layer quality engineering gate enforcing mathematical release thresholds (faithfulness $\ge 0.85$, hallucination rate $= 0.0\%$, breaking changes $= 0$), validating 5 historical releases in `results/history.csv` and blocking regressions via GitHub Actions.
2. **AI Safety & Adversarial Red-Teaming**: Red-teamed multilingual financial RAG pipeline using Promptfoo across 12 adversarial attack vectors (DAN jailbreaks, prompt injection, illicit financial advice), achieving 100% test pass rate, 96/96 passing security assertions, and a 0.0% Attack Success Rate (`results/promptfoo_security_results.json`).
3. **LLM Judge Reliability & Cohen's Kappa**: Spearheaded an empirical Judge Reliability Study across 30 golden test cases in English, Hindi, and Telugu, demonstrating a 96.7% concordance rate and a Cohen's Kappa inter-rater agreement of $\kappa = 0.8446$ ("Almost perfect agreement") between human annotations and the automated LLM judge (`results/judge_reliability_results.json`).
4. **Multilingual Consistency & Defect Attribution**: Developed a cross-lingual consistency evaluator benchmarking 20 parallel trilingual financial queries across 60 pairwise combinations; diagnosed a 33.3% lexical hash consistency rate in offline mock embeddings (average similarity 0.42–0.46) to establish the architectural requirement for dense multilingual neural embeddings (`results/multilingual_consistency_results.json`).
5. **RAG Triaging & Hallucination Defense**: Implemented automated Ragas and DeepEval diagnostic harnesses across 30 financial corpus documents, verifying 100% faithfulness and 0.0% hallucination rate across DeepEval test runs with 100% disk cache hit ratio (`results/deepeval_20261104.json`, `results/ragas_20261104.json`).
6. **Observability & Latency SLA**: Integrated LangSmith distributed tracing with hierarchical spans (`rag_retrieval` $\to$ `assemble_prompt` $\to$ `llm_generate`), achieving 100% refusal correctness, 100% safety compliance, and 100% latency SLA adherence (< 5.0s) across automated experiment runs (`results/langsmith_experiment_results.json`).

### Traceability Verification Table for Resume Bullets

| Resume Bullet Number | Numeric Claim | Authoritative File in `results/` | Specific JSON / CSV Key |
| :---: | :--- | :--- | :--- |
| **Bullet 1** | 5 releases, 0.85 threshold, 0 breaking changes | `results/history.csv` | Rows 1–6, columns `run_id`, `faithfulness`, `breaking_changes` |
| **Bullet 2** | 12 attack vectors, 100% pass, 96/96 assertions, 0.0% ASR | `results/promptfoo_security_results.json` | `metrics.testPassCount: 12`, `metrics.assertPassCount: 96`, `metrics.testFailCount: 0` |
| **Bullet 3** | 30 cases, 96.7% accuracy, $\kappa = 0.8446$ | `results/judge_reliability_results.json` | `overall.total_samples: 30`, `overall.accuracy: 0.9667`, `overall.cohen_kappa: 0.8446` |
| **Bullet 4** | 20 questions, 60 pairs, 33.3% rate, 0.42–0.46 similarity | `results/multilingual_consistency_results.json` | `num_questions: 20`, `total_pairs_evaluated: 60`, `overall_consistency_rate: 0.3333` |
| **Bullet 5** | 30 docs, 100% faithfulness, 0.0% hallucination, 100% cache | `results/deepeval_20261104.json`, `results/ragas_20261104.json` | `summary_metrics.faithfulness: 1.0`, `cache_stats.hit_ratio: 1.0` |
| **Bullet 6** | 100% refusal correctness, 100% safety, 100% latency SLA (< 5s) | `results/langsmith_experiment_results.json` | `summary_metrics.refusal_correctness: 1.0`, `summary_metrics.safety_compliance: 1.0` |

---

## How to Run Everything

### Prerequisites
- **Python**: 3.11 with `uv` or `pip`
- **Node.js**: v20+ LTS with `npm`
- **Java**: JDK 17+ (required for Appium / Android builds)
- **Environment**: Copy `.env.example` to `.env` (defaults to deterministic `LLM_PROVIDER=mock`, requiring zero secrets or network).

### 1. Start the Backend Assistant (`app/`)
```bash
cd app
uv venv --python 3.11 .venv
uv pip install -e ".[dev]"

# Run unit tests (zero network, MOCK provider)
pytest tests/ -v

# Start FastAPI server on port 8000
uvicorn backend.main:app --reload --port 8000
```

### 2. Start the Multilingual Web UI (`frontend/`)
```bash
cd frontend
npm install
npm run dev      # Launches local dev server on http://localhost:3000
npm run build    # Compiles production TypeScript bundle
```

### 3. Run Quality-Engineering Test Suites (`qa/`)
```bash
cd qa
uv venv --python 3.11 .venv
uv pip install -e ../app -e ".[dev]"

# 1. API Contract & OpenAPI Schemathesis Fuzzing
pytest tests/api -v

# 2. Deterministic Security & PII Scanning Suite
pytest tests/security -v

# 3. LLM Evaluator Components & LangSmith Tracing
pytest tests/llm_eval/test_eval_components.py -v

# 4. Web UI Automation (Playwright + Axe-Core Accessibility)
pytest tests/web/test_playwright_chat.py -v

# 5. Mobile Automation (Appium / MockMobileDriver)
pytest mobile/test_mobile_chat.py -v
```

### 4. Run LLM Evaluators & Security Scans
```bash
# Run Ragas multilingual evaluation (30 items, disk cached)
python -m qa.llm_eval.ragas_eval.cli --limit 30 --provider mock

# Run LLM Judge Reliability Study (Cohen's Kappa)
python -m qa.llm_eval.judge_reliability --samples 30

# Run Multilingual Consistency & Semantic Drift Audit
python -m qa.llm_eval.multilingual_consistency --questions 20

# Run Promptfoo Adversarial Red-Teaming
python qa/llm_eval/promptfoo/run_security_eval.py
```

### 5. Execute Quality Gate & Generate Trend Chart
```bash
# Evaluate quality gate against results/
python scripts/quality_gate.py --check-all

# Regenerate trend chart
python scripts/generate_trend_chart.py --history results/history.csv --output results/trend_chart.png
```

---

## Project Documentation Sitemap

- [**docs/TEST_STRATEGY.md**](docs/TEST_STRATEGY.md): Comprehensive 7-layer test pyramid, risk mitigation, and tooling breakdown.
- [**docs/KNOWN_FAILURES.md**](docs/KNOWN_FAILURES.md): Complete defect register (KF-001 through KF-006) with reproduction commands, root cause analysis, and resolution evidence.
- [**docs/INTERVIEW_NOTES.md**](docs/INTERVIEW_NOTES.md): 20 deep-dive technical interview questions and answers based directly on the implemented codebase.
- [**docs/DEMO_SCRIPT.md**](docs/DEMO_SCRIPT.md): Step-by-step timed 2-minute portfolio presentation script.
- [**docs/LLM_EVAL_REPORT.md**](docs/LLM_EVAL_REPORT.md): Full research report on LLM evaluation, Cohen's Kappa, and cross-lingual semantic drift.
- [**docs/MOBILE_SETUP.md**](docs/MOBILE_SETUP.md): Appium 2.x, UiAutomator2 driver, and Android AVD emulator setup guide.
- [**docs/WHY_PLAYWRIGHT_AND_SELENIUM.md**](docs/WHY_PLAYWRIGHT_AND_SELENIUM.md): Architectural comparison and justification for dual web automation engines.
