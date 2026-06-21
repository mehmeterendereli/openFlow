from __future__ import annotations

import tempfile
import unittest
import wave
from pathlib import Path

from fastapi.testclient import TestClient

from automation.youtube_upload import PublishMetadata
from backend.app.config import Settings
from backend.app.main import create_app
from backend.models import MusicGenOutOfMemoryError


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
            youtube_client_secrets=root / "client_secret.json",
            youtube_token_path=root / "youtube_token.json",
        )
        settings.youtube_client_secrets.write_text("{}", encoding="utf-8")

        def fake_generate(prompt: str, duration_seconds: int, output: Path) -> Path:
            self.assertTrue(prompt)
            output.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(output), "wb") as audio:
                audio.setnchannels(2)
                audio.setsampwidth(2)
                audio.setframerate(44_100)
                audio.writeframes(b"\0\0\0\0" * 44_100 * duration_seconds)
            return output

        def fake_render(audio: Path, output: Path, background: Path) -> Path:
            self.assertTrue(audio.is_file())
            self.assertTrue(background.is_file())
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"mock-mp4")
            return output

        def fake_publish(
            video: Path,
            metadata: PublishMetadata,
            client_secrets: Path,
            token_path: Path,
        ) -> str:
            self.assertTrue(video.is_file())
            self.assertTrue(client_secrets.is_file())
            self.assertEqual(metadata.title, "Night Drive")
            return "https://www.youtube.com/watch?v=test-video"

        self.settings = settings
        self.fake_render = fake_render
        self.fake_publish = fake_publish
        self.client = TestClient(
            create_app(
                settings,
                render_function=fake_render,
                publish_function=fake_publish,
                generation_function=fake_generate,
            )
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_generate_list_render_and_serve_track(self) -> None:
        generated = self.client.post(
            "/generate",
            json={"prompt": "warm nocturnal synthwave", "model": "musicgen", "duration_seconds": 1},
        )
        self.assertEqual(generated.status_code, 201)
        track = generated.json()
        self.assertEqual(track["status"], "ready")
        self.assertFalse(track["mocked"])
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

        dry_run = self.client.post(
            f"/tracks/{track['id']}/publish",
            json={"title": "Night Drive", "tags": ["synthwave"]},
        )
        self.assertEqual(dry_run.status_code, 200)
        self.assertEqual(dry_run.json()["mode"], "dry-run")
        self.assertEqual(dry_run.json()["track"]["publish_status"], "dry_run")

        published = self.client.post(
            f"/tracks/{track['id']}/publish",
            json={"title": "Night Drive", "dry_run": False},
        )
        self.assertEqual(published.status_code, 200)
        self.assertEqual(published.json()["track"]["publish_status"], "published")
        self.assertEqual(published.json()["youtube_url"], "https://www.youtube.com/watch?v=test-video")

    def test_validation_and_missing_track_errors(self) -> None:
        self.assertEqual(self.client.post("/generate", json={"prompt": ""}).status_code, 422)
        self.assertEqual(self.client.get("/tracks/missing").status_code, 404)
        self.assertEqual(self.client.post("/tracks/missing/render").status_code, 404)

    def test_musicgen_oom_is_a_clean_500_and_server_survives(self) -> None:
        def out_of_memory(prompt: str, duration_seconds: int, output: Path) -> Path:
            raise MusicGenOutOfMemoryError("MusicGen ran out of memory on cuda. Reduce duration.")

        client = TestClient(
            create_app(
                self.settings,
                render_function=self.fake_render,
                publish_function=self.fake_publish,
                generation_function=out_of_memory,
            )
        )
        response = client.post(
            "/generate",
            json={"prompt": "large orchestral score", "model": "musicgen", "duration_seconds": 30},
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {"detail": "MusicGen ran out of memory on cuda. Reduce duration."},
        )
        self.assertEqual(client.get("/health").status_code, 200)


if __name__ == "__main__":
    unittest.main()
