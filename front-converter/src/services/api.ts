const YOUTUBE_HOSTS = [
	"youtube.com",
	"www.youtube.com",
	"m.youtube.com",
	"music.youtube.com",
	"youtu.be",
	"www.youtu.be",
];

export type ValidationResult = {
	valid: boolean;
	message?: string;
	normalizedUrl?: string;
};

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
