import {
  TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight,
  Wallet, Activity, AlertTriangle, CalendarDays, RefreshCw,
  FileText, FileSpreadsheet,
} from "lucide-react";
import { Shell } from "@/components/shell";
import { KpiCard } from "@/components/kpi-card";
import { AreaChart } from "@/components/area-chart";
import { BarBreakdown } from "@/components/bar-breakdown";
import { ExportLink } from "@/components/export-link";
import { fcfa, compact, dateFr, dateCourt } from "@/lib/format";
import { getTresorerie } from "@/lib/api";
import { EmptyState } from "@/components/empty-state";

export default async function Page() {
  const { data, live } = await getTresorerie();
  if ((data as { empty?: boolean }).empty) {
    return (
      <Shell title="Point de Trésorerie" subtitle="Mutuelle des Agents de l'Eau et de l'Électricité">
        <EmptyState titre="Aucune donnée de trésorerie" detail="Importez le fichier « POINT RETRAIT » pour afficher la position de trésorerie, son évolution et les anomalies détectées." />
      </Shell>
    );
  }
  const { meta, kpi, serie, repartition, recent, colonnes, anomalies } = data;
  const up = kpi.variation >= 0;

  return (
    <Shell
      title="Point de Trésorerie"
      subtitle={`${meta.institution}`}
      right={
        <div className="flex items-center gap-3">
          <ExportLink path="/api/export/tresorerie.pdf" label="PDF" icon={<FileText className="w-4 h-4" />} />
          <ExportLink path="/api/export/tresorerie.xlsx" label="Excel" icon={<FileSpreadsheet className="w-4 h-4" />} />
          <span className={`badge flex items-center gap-1.5 ${live ? "badge-success" : "badge-warning"}`}>
            <RefreshCw className="w-3 h-3" /> {live ? "API en direct" : "Mode dégradé"}
          </span>
          <div className="text-right">
            <div className="text-[11px] uppercase tracking-wider text-neutral-500 font-semibold">Position au</div>
            <div className="text-sm font-bold tabular-nums">{dateFr(meta.date_position)}</div>
          </div>
        </div>
      }
    >
      {/* ─── KPIs ─────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-px bg-neutral-200 mb-px">
        <KpiCard
          label="Position consolidée"
          value={compact(kpi.position) + " F"}
          sub={fcfa(kpi.position)}
          icon={<Wallet className="w-4 h-4" />}
        />
        <KpiCard
          label="Variation / veille"
          tone={up ? "up" : "down"}
          value={(up ? "+" : "") + compact(kpi.variation) + " F"}
          sub={
            <span className="flex items-center gap-1">
              {up ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
              {kpi.variation_pct.toFixed(2)} %
            </span>
          }
          icon={up ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
        />
        <KpiCard label="Pic maximum" value={compact(kpi.max) + " F"} sub="sur la période" icon={<TrendingUp className="w-4 h-4" />} />
        <KpiCard label="Plancher minimum" value={compact(kpi.min) + " F"} sub="vigilance liquidité" tone="down" icon={<TrendingDown className="w-4 h-4" />} />
        <KpiCard label="Moyenne période" value={compact(kpi.moyenne) + " F"} sub={`${meta.nb_jours} jours`} icon={<Activity className="w-4 h-4" />} />
        <KpiCard label="Anomalies détectées" value={String(kpi.nb_anomalies)} sub="saisies à vérifier" tone={kpi.nb_anomalies ? "down" : "default"} icon={<AlertTriangle className="w-4 h-4" />} />
      </div>

      {/* ─── Graphiques ───────────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-px bg-neutral-200 mb-px">
        <div className="xl:col-span-2 card-pad-lg">
          <div className="section-title"><Activity className="w-3.5 h-3.5" /> Évolution de la trésorerie consolidée</div>
          <AreaChart points={serie} />
          <div className="mt-2 text-xs text-neutral-500 flex items-center gap-1.5">
            <CalendarDays className="w-3 h-3" /> {dateFr(meta.periode_debut)} → {dateFr(meta.periode_fin)} · {meta.nb_jours} jours
          </div>
        </div>
        <div className="card-pad-lg">
          <div className="section-title"><Wallet className="w-3.5 h-3.5" /> Répartition par compte · {dateCourt(meta.date_position)}</div>
          <BarBreakdown items={repartition} />
        </div>
      </div>

      {/* ─── Tableau des positions ────────────────────────── */}
      <div className="card mb-px">
        <div className="section-title"><CalendarDays className="w-3.5 h-3.5" /> Détail des 20 derniers jours</div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                {colonnes.map((c) => <th key={c.code} className="num">{c.libelle}</th>)}
                <th className="num">Total</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((r) => (
                <tr key={r.date}>
                  <td className="font-medium whitespace-nowrap">{dateFr(r.date)}</td>
                  {colonnes.map((c) => (
                    <td key={c.code} className="num text-neutral-600">
                      {(r.comptes as Record<string, number>)[c.code]
                        ? compact((r.comptes as Record<string, number>)[c.code])
                        : "—"}
                    </td>
                  ))}
                  <td className="num font-bold text-primary-700">{compact(r.total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ─── Anomalies ────────────────────────────────────── */}
      <div className="card">
        <div className="section-title"><AlertTriangle className="w-3.5 h-3.5" /> Anomalies de saisie détectées automatiquement</div>
        {anomalies.length === 0 ? (
          <div className="text-sm text-neutral-500">Aucune anomalie.</div>
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
          Détectées sans intervention humaine lors de l'ingestion — gain direct pour le Contrôle Interne.
        </div>
      </div>
    </Shell>
  );
}
