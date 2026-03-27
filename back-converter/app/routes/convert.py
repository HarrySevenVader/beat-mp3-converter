from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.core import metrics_service
from app.models import ConversionError
from app.schemas import (
	AudioOption,
	ConvertPayload,
	CreateJobResponse,
	JobStatusResponse,
	VerifyPayload,
	VerifyResponse,
)
from app.services import ConversionJobManager, ConversionWorkerPool, DownloaderService

router = APIRouter(prefix="/api/convert", tags=["convert"])
job_manager = ConversionJobManager()
worker_pool = ConversionWorkerPool()


def _build_download_name(title: str, extension: str) -> str:
	sanitized = "".join(
		character if character not in '<>:"/\\|?*' else "-"
		for character in title.strip()
	)
	resolved_title = sanitized or "audio-convertido"
	resolved_extension = extension if extension.startswith(".") else f".{extension}"
	return f"{resolved_title}{resolved_extension}"


def _cleanup_job_and_files(job_id: str, service: DownloaderService) -> None:
	job = job_manager.pop_job(job_id)
	if not job or not job.result_file_path:
		return
	service.storage_service.cleanup_job_directory(Path(job.result_file_path).parent)


def _process_job(job_id: str, source_url: str, audio_quality: int) -> None:
	service = DownloaderService()

	try:
		result = service.convert_from_url(
			source_url=source_url,
			audio_quality=audio_quality,
			progress_callback=lambda payload: job_manager.update_progress(job_id, payload),
		)
		job_manager.mark_ready(job_id, result)
		metrics_service.record_job_completed()
	except ConversionError as error:
		job_manager.mark_error(job_id, error)
		metrics_service.record_job_failed()
	except Exception as error:
		job_manager.mark_unexpected_error(job_id, str(error))
		metrics_service.record_job_failed()


def _map_job_status(job_id: str) -> JobStatusResponse:
	job = job_manager.get_job(job_id)
	if not job:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail={
				"code": "JOB_NOT_FOUND",
				"message": "No se encontró la tarea solicitada.",
			},
		)

	return JobStatusResponse(
		job_id=job.job_id,
		state=job.state,
		progress_percent=job.progress_percent,
		message=job.message,
		audio_quality=job.audio_quality,
		eta_seconds=job.eta_seconds,
		error_code=job.error_code,
		error_message=job.error_message,
		title=job.title,
		thumbnail_url=job.thumbnail_url,
	)


@router.post("/verify", response_model=VerifyResponse)
def verify_video(payload: VerifyPayload) -> VerifyResponse:
	service = DownloaderService()

	try:
		metadata = service.fetch_video_metadata(source_url=payload.source_url)
	except ConversionError as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=error.to_dict(),
		) from error

	return VerifyResponse(
		source_url=str(metadata.source_url),
		video_id=metadata.video_id,
		title=metadata.title,
		duration_seconds=metadata.duration_seconds,
		thumbnail_url=metadata.thumbnail_url,
		audio_options=[
			AudioOption(label="MP3 - 320 kbps", bitrate=320),
			AudioOption(label="MP3 - 128 kbps", bitrate=128),
		],
	)


@router.post("/jobs", response_model=CreateJobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_conversion_job(payload: ConvertPayload) -> CreateJobResponse:
	service = DownloaderService()

	try:
		metadata = service.fetch_video_metadata(source_url=payload.source_url)
	except ConversionError as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=error.to_dict(),
		) from error

	job = job_manager.create_job(
		source_url=str(metadata.source_url),
		audio_quality=payload.audio_quality,
		title=metadata.title,
		thumbnail_url=metadata.thumbnail_url,
	)
	metrics_service.record_job_created()

	worker_pool.submit(_process_job, job.job_id, str(metadata.source_url), payload.audio_quality)

	return CreateJobResponse(
		job_id=job.job_id,
		state=job.state,
		progress_percent=job.progress_percent,
		message=job.message,
		audio_quality=job.audio_quality,
		title=job.title,
		thumbnail_url=job.thumbnail_url,
	)


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
def get_conversion_job_status(job_id: str) -> JobStatusResponse:
	return _map_job_status(job_id)


@router.get("/jobs/{job_id}/download")
def download_job_result(job_id: str) -> FileResponse:
	job = job_manager.get_job(job_id)
	if not job:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail={"code": "JOB_NOT_FOUND", "message": "No se encontró la tarea solicitada."},
		)

	if job.state != "ready" or not job.has_download_artifact():
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail={
				"code": "JOB_NOT_READY",
				"message": "La conversión todavía no está lista para descarga.",
			},
		)

	result_path = Path(job.result_file_path or "")
	service = DownloaderService()
	cleanup_task = BackgroundTask(_cleanup_job_and_files, job_id, service)
	download_name = _build_download_name(job.title or "audio-convertido", result_path.suffix or ".mp3")
	metrics_service.record_download()

	return FileResponse(
		path=result_path,
		media_type=job.result_content_type or "application/octet-stream",
		filename=download_name,
		background=cleanup_task,
	)


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
	metrics_service.record_download()

	return FileResponse(
		path=result.file_path,
		media_type=result.content_type,
		filename=download_name,
		background=cleanup_task,
	)

