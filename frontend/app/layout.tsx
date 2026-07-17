import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "MA2E Trésorerie", template: "%s · MA2E Trésorerie" },
  description:
    "Pilote de digitalisation du Point de Trésorerie MA2E — reporting automatisé, conforme BCEAO.",
  applicationName: "MA2E Trésorerie",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#1F4E79",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="min-h-screen bg-background text-foreground">{children}</body>
    </html>
  );
}
