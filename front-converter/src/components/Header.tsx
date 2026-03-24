'use client';

import Link from 'next/link';

export default function Header() {
  return (
    <header className="beat-header">
      <div className="header-container">
        <div className="brand-logo">
          BEAT
        </div>
        
        <nav className="nav-menu">
          <Link href="#convertidor" className="nav-link">CONVERTIDOR</Link>
          <Link href="#caracteristicas" className="nav-link">CARACTERÍSTICAS</Link>
          <Link href="#api" className="nav-link">API</Link>
          <Link href="#soporte" className="nav-link">SOPORTE</Link>
        </nav>

        <div className="header-status">
          <span className="status-dot"></span>
          SISTEMA EN LÍNEA: PROTOCOLO 808
        </div>
      </div>
    </header>
  );
}