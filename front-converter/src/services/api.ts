const YOUTUBE_HOSTS = [
	"youtube.com",
	"www.youtube.com",
	"m.youtube.com",
	"music.youtube.com",
	"youtu.be",
	"www.youtu.be",
];

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8080";

export type ValidationResult = {
	valid: boolean;
	message?: string;
	normalizedUrl?: string;
};

type ApiErrorDetail = {
	code?: string;
	message?: string;
	details?: string;
};

export class ApiClientError extends Error {
	readonly code?: string;

	constructor(message: string, code?: string) {
		super(message);
		this.name = "ApiClientError";
		this.code = code;
	}
}

export function validateYoutubeUrl(value: string): ValidationResult {
	const cleanValue = value.trim();

	if (!cleanValue) {
		return {
			valid: false,
			message: "Debes ingresar una URL de YouTube.",
		};
	}

	let parsedUrl: URL;

	try {
		parsedUrl = new URL(cleanValue);
	} catch {
		return {
			valid: false,
			message: "El formato de la URL no es válido.",
		};
	}

	const host = parsedUrl.hostname.toLowerCase();

	if (!YOUTUBE_HOSTS.includes(host)) {
		return {
			valid: false,
			message: "La URL debe pertenecer a YouTube.",
		};
	}

	const isShortHost = host.includes("youtu.be") && parsedUrl.pathname.length > 1;
	const hasVideoIdInQuery = parsedUrl.searchParams.has("v");
	const isSupportedPath = /^\/(watch|embed|shorts|live)\/?/.test(parsedUrl.pathname);

	if (!isShortHost && !hasVideoIdInQuery && !isSupportedPath) {
		return {
			valid: false,
			message: "No se encontró un identificador de video válido.",
		};
	}

	return {
		valid: true,
		normalizedUrl: parsedUrl.toString(),
	};
}

function parseApiError(status: number, detail: unknown): ApiClientError {
	if (typeof detail === "object" && detail !== null) {
		const parsed = detail as ApiErrorDetail;
		if (parsed.message) {
			return new ApiClientError(parsed.message, parsed.code);
		}
	}

	if (status >= 500) {
		return new ApiClientError("El servidor no está disponible en este momento.");
	}

	return new ApiClientError("No se pudo procesar la solicitud de conversión.");
}

function extractFileName(contentDisposition: string): string | null {
	if (!contentDisposition) {
		return null;
	}

	const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
	if (utf8Match?.[1]) {
		try {
			return decodeURIComponent(utf8Match[1]);
		} catch {
			return utf8Match[1];
		}
	}

	const plainMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
	if (plainMatch?.[1]) {
		return plainMatch[1];
	}

	return null;
}

export async function downloadConvertedMp3(sourceUrl: string, audioQuality = 192): Promise<void> {
	const response = await fetch(`${API_BASE_URL}/api/convert/download`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({
			source_url: sourceUrl,
			audio_quality: audioQuality,
		}),
	});

	if (!response.ok) {
		let detail: unknown = null;
		try {
			const payload = (await response.json()) as { detail?: unknown };
			detail = payload.detail;
		} catch {
			detail = null;
		}

		throw parseApiError(response.status, detail);
	}

	const blob = await response.blob();
	const contentDisposition = response.headers.get("content-disposition") ?? "";
	const fileName = extractFileName(contentDisposition) ?? "audio-convertido.mp3";

	const blobUrl = window.URL.createObjectURL(blob);
	const anchor = document.createElement("a");
	anchor.href = blobUrl;
	anchor.download = fileName;
	document.body.append(anchor);
	anchor.click();
	anchor.remove();
	window.URL.revokeObjectURL(blobUrl);
}
