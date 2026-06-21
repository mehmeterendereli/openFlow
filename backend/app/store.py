from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TRACK_FIELDS = {
    "prompt",
    "model",
    "duration_seconds",
    "status",
    "audio_filename",
    "video_filename",
    "publish_status",
    "youtube_url",
    "error",
    "updated_at",
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class TrackStore:
    """Small SQLite repository; every operation owns its connection for thread safety."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tracks (
                    id TEXT PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    model TEXT NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    audio_filename TEXT,
                    video_filename TEXT,
                    publish_status TEXT NOT NULL DEFAULT 'not_published',
                    youtube_url TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, *, track_id: str, prompt: str, model: str, duration_seconds: int) -> dict[str, Any]:
        timestamp = utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tracks (
                    id, prompt, model, duration_seconds, status,
                    publish_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'generating', 'not_published', ?, ?)
                """,
                (track_id, prompt, model, duration_seconds, timestamp, timestamp),
            )
        return self.require(track_id)

    def get(self, track_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM tracks WHERE id = ?", (track_id,)).fetchone()
        return dict(row) if row else None

    def require(self, track_id: str) -> dict[str, Any]:
        track = self.get(track_id)
        if track is None:
            raise KeyError(track_id)
        return track

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM tracks ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def update(self, track_id: str, **values: Any) -> dict[str, Any]:
        unknown = set(values) - TRACK_FIELDS
        if unknown:
            raise ValueError(f"Unknown track fields: {', '.join(sorted(unknown))}")
        if not values:
            return self.require(track_id)
        values["updated_at"] = utc_now()
        assignments = ", ".join(f"{field} = ?" for field in values)
        parameters = [*values.values(), track_id]
        with self._connect() as connection:
            cursor = connection.execute(
                f"UPDATE tracks SET {assignments} WHERE id = ?",  # noqa: S608 - fields are allowlisted
                parameters,
            )
            if cursor.rowcount == 0:
                raise KeyError(track_id)
        return self.require(track_id)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection
