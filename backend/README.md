# openFlow backend

FastAPI loads `facebook/musicgen-small` through the local AudioCraft adapter on the
first generation request. CUDA is preferred; CPU is selected when CUDA is unavailable.
The model instance is cached, inference is serialized for GPU safety, and generated
32 kHz WAV files feed the existing FFmpeg render pipeline directly.

Track metadata and job state are persisted locally in SQLite under `backend/data/`.

```bash
make setup-ai
make backend-ai
```

The first `POST /generate` request downloads the model weights. Use
`OPENFLOW_MUSICGEN_DEVICE=cpu` to force CPU or leave it at `auto` for CUDA-first
selection. See `setup_notes.md` for Windows/WSL and system dependencies.

Development tests use an injected audio runtime and do not download weights:

```bash
make setup
make test
make smoke
```

API documentation is available at `http://localhost:8000/docs`. The API exposes
generation at `POST /generate`, a persistent library at `GET /tracks`, and 1080p
rendering at `POST /tracks/{track_id}/render`.
