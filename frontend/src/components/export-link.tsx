import { ReactNode } from "react";
import { API } from "@/lib/auth";

/** Lien de téléchargement vers un export du backend (carré, sans bordure). */
export function ExportLink({ path, label, icon }: { path: string; label: string; icon: ReactNode }) {
  return (
    <a href={`${API}${path}`}
      className="h-9 px-3 bg-white text-primary-700 text-sm font-medium flex items-center gap-1.5 hover:bg-neutral-100 transition-colors">
      {icon} {label}
    </a>
  );
}
