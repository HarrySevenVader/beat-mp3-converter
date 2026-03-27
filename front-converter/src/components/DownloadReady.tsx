import Image from "next/image";
import { ConversionJobStatus, VerifiedVideo } from "@/types";

type DownloadReadyProps = {
  video: VerifiedVideo;
  selectedBitrate: number;
  isBusy: boolean;
  panelState: "verified" | "converting" | "ready";
  status: ConversionJobStatus | null;
  onPickAndConvert: (bitrate: number) => Promise<void>;
  onDownload: () => Promise<void>;
  onEditUrl: () => void;
};

function formatDuration(value: number | null): string {
  if (typeof value !== "number" || value <= 0) {
    return "Duracion no disponible";
  }

  const minutes = Math.floor(value / 60);
  const seconds = value % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function statusLabel(status: ConversionJobStatus | null): string {
  if (!status) {
    return "Video verificado en el servidor";
  }

  if (status.eta_seconds && status.eta_seconds > 0) {
    return `${status.message} (${status.eta_seconds}s)`;
  }

  return status.message;
}

export default function DownloadReady({
  video,
  selectedBitrate,
  isBusy,
  panelState,
  status,
  onPickAndConvert,
  onDownload,
  onEditUrl,
}: DownloadReadyProps) {
  const isConverting = panelState === "converting";
  const isReady = panelState === "ready";

  return (
    <section className="download-ready-panel" aria-label="Conversión lista para descarga">
      <p className="download-ready-label">HOST VERIFICADO EN EL SERVIDOR</p>

      <div className="verified-video-card">
        {video.thumbnail_url ? (
          <Image
            src={video.thumbnail_url}
            alt={`Miniatura de ${video.title}`}
            className="verified-video-thumbnail"
            width={640}
            height={360}
          />
        ) : (
          <div className="verified-video-thumbnail verified-video-thumbnail-fallback" aria-hidden="true">
            AUDIO
          </div>
        )}

        <div className="verified-video-info">
          <h3>{video.title}</h3>
          <p>{formatDuration(video.duration_seconds)}</p>
          <span>{video.source_url}</span>
        </div>
      </div>

      <div className="audio-options-table" role="table" aria-label="Opciones de audio mp3">
        <div className="audio-options-header" role="row">
          <span role="columnheader">Tipo</span>
          <span role="columnheader">Formato</span>
          <span role="columnheader">Accion</span>
        </div>

        {video.audio_options.map((option) => {
          const isCurrentBitrate = selectedBitrate === option.bitrate;
          const canDownload = isReady && status?.audio_quality === option.bitrate;

          return (
            <div className="audio-option-row" role="row" key={option.bitrate}>
              <span role="cell">{option.label}</span>
              <span role="cell">MP3</span>
              <span role="cell">
                {canDownload ? (
                  <button type="button" className="option-button option-download" onClick={onDownload} disabled={isBusy}>
                    Descargar
                  </button>
                ) : (
                  <button
                    type="button"
                    className={`option-button ${isCurrentBitrate ? "option-selected" : ""}`}
                    onClick={() => onPickAndConvert(option.bitrate)}
                    disabled={isBusy}
                  >
                    {isConverting && isCurrentBitrate ? "Convirtiendo..." : "Convertir"}
                  </button>
                )}
              </span>
            </div>
          );
        })}
      </div>

      <div className="conversion-status" aria-live="polite">
        {isConverting ? (
          <>
            <span className="panel-spinner" aria-hidden="true" />
            <div>
              <p>{statusLabel(status)}</p>
              <strong>{status?.progress_percent ?? 0}%</strong>
            </div>
          </>
        ) : (
          <p>{statusLabel(status)}</p>
        )}
      </div>

      <div className="download-ready-actions">
        <button type="button" className="edit-url-button" onClick={onEditUrl} disabled={isBusy}>
          Editar URL
        </button>
      </div>
    </section>
  );
}
