from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from automation.video_render import find_ffmpeg, render_video
from automation.youtube_upload import PublishMetadata, upload_to_youtube, write_publish_manifest

from ..models import MusicGenAdapter, MusicGenError, MusicGenOutOfMemoryError
from .config import Settings
from .schemas import GenerateRequest, HealthResponse, PublishRequest, PublishResponse, TrackResponse
from .store import TrackStore

RenderFunction = Callable[[Path, Path, Path], Path]
PublishFunction = Callable[[Path, PublishMetadata, Path, Path], str]
GenerationFunction = Callable[[str, int, Path], Path]


def create_app(
    settings: Settings | None = None,
    render_function: RenderFunction = render_video,
    publish_function: PublishFunction = upload_to_youtube,
    generation_function: GenerationFunction | None = None,
) -> FastAPI:
    active_settings = settings or Settings.from_environment()
    active_settings.prepare()
    store = TrackStore(active_settings.database_path)
    store.initialize()
    musicgen = MusicGenAdapter()
    generate_audio = generation_function or musicgen.generate

    application = FastAPI(
        title="openFlow API",
        description="Local-first music generation, rendering, and publishing API.",
        version="0.2.0",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(active_settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.state.settings = active_settings
    application.state.store = store
    application.state.musicgen = musicgen

    def response_for(track: dict[str, Any]) -> TrackResponse:
        return TrackResponse(
            **track,
            audio_url=f"/media/audio/{track['id']}" if track.get("audio_filename") else None,
            video_url=f"/media/video/{track['id']}" if track.get("video_filename") else None,
        )

    def require_track(track_id: str) -> dict[str, Any]:
        track = store.get(track_id)
        if track is None:
            raise HTTPException(status_code=404, detail="Track not found")
        return track

    @application.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(
            engine="musicgen",
            model_name=musicgen.model_name,
            device=musicgen.device,
            model_loaded=musicgen.loaded,
            ffmpeg_available=find_ffmpeg() is not None,
            track_count=len(store.list()),
        )

    @application.post("/generate", response_model=TrackResponse, status_code=201)
    async def generate(request: GenerateRequest) -> TrackResponse:
        track_id = uuid4().hex
        prompt = request.prompt.strip()
        track = store.create(
            track_id=track_id,
            prompt=prompt,
            model=request.model,
            duration_seconds=request.duration_seconds,
        )
        filename = f"{track_id}.wav"
        try:
            await asyncio.to_thread(
                generate_audio,
                prompt,
                request.duration_seconds,
                active_settings.generated_dir / filename,
            )
            track = store.update(track_id, status="ready", audio_filename=filename, error=None)
        except MusicGenOutOfMemoryError as error:
            store.update(track_id, status="failed", error=str(error))
            raise HTTPException(status_code=500, detail=str(error)) from error
        except MusicGenError as error:
            store.update(track_id, status="failed", error=str(error))
            raise HTTPException(status_code=500, detail=str(error)) from error
        except Exception as error:
            store.update(track_id, status="failed", error=str(error))
            raise HTTPException(status_code=500, detail=f"MusicGen generation failed: {error}") from error
        return response_for(track)

    @application.get("/tracks", response_model=list[TrackResponse])
    async def list_tracks(limit: int = Query(default=50, ge=1, le=100)) -> list[TrackResponse]:
        return [response_for(track) for track in store.list(limit)]

    @application.get("/tracks/{track_id}", response_model=TrackResponse)
    async def get_track(track_id: str) -> TrackResponse:
        return response_for(require_track(track_id))

    @application.post("/tracks/{track_id}/render", response_model=TrackResponse)
    async def render_track(track_id: str) -> TrackResponse:
        track = require_track(track_id)
        if not track.get("audio_filename"):
            raise HTTPException(status_code=409, detail="Track has no generated audio")
        if track["status"] == "rendering":
            raise HTTPException(status_code=409, detail="Track is already rendering")

        audio_path = active_settings.generated_dir / track["audio_filename"]
        video_filename = f"{track_id}.mp4"
        video_path = active_settings.rendered_dir / video_filename
        store.update(track_id, status="rendering", error=None)
        try:
            await asyncio.to_thread(
                render_function,
                audio_path,
                video_path,
                active_settings.default_background,
            )
            track = store.update(
                track_id,
                status="rendered",
                video_filename=video_filename,
                error=None,
            )
        except Exception as error:
            store.update(track_id, status="failed", error=str(error))
            raise HTTPException(status_code=500, detail=f"Video render failed: {error}") from error
        return response_for(track)

    @application.post("/tracks/{track_id}/publish", response_model=PublishResponse)
    async def publish_track(track_id: str, request: PublishRequest) -> PublishResponse:
        track = require_track(track_id)
        if not track.get("video_filename"):
            raise HTTPException(status_code=409, detail="Render the track before publishing")
        video_path = active_settings.rendered_dir / track["video_filename"]
        metadata = PublishMetadata(
            title=request.title.strip(),
            description=request.description,
            tags=tuple(request.tags),
            privacy_status=request.privacy_status,
        )
        store.update(track_id, publish_status="publishing", error=None)

        if request.dry_run:
            manifest = active_settings.data_dir / "publish" / f"{track_id}.json"
            try:
                await asyncio.to_thread(write_publish_manifest, video_path, metadata, manifest)
                track = store.update(track_id, publish_status="dry_run", error=None)
            except Exception as error:
                store.update(track_id, publish_status="failed", error=str(error))
                raise HTTPException(status_code=500, detail=f"Publish dry-run failed: {error}") from error
            return PublishResponse(
                track=response_for(track),
                mode="dry-run",
                message=f"Upload manifest saved locally at {manifest}",
            )

        client_secrets = active_settings.youtube_client_secrets
        token_path = active_settings.youtube_token_path
        if client_secrets is None or token_path is None:
            store.update(track_id, publish_status="failed", error="YouTube OAuth is not configured")
            raise HTTPException(
                status_code=503,
                detail="Set OPENFLOW_YOUTUBE_CLIENT_SECRETS before a real upload",
            )
        try:
            youtube_url = await asyncio.to_thread(
                publish_function,
                video_path,
                metadata,
                client_secrets,
                token_path,
            )
            track = store.update(
                track_id,
                publish_status="published",
                youtube_url=youtube_url,
                error=None,
            )
        except Exception as error:
            store.update(track_id, publish_status="failed", error=str(error))
            raise HTTPException(status_code=502, detail=f"YouTube upload failed: {error}") from error
        return PublishResponse(
            track=response_for(track),
            mode="youtube",
            message="Video uploaded to YouTube",
            youtube_url=youtube_url,
        )

    @application.get("/media/audio/{track_id}", response_class=FileResponse)
    async def audio(track_id: str) -> FileResponse:
        track = require_track(track_id)
        return media_response(
            active_settings.generated_dir,
            track.get("audio_filename"),
            "audio/wav",
            "Audio file not found",
        )

    @application.get("/media/video/{track_id}", response_class=FileResponse)
    async def video(track_id: str) -> FileResponse:
        track = require_track(track_id)
        return media_response(
            active_settings.rendered_dir,
            track.get("video_filename"),
            "video/mp4",
            "Video file not found",
        )

    # Compatibility for clients generated from the initial prototype.
    @application.get("/audio/{filename}", response_class=FileResponse, include_in_schema=False)
    async def legacy_audio(filename: str) -> FileResponse:
        if Path(filename).name != filename:
            raise HTTPException(status_code=400, detail="Invalid audio filename")
        return media_response(active_settings.generated_dir, filename, "audio/wav", "Audio file not found")

    return application


def media_response(directory: Path, filename: str | None, media_type: str, detail: str) -> FileResponse:
    if not filename or Path(filename).name != filename:
        raise HTTPException(status_code=404, detail=detail)
    path = directory / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail=detail)
    return FileResponse(path, media_type=media_type, filename=filename)


app = create_app()
