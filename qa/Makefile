# VeriCoach QA Subdirectory Makefile

PYTHON ?= uv run --no-sync python
PYTEST ?= uv run --no-sync pytest

.PHONY: test test-smoke test-api test-contract test-schemathesis newman export-openapi generate-postman test-parallel report triage lint format help

help:
	@echo "VeriCoach QA (Subdirectory) Targets:"
	@echo "  make test              - Run framework sample tests"
	@echo "  make test-smoke        - Run smoke tests"
	@echo "  make test-api          - Run API test suite (pytest -m api)"
	@echo "  make test-contract     - Run OpenAPI breaking contract test"
	@echo "  make test-schemathesis - Run Schemathesis property tests"
	@echo "  make newman            - Run Newman collection suite with htmlextra reporter"
	@echo "  make export-openapi    - Export fresh openapi.json"
	@echo "  make generate-postman  - Generate Postman collection & environments"
	@echo "  make test-parallel     - Run tests with pytest-xdist"
	@echo "  make report            - Compile Allure HTML report"
	@echo "  make triage            - Show triage summary"
	@echo "  make lint              - Lint qa/framework and tests"

test:
	$(PYTEST) tests/sample -v --alluredir=allure-results

test-smoke:
	$(PYTEST) tests/sample -m smoke -v --alluredir=allure-results

test-api:
	$(PYTEST) tests/api -m api -v --alluredir=allure-results

test-contract:
	$(PYTEST) tests/api/test_contract_breaking.py -v --alluredir=allure-results

test-schemathesis:
	$(PYTEST) tests/api/test_schemathesis.py -v --alluredir=allure-results

newman:
	$(PYTHON) api/run_newman.py

export-openapi:
	$(PYTHON) api/export_openapi.py

generate-postman:
	$(PYTHON) api/generate_postman.py

test-parallel:
	$(PYTEST) tests/sample -n auto -v --alluredir=allure-results

report:
	$(PYTHON) -m qa.framework.reporting.allure_report allure-results allure-report

triage:
	$(PYTHON) -c "import json, sys; sys.stdout.write(json.dumps(json.load(open('triage.json')), indent=2) + '\n')"

lint:
	uv run --no-sync ruff check framework tests
	uv run --no-sync black --check framework tests

format:
	uv run --no-sync ruff check --fix framework tests
	uv run --no-sync black framework tests

