# openFlow backend

The FastAPI service currently uses a deterministic mock synthesizer so the complete
workflow functions without CUDA, PyTorch, or model weights. The adapter can later be
replaced by ACE-Step, MusicGen, or RVC while keeping the API contract stable.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

From the repository root, test the dependency-free audio engine with:

```bash
PYTHONPATH=backend python3 -m unittest discover -s backend/tests
```

API documentation is available at `http://localhost:8000/docs`.
