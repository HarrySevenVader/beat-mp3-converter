from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str
    cors_origins: list[str]
    cors_allow_credentials: bool
    jobs_db_path: Path
    worker_max_workers: int


@lru_cache
def get_settings() -> Settings:
    cors_origins = _split_csv(os.getenv("BACKEND_CORS_ORIGINS"))
    if not cors_origins:
        cors_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

    return Settings(
        app_name=os.getenv("BACKEND_APP_NAME", "Beat MP3 Converter API"),
        cors_origins=cors_origins,
        cors_allow_credentials=os.getenv("BACKEND_CORS_ALLOW_CREDENTIALS", "true").lower() == "true",
        jobs_db_path=Path(os.getenv("BACKEND_JOBS_DB_PATH", "downloads/jobs.db")),
        worker_max_workers=max(1, int(os.getenv("BACKEND_WORKER_MAX_WORKERS", "2"))),
    )
