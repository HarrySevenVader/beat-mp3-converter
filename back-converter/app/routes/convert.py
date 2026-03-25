from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask

from app.models import ConversionError
from app.services import DownloaderService

router = APIRouter(prefix="/api/convert", tags=["convert"])


class ConvertPayload(BaseModel):
	source_url: str = Field(..., description="URL de YouTube")
	audio_quality: int = Field(default=192, ge=64, le=320)


def _build_download_name(title: str, extension: str) -> str:
	sanitized = "".join(
		character if character not in '<>:"/\\|?*' else "-"
		for character in title.strip()
	)
	resolved_title = sanitized or "audio-convertido"
	resolved_extension = extension if extension.startswith(".") else f".{extension}"
	return f"{resolved_title}{resolved_extension}"


@router.post("/download")
def download_mp3(payload: ConvertPayload) -> FileResponse:
	service = DownloaderService()

	try:
		result = service.convert_from_url(
			source_url=payload.source_url,
			audio_quality=payload.audio_quality,
		)
	except ConversionError as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=error.to_dict(),
		) from error

	cleanup_task = BackgroundTask(
		service.storage_service.cleanup_job_directory,
		result.file_path.parent,
	)
	download_name = _build_download_name(result.title, result.file_path.suffix)

	return FileResponse(
		path=result.file_path,
		media_type=result.content_type,
		filename=download_name,
		background=cleanup_task,
	)

