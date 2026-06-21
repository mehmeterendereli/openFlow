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

## YouTube publishing

Validate metadata and write a local manifest without network access:

```bash
python3 automation/youtube_upload.py automation/output/track.mp4 \
  --title "Night Drive" --tag synthwave --dry-run
```

For a real upload, enable the YouTube Data API, download an OAuth desktop client JSON,
install `backend/requirements-youtube.txt`, and omit `--dry-run`. Uploads default to
`private`; use `--privacy unlisted` or `--privacy public` explicitly.
