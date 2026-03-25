import Link from "next/link";

const FOOTER_LINKS = [
  { href: "#", label: "TÉRMINOS" },
  { href: "#", label: "PRIVACIDAD" },
  { href: "#", label: "CONTACTO" },
];

export default function Footer() {
  return (
    <footer id="soporte" className="beat-footer" aria-label="Información de pie de página">
      <div className="footer-container">
        <p className="footer-copy">
          © 2026 BEAT. TODOS LOS DERECHOS RESERVADOS.
        </p>

        <nav className="footer-nav" aria-label="Enlaces de pie de página">
          {FOOTER_LINKS.map((link) => (
            <Link key={link.label} href={link.href} className="footer-link">
              {link.label}
            </Link>
          ))}

          <span className="footer-status">
            ESTADO <em aria-hidden="true">■</em>
          </span>
        </nav>
      </div>
    </footer>
  );
}
