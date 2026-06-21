#!/usr/bin/env python3
"""Render an audio track and still image as a publish-ready 1080p MP4."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

DEFAULT_BACKGROUND = Path(__file__).with_name("placeholder.ppm")


def find_ffmpeg() -> str | None:
    """Resolve FFmpeg from configuration, PATH, or the optional bundled wheel."""

    configured = os.getenv("OPENFLOW_FFMPEG")
    if configured and Path(configured).is_file():
        return configured
    executable = shutil.which("ffmpeg")
    if executable:
        return executable
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError):
        return None


def build_ffmpeg_command(
    ffmpeg: str,
    audio: Path,
    background: Path,
    output: Path,
) -> list[str]:
    return [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-loop",
        "1",
        "-framerate",
        "30",
        "-i",
        str(background),
        "-i",
        str(audio),
        "-vf",
        "scale=1920:1080:force_original_aspect_ratio=decrease,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-tune",
        "stillimage",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(output),
    ]


def render_video(audio: Path, output: Path, background: Path = DEFAULT_BACKGROUND) -> Path:
    """Combine audio and a still background, returning the rendered file path."""

    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        raise RuntimeError("FFmpeg is required but was not found on PATH.")
    if not audio.is_file():
        raise FileNotFoundError(f"Audio input not found: {audio}")
    if not background.is_file():
        raise FileNotFoundError(f"Background image not found: {background}")
    if output.suffix.lower() != ".mp4":
        raise ValueError("Output filename must use the .mp4 extension.")

    output.parent.mkdir(parents=True, exist_ok=True)
    command = build_ffmpeg_command(ffmpeg, audio, background, output)
    subprocess.run(command, check=True)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path, help="Input WAV, MP3, FLAC, or other FFmpeg-supported audio")
    parser.add_argument("output", type=Path, help="Destination .mp4 path")
    parser.add_argument("--image", type=Path, default=DEFAULT_BACKGROUND, help="Still background image")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = render_video(args.audio, args.output, args.image)
    except (FileNotFoundError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Render failed: {error}") from error
    print(f"Rendered video: {result.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
