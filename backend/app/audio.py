"""Dependency-free mock audio synthesis used until model adapters are installed."""

from __future__ import annotations

import math
import random
import wave
from pathlib import Path

SAMPLE_RATE = 44_100


def synthesize_mock_track(destination: Path, prompt: str, duration_seconds: int) -> None:
    """Write a deterministic stereo WAV derived from a prompt.

    The result is intentionally musical enough to exercise playback and rendering while
    keeping the API operational on machines without CUDA or model dependencies.
    """

    destination.parent.mkdir(parents=True, exist_ok=True)
    randomizer = random.Random(prompt)
    root = randomizer.choice((110.0, 130.81, 146.83, 164.81, 196.0))
    chord = (1.0, 1.25, 1.5, 2.0)
    frame_count = duration_seconds * SAMPLE_RATE

    with wave.open(str(destination), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)

        chunk = bytearray()
        for index in range(frame_count):
            time = index / SAMPLE_RATE
            beat = int(time * 2) % len(chord)
            frequency = root * chord[beat]
            fade_in = min(1.0, time / 0.25)
            fade_out = min(1.0, (duration_seconds - time) / 0.4)
            envelope = max(0.0, fade_in * fade_out)
            pulse = 0.58 * math.sin(2 * math.pi * frequency * time)
            texture = 0.18 * math.sin(2 * math.pi * frequency * 2.005 * time)
            kick_phase = time % 0.5
            kick = (
                0.24
                * math.sin(2 * math.pi * (55 - kick_phase * 50) * kick_phase)
                * math.exp(-18 * kick_phase)
            )
            sample = int(max(-1.0, min(1.0, (pulse + texture + kick) * envelope * 0.48)) * 32_767)
            delayed = int(sample * (0.94 + 0.04 * math.sin(2 * math.pi * 0.2 * time)))
            chunk.extend(sample.to_bytes(2, "little", signed=True))
            chunk.extend(delayed.to_bytes(2, "little", signed=True))

            if len(chunk) >= 16_384:
                output.writeframesraw(chunk)
                chunk.clear()

        if chunk:
            output.writeframesraw(chunk)
