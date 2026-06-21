PYTHON := .venv/bin/python
PIP := uv pip
NPM := npm

.PHONY: setup setup-ai test smoke e2e backend backend-ai frontend

setup:
	uv venv .venv
	$(PIP) install -r backend/requirements-dev.txt
	cd frontend && $(NPM) ci

setup-ai:
	uv venv --python 3.9 .venv-musicgen
	uv pip install --python .venv-musicgen/bin/python -r backend/requirements.txt
	cd frontend && $(NPM) ci

test:
	$(PYTHON) -m ruff check backend automation scripts
	$(PYTHON) -m pytest
	cd frontend && $(NPM) run test && $(NPM) run typecheck && $(NPM) run build

smoke:
	$(PYTHON) -m scripts.e2e_smoke

e2e:
	cd frontend && npx playwright install chromium && npm run test:e2e

backend:
	$(PYTHON) -m uvicorn backend.app.main:app --reload --port 8000

backend-ai:
	.venv-musicgen/bin/python -m uvicorn backend.app.main:app --reload --port 8000

frontend:
	cd frontend && $(NPM) run dev
