from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4


class StorageService:
    def __init__(self, base_dir: Path | None = None) -> None:
        project_root = Path(__file__).resolve().parents[2]
        self.base_dir = base_dir or (project_root / "downloads")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_job_directory(self, job_id: str | None = None) -> tuple[str, Path]:
        resolved_job_id = job_id or uuid4().hex
        job_directory = self.base_dir / resolved_job_id
        job_directory.mkdir(parents=True, exist_ok=True)
        return resolved_job_id, job_directory

    def find_generated_mp3(self, job_directory: Path) -> Path | None:
        matches = sorted(job_directory.glob("*.mp3"), key=lambda item: item.stat().st_mtime, reverse=True)
        return matches[0] if matches else None

    def find_generated_audio(self, job_directory: Path) -> Path | None:
        audio_extensions = ("*.mp3", "*.m4a", "*.webm", "*.opus", "*.ogg")
        candidates: list[Path] = []
        for extension in audio_extensions:
            candidates.extend(job_directory.glob(extension))

        matches = sorted(candidates, key=lambda item: item.stat().st_mtime, reverse=True)
        return matches[0] if matches else None

    def cleanup_job_directory(self, job_directory: Path) -> None:
        if job_directory.exists() and job_directory.is_dir():
            shutil.rmtree(job_directory, ignore_errors=True)
