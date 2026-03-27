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
    runtime_mode: str
    app_name: str
    cors_origins: list[str]
    cors_allow_credentials: bool
    jobs_db_path: Path
    worker_max_workers: int


def _resolve_runtime_mode() -> str:
    FORCE_RUNTIME_MODE = None
    # FORCE_RUNTIME_MODE = "prod"
    mode = (FORCE_RUNTIME_MODE or os.getenv("BACKEND_RUNTIME_MODE", "dev")).lower()
    return "prod" if mode == "prod" else "dev"


@lru_cache
def get_settings() -> Settings:
    runtime_mode = _resolve_runtime_mode()

    cors_env_key = "BACKEND_CORS_ORIGINS_PROD" if runtime_mode == "prod" else "BACKEND_CORS_ORIGINS_DEV"
    cors_origins = _split_csv(os.getenv(cors_env_key))
    if not cors_origins:
        cors_origins = (
            ["https://tu-frontend.vercel.app"]
            if runtime_mode == "prod"
            else [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]
        )

    jobs_db_path = Path(
        os.getenv(
            "BACKEND_JOBS_DB_PATH_PROD" if runtime_mode == "prod" else "BACKEND_JOBS_DB_PATH_DEV",
            "downloads/jobs.db" if runtime_mode == "prod" else "downloads/jobs-dev.db",
        )
    )

    worker_max_workers = max(
        1,
        int(
            os.getenv(
                "BACKEND_WORKER_MAX_WORKERS_PROD" if runtime_mode == "prod" else "BACKEND_WORKER_MAX_WORKERS_DEV",
                "2" if runtime_mode == "prod" else "1",
            )
        ),
    )

    return Settings(
        runtime_mode=runtime_mode,
        app_name=os.getenv("BACKEND_APP_NAME", "Beat MP3 Converter API"),
        cors_origins=cors_origins,
        cors_allow_credentials=os.getenv("BACKEND_CORS_ALLOW_CREDENTIALS", "true").lower() == "true",
        jobs_db_path=jobs_db_path,
        worker_max_workers=worker_max_workers,
    )
