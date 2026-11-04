# Ragas Evaluation Framework for VeriCoach

VeriCoach evaluates its Retrieval-Augmented Generation (RAG) assistant across English, Hindi, and Telugu using [Ragas](https://docs.ragas.io/). The evaluation operates on the golden evaluation dataset (`qa/data/golden/golden_v1.jsonl`), runs queries through the real pipeline (`app/backend/main.py`), and calculates four standard RAG triaging metrics using LLM-as-a-judge and embeddings.

---

## 1. Metric Definitions & Interpretation

| Metric | What It Measures | Target Score | Diagnostic Meaning |
|---|---|---|---|
| **`context_precision`** | **Signal-to-noise ratio in retrieval**: Are the retrieved knowledge chunks actually relevant to the question, and are relevant chunks ranked at the top? | $\ge 0.70$ | **Low score**: Retrieval fetched irrelevant or noisy context. Requires tuning chunk size, embeddings, top-$k$, or metadata filtering. |
| **`context_recall`** | **Retrieval completeness**: Did the retrieved contexts include all the necessary facts required to formulate the reference answer? | $\ge 0.80$ | **Low score**: The retriever missed key source knowledge chunks. Requires checking index coverage, dense/sparse query expansion, or hybrid search. |
| **`faithfulness`** | **Groundedness & hallucination avoidance**: Can every factual claim in the generated answer be directly inferred from the retrieved contexts? | $\ge 0.85$ | **Low score**: The generator hallucinated external or unsubstantiated facts not present in retrieved context. Requires system prompt tuning or temperature reduction. |
| **`answer_relevancy`** | **Answer focus & directness**: Does the generated answer directly address the user's question without rambling, evasiveness, or introducing irrelevant digressions? | $\ge 0.80$ | **Low score**: The answer evaded the prompt, answered a different question, or was too verbose/vague. |

---

## 2. Triaging Failure Modes (Attribution Workflow)

When an evaluation item performs poorly, use the following decision matrix to pinpoint whether the issue is in the **Retriever** or the **Generator**:

```
                              Low Context Precision / Recall?
                                       /              \
                                     YES               NO
                                     /                  \
                        [Retriever Failure]       Low Faithfulness?
                        - Tune chunk size                /       \
                        - Re-index documents           YES        NO
                        - Hybrid dense/sparse          /           \
                                              [Generator]      Low Relevancy?
                                              Hallucination      /         \
                                              Prompt/Temp      YES          NO
                                                                /            \
                                                      Evasion / Drift    High Quality
```

1. **Retriever Error** (`context_recall < 0.7` or `context_precision < 0.6`):
   - Check `retrieved_contexts` in `results/ragas_YYYYMMDD.json` or `.csv`.
   - If contexts are empty or off-topic, verify query language alignment with document index language.
2. **Generator Error** (`faithfulness < 0.7` with high `context_recall`):
   - The LLM has the necessary facts in context, but introduced unsupported claims.
   - Adjust system prompt constraint: *"Answer only based on the provided context. If unknown, politely refuse."*
3. **Refusal & Safety Handling**:
   - For `unanswerable` and `advice_refusal` queries, polite refusal with empty contexts is considered fully faithful (faithfulness = 1.0) because no false facts were asserted.

---

## 3. Metric Limits & Evaluation Biases

When reviewing Ragas scores, keep the following known limitations in mind:

### A. Judge LLM Biases
- **Length Bias**: LLM judges systematically favor longer, verbose answers over concise answers, even when both convey identical facts.
- **Sycophancy & Self-Preference**: When using Gemini as a judge to evaluate a Gemini-generated answer, the judge may grade its own phrasing and formatting more leniently than an external model.
- **Position Bias**: In context precision, judges may overlook relevant evidence placed in the middle of long context windows ("lost in the middle").

### B. Non-English Quality Degradation (Hindi & Telugu)
- **Token Fragmentation**: Indic scripts (Devanagari, Telugu) require significantly more sub-word tokens per word than English. This increases judge latency and context truncation risk.
- **Semantic Translation Drift**: When evaluating Hindi (`hi`) or Telugu (`te`) items, embedding models and judge LLMs often exhibit lower semantic sensitivity compared to English. A factually accurate Telugu phrasing might receive lower `answer_relevancy` if the judge defaults to English reasoning internally.
- **Code-Mixing**: Mixed English-Hindi or English-Telugu financial terminology (e.g., "Mutual Fund SIP పెట్టుబడి") may confuse mono-lingual metric parsers. Multilingual embeddings (`text-embedding-004`) should always be configured for non-English benchmarks.

---

## 4. How to Run Ragas Evaluation

### Running via CLI

From the workspace root:

```bash
# 1. Deterministic offline run (MOCK provider, zero network, fast CI)
qa/.venv/Scripts/python.exe -m qa.llm_eval.ragas_eval.cli --limit 30 --provider mock

# 2. Re-run to verify disk cache hits (sub-second execution)
qa/.venv/Scripts/python.exe -m qa.llm_eval.ragas_eval.cli --limit 30 --provider mock

# 3. Full evaluation with Gemini LLM judge & text-embedding-004
export GOOGLE_API_KEY="your-google-api-key"
qa/.venv/Scripts/python.exe -m qa.llm_eval.ragas_eval.cli --limit 120 --provider gemini
```

### Running Automated Tests

```bash
qa/.venv/Scripts/pytest.exe qa/tests/test_ragas_eval.py -v
```

---

## 5. Reading Output Artifacts

Each evaluation run produces two timestamped artifacts in `results/`:

1. **`results/ragas_YYYYMMDD.json`**:
   - `summary.metrics`: Mean score across all items for all 4 metrics.
   - `summary.per_language`: Score breakdown for `en`, `hi`, `te`.
   - `summary.per_category`: Score breakdown for `answerable`, `unanswerable`, `advice_refusal`, `adversarial`.
   - `worst_10_items`: Full details of the 10 lowest-scoring items, including query, answer, ground truth, retrieved contexts, and individual metric scores.
2. **`results/ragas_YYYYMMDD.csv`**:
   - Tabular view for easy filtering and spreadsheet inspection in Excel, Google Sheets, or pandas.
