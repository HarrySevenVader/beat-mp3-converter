from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from app.core import get_settings
from app.models import ConversionError, ConversionResult
from app.services.job_repository import ConversionJobRepository


@dataclass
class ConversionJob:
    job_id: str
    source_url: str
    audio_quality: int
    state: str = "queued"
    progress_percent: int = 0
    message: str = "En cola"
    eta_seconds: int | None = None
    error_code: str | None = None
    error_message: str | None = None
    error_details: str | None = None
    title: str | None = None
    thumbnail_url: str | None = None
    result_file_path: str | None = None
    result_file_name: str | None = None
    result_content_type: str | None = None
    result_output_format: str | None = None
    result_file_size_bytes: int | None = None
    result_duration_seconds: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def has_download_artifact(self) -> bool:
        return bool(self.result_file_path and self.result_file_name and self.result_content_type)


class ConversionJobManager:
    def __init__(self, repository: ConversionJobRepository | None = None) -> None:
        settings = get_settings()
        self._repository = repository or ConversionJobRepository(settings.jobs_db_path)
        self._lock = Lock()

    def create_job(
        self,
        *,
        source_url: str,
        audio_quality: int,
        title: str | None = None,
        thumbnail_url: str | None = None,
    ) -> ConversionJob:
        job = ConversionJob(
            job_id=uuid4().hex,
            source_url=source_url,
            audio_quality=audio_quality,
            title=title,
            thumbnail_url=thumbnail_url,
            state="queued",
            progress_percent=0,
            message="Esperando inicio de conversión",
        )
        with self._lock:
            self._repository.upsert_job(self._to_record(job))
        return job

    def get_job(self, job_id: str) -> ConversionJob | None:
        with self._lock:
            row = self._repository.get_job(job_id)
        return self._from_record(row) if row else None

    def pop_job(self, job_id: str) -> ConversionJob | None:
        with self._lock:
            row = self._repository.delete_job(job_id)
        return self._from_record(row) if row else None

    def clear_all_jobs(self) -> None:
        with self._lock:
            self._repository.clear_all()

    def update_progress(self, job_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            row = self._repository.get_job(job_id)
            job = self._from_record(row) if row else None
            if not job:
                return

            state = payload.get("state")
            if isinstance(state, str) and state:
                job.state = state

            progress = payload.get("progress_percent")
            if isinstance(progress, int):
                job.progress_percent = max(0, min(progress, 100))
            elif isinstance(progress, float):
                job.progress_percent = max(0, min(int(progress), 100))

            message = payload.get("message")
            if isinstance(message, str) and message:
                job.message = message

            eta_seconds = payload.get("eta_seconds")
            if isinstance(eta_seconds, int):
                job.eta_seconds = max(0, eta_seconds)
            elif eta_seconds is None:
                job.eta_seconds = None

            job.updated_at = datetime.now(timezone.utc)
            self._repository.upsert_job(self._to_record(job))

    def mark_ready(self, job_id: str, result: ConversionResult) -> None:
        with self._lock:
            row = self._repository.get_job(job_id)
            job = self._from_record(row) if row else None
            if not job:
                return

            job.state = "ready"
            job.progress_percent = 100
            job.message = "Conversión completada"
            job.title = result.title
            job.eta_seconds = None
            job.result_file_path = str(result.file_path)
            job.result_file_name = result.file_name
            job.result_content_type = result.content_type
            job.result_output_format = result.output_format
            job.result_file_size_bytes = result.file_size_bytes
            job.result_duration_seconds = result.duration_seconds
            job.updated_at = datetime.now(timezone.utc)
            self._repository.upsert_job(self._to_record(job))

    def mark_error(self, job_id: str, error: ConversionError) -> None:
        with self._lock:
            row = self._repository.get_job(job_id)
            job = self._from_record(row) if row else None
            if not job:
                return

            job.state = "error"
            job.message = "Conversión fallida"
            job.error_code = error.code
            job.error_message = error.message
            job.error_details = error.details
            job.eta_seconds = None
            job.updated_at = datetime.now(timezone.utc)
            self._repository.upsert_job(self._to_record(job))

    def mark_unexpected_error(self, job_id: str, details: str) -> None:
        with self._lock:
            row = self._repository.get_job(job_id)
            job = self._from_record(row) if row else None
            if not job:
                return

            job.state = "error"
            job.message = "Conversión fallida"
            job.error_code = "UNEXPECTED_ERROR"
            job.error_message = "Se produjo un error inesperado durante la conversión."
            job.error_details = details
            job.eta_seconds = None
            job.updated_at = datetime.now(timezone.utc)
            self._repository.upsert_job(self._to_record(job))

    @staticmethod
    def _to_record(job: ConversionJob) -> dict[str, Any]:
        return {
            "job_id": job.job_id,
            "source_url": job.source_url,
            "audio_quality": job.audio_quality,
            "state": job.state,
            "progress_percent": job.progress_percent,
            "message": job.message,
            "eta_seconds": job.eta_seconds,
            "error_code": job.error_code,
            "error_message": job.error_message,
            "error_details": job.error_details,
            "title": job.title,
            "thumbnail_url": job.thumbnail_url,
            "result_file_path": job.result_file_path,
            "result_file_name": job.result_file_name,
            "result_content_type": job.result_content_type,
            "result_output_format": job.result_output_format,
            "result_file_size_bytes": job.result_file_size_bytes,
            "result_duration_seconds": job.result_duration_seconds,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
        }

    @staticmethod
    def _from_record(row: dict[str, Any]) -> ConversionJob:
        return ConversionJob(
            job_id=row["job_id"],
            source_url=row["source_url"],
            audio_quality=row["audio_quality"],
            state=row["state"],
            progress_percent=row["progress_percent"],
            message=row["message"],
            eta_seconds=row["eta_seconds"],
            error_code=row["error_code"],
            error_message=row["error_message"],
            error_details=row["error_details"],
            title=row["title"],
            thumbnail_url=row["thumbnail_url"],
            result_file_path=row["result_file_path"],
            result_file_name=row["result_file_name"],
            result_content_type=row["result_content_type"],
            result_output_format=row["result_output_format"],
            result_file_size_bytes=row["result_file_size_bytes"],
            result_duration_seconds=row["result_duration_seconds"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
