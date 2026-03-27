from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
}


class ConversionRequest(BaseModel):
    source_url: HttpUrl = Field(..., description="URL de origen del video de YouTube")
    audio_quality: int = Field(
        default=192,
        ge=64,
        le=320,
        description="Calidad de salida MP3 en kbps",
    )

    @field_validator("source_url")
    @classmethod
    def validate_youtube_source(cls, value: HttpUrl) -> HttpUrl:
        host = value.host.lower() if value.host else ""

        if host not in YOUTUBE_HOSTS:
            raise ValueError("La URL debe pertenecer a YouTube")

        parsed = urlparse(str(value))
        query_params = parse_qs(parsed.query)
        video_query_value = query_params.get("v", [""])[0].strip()

        is_short = "youtu.be" in host and parsed.path.strip("/") != ""
        has_video_query = bool(video_query_value)
        is_supported_path = parsed.path.startswith(("/watch", "/embed", "/shorts", "/live"))

        if not any((is_short, has_video_query, is_supported_path)):
            raise ValueError("No se encontró un identificador de video válido")

        return value


class ConversionResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    job_id: str
    source_url: HttpUrl
    title: str
    file_name: str
    file_path: Path
    content_type: str
    output_format: str
    file_size_bytes: int
    duration_seconds: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VideoMetadata(BaseModel):
    source_url: HttpUrl
    video_id: str
    title: str
    duration_seconds: int | None = None
    thumbnail_url: str | None = None
