type DownloadReadyProps = {
  sourceUrl: string;
  isLoading: boolean;
  onDownload: () => Promise<void>;
  onEditUrl: () => void;
};

export default function DownloadReady({
  sourceUrl,
  isLoading,
  onDownload,
  onEditUrl,
}: DownloadReadyProps) {
  return (
    <section className="download-ready-panel" aria-label="Conversión lista para descarga">
      <p className="download-ready-label">URL VERIFICADA</p>
      <p className="download-ready-url">{sourceUrl}</p>

      <div className="download-ready-actions">
        <button
          type="button"
          className="start-button"
          onClick={onDownload}
          disabled={isLoading}
        >
          {isLoading ? "PROCESANDO..." : "DESCARGAR MP3"}
        </button>

        <button type="button" className="edit-url-button" onClick={onEditUrl} disabled={isLoading}>
          EDITAR URL
        </button>
      </div>
    </section>
  );
}
