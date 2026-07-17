import {
  FileBarChart, Database, CalendarDays, ShieldCheck, ListChecks,
  FileSignature, Send, UserCheck, UserCog, Server, Gauge, Info, FileClock,
} from "lucide-react";
import { Shell } from "@/components/shell";
import { KpiCard } from "@/components/kpi-card";
import { FileSpreadsheet } from "lucide-react";
import { dateFr, compact, fcfa } from "@/lib/format";
import { getBceao } from "@/lib/api";
import { ExportLink } from "@/components/export-link";

const PER_BADGE: Record<string, string> = {
  Mensuelle: "badge-info", Trimestrielle: "badge-warning",
  Annuelle: "badge-neutral", Variable: "badge-neutral",
};
const STEP_ICON = [UserCheck, UserCog, FileSignature, Server];

export default async function Page() {
  const { data } = await getBceao();
  const { meta, balance, workflow, etats, indicateurs } = data;

  return (
    <Shell
      title="Reporting réglementaire BCEAO"
      subtitle={`${meta.titre} · période ${meta.periode}`}
      right={
        <div className="flex items-center gap-3">
          <ExportLink path="/api/export/bceao.xlsx" label="Excel" icon={<FileSpreadsheet className="w-4 h-4" />} />
          <span className="badge badge-success flex items-center gap-1.5">
            <Database className="w-3 h-3" /> {balance.core_banking}
          </span>
        </div>
      }
    >
      {/* ─── KPIs ─────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-px bg-neutral-200 mb-px">
        <KpiCard label="Total bilan" value={balance.total_bilan ? compact(balance.total_bilan) + " F" : "—"} sub={balance.total_bilan ? fcfa(balance.total_bilan) + " · indicatif" : "—"} icon={<Database className="w-4 h-4" />} />
        <KpiCard label="Résultat net" value={balance.resultat_net ? compact(balance.resultat_net) + " F" : "—"} sub="indicatif (balance)" tone="up" icon={<Gauge className="w-4 h-4" />} />
        <KpiCard label="États à produire" value={String(etats.length)} sub="catalogue SICSSFD" icon={<FileBarChart className="w-4 h-4" />} />
        <KpiCard label="Balance importée" value={balance.date_arrete ? dateFr(balance.date_arrete) : "à importer"} sub={balance.total_bilan ? "agrégats disponibles" : "aucune balance"} icon={<CalendarDays className="w-4 h-4" />} />
        <KpiCard label="Validation" value="3 + 1" sub="préparateur → système" icon={<ShieldCheck className="w-4 h-4" />} />
        <KpiCard label="Balance arrêtée" value={balance.date_arrete ? dateFr(balance.date_arrete) : "—"} sub={balance.core_banking} icon={<FileClock className="w-4 h-4" />} />
      </div>

      {/* ─── Bannière source de données (transparence) ────── */}
      <div className="bg-info-light px-4 py-3 mb-px flex items-start gap-3">
        <Info className="w-4 h-4 text-info-dark shrink-0 mt-0.5" />
        <div className="text-xs text-neutral-700">
          <span className="font-semibold text-info-dark">Source détectée : {balance.source} ({balance.format}).</span>{" "}
          {balance.note} Le circuit de validation et le catalogue ci-dessous sont, eux, déjà opérationnels.
        </div>
      </div>

      {/* ─── Circuit de validation 4 niveaux ──────────────── */}
      <div className="card-pad-lg mb-px">
        <div className="section-title"><ListChecks className="w-3.5 h-3.5" /> Circuit de validation des états BCEAO</div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-px bg-neutral-200">
          {workflow.map((w, i) => {
            const Icon = STEP_ICON[i] ?? UserCheck;
            return (
              <div key={w.niveau} className="bg-white p-4 flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 bg-primary-600 text-white flex items-center justify-center text-xs font-bold shrink-0">
                    {w.niveau}
                  </div>
                  <Icon className="w-4 h-4 text-primary-600" />
                  {w.sla !== "—" && <span className="ml-auto badge badge-neutral">SLA {w.sla}</span>}
                </div>
                <div className="text-sm font-semibold text-neutral-800">{w.role}</div>
                <div className="text-xs text-neutral-500 leading-snug">{w.desc}</div>
              </div>
            );
          })}
        </div>
        <div className="mt-3 flex items-center gap-2 text-xs text-neutral-500">
          <FileSignature className="w-3.5 h-3.5" /> Signature électronique XAdES en niveau 3
          <span className="mx-1">·</span>
          <Send className="w-3.5 h-3.5" /> Envoi + archivage WORM 7 ans en niveau 4
        </div>
      </div>

      {/* ─── Catalogue des états ──────────────────────────── */}
      <div className="card mb-px">
        <div className="section-title"><FileBarChart className="w-3.5 h-3.5" /> Catalogue des états réglementaires (SICSSFD)</div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr><th>N°</th><th>État</th><th>Périodicité</th><th>Statut</th></tr>
            </thead>
            <tbody>
              {etats.map((e) => (
                <tr key={e.code}>
                  <td className="font-medium">{e.code}</td>
                  <td>{e.libelle}</td>
                  <td><span className={`badge ${PER_BADGE[e.periodicite] || "badge-neutral"}`}>{e.periodicite}</span></td>
                  <td><span className="badge badge-neutral">À générer</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-3 text-xs text-neutral-500">
          Source : {meta.source_catalogue} — catalogue officiel des feuilles de reporting BCEAO/SFD.
        </div>
      </div>

      {/* ─── Indicateurs prudentiels & portefeuille ───────── */}
      <div className="card">
        <div className="section-title"><Gauge className="w-3.5 h-3.5" /> Indicateurs prudentiels & de portefeuille</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-neutral-200">
          {indicateurs.map((g) => (
            <div key={g.groupe} className="bg-white p-4">
              <div className="text-xs uppercase tracking-wider text-primary-700 font-semibold mb-2">{g.groupe}</div>
              <ul className="space-y-2">
                {g.items.map((it) => (
                  <li key={it.libelle} className="text-sm text-neutral-700 flex items-center justify-between gap-2">
                    <span className="flex items-start gap-2 min-w-0">
                      <span className="w-1.5 h-1.5 bg-primary-600 mt-1.5 shrink-0" />
                      <span>{it.libelle}</span>
                    </span>
                    <span className="badge badge-neutral shrink-0">{it.norme}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </Shell>
  );
}
