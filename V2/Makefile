PYTHON ?= python3
PNPM ?= pnpm

.PHONY: install dev-web dev-api lint test build

install:
	$(PNPM) install
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install -r python-requirements.txt

dev-web:
	$(PNPM) dev:web

dev-api:
	.venv/bin/uvicorn mindfolio_api.main:app --reload --port 8000

lint:
	$(PNPM) lint:web

test:
	$(PNPM) test:web
	.venv/bin/python -m pytest packages/mindfolio-core/tests apps/api/tests apps/ai-training/tests

build:
	$(PNPM) build:web
