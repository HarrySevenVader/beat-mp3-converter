import { useEffect, useRef, useState } from "react";
import {
	ApiClientError,
	createConversionJob,
	downloadConversionJob,
	getConversionJobStatus,
	validateYoutubeUrl,
	verifyYoutubeVideo,
} from "@/services/api";
import { ConversionJobStatus, VerifiedVideo } from "@/types";

export type ConverterPanelState = "idle" | "verifying" | "verified" | "converting" | "ready";

type UseConvertResult = {
	sourceUrl: string;
	verifiedVideo: VerifiedVideo | null;
	panelState: ConverterPanelState;
	selectedBitrate: number;
	jobStatus: ConversionJobStatus | null;
	isBusy: boolean;
	setSourceUrl: (value: string) => void;
	verifySourceUrl: () => Promise<void>;
	pickAndConvert: (bitrate: number) => Promise<void>;
	downloadReadyFile: () => Promise<void>;
	resetVerification: () => void;
};

export function useConvert(): UseConvertResult {
	const [sourceUrl, setSourceUrl] = useState("");
	const [verifiedVideo, setVerifiedVideo] = useState<VerifiedVideo | null>(null);
	const [panelState, setPanelState] = useState<ConverterPanelState>("idle");
	const [selectedBitrate, setSelectedBitrate] = useState(320);
	const [jobStatus, setJobStatus] = useState<ConversionJobStatus | null>(null);

	const pollingRef = useRef(true);
	const activeJobIdRef = useRef<string | null>(null);

	const isBusy = panelState === "verifying" || panelState === "converting";

	const verifySourceUrl = async () => {
		const validation = validateYoutubeUrl(sourceUrl);
		if (!validation.valid) {
			throw new ApiClientError(validation.message ?? "Ingresa una URL válida de YouTube para continuar.");
		}

		const normalizedUrl = validation.normalizedUrl ?? sourceUrl.trim();
		setPanelState("verifying");
		setJobStatus(null);

		try {
			const verified = await verifyYoutubeVideo(normalizedUrl);
			setSourceUrl(verified.source_url);
			setVerifiedVideo(verified);
			setSelectedBitrate(verified.audio_options[0]?.bitrate ?? 320);
			setPanelState("verified");
		} catch (error) {
			setPanelState("idle");

			if (error instanceof ApiClientError) {
				throw error;
			}

			throw new ApiClientError("No se pudo verificar la URL en este momento.");
		}
	};

	const pollJobUntilReady = async (jobId: string): Promise<void> => {
		pollingRef.current = true;

		while (pollingRef.current) {
			const status = await getConversionJobStatus(jobId);
			setJobStatus(status);

			if (status.state === "ready") {
				return;
			}

			if (status.state === "error") {
				throw new ApiClientError(
					status.error_message ?? "La conversión falló durante el proceso.",
					status.error_code ?? undefined,
				);
			}

			await new Promise((resolve) => setTimeout(resolve, 800));
		}

		throw new ApiClientError("El seguimiento de la conversión fue cancelado.");
	};

	const pickAndConvert = async (bitrate: number) => {
		if (!verifiedVideo) {
			throw new ApiClientError("Primero debes verificar una URL válida.");
		}

		setSelectedBitrate(bitrate);
		setPanelState("converting");

		try {
			const job = await createConversionJob(verifiedVideo.source_url, bitrate);
			activeJobIdRef.current = job.job_id;
			setJobStatus({
				job_id: job.job_id,
				state: job.state,
				progress_percent: job.progress_percent,
				message: job.message,
				audio_quality: job.audio_quality,
				eta_seconds: null,
				error_code: null,
				error_message: null,
				title: job.title,
				thumbnail_url: job.thumbnail_url,
			});

			await pollJobUntilReady(job.job_id);
			setPanelState("ready");
		} catch (error) {
			setPanelState("verified");

			if (error instanceof ApiClientError) {
				throw error;
			}

			throw new ApiClientError("No se pudo completar la conversión del MP3.");
		}
	};

	const downloadReadyFile = async () => {
		if (!activeJobIdRef.current) {
			throw new ApiClientError("La conversión todavía no está lista para descargar.");
		}

		try {
			await downloadConversionJob(activeJobIdRef.current);
			activeJobIdRef.current = null;
			setPanelState("verified");
			setJobStatus(null);
		} catch (error) {
			if (error instanceof ApiClientError) {
				throw error;
			}

			throw new ApiClientError("No se pudo descargar el MP3 en este momento.");
		}
	};

	const resetVerification = () => {
		pollingRef.current = false;
		activeJobIdRef.current = null;
		setVerifiedVideo(null);
		setJobStatus(null);
		setPanelState("idle");
	};

	useEffect(() => {
		return () => {
			pollingRef.current = false;
		};
	}, []);

	return {
		sourceUrl,
		verifiedVideo,
		panelState,
		selectedBitrate,
		jobStatus,
		isBusy,
		setSourceUrl,
		verifySourceUrl,
		pickAndConvert,
		downloadReadyFile,
		resetVerification,
	};
}
