# VeriCoach: Verifiable Engineering Evidence for Resume

Each bullet below represents an empirically verified engineering achievement. In accordance with zero-fabrication quality principles, every single metric and claim is traceable to an exact version-controlled artifact file and data key in `results/` or `docs/KNOWN_FAILURES.md`.

---

### Bullet 1: Multi-Layer Test Automation Framework & Flakiness Tracking
- **Bullet Text**: Designed and deployed a cross-platform test automation suite spanning FastAPI backend endpoints (20 tests, 6.69s execution), Playwright web UI (10 tests, 80.0% 3-run consistency), and Selenium cross-browser smoke tests across headless Chrome and Firefox (10 tests, 90.0% 3-run consistency), incorporating automated flakiness detection and JUnit XML metric aggregation.
- **Traceability**:
  - `results/test_summary.json` -> `suites.api.summary.passed: 20`, `suites.api.summary.duration_seconds: 6.685`
  - `results/test_summary.json` -> `suites.web_playwright.flakiness.consistency_rate: 0.8` (flaky tests: `test_chat_happy_path_hindi`, `test_chat_happy_path_telugu`)
  - `results/test_summary.json` -> `suites.web_selenium.flakiness.consistency_rate: 0.9` (flaky test: `test_smoke_citations_disclosure[firefox]`)
  - `results/junit_api.xml`, `results/junit_playwright_run1.xml`, `results/junit_selenium_run1.xml`

---

### Bullet 2: API Contract Fuzzing & Uncaught 500 Crash Discovery (KF-001)
- **Bullet Text**: Implemented property-based OpenAPI fuzz testing using Schemathesis (15 hypothesis test cases per endpoint), discovering and resolving a critical unhandled HTTP 500 `AttributeError` (KF-001) caused by dataclass serialization mismatches on `/api/v1/synthetic-user`, preventing server crash cascades in production.
- **Traceability**:
  - `docs/KNOWN_FAILURES.md` -> Section `## KF-001: 500 Internal Server Error on GET /api/v1/synthetic-user`
  - `qa/tests/api/test_schemathesis.py` -> `test_schemathesis_no_server_errors`
  - `app/backend/main.py` -> line 434 (`legacy_synthetic_user` dataclass serialization fix)

---

### Bullet 3: Automated Accessibility Auditing & Compliance Remediation (KF-002)
- **Bullet Text**: Integrated Axe-Core automated accessibility scanning within Playwright end-to-end tests, intercepting a high-severity WCAG 2.1 AA violation (KF-002) caused by viewport zoom suppression (`user-scalable=no`), restoring mobile assistive zoom capabilities and establishing zero-violation CI gating.
- **Traceability**:
  - `docs/KNOWN_FAILURES.md` -> Section `## KF-002: WCAG 2.1 AA Critical Accessibility Violation`
  - `qa/tests/web/test_playwright_chat.py` -> `test_accessibility_scan_with_axe`
  - `app/frontend/index.html` -> line 6 (`meta name="viewport"` remediation)

---

### Bullet 4: Automated PII Leak Interception in Feedback Logging (KF-003)
- **Bullet Text**: Developed a deterministic multi-pattern PII audit engine detecting Indian regulatory identifiers (PAN, Aadhaar, Phone, Email, UPI); uncovered a critical security flaw (KF-003) persisting unredacted customer PAN and phone numbers in user feedback stores, remediating the data pipeline with zero-leak masking.
- **Traceability**:
  - `docs/KNOWN_FAILURES.md` -> Section `## KF-003: Raw Sensitive PII Persisted Unredacted in Feedback Store`
  - `qa/tests/test_pii_guards.py` -> `test_feedback_store_pii_leak`
  - `results/history.csv` -> column `pii_leaks: 0`

---

### Bullet 5: Mobile Appium Automation Suite for Android
- **Bullet Text**: Engineered an Appium 2.x / UiAutomator2 native Android test framework for Capacitor (`com.vericoach.app`), establishing automated flows for conversation state retention during backgrounding/foregrounding, portrait-to-landscape layout responsiveness, network offline mode banners, and failure video recording.
- **Traceability**:
  - `qa/mobile/test_mobile_chat.py` -> `test_mobile_launch_and_ask_question_english`, `test_mobile_multilingual_script_rendering`, `test_mobile_background_foreground_state_retention`
  - `qa/mobile/conftest.py` -> lines 40-115 (`mobile_driver` lifecycle, automated screenshot and screen recording capture)
  - `scripts/check_mobile_env.ps1` -> environment verification tool for ADB, Appium 2.x, and APK installation

---

### Bullet 6: Multi-Stage Adversarial Red-Teaming (Regression vs Held-Out Attacks)
- **Bullet Text**: Audited safety guardrails across 3 distinct test suites: verified 100% block rate (0.0% ASR) on the 12-case regression suite; exposed a 43.33% Attack Success Rate (95% Wilson CI: [27.38%, 60.80%]) on an unseen 30-item multilingual held-out set (KF-007); resolved Indic vulnerabilities down to 0.00% ASR ([0.00%, 11.35%]); and documented a 33.33% ASR ([15.18%, 58.29%]) on a second fresh 15-case suite (KF-008), establishing empirical limits of heuristic regex guardrails.
- **Traceability**:
  - Regression Suite (n=12): `results/promptfoo_security_results.json` -> `metrics.testPassCount: 12`, `suite_type: "regression_suite"`
  - Held-Out Suite v1 Pre-Fix (n=30): `results/held_out_adversarial_results_pre_fix.json` -> `total_attacks: 30`, `successful_breaches: 13`, `attack_success_rate: 0.4333`, `wilson_ci_95: [0.2738, 0.608]`
  - Held-Out Suite v1 Post-Fix (n=30): `results/held_out_adversarial_results_post_fix.json` -> `total_attacks: 30`, `successful_breaches: 0`, `attack_success_rate: 0.0`, `wilson_ci_95: [0.0, 0.1135]`
  - Fresh Held-Out Suite v2 (n=15): `results/fresh_adversarial_v2_results.json` -> `total_attacks: 15`, `successful_breaches: 5`, `attack_success_rate: 0.3333`, `wilson_ci_95: [0.1518, 0.5829]`
  - `docs/KNOWN_FAILURES.md` -> `KF-007` and `KF-008`

---

### Bullet 7: LLM-as-a-Judge Reliability & Human Inter-Rater Study
- **Bullet Text**: Conducted an empirical inter-rater reliability study ($N=30$ blinded samples across English, Hindi, and Telugu) auditing automated LLM evaluation against human ground truth; exposed that naive rule-based judges yielded only 36.67% accuracy (11/30 concordant) and near-zero Cohen's Kappa ($\kappa = 0.029$, 95% bootstrap CI: [-0.0154, 0.0984]) due to keyword-bias over-grading and Indic misclassification, contrasting against Ragas faithfulness of 92.11% (mock baseline) and 100.0% on live Gemini (`gemini-3.5-flash-lite`, $n=6$).
- **Traceability**:
  - `results/judge_reliability_results.json` -> `overall.total_samples: 30`, `overall.matches: 11`, `overall.accuracy: 0.3667`, `overall.cohen_kappa: 0.029`, `overall.ci_95: [-0.0154, 0.0984]`
  - `results/judge_reliability_results.json` -> `by_language.en.accuracy: 0.5`, `by_language.hi.accuracy: 0.3`, `by_language.te.accuracy: 0.3`
  - `results/judge_reliability_results.json` -> `label_origin: "Human verified (job applicant ground truth)"`
  - `results/deepeval_live_20261105.json` -> `summary_metrics.faithfulness: 1.0`, `provider: "gemini"`, `model: "models/gemini-3.5-flash-lite"`
  - `results/ragas_20261104.json` -> `overall_scores.faithfulness: 0.9211`, `provider: "mock"`

