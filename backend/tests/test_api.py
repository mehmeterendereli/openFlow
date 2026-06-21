from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        settings = Settings(
            data_dir=root,
            generated_dir=root / "audio",
            rendered_dir=root / "video",
            database_path=root / "openflow.db",
            default_background=Path(__file__).resolve().parents[2] / "automation" / "placeholder.ppm",
        )

        def fake_render(audio: Path, output: Path, background: Path) -> Path:
            self.assertTrue(audio.is_file())
            self.assertTrue(background.is_file())
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"mock-mp4")
            return output

        self.client = TestClient(create_app(settings, fake_render))

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_generate_list_render_and_serve_track(self) -> None:
        generated = self.client.post(
            "/generate",
            json={"prompt": "warm nocturnal synthwave", "model": "ace-step", "duration_seconds": 1},
        )
        self.assertEqual(generated.status_code, 201)
        track = generated.json()
        self.assertEqual(track["status"], "ready")
        self.assertTrue(track["audio_url"].startswith("/media/audio/"))

        audio = self.client.get(track["audio_url"])
        self.assertEqual(audio.status_code, 200)
        self.assertEqual(audio.headers["content-type"], "audio/wav")
        self.assertGreater(len(audio.content), 100_000)

        listing = self.client.get("/tracks")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual([item["id"] for item in listing.json()], [track["id"]])

        rendered = self.client.post(f"/tracks/{track['id']}/render")
        self.assertEqual(rendered.status_code, 200)
        self.assertEqual(rendered.json()["status"], "rendered")
        self.assertEqual(self.client.get(rendered.json()["video_url"]).content, b"mock-mp4")

        persisted = self.client.get(f"/tracks/{track['id']}")
        self.assertEqual(persisted.json()["video_url"], rendered.json()["video_url"])

    def test_validation_and_missing_track_errors(self) -> None:
        self.assertEqual(self.client.post("/generate", json={"prompt": ""}).status_code, 422)
        self.assertEqual(self.client.get("/tracks/missing").status_code, 404)
        self.assertEqual(self.client.post("/tracks/missing/render").status_code, 404)


if __name__ == "__main__":
    unittest.main()
