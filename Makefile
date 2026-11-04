# VeriCoach QA Platform Automation Framework Makefile

PYTHON ?= uv run --directory qa --no-sync python
PYTEST ?= uv run --directory qa --no-sync pytest

.PHONY: test test-smoke test-web test-selenium test-parallel test-security eval-security report triage lint format docker-build docker-run help

help:
	@echo "VeriCoach QA Framework Targets:"
	@echo "  make test          - Run framework test suite with Allure raw results"
	@echo "  make test-smoke    - Run smoke tests"
	@echo "  make test-web      - Run Playwright Web UI test suite"
	@echo "  make test-selenium - Run Selenium cross-browser smoke suite"
	@echo "  make test-parallel - Run test suite with pytest-xdist parallel execution"
	@echo "  make test-security - Run deterministic AI security test suite"
	@echo "  make eval-security - Run promptfoo LLM adversarial evaluation and generate HTML report"
	@echo "  make report        - Generate Allure HTML report in qa/allure-report"
	@echo "  make triage        - Display latest triage.json failure summary"
	@echo "  make lint          - Check code quality with ruff and black"
	@echo "  make format        - Auto-format code with black and ruff"
	@echo "  make docker-build  - Build container image for the test framework"
	@echo "  make docker-run    - Run full test suite inside Docker"

test:
	$(PYTEST) qa/tests/sample -v --alluredir=qa/allure-results

test-smoke:
	$(PYTEST) qa/tests/sample -m smoke -v --alluredir=qa/allure-results

test-web:
	$(PYTEST) qa/tests/web -v --alluredir=qa/allure-results

test-selenium:
	$(PYTEST) qa/tests/web_selenium -v --alluredir=qa/allure-results

test-parallel:
	$(PYTEST) qa/tests/sample -n auto -v --alluredir=qa/allure-results

test-security:
	$(PYTEST) tests/security -v

eval-security:
	$(PYTHON) ../qa/llm_eval/promptfoo/run_security_eval.py

report:
	$(PYTHON) -m qa.framework.reporting.allure_report qa/allure-results qa/allure-report

triage:
	$(PYTHON) -c "import json, sys; sys.stdout.write(json.dumps(json.load(open('qa/triage.json')), indent=2) + '\n')"

lint:
	uv run --directory qa --no-sync ruff check qa/framework qa/tests
	uv run --directory qa --no-sync black --check qa/framework qa/tests

format:
	uv run --directory qa --no-sync ruff check --fix qa/framework qa/tests
	uv run --directory qa --no-sync black qa/framework qa/tests

docker-build:
	docker build -t vericoach-qa -f qa/Dockerfile .

docker-run:
	docker run --rm -v $(PWD)/qa/allure-report:/app/qa/allure-report vericoach-qa

