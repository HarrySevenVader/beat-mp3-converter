class ConversionError(Exception):
    """Error base para la lógica de conversión."""

    code = "CONVERSION_ERROR"
    default_message = "Se produjo un error durante la conversión."

    def __init__(self, message: str | None = None, *, details: str | None = None) -> None:
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> dict[str, str]:
        payload = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            payload["details"] = self.details
        return payload


class InvalidSourceUrlError(ConversionError):
    """URL de origen inválida o no compatible."""

    code = "INVALID_SOURCE_URL"
    default_message = "La URL de origen no es válida."


class DownloadProcessError(ConversionError):
    """Falla durante la descarga del contenido."""

    code = "DOWNLOAD_PROCESS_ERROR"
    default_message = "No se pudo descargar el recurso solicitado."


class AudioExtractionError(ConversionError):
    """Falla durante la extracción/transcodificación de audio."""

    code = "AUDIO_EXTRACTION_ERROR"
    default_message = "No se pudo extraer el audio del recurso."


class ConvertedFileNotFoundError(ConversionError):
    """No se encontró el archivo MP3 de salida."""

    code = "CONVERTED_FILE_NOT_FOUND"
    default_message = "No se encontró el archivo MP3 generado."
