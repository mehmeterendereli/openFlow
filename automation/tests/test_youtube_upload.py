from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from automation.youtube_upload import PublishMetadata, write_publish_manifest


class YoutubeUploadTests(unittest.TestCase):
    def test_dry_run_manifest_contains_video_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            video = root / "track.mp4"
            video.write_bytes(b"video")
            manifest = root / "publish" / "track.json"
            metadata = PublishMetadata(
                title="Night Drive",
                tags=("synthwave", "local-ai"),
                privacy_status="unlisted",
            )

            result = write_publish_manifest(video, metadata, manifest)
            payload = json.loads(result.read_text(encoding="utf-8"))

            self.assertEqual(payload["mode"], "dry-run")
            self.assertEqual(payload["metadata"]["title"], "Night Drive")
            self.assertEqual(payload["metadata"]["tags"], ["synthwave", "local-ai"])
            self.assertEqual(payload["metadata"]["privacy_status"], "unlisted")
