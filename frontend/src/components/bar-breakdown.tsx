import { compact } from "@/lib/format";

type Item = { code: string; libelle: string; type: string; montant: number; part: number };

// Dégradé de marine selon le rang (pas de couleurs vives — sobriété bancaire).
const SHADES = ["#1F4E79", "#2E75B6", "#5B97CC", "#8AB6DC", "#173D60", "#102C47", "#B6D2EA", "#A1A1AA"];

/** Répartition par compte : barres horizontales rectangulaires. */
export function BarBreakdown({ items }: { items: Item[] }) {
  const max = Math.max(...items.map((i) => i.montant));
  return (
    <div className="space-y-3">
      {items.map((it, k) => (
        <div key={it.code}>
          <div className="flex items-baseline justify-between mb-1">
            <span className="text-sm font-medium text-neutral-700">{it.libelle}</span>
            <span className="text-sm tabular-nums text-neutral-800">
              {compact(it.montant)} <span className="text-neutral-400">· {it.part}%</span>
            </span>
          </div>
          {/* piste + barre, parfaitement rectangulaires */}
          <div className="h-3 w-full bg-neutral-100">
            <div
              className="h-3"
              style={{ width: `${(it.montant / max) * 100}%`, background: SHADES[k % SHADES.length] }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
