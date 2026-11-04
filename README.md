# VeriCoach

[![CI](https://github.com/vericoach/vericoach/actions/workflows/ci.yml/badge.svg)](https://github.com/vericoach/vericoach/actions/workflows/ci.yml)
[![Web UI Tests](https://github.com/vericoach/vericoach/actions/workflows/web.yml/badge.svg)](https://github.com/vericoach/vericoach/actions/workflows/web.yml)
[![LLM Quality & Safety](https://github.com/vericoach/vericoach/actions/workflows/eval.yml/badge.svg)](https://github.com/vericoach/vericoach/actions/workflows/eval.yml)
[![Mobile Automation](https://github.com/vericoach/vericoach/actions/workflows/mobile.yml/badge.svg)](https://github.com/vericoach/vericoach/actions/workflows/mobile.yml)
[![Allure Report](https://img.shields.io/badge/Allure_Report-GitHub_Pages-2980b9?style=flat&logo=allure)](https://vericoach.github.io/vericoach/allure-report/)
[![Quality Gate](https://img.shields.io/badge/Quality_Gate-Passing-10b981?style=flat&logo=checkmarx)](scripts/quality_gate.py)

A multilingual (**English · हिन्दी · తెలుగు**) personal-finance assistant with RAG, and an automated quality-engineering platform that tests it.

## Monorepo Architecture

```
VerCoach/
├── app/        # Personal-finance assistant (Python 3.11, FastAPI, RAG, LangChain)
│   ├── app/api/          # REST API endpoints (/health, /api/v1/chat, etc.)
│   ├── app/providers/    # Gemini, deterministic MOCK (zero-network), and Ollama
│   ├── app/rag/          # Text chunker, embedder, and cosine in-memory retriever
│   ├── app/data/         # Synthetic PII data generator (100% fake Faker data)
│   ├── app/i18n/         # English, Hindi, and Telugu localization
│   └── tests/            # 72 unit and API integration tests
├── qa/         # Quality-engineering evaluation platform
│   ├── qa/evaluators/    # RAG metrics (Faithfulness, Relevancy, Precision, Recall)
│   │                     # PII scanners (PAN, Aadhaar, credit cards)
│   │                     # Adversarial safety guards (jailbreaks, insider trading)
│   └── tests/            # 27 automated contract, RAG eval, PII, and safety tests
└── frontend/   # Multilingual web interface (Node 20 / React 18, Vite, TypeScript)
    └── src/              # Multilingual chat, synthetic user generator, RAG controls
```

## Quick Start

### 1. Backend (`app/`)

```bash
cd app
uv venv --python 3.11 .venv
uv pip install -e ".[dev]"

# Run tests (MOCK provider, zero network required)
.venv/Scripts/pytest.exe tests/ -v

# Start FastAPI server
.venv/Scripts/uvicorn.exe app.api.main:app --reload --port 8000
```

### 2. QA Evaluation Platform (`qa/`)

```bash
cd qa
uv venv --python 3.11 .venv
uv pip install -e ../app -e ".[dev]"

# Run full QA test suite (OpenAPI contract, RAG metrics, PII guards, safety)
.venv/Scripts/pytest.exe tests/ -v

# Run Ragas multilingual evaluation (30 items, disk cached)
.venv/Scripts/python.exe -m qa.llm_eval.ragas_eval.cli --limit 30 --provider mock
```

### 3. Frontend (`frontend/`)

```bash
cd frontend
npm install
npm run dev      # Starts UI on http://localhost:3000
npm run build    # Production build
```

## Ragas Multilingual Evaluation (`qa/llm_eval/ragas_eval`)

VeriCoach includes an automated RAG triaging framework using Ragas and disk-cached LLM judges across English, Hindi, and Telugu. See full documentation in [docs/RAGAS_EVALUATION.md](docs/RAGAS_EVALUATION.md).

### Core Metrics

- **`context_precision`**: Signal-to-noise ratio in retrieved context chunks.
- **`context_recall`**: Completeness of retrieved contexts relative to reference ground truth.
- **`faithfulness`**: Groundedness of generated answers; penalizes hallucinations.
- **`answer_relevancy`**: Directness of the response without evasion or topic drift.

### Failure Attribution Workflow

- **Low Precision/Recall**: Retriever failure — adjust chunk size, top-$k$, or multilingual indexing.
- **Low Faithfulness**: Generator failure — tune system prompt constraints or temperature.
- **Unanswerable / Refusal**: Safe refusals are scored with 1.0 faithfulness.

### Metric Limits & Evaluation Biases

- **LLM Judge Biases**: Sycophancy toward own output format, length bias favoring verbose answers, and position bias ("lost in the middle").
- **Non-English Quality**: Indic token fragmentation, code-mixing in financial terms, and semantic drift in multilingual judges (e.g., lower judge sensitivity for Telugu).

## LLM Providers

| Provider | Config Env Var | Notes |
|---|---|---|
| `gemini` | `GOOGLE_API_KEY` | Default production provider via Gemini 1.5 Flash |
| `mock` | `LLM_PROVIDER=mock` | Deterministic, zero-network, derived SHA-256 embeddings for CI |
| `ollama` | `OLLAMA_BASE_URL` | Optional local LLMs (e.g. Llama 3) |

## Quality & Compliance Standards

- **Synthetic Data Guarantee**: All personal data (names, PAN numbers `AAAAA1234A`, 12-digit Aadhaar `[2-9]...`, UPI handles, balances) are strictly fake, generated dynamically via Faker.
- **Multilingual Support**: First-class support for English (`en`), Hindi (`hi`), and Telugu (`te`).
- **Linters & Code Style**: Strict enforcement via `ruff` and `black` on Python 3.11, strict TypeScript compilation for frontend.
- **Total Test Count**: 99 automated tests passing across `app/` and `qa/`.
