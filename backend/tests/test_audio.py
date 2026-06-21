import tempfile
import unittest
import wave
from pathlib import Path

from app.audio import SAMPLE_RATE, synthesize_mock_track


class MockAudioTests(unittest.TestCase):
    def test_synthesizer_writes_expected_wav(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "track.wav"
            synthesize_mock_track(output, "night drive", 1)

            with wave.open(str(output), "rb") as audio:
                self.assertEqual(audio.getnchannels(), 2)
                self.assertEqual(audio.getframerate(), SAMPLE_RATE)
                self.assertEqual(audio.getnframes(), SAMPLE_RATE)


if __name__ == "__main__":
    unittest.main()
