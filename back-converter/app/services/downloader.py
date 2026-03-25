from __future__ import annotations

import mimetypes
from pathlib import Path
from shutil import which

from pydantic import ValidationError
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError as YtDlpDownloadError

from app.models import (
	AudioExtractionError,
	ConversionRequest,
	ConversionResult,
	ConvertedFileNotFoundError,
	DownloadProcessError,
	InvalidSourceUrlError,
)
from app.services.storage import StorageService


class DownloaderService:
	def __init__(self, storage_service: StorageService | None = None) -> None:
		self.storage_service = storage_service or StorageService()

	def convert_from_url(self, source_url: str, audio_quality: int = 192) -> ConversionResult:
		request = self._build_request(source_url=source_url, audio_quality=audio_quality)
		ffmpeg_location = self._resolve_ffmpeg_location()

		job_id, job_directory = self.storage_service.create_job_directory()
		output_template = str(job_directory / "%(title)s.%(ext)s")

		ydl_options = {
			"format": "bestaudio/best",
			"noplaylist": True,
			"quiet": True,
			"no_warnings": True,
			"restrictfilenames": True,
			"outtmpl": output_template,
			"ffmpeg_location": ffmpeg_location,
			"postprocessors": [
				{
					"key": "FFmpegExtractAudio",
					"preferredcodec": "mp3",
					"preferredquality": str(request.audio_quality),
				}
			],
		}

		try:
			with YoutubeDL(ydl_options) as youtube_dl:
				info = youtube_dl.extract_info(str(request.source_url), download=True)
		except YtDlpDownloadError as error:
			self.storage_service.cleanup_job_directory(job_directory)
			raise DownloadProcessError(
				"No se pudo descargar el recurso solicitado",
				details=str(error),
			) from error
		except Exception as error:
			self.storage_service.cleanup_job_directory(job_directory)
			raise AudioExtractionError("No se pudo convertir el audio a MP3", details=str(error)) from error

		generated_file = self.storage_service.find_generated_mp3(job_directory)
		if generated_file is None:
			self.storage_service.cleanup_job_directory(job_directory)
			raise ConvertedFileNotFoundError(
				"La conversión terminó, pero no se encontró el archivo MP3"
			)

		content_type = mimetypes.guess_type(generated_file.name)[0] or "application/octet-stream"
		output_format = generated_file.suffix.replace(".", "").lower() or "audio"

		return ConversionResult(
			job_id=job_id,
			source_url=request.source_url,
			title=self._resolve_title(info=info, fallback=generated_file),
			file_name=generated_file.name,
			file_path=generated_file,
			content_type=content_type,
			output_format=output_format,
			file_size_bytes=generated_file.stat().st_size,
			duration_seconds=self._resolve_duration_seconds(info),
		)

	@staticmethod
	def _resolve_ffmpeg_location() -> str:
		ffmpeg_in_path = which("ffmpeg")
		if ffmpeg_in_path:
			return ffmpeg_in_path

		try:
			from imageio_ffmpeg import get_ffmpeg_exe

			return get_ffmpeg_exe()
		except Exception as error:
			raise AudioExtractionError(
				"No se encontró FFmpeg para convertir a MP3.",
				details=(
					"Instala FFmpeg en el sistema o instala la dependencia imageio-ffmpeg "
					"en el entorno del backend."
				),
			) from error

	def _build_request(self, source_url: str, audio_quality: int) -> ConversionRequest:
		try:
			return ConversionRequest(source_url=source_url, audio_quality=audio_quality)
		except ValidationError as error:
			message = self._map_validation_message(error)
			raise InvalidSourceUrlError(message, details=str(error)) from error

	@staticmethod
	def _map_validation_message(error: ValidationError) -> str:
		error_text = str(error)
		if "La URL debe pertenecer a YouTube" in error_text:
			return "La URL debe pertenecer a YouTube."
		if "No se encontró un identificador de video válido" in error_text:
			return "No se encontró un identificador de video válido."
		if "URL" in error_text or "url" in error_text:
			return "El formato de la URL no es válido."
		return "La URL de origen no es válida."

	@staticmethod
	def _resolve_title(info: object, fallback: Path) -> str:
		if isinstance(info, dict):
			title = info.get("title")
			if isinstance(title, str) and title.strip():
				return title.strip()
		return fallback.stem

	@staticmethod
	def _resolve_duration_seconds(info: object) -> int | None:
		if isinstance(info, dict):
			duration = info.get("duration")
			if isinstance(duration, int):
				return duration
			if isinstance(duration, float):
				return int(duration)
		return None
