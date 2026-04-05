from __future__ import annotations

import mimetypes
from pathlib import Path
from shutil import which
from typing import Any, Callable
from urllib.parse import parse_qs, quote, urlparse

from pydantic import ValidationError
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError as YtDlpDownloadError

from app.core import get_settings
from app.models import (
	AudioExtractionError,
	ConversionRequest,
	ConversionResult,
	ConvertedFileNotFoundError,
	DownloadProcessError,
	InvalidSourceUrlError,
	VideoMetadata,
)
from app.services.storage import StorageService


ProgressCallback = Callable[[dict[str, object]], None]


class DownloaderService:
	def __init__(self, storage_service: StorageService | None = None) -> None:
		self.storage_service = storage_service or StorageService()
		self.settings = get_settings()

	def _build_cookie_options(self) -> dict[str, Any]:
		if not self.settings.ytdlp_cookies_enabled:
			return {}

		cookie_file = self.settings.ytdlp_cookies_file
		cookie_file.parent.mkdir(parents=True, exist_ok=True)

		cookie_options: dict[str, Any] = {
			"cookiefile": str(cookie_file),
		}

		if self.settings.ytdlp_cookies_browser:
			cookie_options["cookiesfrombrowser"] = (self.settings.ytdlp_cookies_browser,)

		return cookie_options

	def fetch_video_metadata(self, source_url: str) -> VideoMetadata:
		request = self._build_request(source_url=source_url, audio_quality=192)
		resolved_source_url = self._canonicalize_youtube_url(str(request.source_url))

		ydl_options = {
			"noplaylist": True,
			"quiet": True,
			"no_warnings": True,
			"geo_bypass": True,
			"skip_download": True,
			"retries": 3,
			"extractor_args": {
				"youtube": {"player_client": ["android", "web"]},
			},
			**self._build_cookie_options(),
		}

		try:
			with YoutubeDL(ydl_options) as youtube_dl:
				info = youtube_dl.extract_info(resolved_source_url, download=False)
		except YtDlpDownloadError as error:
			message = self._map_ytdlp_error_message(str(error), verify_mode=True)
			raise DownloadProcessError(
				message,
				details=str(error),
			) from error
		except Exception as error:
			raise AudioExtractionError(
				"No se pudieron obtener los metadatos del video.",
				details=str(error),
			) from error

		video_id = self._resolve_video_id(info)
		if not video_id:
			raise DownloadProcessError("No se pudo determinar el identificador del video.")

		return VideoMetadata(
			source_url=request.source_url,
			video_id=video_id,
			title=self._resolve_title(info=info, fallback=Path(video_id)),
			duration_seconds=self._resolve_duration_seconds(info),
			thumbnail_url=self._resolve_thumbnail_url(info),
		)

	def convert_from_url(
		self,
		source_url: str,
		audio_quality: int = 192,
		progress_callback: ProgressCallback | None = None,
	) -> ConversionResult:
		request = self._build_request(source_url=source_url, audio_quality=audio_quality)
		resolved_source_url = self._canonicalize_youtube_url(str(request.source_url))
		ffmpeg_location = self._resolve_ffmpeg_location()

		job_id, job_directory = self.storage_service.create_job_directory()
		output_template = str(job_directory / "%(title)s.%(ext)s")
		self._emit_progress(
			progress_callback,
			{
				"state": "starting",
				"progress_percent": 2,
				"message": "Inicializando descarga",
			},
		)

		ydl_options = {
			"format": "bestaudio/best",
			"noplaylist": True,
			"quiet": True,
			"no_warnings": True,
			"geo_bypass": True,
			"retries": 3,
			"restrictfilenames": True,
			"outtmpl": output_template,
			"ffmpeg_location": ffmpeg_location,
			"extractor_args": {
				"youtube": {"player_client": ["android", "web"]},
			},
			**self._build_cookie_options(),
			"postprocessors": [
				{
					"key": "FFmpegExtractAudio",
					"preferredcodec": "mp3",
					"preferredquality": str(request.audio_quality),
				}
			],
			"progress_hooks": [self._build_progress_hook(progress_callback)],
			"postprocessor_hooks": [self._build_postprocessor_hook(progress_callback)],
		}

		try:
			with YoutubeDL(ydl_options) as youtube_dl:
				info = youtube_dl.extract_info(resolved_source_url, download=True)
		except YtDlpDownloadError as error:
			self.storage_service.cleanup_job_directory(job_directory)
			self._emit_progress(
				progress_callback,
				{"state": "error", "progress_percent": 0, "message": "Error durante la descarga"},
			)
			message = self._map_ytdlp_error_message(str(error), verify_mode=False)
			raise DownloadProcessError(
				message,
				details=str(error),
			) from error
		except Exception as error:
			self.storage_service.cleanup_job_directory(job_directory)
			self._emit_progress(
				progress_callback,
				{"state": "error", "progress_percent": 0, "message": "Error durante la conversión"},
			)
			raise AudioExtractionError("No se pudo convertir el audio a MP3", details=str(error)) from error

		generated_file = self.storage_service.find_generated_mp3(job_directory)
		if generated_file is None:
			self.storage_service.cleanup_job_directory(job_directory)
			raise ConvertedFileNotFoundError(
				"La conversión terminó, pero no se encontró el archivo MP3"
			)

		content_type = mimetypes.guess_type(generated_file.name)[0] or "application/octet-stream"
		output_format = generated_file.suffix.replace(".", "").lower() or "audio"
		self._emit_progress(
			progress_callback,
			{"state": "ready", "progress_percent": 100, "message": "Conversión completada"},
		)

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
	def _canonicalize_youtube_url(source_url: str) -> str:
		parsed = urlparse(source_url)
		host = parsed.netloc.lower()
		path_segments = [segment for segment in parsed.path.split("/") if segment]
		query = parse_qs(parsed.query)

		video_id = ""
		if "youtu.be" in host and path_segments:
			video_id = path_segments[0]
		elif path_segments and path_segments[0] in {"shorts", "embed", "live"} and len(path_segments) > 1:
			video_id = path_segments[1]
		else:
			video_id = (query.get("v") or [""])[0]

		video_id = video_id.strip()
		if not video_id:
			return source_url

		return f"https://www.youtube.com/watch?v={quote(video_id)}"

	@staticmethod
	def _map_ytdlp_error_message(error_text: str, *, verify_mode: bool) -> str:
		normalized = error_text.lower()

		if "private video" in normalized or "is private" in normalized:
			return "El video es privado y no se puede procesar."
		if "video unavailable" in normalized or "this video is unavailable" in normalized:
			return "El video no está disponible en este momento."
		if "sign in to confirm you're not a bot" in normalized or "confirm you're not a bot" in normalized:
			return (
				"YouTube bloqueó temporalmente la consulta del servidor. "
				"Habilita cookies de navegador en el backend o intenta con otra URL pública."
			)

		if verify_mode:
			return "No se pudo verificar la URL en el servidor."
		return "No se pudo descargar el recurso solicitado."

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

	@staticmethod
	def _resolve_video_id(info: object) -> str | None:
		if isinstance(info, dict):
			video_id = info.get("id")
			if isinstance(video_id, str) and video_id.strip():
				return video_id.strip()
		return None

	@staticmethod
	def _resolve_thumbnail_url(info: object) -> str | None:
		if not isinstance(info, dict):
			return None

		thumbnail = info.get("thumbnail")
		if isinstance(thumbnail, str) and thumbnail.strip():
			return thumbnail.strip()

		thumbnails = info.get("thumbnails")
		if isinstance(thumbnails, list):
			for item in reversed(thumbnails):
				if isinstance(item, dict):
					url = item.get("url")
					if isinstance(url, str) and url.strip():
						return url.strip()
		return None

	def _build_progress_hook(self, callback: ProgressCallback | None) -> Callable[[dict[str, Any]], None]:
		def hook(data: dict[str, Any]) -> None:
			if callback is None:
				return

			status = str(data.get("status", ""))
			if status == "downloading":
				total_bytes = data.get("total_bytes") or data.get("total_bytes_estimate")
				downloaded_bytes = data.get("downloaded_bytes")
				percent = 10
				if isinstance(total_bytes, (int, float)) and isinstance(downloaded_bytes, (int, float)) and total_bytes > 0:
					percent = int((downloaded_bytes / total_bytes) * 80)
				percent = max(5, min(percent, 90))

				eta = data.get("eta")
				eta_seconds = int(eta) if isinstance(eta, (int, float)) else None

				self._emit_progress(
					callback,
					{
						"state": "downloading",
						"progress_percent": percent,
						"message": "Descargando audio del video",
						"eta_seconds": eta_seconds,
					},
				)
			elif status == "finished":
				self._emit_progress(
					callback,
					{
						"state": "extracting",
						"progress_percent": 92,
						"message": "Extrayendo audio a MP3",
						"eta_seconds": None,
					},
				)

		return hook

	def _build_postprocessor_hook(self, callback: ProgressCallback | None) -> Callable[[dict[str, Any]], None]:
		def hook(data: dict[str, Any]) -> None:
			if callback is None:
				return

			status = str(data.get("status", ""))
			if status == "started":
				self._emit_progress(
					callback,
					{
						"state": "extracting",
						"progress_percent": 94,
						"message": "Iniciando transcodificación",
					},
				)
			elif status == "finished":
				self._emit_progress(
					callback,
					{
						"state": "finalizing",
						"progress_percent": 98,
						"message": "Finalizando archivo MP3",
					},
				)

		return hook

	@staticmethod
	def _emit_progress(callback: ProgressCallback | None, payload: dict[str, object]) -> None:
		if callback is not None:
			callback(payload)
