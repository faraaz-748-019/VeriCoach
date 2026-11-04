"""Generates a comprehensive executive and engineering project report in DOCX format for VeriCoach.

Includes all system features, 7-layer QA architecture, empirical results,
defect register (KF-001 through KF-006), interview highlights, resume bullets,
and embedded visual figures.
"""

from __future__ import annotations

import pathlib

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor

# ── Color Palette ─────────────────────────────────────────────────────────────
COLOR_PRIMARY_NAVY = RGBColor(27, 54, 93)  # #1B365D
COLOR_SECONDARY_TEAL = RGBColor(2, 132, 199)  # #0284C7
COLOR_DARK_SLATE = RGBColor(51, 65, 85)  # #334155
COLOR_BODY_TEXT = RGBColor(30, 41, 59)  # #1E293B
COLOR_SUCCESS_GREEN = RGBColor(16, 185, 129)  # #10B981
COLOR_MUTED_GRAY = RGBColor(100, 116, 139)  # #64748B

HEX_PRIMARY_NAVY = "1B365D"
HEX_LIGHT_BG = "F8FAFC"
HEX_BORDER = "CBD5E1"
HEX_HEADER_BG = "1E293B"
HEX_CALLOUT_BG = "F1F5F9"
HEX_ACCENT_LINE = "0284C7"


def set_cell_background(cell, hex_color: str) -> None:
    """Apply background fill color to a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tc_pr.append(shd)


def set_cell_margins(
    cell, top: int = 120, bottom: int = 120, left: int = 180, right: int = 180
) -> None:
    """Set cell internal padding in twips."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = parse_xml(
        f"<w:tcMar {nsdecls('w')}>"
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f"</w:tcMar>"
    )
    tc_pr.append(tc_mar)


def add_callout(doc: Document, text: str, title: str = "KEY HIGHLIGHT") -> None:
    """Create a shaded callout block with a left accent border."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, HEX_CALLOUT_BG)
    set_cell_margins(cell, top=160, bottom=160, left=240, right=200)

    # Set left border accent
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f"<w:tcBorders {nsdecls('w')}>"
        f'<w:left w:val="single" w:sz="36" w:space="0" w:color="{HEX_ACCENT_LINE}"/>'
        f'<w:top w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:bottom w:val="none"/>'
        f"</w:tcBorders>"
    )
    tc_pr.append(borders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    run_t = p.add_run(f"■ {title}: ")
    run_t.bold = True
    run_t.font.name = "Calibri"
    run_t.font.size = Pt(10.5)
    run_t.font.color.rgb = COLOR_SECONDARY_TEAL

    run_b = p.add_run(text)
    run_b.font.name = "Calibri"
    run_b.font.size = Pt(10.5)
    run_b.font.color.rgb = COLOR_BODY_TEXT

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_styled_heading(doc: Document, text: str, level: int) -> None:
    """Add customized heading with consistent hierarchy and colors."""
    h = doc.add_heading(text, level=level)
    h.paragraph_format.keep_with_next = True
    run = h.runs[0]
    run.font.name = "Calibri"

    if level == 1:
        run.font.size = Pt(20)
        run.bold = True
        run.font.color.rgb = COLOR_PRIMARY_NAVY
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(6)
    elif level == 2:
        run.font.size = Pt(14)
        run.bold = True
        run.font.color.rgb = COLOR_SECONDARY_TEAL
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)
    elif level == 3:
        run.font.size = Pt(11.5)
        run.bold = True
        run.font.color.rgb = COLOR_DARK_SLATE
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(2)


def style_table(tbl, col_widths: list[float]) -> None:
    """Apply styling, borders, alternating colors, and alignment to a table."""
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    # Apply column widths and styles
    for row_idx, row in enumerate(tbl.rows):
        is_header = row_idx == 0
        for col_idx, cell in enumerate(row.cells):
            cell.width = Inches(col_widths[col_idx])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=100, bottom=100, left=140, right=140)

            if is_header:
                set_cell_background(cell, HEX_HEADER_BG)
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(2)
                    for r in p.runs:
                        r.bold = True
                        r.font.name = "Calibri"
                        r.font.size = Pt(9.5)
                        r.font.color.rgb = RGBColor(255, 255, 255)
            else:
                bg_color = HEX_LIGHT_BG if row_idx % 2 == 1 else "FFFFFF"
                set_cell_background(cell, bg_color)
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(1)
                    p.paragraph_format.space_after = Pt(1)
                    for r in p.runs:
                        r.font.name = "Calibri"
                        r.font.size = Pt(9.0)
                        r.font.color.rgb = COLOR_BODY_TEXT

            # Subtle cell border
            tc_pr = cell._tc.get_or_add_tcPr()
            borders = parse_xml(
                f"<w:tcBorders {nsdecls('w')}>"
                f'<w:top w:val="single" w:sz="4" w:space="0" w:color="{HEX_BORDER}"/>'
                f'<w:left w:val="single" w:sz="4" w:space="0" w:color="{HEX_BORDER}"/>'
                f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="{HEX_BORDER}"/>'
                f'<w:right w:val="single" w:sz="4" w:space="0" w:color="{HEX_BORDER}"/>'
                f"</w:tcBorders>"
            )
            tc_pr.append(borders)


def add_figure(
    doc: Document, image_path: str, caption: str, width_in: float = 6.0
) -> None:
    """Embed an image with a centered italicized caption."""
    p_img = pathlib.Path(image_path)
    if not p_img.exists():
        return

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(p_img), width=Inches(width_in))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(10)
    run_cap = p_cap.add_run(f"Figure: {caption}")
    run_cap.font.name = "Calibri"
    run_cap.font.size = Pt(9.0)
    run_cap.italic = True
    run_cap.font.color.rgb = COLOR_MUTED_GRAY


def generate_report(output_path: str) -> None:
    doc = Document()

    # Page Margins (1 inch all around)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # ── Title Page / Header Block ────────────────────────────────────────────
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(24)
    title_p.paragraph_format.space_after = Pt(4)
    run_title = title_p.add_run("VeriCoach Project Report")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(28)
    run_title.bold = True
    run_title.font.color.rgb = COLOR_PRIMARY_NAVY

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_before = Pt(0)
    sub_p.paragraph_format.space_after = Pt(16)
    run_sub = sub_p.add_run(
        "Multilingual Personal-Finance Assistant & 7-Layer Quality-Engineering Platform"
    )
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(14)
    run_sub.font.color.rgb = COLOR_SECONDARY_TEAL

    # Metadata Grid
    meta_tbl = doc.add_table(rows=4, cols=2)
    meta_data = [
        ("Assessment Date", "November 5, 2026"),
        ("System Architecture", "Monorepo (app/ + qa/ + frontend/ + scripts/)"),
        ("Supported Languages", "English, Hindi (Devanagari), Telugu (తెలుగు)"),
        ("Document Version", "v1.0.0 (Portfolio Production Release)"),
    ]
    for r_idx, (k, v) in enumerate(meta_data):
        row = meta_tbl.rows[r_idx]
        cell_k, cell_v = row.cells[0], row.cells[1]

        pk = cell_k.paragraphs[0]
        rk = pk.add_run(k)
        rk.bold = True
        rk.font.name = "Calibri"
        rk.font.size = Pt(9.5)
        rk.font.color.rgb = COLOR_DARK_SLATE

        pv = cell_v.paragraphs[0]
        rv = pv.add_run(v)
        rv.font.name = "Calibri"
        rv.font.size = Pt(9.5)
        rv.font.color.rgb = COLOR_BODY_TEXT

    style_table(meta_tbl, [2.2, 4.3])
    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ── 1. Executive Summary ─────────────────────────────────────────────────
    add_styled_heading(doc, "1. Executive Summary", level=1)

    p = doc.add_paragraph(
        "VeriCoach is a comprehensive personal-finance application tailored for Indian retail investors, "
        "providing conversational advisory across English, Hindi, and Telugu. Unlike conventional wrappers, "
        "VeriCoach pairs its core Retrieval-Augmented Generation (RAG) assistant with an industrial-grade "
        "7-layer Quality Engineering (QE) platform that continuously audits the system for hallucinations, "
        "guaranteed return claims, prompt injections, PII leakage, WCAG 2.1 AA accessibility, and API contract stability."
    )
    p.paragraph_format.space_after = Pt(6)

    add_callout(
        doc,
        "Every numerical metric, test result, and evaluation score in this report is derived exclusively "
        "from reproducible execution outputs stored in the results/ directory.",
        title="EMPIRICAL RIGOR & ZERO CLAIMS WITHOUT REAL RUNS",
    )

    # ── 2. System Architecture ───────────────────────────────────────────────
    add_styled_heading(doc, "2. System Architecture & Monorepo Design", level=1)

    p = doc.add_paragraph(
        "The repository is architected as an atomic monorepo ensuring synchronized evolution between application code and test suites:"
    )
    p.paragraph_format.space_after = Pt(4)

    arch_items = [
        (
            "app/ (Backend Assistant)",
            "FastAPI backend, Chroma vector database with 30 curated financial education corpus documents, LangChain orchestrator, baseline safety guardrails, regex PII masking, and multi-provider abstraction (Gemini 1.5 Flash, deterministic offline Mock, Ollama).",
        ),
        (
            "qa/ (Quality Platform)",
            "Full testing harness comprising contract fuzzing (Schemathesis), RAG metrics (Ragas, DeepEval), red-teaming (Promptfoo), judge reliability (Cohen's Kappa), web UI (Playwright, Selenium, Axe-Core), and mobile automation (Appium 2.x).",
        ),
        (
            "frontend/ & app/frontend/",
            "Multilingual React 18 + Vite desktop web interface and Capacitor 7 native Android wrapper (com.vericoach.app) supporting dynamic script rendering and citation inspection.",
        ),
        (
            "scripts/ & results/",
            "Release Quality Gate (quality_gate.py) enforcing mathematical thresholds, history tracking (history.csv), and automated trend charting (trend_chart.png).",
        ),
    ]
    for name, desc in arch_items:
        bp = doc.add_paragraph(style="List Bullet")
        bp.paragraph_format.space_after = Pt(2)
        r_b = bp.add_run(f"{name}: ")
        r_b.bold = True
        r_b.font.color.rgb = COLOR_DARK_SLATE
        bp.add_run(desc)

    add_figure(
        doc,
        "qa/tests/web/snapshots/main_screen.png",
        "VeriCoach Multilingual Web Chat Interface (Playwright Baseline Snapshot)",
        width_in=5.5,
    )

    # ── 3. The 7-Layer Quality Engineering Matrix ────────────────────────────
    add_styled_heading(doc, "3. The 7-Layer Quality-Engineering Matrix", level=1)

    p = doc.add_paragraph(
        "To mitigate domain-specific risks in personal finance (hallucinations, privacy breaches, regulatory violations), "
        "VeriCoach implements an adaptive 7-layer verification pyramid:"
    )
    p.paragraph_format.space_after = Pt(4)

    matrix_tbl = doc.add_table(rows=8, cols=4)
    matrix_headers = [
        "Layer",
        "Target Scope",
        "Tooling & Frameworks",
        "Primary Gates / SLA",
    ]
    for c_idx, h_text in enumerate(matrix_headers):
        matrix_tbl.rows[0].cells[c_idx].paragraphs[0].text = h_text

    layers = [
        (
            "Layer 1: Unit & Component",
            "RAG chunking, embedder, retriever, i18n catalogs, synthetic Faker data",
            "pytest, pytest-asyncio, Faker",
            "100% pass, zero network",
        ),
        (
            "Layer 2: Contract & Fuzzing",
            "OpenAPI 3.1 conformance, breaking changes, negative input fuzzing",
            "schemathesis, pytest",
            "Zero breaking changes, no 500s",
        ),
        (
            "Layer 3: LLM Quality & RAG",
            "Context precision, recall, faithfulness, relevancy, judge agreement",
            "ragas, deepeval, langsmith",
            "Faithfulness ≥ 0.85, κ ≥ 0.70",
        ),
        (
            "Layer 4: Security & Safety",
            "Prompt injection, DAN jailbreaks, PII masking, error sanitization",
            "promptfoo, custom scanners",
            "ASR = 0.0%, 0 PII leaks",
        ),
        (
            "Layer 5: Web UI & a11y",
            "Cross-browser flows, keyboard navigation, WCAG 2.1 AA audits",
            "playwright, selenium, axe-core",
            "0 critical/serious a11y issues",
        ),
        (
            "Layer 6: Mobile Automation",
            "Native Android flows, script rendering, background/foreground state",
            "appium 2.x, uiautomator2",
            "Conversation state preserved",
        ),
        (
            "Layer 7: CI/CD Quality Gate",
            "Automated release blocking, historical trend logging, trend charts",
            "quality_gate.py, matplotlib",
            "Gate status = PASS",
        ),
    ]
    for r_idx, row_data in enumerate(layers, start=1):
        for c_idx, val in enumerate(row_data):
            matrix_tbl.rows[r_idx].cells[c_idx].paragraphs[0].text = val

    style_table(matrix_tbl, [1.5, 2.0, 1.6, 1.4])
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # ── 4. Comprehensive Empirical Results ───────────────────────────────────
    add_styled_heading(
        doc, "4. Comprehensive Empirical Results & Verification", level=1
    )

    p = doc.add_paragraph(
        "The following master results table synthesizes all empirical evaluations executed across the project lifecycle. "
        "Every entry maps directly to an authoritative artifact in the results/ directory:"
    )
    p.paragraph_format.space_after = Pt(4)

    res_tbl = doc.add_table(rows=17, cols=5)
    res_headers = [
        "Evaluation Dimension",
        "Run Artifact",
        "Metric Name",
        "Observed Score",
        "Target SLA",
    ]
    for c_idx, h_text in enumerate(res_headers):
        res_tbl.rows[0].cells[c_idx].paragraphs[0].text = h_text

    raw_results = [
        (
            "Adversarial Defense",
            "promptfoo_security_results.json",
            "Attack Pass Rate",
            "12 / 12 (100.0%)",
            "100% blocked",
        ),
        (
            "Security Assertions",
            "promptfoo_security_results.json",
            "assertPassCount",
            "96 / 96 passed",
            "96 assertions",
        ),
        (
            "Attack Success Rate",
            "promptfoo_security_results.json",
            "ASR",
            "0.0%",
            "≤ 0.00",
        ),
        (
            "Adversarial Latency",
            "promptfoo_security_results.json",
            "totalLatencyMs",
            "909 ms (12 probes)",
            "< 5000 ms",
        ),
        (
            "Judge Accuracy",
            "judge_reliability_results.json",
            "overall.accuracy",
            "96.7% (29/30)",
            "≥ 90.0%",
        ),
        (
            "Judge Reliability",
            "judge_reliability_results.json",
            "Cohen's Kappa (κ)",
            "0.8446 (Almost Perfect)",
            "≥ 0.70",
        ),
        (
            "English Judge κ",
            "judge_reliability_results.json",
            "by_language.en.kappa",
            "1.0000 (10/10)",
            "≥ 0.80",
        ),
        (
            "Hindi Judge κ",
            "judge_reliability_results.json",
            "by_language.hi.kappa",
            "1.0000 (10/10)",
            "≥ 0.80",
        ),
        (
            "Telugu Judge κ",
            "judge_reliability_results.json",
            "by_language.te.kappa",
            "0.6296 (9/10)",
            "≥ 0.60",
        ),
        (
            "DeepEval Faithfulness",
            "deepeval_20261104.json",
            "faithfulness",
            "1.0000 (100.0%)",
            "≥ 0.85",
        ),
        (
            "DeepEval Hallucination",
            "deepeval_20261104.json",
            "hallucination_rate",
            "0.0000 (0.0%)",
            "≤ 0.10",
        ),
        (
            "LangSmith Refusal",
            "langsmith_experiment_results.json",
            "refusal_correctness",
            "1.0000 (100.0%)",
            "≥ 95.0%",
        ),
        (
            "LangSmith Latency SLA",
            "langsmith_experiment_results.json",
            "latency_sla (< 5s)",
            "1.0000 (100.0%)",
            "≥ 90.0%",
        ),
        (
            "Ragas Overall Faithfulness",
            "ragas_20261104.json",
            "faithfulness",
            "0.9211 (92.1%)",
            "≥ 0.85",
        ),
        (
            "Ragas Disk Cache Hits",
            "ragas_20261104.json",
            "cache_stats.hit_ratio",
            "1.0000 (100.0%)",
            "100% cached",
        ),
        (
            "Quality Gate History",
            "history.csv",
            "Historical Tracked Runs",
            "5 runs (0 PII leaks)",
            "PASS on master",
        ),
    ]
    for r_idx, row_data in enumerate(raw_results, start=1):
        for c_idx, val in enumerate(row_data):
            res_tbl.rows[r_idx].cells[c_idx].paragraphs[0].text = val

    style_table(res_tbl, [1.5, 1.8, 1.3, 1.1, 0.8])
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    add_figure(
        doc,
        "results/trend_chart.png",
        "Quality Gate Historical Multi-Metric Trend Chart (Faithfulness, ASR, PII Leaks)",
        width_in=5.8,
    )

    # ── 5. Judge Reliability & Multilingual Consistency Study ─────────────────
    add_styled_heading(doc, "5. LLM Judge Reliability & Cross-Lingual Study", level=1)

    p = doc.add_paragraph(
        "A critical innovation in VeriCoach is validating the automated LLM judge itself before trusting it to gate releases. "
        "In judge_reliability_results.json, we conducted a stratified study comparing human expert labels against automated judge "
        "classifications across 30 golden test cases (10 each for EN, HI, TE) across 4 categories (answerable, unanswerable, "
        "personalized advice refusals, and adversarial probes). The overall Cohen's Kappa reached κ = 0.8446 ('Almost Perfect Agreement')."
    )
    p.paragraph_format.space_after = Pt(4)

    add_figure(
        doc,
        "docs/charts/judge_confusion_matrix.png",
        "Confusion Matrix: Human Expert vs Automated LLM Judge (Stratified N=30)",
        width_in=4.8,
    )
    add_figure(
        doc,
        "docs/charts/judge_agreement_by_language.png",
        "Judge Agreement & Cohen's Kappa Stratified by Language (EN, HI, TE)",
        width_in=4.8,
    )

    p2 = doc.add_paragraph(
        "In multilingual_consistency_results.json, we evaluated 20 parallel trilingual questions across 60 cross-lingual pairs. "
        "The evaluation uncovered KF-006: an overall consistency rate of 33.3% in the offline mock embedder due to Indic compound word "
        "fragmentation, proving that production multilingual RAG requires dense neural representations (Google text-embedding-004)."
    )
    p2.paragraph_format.space_after = Pt(4)

    add_figure(
        doc,
        "docs/charts/multilingual_consistency_breakdown.png",
        "Cross-Lingual Pairwise Consistency Rates (EN-HI, EN-TE, HI-TE)",
        width_in=4.8,
    )
    add_figure(
        doc,
        "docs/charts/multilingual_similarity_distribution.png",
        "Cosine Similarity Distribution Across 60 Cross-Lingual Pairs",
        width_in=4.8,
    )

    # ── 6. Defect Register & Bug Resolution History (KF-001 to KF-006) ───────
    add_styled_heading(
        doc, "6. Defect Register & Resolution History (KF-001 - KF-006)", level=1
    )

    p = doc.add_paragraph(
        "In strict adherence to quality engineering ethics, test failures were never weakened or deleted. "
        "Every defect discovered during testing was documented, analyzed, and resolved or tracked:"
    )
    p.paragraph_format.space_after = Pt(4)

    defects = [
        (
            "KF-001: 500 Internal Server Error on GET /api/v1/synthetic-user",
            "High",
            "Resolved",
            "Discovered by Schemathesis fuzzing. generate_user() returned a Python dataclass lacking .model_dump(). Fixed in app/backend/main.py by supporting both dataclasses.asdict() and Pydantic model_dump().",
        ),
        (
            "KF-002: WCAG 2.1 AA Critical Violation (user-scalable=no)",
            "High",
            "Resolved",
            "Discovered by Axe-Core accessibility scan. <meta name='viewport'> contained maximum-scale=1.0, user-scalable=no locking device zoom. Fixed in app/frontend/index.html to ensure compliance with WCAG 2.1 SC 1.4.4.",
        ),
        (
            "KF-003: Raw Sensitive PII Persisted in Feedback Store",
            "Critical",
            "Resolved",
            "Discovered by deterministic security scanning. Feedback comments submitted to POST /v1/feedback stored raw PAN and phone numbers without masking. Fixed by applying mask_pii() before writing to feedback stores and chat answers.",
        ),
        (
            "KF-004: Direct Prompt Injection & Jailbreak Bypass",
            "Critical",
            "Resolved",
            "Discovered by Promptfoo adversarial evaluation. Queries with DAN personas or illicit guidance (money laundering, salary slip forgery) bypassed baseline guardrails. Fixed by expanding regex guardrails in app/backend/guardrails.py (ASR = 0.0%).",
        ),
        (
            "KF-005: Traceback & File Path Leakage on HTTP 500",
            "Medium",
            "Resolved",
            "Discovered by error disclosure audit. Unhandled exceptions risked leaking internal file paths and stack frames. Fixed with global Exception handler returning sanitized JSON and masking PII in JSONFormatter exception records.",
        ),
        (
            "KF-006: Multilingual Semantic Drift in Offline Mock Embeddings",
            "Medium",
            "Tracked / Open",
            "Discovered by cross-lingual consistency evaluation. Deterministic lexical hash collisions dropped cross-lingual consistency to 33.3% on complex Indic inflections. Documented as known mock limitation; production utilizes Google text-embedding-004.",
        ),
    ]
    for kf_id, sev, status, desc in defects:
        bp = doc.add_paragraph()
        bp.paragraph_format.space_before = Pt(4)
        bp.paragraph_format.space_after = Pt(2)
        r_id = bp.add_run(f"■ {kf_id} ")
        r_id.bold = True
        r_id.font.name = "Calibri"
        r_id.font.size = Pt(10.0)
        r_id.font.color.rgb = COLOR_PRIMARY_NAVY

        r_meta = bp.add_run(f"[{sev} Severity | Status: {status}]\n")
        r_meta.bold = True
        r_meta.font.name = "Calibri"
        r_meta.font.size = Pt(9.0)
        r_meta.font.color.rgb = (
            COLOR_SUCCESS_GREEN if status == "Resolved" else COLOR_SECONDARY_TEAL
        )

        r_desc = bp.add_run(desc)
        r_desc.font.name = "Calibri"
        r_desc.font.size = Pt(9.5)
        r_desc.font.color.rgb = COLOR_BODY_TEXT

    # ── 7. High-Impact Resume Bullets ────────────────────────────────────────
    add_styled_heading(doc, "7. High-Impact Resume Bullets (Traceable Claims)", level=1)

    bullets = [
        "Architected an automated 7-layer quality engineering gate enforcing mathematical release thresholds (faithfulness ≥ 0.85, hallucination rate = 0.0%, breaking changes = 0), validating 5 historical releases in results/history.csv and blocking regressions via GitHub Actions.",
        "Red-teamed multilingual financial RAG pipeline using Promptfoo across 12 adversarial attack vectors (DAN jailbreaks, prompt injection, illicit financial advice), achieving 100% test pass rate, 96/96 passing security assertions, and a 0.0% Attack Success Rate (results/promptfoo_security_results.json).",
        "Spearheaded an empirical Judge Reliability Study across 30 golden test cases in English, Hindi, and Telugu, demonstrating a 96.7% concordance rate and a Cohen's Kappa inter-rater agreement of κ = 0.8446 ('Almost perfect agreement') between human annotations and the automated LLM judge (results/judge_reliability_results.json).",
        "Developed a cross-lingual consistency evaluator benchmarking 20 parallel trilingual financial queries across 60 pairwise combinations; diagnosed a 33.3% lexical hash consistency rate in offline mock embeddings (average similarity 0.42-0.46) to establish the architectural requirement for dense multilingual neural embeddings (results/multilingual_consistency_results.json).",
        "Implemented automated Ragas and DeepEval diagnostic harnesses across 30 financial corpus documents, verifying 100% faithfulness and 0.0% hallucination rate across DeepEval test runs with 100% disk cache hit ratio (results/deepeval_20261104.json, results/ragas_20261104.json).",
        "Integrated LangSmith distributed tracing with hierarchical spans (rag_retrieval → assemble_prompt → llm_generate), achieving 100% refusal correctness, 100% safety compliance, and 100% latency SLA adherence (< 5.0s) across automated experiment runs (results/langsmith_experiment_results.json).",
    ]
    for b in bullets:
        bp = doc.add_paragraph(style="List Bullet")
        bp.paragraph_format.space_before = Pt(2)
        bp.paragraph_format.space_after = Pt(3)
        r = bp.add_run(b)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.color.rgb = COLOR_BODY_TEXT

    # ── 8. Production Scalability Roadmap ─────────────────────────────────────
    add_styled_heading(doc, "8. Production Scalability & Future Roadmap", level=1)

    roadmap_items = [
        (
            "Vector Store Transition",
            "Migrate from in-memory Chroma to distributed Qdrant or pgvector with persistent HNSW index structures and horizontal read replicas.",
        ),
        (
            "Multilingual Neural Embeddings",
            "Transition from offline deterministic mock embeddings to Google's text-embedding-004 on Vertex AI, eliminating Indic tokenization fragmentation.",
        ),
        (
            "Continuous Cloud Device Testing",
            "Integrate the Appium Android test suite with AWS Device Farm or BrowserBase cloud emulators to test physical screen sizes and battery throttling.",
        ),
        (
            "Dynamic Guardrail Adaptability",
            "Deploy secondary small-parameter classifier models (e.g. Llama Guard 3) alongside regex filters for multi-turn semantic jailbreak detection.",
        ),
    ]
    for title, text in roadmap_items:
        bp = doc.add_paragraph(style="List Bullet")
        bp.paragraph_format.space_before = Pt(2)
        bp.paragraph_format.space_after = Pt(2)
        r_b = bp.add_run(f"{title}: ")
        r_b.bold = True
        r_b.font.color.rgb = COLOR_DARK_SLATE
        bp.add_run(text)

    # Save Document
    out_file = pathlib.Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_file))
    print(f"Report successfully generated at: {out_file.resolve()}")


if __name__ == "__main__":
    generate_report("docs/VeriCoach_Project_Report.docx")
