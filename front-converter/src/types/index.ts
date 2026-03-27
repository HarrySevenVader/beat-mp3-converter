export type AudioOption = {
	label: string;
	bitrate: number;
};

export type VerifiedVideo = {
	source_url: string;
	video_id: string;
	title: string;
	duration_seconds: number | null;
	thumbnail_url: string | null;
	audio_options: AudioOption[];
};

export type ConversionJobCreation = {
	job_id: string;
	state: string;
	progress_percent: number;
	message: string;
	audio_quality: number;
	title: string | null;
	thumbnail_url: string | null;
};

export type ConversionJobStatus = {
	job_id: string;
	state: string;
	progress_percent: number;
	message: string;
	audio_quality: number;
	eta_seconds: number | null;
	error_code: string | null;
	error_message: string | null;
	title: string | null;
	thumbnail_url: string | null;
};
