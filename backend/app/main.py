from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .audio import synthesize_mock_track

BASE_DIR = Path(__file__).resolve().parents[1]
GENERATED_DIR = BASE_DIR / "generated"
ALLOWED_ORIGINS = os.getenv("OPENFLOW_ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app = FastAPI(
    title="openFlow Generation API",
    description="Local-first audio generation service with a dependency-free mock engine.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)
    model: Literal["ace-step", "musicgen", "rvc"] = "ace-step"
    duration_seconds: int = Field(default=8, ge=1, le=30)


class GenerateResponse(BaseModel):
    id: str
    prompt: str
    model: str
    duration_seconds: int
    audio_url: str
    mocked: bool = True


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "engine": "mock"}


@app.post("/generate", response_model=GenerateResponse, status_code=201)
async def generate(request: GenerateRequest) -> GenerateResponse:
    track_id = uuid4().hex
    filename = f"{track_id}.wav"
    destination = GENERATED_DIR / filename
    await asyncio.to_thread(
        synthesize_mock_track,
        destination,
        request.prompt.strip(),
        request.duration_seconds,
    )
    return GenerateResponse(
        id=track_id,
        prompt=request.prompt.strip(),
        model=request.model,
        duration_seconds=request.duration_seconds,
        audio_url=f"/audio/{filename}",
    )


@app.get("/audio/{filename}", response_class=FileResponse)
async def audio(filename: str) -> FileResponse:
    if not filename.endswith(".wav") or Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid audio filename")
    path = GENERATED_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(path, media_type="audio/wav", filename=filename)
