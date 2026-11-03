# VeriCoach

A multilingual (English · Hindi · Telugu) personal-finance assistant with RAG, and a quality-engineering platform that tests it.

## Monorepo layout

```
VerCoach/
├── app/   – finance assistant (Python 3.11, FastAPI, LangChain)
└── qa/    – QA platform (DeepEval, Ragas, Playwright, Schemathesis)
```

## Quick start

```bash
# 1. Clone & enter
git clone <repo> && cd VerCoach

# 2. Copy env template
cp .env.example .env   # fill in GOOGLE_API_KEY

# 3. App – create venv & install
cd app
uv venv
uv pip install -e ".[dev]"

# 4. Run tests (MOCK provider – no network needed)
LLM_PROVIDER=mock pytest tests/ -v

# 5. Lint
ruff check app/ tests/
black --check app/ tests/
```

## LLM providers

| Provider | Env var | Notes |
|---|---|---|
| `gemini` | `GOOGLE_API_KEY` | Default, requires network |
| `mock` | — | Deterministic, no network, used in CI |
| `ollama` | `OLLAMA_BASE_URL` | Optional local models |

## Locales

`en` (English), `hi` (Hindi), `te` (Telugu)

## Docs

- [Known failures](docs/KNOWN_FAILURES.md)

