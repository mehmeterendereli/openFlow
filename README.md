# openFlow

openFlow is an open-source, local-first music production pipeline. It turns a text
direction into audio, stores every take in a local library, renders a 1080p video,
and prepares or performs a YouTube upload from one dashboard.

Audio generation runs locally through Meta AudioCraft's `facebook/musicgen-small`.
The backend selects CUDA first and falls back to CPU when no CUDA device is detected.

## What works

- Next.js 16 dark studio with generation, waveform playback, history, video preview,
  and publication controls
- FastAPI service with a persistent SQLite track catalog
- Lazy-loaded, GPU-accelerated MusicGen text-to-music inference with CPU fallback
- FFmpeg 1920×1080 H.264/AAC rendering with a built-in placeholder cover
- Safe YouTube dry-run manifests by default
- Real YouTube Data API uploads through local OAuth credentials
- Python, frontend contract, and complete WAV→MP4→publish smoke tests

All generated audio, video, OAuth tokens, and publication manifests remain under
`backend/data/` and are excluded from Git.

## Prerequisites

- Python 3.9 for the AudioCraft environment
- Node.js 22+
- [uv](https://docs.astral.sh/uv/) for the Python environment
- FFmpeg on `PATH`; if absent, the Python package provides a local binary fallback

## Setup

```bash
git clone https://github.com/mehmeterendereli/openFlow.git
cd openFlow
make setup-ai
```

Run the API and dashboard in separate terminals:

```bash
make backend-ai
```

```bash
make frontend
```

Open `http://localhost:3000`. FastAPI documentation is available at
`http://localhost:8000/docs`.

Without `make`, use the equivalent commands:

```bash
uv venv --python 3.9 .venv-musicgen
uv pip install --python .venv-musicgen/bin/python -r backend/requirements.txt
cd frontend && npm ci
```

## Verification

```bash
make test
make smoke
```

`make smoke` uses an injected WAV fixture so CI does not download model weights. It
serves the WAV through the real API, renders a real 1080p MP4, and writes a publication
dry-run manifest. Adapter tests cover CUDA selection, CPU fallback, model caching, and
OOM handling. Run a dashboard generation for the live model test.

See [setup_notes.md](setup_notes.md) for Windows/WSL CUDA setup, AudioCraft's Python
compatibility constraints, device overrides, and model-weight licensing.

## YouTube OAuth

Dry-run publication requires no account configuration. For a real upload:

1. Enable the YouTube Data API v3 in a Google Cloud project.
2. Create an OAuth desktop application and download its client JSON.
3. Install the optional dependencies:

   ```bash
   uv pip install --python .venv-musicgen/bin/python -r backend/requirements-youtube.txt
   ```

4. Set the local path before starting the API:

   ```bash
   export OPENFLOW_YOUTUBE_CLIENT_SECRETS=/absolute/path/to/client_secret.json
   ```

5. Check **Enable real YouTube upload** in the dashboard. The first upload opens the
   local OAuth consent flow. Videos default to private.

Never commit the client secret or generated OAuth token; both patterns are ignored.

## API workflow

```text
POST /generate
  -> GET /media/audio/{track_id}
  -> POST /tracks/{track_id}/render
  -> GET /media/video/{track_id}
  -> POST /tracks/{track_id}/publish
```

`GET /tracks` returns the persistent local project library. Set
`OPENFLOW_DATA_DIR` to move local media and SQLite storage elsewhere.

## License

[MIT](LICENSE)
