import { ReactNode } from "react";

/** Carte KPI : fond blanc, carrée, sans bordure. Accent marine à gauche. */
export function KpiCard({ label, value, sub, tone = "default", icon }: {
  label: string;
  value: string;
  sub?: ReactNode;
  tone?: "default" | "up" | "down";
  icon?: ReactNode;
}) {
  const toneCls =
    tone === "up" ? "text-success" : tone === "down" ? "text-danger" : "text-foreground";
  return (
    <div className="bg-white p-4 flex items-stretch gap-3">
      <div className="w-1 bg-primary-600 shrink-0" aria-hidden />
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between">
          <div className="text-[11px] uppercase tracking-wider text-neutral-500 font-semibold">
            {label}
          </div>
          {icon && <span className="text-neutral-400">{icon}</span>}
        </div>
        <div className={`mt-1.5 text-2xl font-bold tabular-nums leading-tight ${toneCls}`}>
          {value}
        </div>
        {sub && <div className="mt-1 text-xs text-neutral-500">{sub}</div>}
      </div>
    </div>
  );
}
