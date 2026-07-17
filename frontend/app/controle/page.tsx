import {
  ShieldAlert, ShieldCheck, Database, CalendarDays, AlertTriangle,
  CheckCircle2, XCircle, ListChecks,
} from "lucide-react";
import { Shell } from "@/components/shell";
import { KpiCard } from "@/components/kpi-card";
import { getControle } from "@/lib/api";
import { dateFr } from "@/lib/format";
import { EmptyState } from "@/components/empty-state";

export default async function Page() {
  const { data } = await getControle();
  if ((data as { empty?: boolean }).empty) {
    return (
      <Shell title="Anomalies & Contrôle" subtitle="Qualité des données & points de contrôle automatiques">
        <EmptyState titre="Aucune donnée à contrôler" detail="Importez le fichier « POINT RETRAIT » pour lancer les contrôles qualité et la détection d'anomalies." />
      </Shell>
    );
  }
  const { kpi, controles, anomalies } = data;

  return (
    <Shell
      title="Anomalies & Contrôle"
      subtitle="Qualité des données & points de contrôle automatiques"
      right={
        <span className={`badge flex items-center gap-1.5 ${kpi.nb_anomalies ? "badge-warning" : "badge-success"}`}>
          <ShieldAlert className="w-3 h-3" /> {kpi.nb_anomalies} anomalie(s)
        </span>
      }
    >
      {/* ─── KPIs ─────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-neutral-200 mb-px">
        <KpiCard label="Soldes contrôlés" value={kpi.nb_soldes.toLocaleString("fr-FR")} sub={`${kpi.nb_jours} jours`} icon={<Database className="w-4 h-4" />} />
        <KpiCard label="Points de contrôle OK" value={`${kpi.nb_controles_ok} / ${kpi.nb_controles}`} sub="contrôles automatiques" tone={kpi.nb_controles_ok === kpi.nb_controles ? "up" : "down"} icon={<ShieldCheck className="w-4 h-4" />} />
        <KpiCard label="Anomalies détectées" value={String(kpi.nb_anomalies)} sub="à corriger à la source" tone={kpi.nb_anomalies ? "down" : "up"} icon={<AlertTriangle className="w-4 h-4" />} />
        <KpiCard label="Couverture" value="100 %" sub="ingestion automatisée" icon={<CalendarDays className="w-4 h-4" />} />
      </div>

      {/* ─── Points de contrôle ───────────────────────────── */}
      <div className="card mb-px">
        <div className="section-title"><ListChecks className="w-3.5 h-3.5" /> Points de contrôle automatiques</div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr><th>Code</th><th>Contrôle</th><th>Détail</th><th>Statut</th></tr>
            </thead>
            <tbody>
              {controles.map((c) => (
                <tr key={c.code}>
                  <td className="font-medium whitespace-nowrap">{c.code}</td>
                  <td>{c.libelle}</td>
                  <td className="text-neutral-500">{c.detail}</td>
                  <td>
                    {c.statut === "OK" ? (
                      <span className="badge badge-success flex items-center gap-1 w-fit"><CheckCircle2 className="w-3 h-3" /> OK</span>
                    ) : (
                      <span className="badge badge-warning flex items-center gap-1 w-fit"><XCircle className="w-3 h-3" /> Alerte</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ─── Anomalies ────────────────────────────────────── */}
      <div className="card">
        <div className="section-title"><AlertTriangle className="w-3.5 h-3.5" /> Anomalies de saisie détectées</div>
        {anomalies.length === 0 ? (
          <div className="text-sm text-neutral-500">Aucune anomalie détectée.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-px bg-neutral-200">
            {anomalies.map((a, i) => (
              <div key={i} className="bg-warning-light px-3 py-2.5 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-warning-dark shrink-0 mt-0.5" />
                <div className="text-xs">
                  <div className="font-semibold text-warning-dark">{a.type}</div>
                  <div className="text-neutral-600">Onglet « {a.onglet.trim()} » · date {dateFr(a.date)}</div>
                </div>
              </div>
            ))}
          </div>
        )}
        <div className="mt-3 text-xs text-neutral-500">
          Détectées automatiquement à l'ingestion — sans intervention humaine. Gain direct pour le Contrôle Interne.
        </div>
      </div>
    </Shell>
  );
}
