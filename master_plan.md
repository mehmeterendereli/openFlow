# SynthFlow - End-to-End Master Plan
## Architecture
1. **Frontend (Next.js/Tailwind):** Dark-mode dashboard for prompt entry, model selection, and waveform playback.
2. **Backend (FastAPI):** Local Python server running AI models (ACE-Step/MusicGen/RVC) via REST API.
3. **Automation Pipeline (Python/FFmpeg):** Converts audio + background image to 1080p MP4 and auto-uploads to YouTube.
## Workflow
Prompt -> Backend generates audio -> API returns audio to UI -> UI triggers render -> Video created -> YouTube upload.
