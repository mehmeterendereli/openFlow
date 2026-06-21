PYTHON := .venv/bin/python
PIP := uv pip
NPM := npm

.PHONY: setup test smoke backend frontend

setup:
	uv venv .venv
	$(PIP) install -r backend/requirements-dev.txt
	cd frontend && $(NPM) ci

test:
	$(PYTHON) -m ruff check backend automation scripts
	$(PYTHON) -m pytest
	cd frontend && $(NPM) run test && $(NPM) run typecheck && $(NPM) run build

smoke:
	$(PYTHON) -m scripts.e2e_smoke

backend:
	$(PYTHON) -m uvicorn backend.app.main:app --reload --port 8000

frontend:
	cd frontend && $(NPM) run dev
