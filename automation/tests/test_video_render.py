import unittest
from pathlib import Path

from automation.video_render import build_ffmpeg_command


class VideoRenderTests(unittest.TestCase):
    def test_command_produces_1080p_h264_mp4(self) -> None:
        command = build_ffmpeg_command(
            "/usr/bin/ffmpeg",
            Path("track.wav"),
            Path("cover.png"),
            Path("output.mp4"),
        )
        joined = " ".join(command)
        self.assertIn("scale=1920:1080", joined)
        self.assertIn("libx264", command)
        self.assertIn("aac", command)
        self.assertIn("-shortest", command)
        self.assertEqual(command[-1], "output.mp4")


if __name__ == "__main__":
    unittest.main()
