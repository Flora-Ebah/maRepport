import {
  ArrowDownToLine, ArrowUpFromLine, AlertTriangle, CalendarClock,
  Percent, ArrowLeftRight, CheckCircle2, Clock,
} from "lucide-react";
import { Shell } from "@/components/shell";
import { KpiCard } from "@/components/kpi-card";
import { fcfa, compact } from "@/lib/format";
import { getReversements } from "@/lib/api";
import { EmptyState } from "@/components/empty-state";
import { ExportLink } from "@/components/export-link";
import { FileSpreadsheet } from "lucide-react";

export default async function Page() {
  const { data } = await getReversements();
  if ((data as { empty?: boolean }).empty) {
    return (
      <Shell title="Rapprochements — Reversements SIVE" subtitle="Suivi des prélèvements & reversements">
        <EmptyState titre="Aucun reversement à afficher" detail="Importez le fichier « POINT SIVE » pour suivre les prélèvements, les reversements et les écarts en attente." />
      </Shell>
    );
  }
  const { meta, kpi, lignes } = data;
  const maxTotal = Math.max(...lignes.map((l) => l.total_fichier || 0));

  return (
    <Shell
      title="Rapprochements — Reversements SIVE"
      subtitle={`${meta.titre} · exercice ${meta.exercice}`}
      right={
        <div className="flex items-center gap-3">
          <ExportLink path="/api/export/reversements.xlsx" label="Excel" icon={<FileSpreadsheet className="w-4 h-4" />} />
          <span className="badge badge-warning flex items-center gap-1.5">
            <Clock className="w-3 h-3" /> {kpi.nb_mois_attente} mois en attente
          </span>
        </div>
      }
    >
      {/* ─── KPIs ─────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-neutral-200 mb-px">
        <KpiCard label="Total prélevé" value={compact(kpi.total_preleve) + " F"} sub={fcfa(kpi.total_preleve)} icon={<ArrowDownToLine className="w-4 h-4" />} />
        <KpiCard label="Total reversé" value={compact(kpi.total_reverse) + " F"} sub={fcfa(kpi.total_reverse)} tone="up" icon={<ArrowUpFromLine className="w-4 h-4" />} />
        <KpiCard label="Écart en attente" value={compact(kpi.ecart_total) + " F"} sub="à reverser / régulariser" tone="down" icon={<AlertTriangle className="w-4 h-4" />} />
        <KpiCard label="Taux de reversement" value={kpi.taux_reversement + " %"} sub={`${kpi.nb_mois_attente} mois non soldés`} tone={kpi.taux_reversement < 100 ? "down" : "up"} icon={<Percent className="w-4 h-4" />} />
      </div>

      {/* ─── Suivi mensuel (barres prélevé vs reversé) ────── */}
      <div className="card-pad-lg mb-px">
        <div className="section-title"><ArrowLeftRight className="w-3.5 h-3.5" /> Prélevé vs reversé par mois</div>
        <div className="space-y-3">
          {lignes.map((l) => (
            <div key={l.periode}>
              <div className="flex items-baseline justify-between mb-1">
                <span className="text-sm font-medium text-neutral-700">{l.periode}</span>
                <span className="text-sm tabular-nums text-neutral-800">
                  {compact(l.total_fichier || 0)}
                  {!l.regle && <span className="text-danger"> · écart {compact(l.ecart)}</span>}
                </span>
              </div>
              {/* piste = total prélevé ; remplissage = part reversée */}
              <div className="h-3 w-full bg-danger-light" style={{ width: `${((l.total_fichier || 0) / maxTotal) * 100}%` }}>
                <div className="h-3 bg-primary-600" style={{ width: `${l.total_fichier ? ((l.montant_vir || 0) / l.total_fichier) * 100 : 0}%` }} />
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex items-center gap-4 text-xs text-neutral-500">
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 bg-primary-600 inline-block" /> Reversé</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 bg-danger-light inline-block" /> Écart en attente</span>
        </div>
      </div>

      {/* ─── Détail mensuel ───────────────────────────────── */}
      <div className="card">
        <div className="section-title"><CalendarClock className="w-3.5 h-3.5" /> Détail mensuel des prélèvements</div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Période</th>
                <th className="num">Épargne</th>
                <th className="num">Prêt</th>
                <th className="num">Total fichier</th>
                <th className="num">Montant viré</th>
                <th className="num">Écart</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {lignes.map((l) => (
                <tr key={l.periode}>
                  <td className="font-medium whitespace-nowrap">{l.periode}</td>
                  <td className="num text-neutral-600">{l.epargne ? compact(l.epargne) : "—"}</td>
                  <td className="num text-neutral-600">{l.pret ? compact(l.pret) : "—"}</td>
                  <td className="num">{l.total_fichier ? compact(l.total_fichier) : "—"}</td>
                  <td className="num">{l.montant_vir ? compact(l.montant_vir) : "—"}</td>
                  <td className={`num font-semibold ${l.regle ? "text-neutral-400" : "text-danger"}`}>
                    {l.ecart ? compact(l.ecart) : "0"}
                  </td>
                  <td>
                    {l.regle ? (
                      <span className="badge badge-success flex items-center gap-1 w-fit"><CheckCircle2 className="w-3 h-3" /> Soldé</span>
                    ) : (
                      <span className="badge badge-warning flex items-center gap-1 w-fit"><Clock className="w-3 h-3" /> En attente</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-3 text-xs text-neutral-500">
          Rapprochement automatique « Total fichier » (prélevé) vs « Montant viré » (reversé) — les écarts
          sont remontés pour relance, conformément au suivi des suspens (M1).
        </div>
      </div>
    </Shell>
  );
}
