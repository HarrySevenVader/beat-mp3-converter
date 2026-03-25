type RailIconType = "headphones" | "music" | "mic" | "signature" | "speaker";

function RailIcon({ type }: { type: RailIconType }) {
  if (type === "headphones") {
    return (
      <span className="rail-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" className="rail-svg" role="presentation">
          <path d="M6.5 10.5a5.5 5.5 0 0 1 11 0" />
          <rect x="5" y="10.5" width="3.2" height="6.2" rx="1.2" />
          <rect x="15.8" y="10.5" width="3.2" height="6.2" rx="1.2" />
        </svg>
      </span>
    );
  }

  if (type === "music") {
    return (
      <span className="rail-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" className="rail-svg" role="presentation">
          <path d="M14 5v9.4" />
          <path d="M14 5l4.3-1.3v8.8" />
          <circle cx="10" cy="15.8" r="2.2" />
          <circle cx="17.4" cy="13.9" r="1.8" />
        </svg>
      </span>
    );
  }

  if (type === "mic") {
    return (
      <span className="rail-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" className="rail-svg" role="presentation">
          <rect x="9" y="4" width="6" height="9" rx="3" />
          <path d="M7.2 10.5a4.8 4.8 0 0 0 9.6 0" />
          <path d="M12 15.3v3.2" />
          <path d="M9.3 19h5.4" />
        </svg>
      </span>
    );
  }

  if (type === "signature") {
    return (
      <span className="rail-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" className="rail-svg rail-svg-signature" role="presentation">
          <rect x="3" y="12" width="2.2" height="6" rx="0.6" />
          <rect x="6.5" y="9.5" width="2.2" height="8.5" rx="0.6" />
          <rect x="10" y="7" width="2.2" height="11" rx="0.6" />
          <path d="M15.2 9.3h4.8c1 0 1.4 1.2.5 1.7l-3.1 1.7c-.8.5-.5 1.7.5 1.7h2.9" />
        </svg>
      </span>
    );
  }

  return (
    <span className="rail-icon" aria-hidden="true">
      <svg viewBox="0 0 24 24" className="rail-svg" role="presentation">
        <path d="M4.4 10.3h3.3l3.9-3v10l-3.9-3H4.4z" />
        <path d="M14.6 9.2a3.6 3.6 0 0 1 0 6.1" />
        <path d="M16.9 7.4a6.2 6.2 0 0 1 0 9.7" />
      </svg>
    </span>
  );
}

export default function Convertidor() {
  return (
    <section id="convertidor" className="converter-screen">
      <aside className="side-rail side-rail-left" aria-hidden="true">
        <RailIcon type="headphones" />
        <RailIcon type="music" />
        <RailIcon type="mic" />
        <RailIcon type="signature" />
        <RailIcon type="speaker" />
      </aside>

      <div className="converter-content">
        <div className="protocol-tag">
          <span className="protocol-dot" />
          SISTEMA EN LÍNEA: PROTOCOLO 808
        </div>

        <h1 className="converter-title">
          EXTRAE TU <span>MÚSICA</span>
        </h1>

        <p className="converter-subtitle">
          Extracción de audio de alta fidelidad desde la red digital. Convierte
          frecuencias de YouTube a flujos puros de MP3 con precisión cinética.
        </p>

        <div className="converter-panel">
          <label htmlFor="url" className="input-label">
            PAYLOAD DE ORIGEN DE LA URL
          </label>

          <input
            id="url"
            type="text"
            className="url-field"
            placeholder="URL DEL PAYLOAD DE ORIGEN..."
            readOnly
            aria-label="URL de origen"
          />

          <button type="button" className="start-button">
            INICIAR CONVERSIÓN
          </button>

          <div className="panel-footer">
            <span>◉ 320 KBPS &nbsp;&nbsp; 🔒 ENCRIPTADO</span>
            <span>
              LISTO <em>■</em>
            </span>
          </div>
        </div>
      </div>

      <aside className="side-rail side-rail-right" aria-hidden="true">
        <RailIcon type="speaker" />
        <RailIcon type="signature" />
        <RailIcon type="mic" />
        <RailIcon type="music" />
        <RailIcon type="headphones" />
      </aside>
    </section>
  );
}