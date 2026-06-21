from __future__ import annotations

import os
import threading
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Any

MODEL_NAME = "facebook/musicgen-small"
Runtime = tuple[Any, Any, Any]
RuntimeLoader = Callable[[], Runtime]


class MusicGenError(RuntimeError):
    """Base class for errors safe to expose through the generation API."""


class MusicGenLoadError(MusicGenError):
    """The PyTorch/AudioCraft runtime or pretrained model could not be loaded."""


class MusicGenGenerationError(MusicGenError):
    """MusicGen failed while generating or encoding audio."""


class MusicGenOutOfMemoryError(MusicGenGenerationError):
    """The selected device ran out of memory during inference."""


def load_musicgen_runtime() -> Runtime:
    """Import heavyweight dependencies only when the first request needs them."""

    import torch
    import torchaudio
    from audiocraft.models import MusicGen

    return torch, torchaudio, MusicGen


class MusicGenAdapter:
    """Lazy, process-local adapter for Meta's small text-to-music model."""

    def __init__(
        self,
        model_name: str = MODEL_NAME,
        device: str | None = None,
        runtime_loader: RuntimeLoader = load_musicgen_runtime,
    ) -> None:
        self.model_name = model_name
        self.requested_device = device or os.getenv("OPENFLOW_MUSICGEN_DEVICE", "auto")
        if self.requested_device not in {"auto", "cuda", "cpu"}:
            raise ValueError("MusicGen device must be auto, cuda, or cpu")
        self._runtime_loader = runtime_loader
        self._torch: Any | None = None
        self._torchaudio: Any | None = None
        self._model: Any | None = None
        self._device: str | None = None
        self._load_lock = threading.Lock()
        self._generation_lock = threading.Lock()

    @property
    def device(self) -> str:
        return self._device or self.requested_device

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def generate(
        self,
        prompt: str,
        duration_seconds: int,
        output_path: Path = Path("output.wav"),
    ) -> Path:
        """Generate one text-conditioned WAV file.

        The model is cached after its first load. Generation is serialized because a
        single MusicGen instance and a single GPU cannot safely serve concurrent jobs.
        """

        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise ValueError("MusicGen prompt cannot be empty")
        if duration_seconds < 1:
            raise ValueError("MusicGen duration must be at least one second")

        model = self._load_model()
        output_path = Path(output_path)
        temporary_path = output_path.with_name(f".{output_path.stem}.generating.wav")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with self._generation_lock:
            try:
                model.set_generation_params(duration=duration_seconds)
                with self._torch.inference_mode():
                    generated = model.generate([normalized_prompt], progress=False)
                waveform = generated[0].detach().to("cpu").float()
                if waveform.ndim == 1:
                    waveform = waveform.unsqueeze(0)
                self._torchaudio.save(
                    str(temporary_path),
                    waveform,
                    model.sample_rate,
                    format="wav",
                )
                temporary_path.replace(output_path)
                return output_path
            except Exception as error:
                with suppress(OSError):
                    temporary_path.unlink()
                if self._is_out_of_memory(error):
                    self._release_cuda_cache()
                    raise MusicGenOutOfMemoryError(
                        f"MusicGen ran out of memory on {self.device}. "
                        "Reduce duration or set OPENFLOW_MUSICGEN_DEVICE=cpu."
                    ) from error
                raise MusicGenGenerationError(f"MusicGen generation failed: {error}") from error

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model

        with self._load_lock:
            if self._model is not None:
                return self._model
            try:
                torch, torchaudio, musicgen_class = self._runtime_loader()
                device = self._select_device(torch)
                model = musicgen_class.get_pretrained(self.model_name, device=device)
            except Exception as error:
                loading_torch = torch if "torch" in locals() else None
                if self._is_out_of_memory(error, loading_torch):
                    self._release_cuda_cache(loading_torch)
                    failed_device = device if "device" in locals() else "the selected device"
                    raise MusicGenOutOfMemoryError(
                        f"MusicGen could not load on {failed_device} "
                        "because available memory is insufficient."
                    ) from error
                raise MusicGenLoadError(f"Could not load {self.model_name}: {error}") from error

            self._torch = torch
            self._torchaudio = torchaudio
            self._device = device
            self._model = model
            return model

    def _select_device(self, torch: Any) -> str:
        cuda_available = bool(torch.cuda.is_available())
        if self.requested_device == "cpu":
            return "cpu"
        if self.requested_device == "cuda" and not cuda_available:
            return "cpu"
        return "cuda" if cuda_available else "cpu"

    def _is_out_of_memory(self, error: Exception, torch: Any | None = None) -> bool:
        active_torch = torch or self._torch
        if active_torch is not None:
            oom_type = getattr(getattr(active_torch, "cuda", None), "OutOfMemoryError", None)
            if isinstance(oom_type, type) and isinstance(error, oom_type):
                return True
        return isinstance(error, RuntimeError) and "out of memory" in str(error).lower()

    def _release_cuda_cache(self, torch: Any | None = None) -> None:
        active_torch = torch or self._torch
        if active_torch is None:
            return
        with suppress(Exception):
            if active_torch.cuda.is_available():
                active_torch.cuda.empty_cache()
