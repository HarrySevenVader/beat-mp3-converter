import React from 'react';
import '../styles/Header.css';

const Header: React.FC = () => {
  return (
    <header className="beat-header">
      <div className="header-container">
        <div className="brand-logo">
          BEAT
        </div>
        
        <nav className="nav-menu">
          <a href="#convertidor" className="nav-link">CONVERTIDOR</a>
          <a href="#caracteristicas" className="nav-link">CARACTERÍSTICAS</a>
          <a href="#api" className="nav-link">API</a>
          <a href="#soporte" className="nav-link">SOPORTE</a>
        </nav>

        <div className="header-status">
          <span className="status-dot"></span>
          SISTEMA EN LÍNEA: PROTOCOLO 808
        </div>
      </div>
    </header>
  );
};

export default Header;
