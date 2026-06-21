from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ModelName = Literal["ace-step", "musicgen", "rvc"]
TrackStatus = Literal["generating", "ready", "rendering", "rendered", "failed"]
PublishStatus = Literal["not_published", "publishing", "dry_run", "published", "failed"]


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)
    model: ModelName = "ace-step"
    duration_seconds: int = Field(default=8, ge=1, le=30)


class TrackResponse(BaseModel):
    id: str
    prompt: str
    model: ModelName
    duration_seconds: int
    status: TrackStatus
    publish_status: PublishStatus
    audio_url: str | None = None
    video_url: str | None = None
    youtube_url: str | None = None
    error: str | None = None
    mocked: bool = True
    created_at: str
    updated_at: str


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    engine: str
    ffmpeg_available: bool
    track_count: int


class PublishRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="Generated locally with openFlow.", max_length=5000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    privacy_status: Literal["private", "unlisted", "public"] = "private"
    dry_run: bool = True


class PublishResponse(BaseModel):
    track: TrackResponse
    mode: Literal["dry-run", "youtube"]
    message: str
    youtube_url: str | None = None
