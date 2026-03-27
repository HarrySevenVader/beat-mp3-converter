import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "../styles/Header.css"; // 👈 IMPORTANTE
import "../styles/Convertidor.css";
import "../styles/Steps.css";
import "../styles/Footer.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Beat | Convierte videos de YouTube a MP3 en segundos",
  description:
    "Pega tu enlace de YouTube, elige la calidad y descarga tu musica en MP3 de forma rapida, simple y sin complicaciones.",
  icons: {
    icon: "/icon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}