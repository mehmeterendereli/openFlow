#!/usr/bin/env python3
"""Exercise generation, media serving, rendering, and dry-run publishing in one process."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="openflow-smoke-") as temporary_directory:
        root = Path(temporary_directory)
        settings = Settings(
            data_dir=root,
            generated_dir=root / "audio",
            rendered_dir=root / "video",
            database_path=root / "openflow.db",
            default_background=Path("automation/placeholder.ppm").resolve(),
        )
        with TestClient(create_app(settings)) as client:
            health = client.get("/health")
            assert health.status_code == 200, health.text
            assert health.json()["ffmpeg_available"], "FFmpeg is unavailable"

            generated = client.post(
                "/generate",
                json={
                    "prompt": "Warm nocturnal synthwave with a patient analog pulse",
                    "model": "ace-step",
                    "duration_seconds": 1,
                },
            )
            assert generated.status_code == 201, generated.text
            track = generated.json()

            audio = client.get(track["audio_url"])
            assert audio.status_code == 200 and len(audio.content) > 100_000

            rendered = client.post(f"/tracks/{track['id']}/render")
            assert rendered.status_code == 200, rendered.text
            assert rendered.json()["status"] == "rendered"
            video = client.get(rendered.json()["video_url"])
            assert video.status_code == 200 and len(video.content) > 10_000

            published = client.post(
                f"/tracks/{track['id']}/publish",
                json={"title": "openFlow smoke test", "dry_run": True},
            )
            assert published.status_code == 200, published.text
            assert published.json()["track"]["publish_status"] == "dry_run"
            manifest = root / "publish" / f"{track['id']}.json"
            assert manifest.is_file()

            print(
                json.dumps(
                    {
                        "track_id": track["id"],
                        "audio_bytes": len(audio.content),
                        "video_bytes": len(video.content),
                        "publish_mode": published.json()["mode"],
                        "result": "ok",
                    },
                    indent=2,
                )
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
