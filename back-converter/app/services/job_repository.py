from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class ConversionJobRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversion_jobs (
                    job_id TEXT PRIMARY KEY,
                    source_url TEXT NOT NULL,
                    audio_quality INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    progress_percent INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    eta_seconds INTEGER,
                    error_code TEXT,
                    error_message TEXT,
                    error_details TEXT,
                    title TEXT,
                    thumbnail_url TEXT,
                    result_file_path TEXT,
                    result_file_name TEXT,
                    result_content_type TEXT,
                    result_output_format TEXT,
                    result_file_size_bytes INTEGER,
                    result_duration_seconds INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def upsert_job(self, payload: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversion_jobs (
                    job_id, source_url, audio_quality, state, progress_percent, message,
                    eta_seconds, error_code, error_message, error_details, title, thumbnail_url,
                    result_file_path, result_file_name, result_content_type, result_output_format,
                    result_file_size_bytes, result_duration_seconds, created_at, updated_at
                )
                VALUES (
                    :job_id, :source_url, :audio_quality, :state, :progress_percent, :message,
                    :eta_seconds, :error_code, :error_message, :error_details, :title, :thumbnail_url,
                    :result_file_path, :result_file_name, :result_content_type, :result_output_format,
                    :result_file_size_bytes, :result_duration_seconds, :created_at, :updated_at
                )
                ON CONFLICT(job_id) DO UPDATE SET
                    source_url = excluded.source_url,
                    audio_quality = excluded.audio_quality,
                    state = excluded.state,
                    progress_percent = excluded.progress_percent,
                    message = excluded.message,
                    eta_seconds = excluded.eta_seconds,
                    error_code = excluded.error_code,
                    error_message = excluded.error_message,
                    error_details = excluded.error_details,
                    title = excluded.title,
                    thumbnail_url = excluded.thumbnail_url,
                    result_file_path = excluded.result_file_path,
                    result_file_name = excluded.result_file_name,
                    result_content_type = excluded.result_content_type,
                    result_output_format = excluded.result_output_format,
                    result_file_size_bytes = excluded.result_file_size_bytes,
                    result_duration_seconds = excluded.result_duration_seconds,
                    updated_at = excluded.updated_at
                """,
                payload,
            )

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM conversion_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            return dict(row) if row else None

    def delete_job(self, job_id: str) -> dict[str, Any] | None:
        row = self.get_job(job_id)
        if row is None:
            return None

        with self._connect() as connection:
            connection.execute("DELETE FROM conversion_jobs WHERE job_id = ?", (job_id,))
        return row

    def clear_all(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM conversion_jobs")
