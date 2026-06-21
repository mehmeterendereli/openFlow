#!/usr/bin/env python3
"""Upload a rendered openFlow video to YouTube using local OAuth credentials."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"


@dataclass(frozen=True)
class PublishMetadata:
    title: str
    description: str = "Generated locally with openFlow."
    tags: tuple[str, ...] = ()
    privacy_status: str = "private"
    category_id: str = "10"


def write_publish_manifest(
    video: Path,
    metadata: PublishMetadata,
    destination: Path,
) -> Path:
    """Persist the exact upload request without contacting YouTube."""

    if not video.is_file():
        raise FileNotFoundError(f"Video input not found: {video}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "video": str(video.resolve()),
        "metadata": asdict(metadata),
        "mode": "dry-run",
    }
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return destination


def upload_to_youtube(
    video: Path,
    metadata: PublishMetadata,
    client_secrets: Path,
    token_path: Path,
) -> str:
    """Upload a video and return its public watch URL.

    Google dependencies are imported lazily so generation and rendering stay usable
    without YouTube integration installed.
    """

    if not video.is_file():
        raise FileNotFoundError(f"Video input not found: {video}")
    if not client_secrets.is_file():
        raise FileNotFoundError(f"OAuth client secrets not found: {client_secrets}")
    if metadata.privacy_status not in {"private", "unlisted", "public"}:
        raise ValueError("privacy_status must be private, unlisted, or public")

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as error:
        raise RuntimeError(
            "YouTube dependencies are missing. Install backend/requirements-youtube.txt."
        ) from error

    credentials = None
    if token_path.is_file():
        credentials = Credentials.from_authorized_user_file(token_path, [YOUTUBE_UPLOAD_SCOPE])
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), [YOUTUBE_UPLOAD_SCOPE])
        credentials = flow.run_local_server(port=0)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    youtube = build("youtube", "v3", credentials=credentials)
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": metadata.title,
                "description": metadata.description,
                "tags": list(metadata.tags),
                "categoryId": metadata.category_id,
            },
            "status": {"privacyStatus": metadata.privacy_status},
        },
        media_body=MediaFileUpload(str(video), chunksize=-1, resumable=True),
    )

    response = None
    while response is None:
        _, response = request.next_chunk()
    video_id = response.get("id")
    if not video_id:
        raise RuntimeError("YouTube upload completed without a video id")
    return f"https://www.youtube.com/watch?v={video_id}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="Generated locally with openFlow.")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--privacy", choices=("private", "unlisted", "public"), default="private")
    parser.add_argument("--client-secrets", type=Path, default=Path("client_secret.json"))
    parser.add_argument("--token", type=Path, default=Path("backend/data/youtube_token.json"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--manifest", type=Path, default=Path("backend/data/publish_manifest.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metadata = PublishMetadata(
        title=args.title,
        description=args.description,
        tags=tuple(args.tag),
        privacy_status=args.privacy,
    )
    if args.dry_run:
        result = write_publish_manifest(args.video, metadata, args.manifest)
        print(f"Dry-run manifest: {result.resolve()}")
    else:
        result = upload_to_youtube(args.video, metadata, args.client_secrets, args.token)
        print(f"Published video: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
