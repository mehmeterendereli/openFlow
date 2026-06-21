from __future__ import annotations

import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path

from backend.models import MusicGenAdapter, MusicGenLoadError, MusicGenOutOfMemoryError


class FakeCuda:
    class OutOfMemoryError(RuntimeError):
        pass

    def __init__(self, available: bool) -> None:
        self.available = available
        self.empty_cache_calls = 0

    def is_available(self) -> bool:
        return self.available

    def empty_cache(self) -> None:
        self.empty_cache_calls += 1


class FakeTorch:
    def __init__(self, cuda_available: bool) -> None:
        self.cuda = FakeCuda(cuda_available)

    @staticmethod
    def inference_mode() -> nullcontext[None]:
        return nullcontext()


class FakeTensor:
    ndim = 2

    def detach(self) -> FakeTensor:
        return self

    def to(self, device: str) -> FakeTensor:
        if device != "cpu":
            raise AssertionError("Generated audio must be moved to CPU before encoding")
        return self

    def float(self) -> FakeTensor:
        return self


class FakeModel:
    sample_rate = 32_000

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.duration: int | None = None
        self.prompts: list[str] | None = None

    def set_generation_params(self, *, duration: int) -> None:
        self.duration = duration

    def generate(self, prompts: list[str], *, progress: bool) -> list[FakeTensor]:
        if progress:
            raise AssertionError("Server inference must not print model progress")
        self.prompts = prompts
        if self.error:
            raise self.error
        return [FakeTensor()]


class FakeTorchAudio:
    def save(self, path: str, waveform: FakeTensor, sample_rate: int, *, format: str) -> None:
        if sample_rate != 32_000 or format != "wav":
            raise AssertionError("Unexpected WAV encoding parameters")
        Path(path).write_bytes(b"RIFF-fake-wave")


class MusicGenAdapterTests(unittest.TestCase):
    def build_runtime(self, *, cuda: bool, model_error: Exception | None = None):
        torch = FakeTorch(cuda)
        model = FakeModel(model_error)

        class FakeMusicGen:
            calls: list[tuple[str, str]] = []

            @classmethod
            def get_pretrained(cls, model_name: str, *, device: str) -> FakeModel:
                cls.calls.append((model_name, device))
                return model

        return torch, FakeTorchAudio(), FakeMusicGen, model

    def test_generates_output_wav_on_cuda_and_caches_model(self) -> None:
        torch, torchaudio, musicgen, model = self.build_runtime(cuda=True)
        adapter = MusicGenAdapter(runtime_loader=lambda: (torch, torchaudio, musicgen))

        with tempfile.TemporaryDirectory() as temporary_directory:
            first = Path(temporary_directory) / "output.wav"
            second = Path(temporary_directory) / "second.wav"
            self.assertEqual(adapter.generate("warm analog synth", 4, first), first)
            adapter.generate("dusty house groove", 2, second)

            self.assertEqual(first.read_bytes(), b"RIFF-fake-wave")
            self.assertEqual(second.read_bytes(), b"RIFF-fake-wave")
            self.assertEqual(model.duration, 2)
            self.assertEqual(model.prompts, ["dusty house groove"])
            self.assertEqual(musicgen.calls, [("facebook/musicgen-small", "cuda")])
            self.assertEqual(adapter.device, "cuda")
            self.assertTrue(adapter.loaded)

    def test_falls_back_to_cpu_when_cuda_is_unavailable(self) -> None:
        torch, torchaudio, musicgen, _ = self.build_runtime(cuda=False)
        adapter = MusicGenAdapter(device="cuda", runtime_loader=lambda: (torch, torchaudio, musicgen))

        with tempfile.TemporaryDirectory() as temporary_directory:
            adapter.generate("minimal piano", 1, Path(temporary_directory) / "output.wav")

        self.assertEqual(adapter.device, "cpu")
        self.assertEqual(musicgen.calls, [("facebook/musicgen-small", "cpu")])

    def test_oom_is_wrapped_and_cuda_cache_is_released(self) -> None:
        torch, torchaudio, musicgen, _ = self.build_runtime(
            cuda=True,
            model_error=RuntimeError("CUDA out of memory while allocating tensor"),
        )
        adapter = MusicGenAdapter(runtime_loader=lambda: (torch, torchaudio, musicgen))

        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "output.wav"
            with self.assertRaisesRegex(MusicGenOutOfMemoryError, "Reduce duration"):
                adapter.generate("huge cinematic score", 30, output)
            self.assertFalse(output.exists())

        self.assertEqual(torch.cuda.empty_cache_calls, 1)

    def test_dependency_load_failure_is_wrapped(self) -> None:
        def missing_runtime():
            raise ImportError("audiocraft is missing")

        adapter = MusicGenAdapter(runtime_loader=missing_runtime)
        with self.assertRaisesRegex(MusicGenLoadError, "audiocraft is missing"):
            adapter.generate("ambient", 1)

    def test_model_load_oom_is_wrapped_by_pytorch_exception_type(self) -> None:
        torch = FakeTorch(cuda_available=True)

        class OutOfMemoryMusicGen:
            @staticmethod
            def get_pretrained(model_name: str, *, device: str):
                raise torch.cuda.OutOfMemoryError("allocation failed")

        adapter = MusicGenAdapter(
            runtime_loader=lambda: (torch, FakeTorchAudio(), OutOfMemoryMusicGen)
        )

        with self.assertRaisesRegex(MusicGenOutOfMemoryError, "memory is insufficient"):
            adapter.generate("orchestral", 4)
        self.assertEqual(torch.cuda.empty_cache_calls, 1)


if __name__ == "__main__":
    unittest.main()
