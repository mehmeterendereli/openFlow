"""Test-only API server for browser E2E; production never uses this fixture generator."""

from __future__ import annotations

import atexit
import shutil
import tempfile
import wave
from pathlib import Path

from backend.app.config import Settings
from backend.app.main import create_app

DATA_DIR = Path(tempfile.mkdtemp(prefix="openflow-browser-e2e-"))
atexit.register(shutil.rmtree, DATA_DIR, True)


def generate_audio_fixture(prompt: str, duration_seconds: int, output: Path) -> Path:
    """Write a valid WAV quickly while exercising every downstream production layer."""

    if not prompt.strip():
        raise ValueError("Prompt is required")
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), "wb") as audio:
        audio.setnchannels(2)
        audio.setsampwidth(2)
        audio.setframerate(44_100)
        audio.writeframes(b"\0\0\0\0" * 44_100 * duration_seconds)
    return output


settings = Settings(
    data_dir=DATA_DIR,
    generated_dir=DATA_DIR / "audio",
    rendered_dir=DATA_DIR / "video",
    database_path=DATA_DIR / "openflow.db",
    default_background=Path(__file__).resolve().parents[1] / "automation" / "placeholder.ppm",
    allowed_origins=("http://localhost:3000", "http://127.0.0.1:3000"),
)

app = create_app(settings=settings, generation_function=generate_audio_fixture)
