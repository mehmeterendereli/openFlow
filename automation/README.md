# openFlow video automation

`video_render.py` combines generated audio with a still image and creates a 1920×1080
H.264/AAC MP4. A small built-in placeholder is used when `--image` is omitted.

FFmpeg must be installed and available on `PATH`.

```bash
python3 automation/video_render.py \
  backend/generated/TRACK_ID.wav \
  automation/output/track.mp4
```

Use custom cover art with `--image path/to/cover.png`.
