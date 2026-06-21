from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    data_dir: Path
    generated_dir: Path
    rendered_dir: Path
    database_path: Path
    default_background: Path
    allowed_origins: tuple[str, ...] = ("http://localhost:3000",)
    youtube_client_secrets: Path | None = None
    youtube_token_path: Path | None = None

    @classmethod
    def from_environment(cls) -> Settings:
        backend_dir = Path(__file__).resolve().parents[1]
        repository_dir = backend_dir.parent
        data_dir = Path(os.getenv("OPENFLOW_DATA_DIR", backend_dir / "data")).resolve()
        origins = tuple(
            origin.strip()
            for origin in os.getenv("OPENFLOW_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
            if origin.strip()
        )
        secrets_value = os.getenv("OPENFLOW_YOUTUBE_CLIENT_SECRETS")
        token_value = os.getenv("OPENFLOW_YOUTUBE_TOKEN")
        return cls(
            data_dir=data_dir,
            generated_dir=data_dir / "audio",
            rendered_dir=data_dir / "video",
            database_path=data_dir / "openflow.db",
            default_background=repository_dir / "automation" / "placeholder.ppm",
            allowed_origins=origins,
            youtube_client_secrets=Path(secrets_value).resolve() if secrets_value else None,
            youtube_token_path=(
                Path(token_value).resolve() if token_value else data_dir / "youtube_token.json"
            ),
        )

    def prepare(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        self.rendered_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "publish").mkdir(parents=True, exist_ok=True)
