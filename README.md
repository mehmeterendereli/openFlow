# openFlow

An open-source, local-first prototype for generating AI music, previewing it in a web
studio, and rendering it as publish-ready video.

## Run locally

Start the API from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

In a second terminal, start the dashboard:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000`, generate a track, then render its WAV using the command
documented in `automation/README.md`. The current audio generator is an intentional
mock so the entire workflow remains usable without GPU model dependencies.

## Prerequisites

- Python 3.11+
- Node.js 20+
- FFmpeg (for MP4 rendering)
