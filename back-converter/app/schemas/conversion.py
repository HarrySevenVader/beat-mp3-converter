from pydantic import BaseModel, Field


class VerifyPayload(BaseModel):
    source_url: str = Field(..., description="URL de YouTube")


class AudioOption(BaseModel):
    label: str
    bitrate: int


class VerifyResponse(BaseModel):
    source_url: str
    video_id: str
    title: str
    duration_seconds: int | None
    thumbnail_url: str | None
    audio_options: list[AudioOption]


class ConvertPayload(BaseModel):
    source_url: str = Field(..., description="URL de YouTube")
    audio_quality: int = Field(default=192, ge=64, le=320)


class CreateJobResponse(BaseModel):
    job_id: str
    state: str
    progress_percent: int
    message: str
    audio_quality: int
    title: str | None = None
    thumbnail_url: str | None = None


class JobStatusResponse(BaseModel):
    job_id: str
    state: str
    progress_percent: int
    message: str
    audio_quality: int
    eta_seconds: int | None = None
    error_code: str | None = None
    error_message: str | None = None
    title: str | None = None
    thumbnail_url: str | None = None
