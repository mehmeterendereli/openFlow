# openFlow backend

The FastAPI service currently uses a deterministic mock synthesizer so the complete
workflow functions without CUDA, PyTorch, or model weights. Track metadata and job
state are persisted locally in SQLite under `backend/data/`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-dev.txt
uvicorn backend.app.main:app --reload --port 8000
```

From the repository root, test the dependency-free audio engine with:

```bash
PYTHONPATH=. pytest -s backend/tests automation/tests
```

API documentation is available at `http://localhost:8000/docs`.

The API exposes generation at `POST /generate`, a persistent library at `GET /tracks`,
and 1080p rendering at `POST /tracks/{track_id}/render`.
