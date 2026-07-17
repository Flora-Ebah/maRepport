import { Wallet, Building2, Landmark, Vault, TrendingUp, TrendingDown, Activity } from "lucide-react";
import { Shell } from "@/components/shell";
import { Sparkline } from "@/components/sparkline";
import { getComptes } from "@/lib/api";
import { fcfa, compact, dateFr } from "@/lib/format";
import { EmptyState } from "@/components/empty-state";

const TYPE_ICON: Record<string, typeof Wallet> = { BANQUE: Landmark, CAISSE: Wallet, COFFRE: Vault };
const TYPE_BADGE: Record<string, string> = { BANQUE: "badge-info", CAISSE: "badge-neutral", COFFRE: "badge-warning" };

export default async function Page() {
  const { data } = await getComptes();
  if ((data as { empty?: boolean }).empty) {
    return (
      <Shell title="Soldes & Comptes" subtitle="Détail par banque, caisse et coffre">
        <EmptyState titre="Aucun compte à afficher" detail="Importez le fichier « POINT RETRAIT » pour voir le détail de chaque banque, caisse et coffre." />
      </Shell>
    );
  }
  const { meta, comptes } = data;

  return (
    <Shell
      title="Soldes & Comptes"
      subtitle="Détail par banque, caisse et coffre"
      right={
        <div className="text-right">
          <div className="text-[11px] uppercase tracking-wider text-neutral-500 font-semibold">Position totale</div>
          <div className="text-sm font-bold tabular-nums">{compact(meta.total)} F · {dateFr(meta.date_position)}</div>
        </div>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-px bg-neutral-200">
        {comptes.map((c) => {
          const Icon = TYPE_ICON[c.type] || Building2;
          return (
            <div key={c.code} className="bg-white p-5">
              {/* en-tête */}
              <div className="flex items-center gap-3 mb-3">
                <div className="w-9 h-9 bg-primary-600 flex items-center justify-center shrink-0">
                  <Icon className="w-4.5 h-4.5 text-white" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-semibold text-neutral-800 leading-tight">{c.libelle}</div>
                  <span className={`badge ${TYPE_BADGE[c.type] || "badge-neutral"} mt-0.5`}>{c.type}</span>
                </div>
                <div className="text-right">
                  <div className="text-[11px] uppercase tracking-wider text-neutral-500 font-semibold">Part</div>
                  <div className="text-sm font-bold text-primary-700 tabular-nums">{c.part} %</div>
                </div>
              </div>

              {/* solde actuel */}
              <div className="text-2xl font-bold tabular-nums text-neutral-900 leading-tight">{compact(c.solde_actuel)} F</div>
              <div className="text-xs text-neutral-500 mb-3">{fcfa(c.solde_actuel)}</div>

              {/* sparkline */}
              <Sparkline values={c.serie} height={44} />

              {/* stats */}
              <div className="grid grid-cols-3 gap-px bg-neutral-200 mt-3">
                <div className="bg-neutral-50 p-2">
                  <div className="text-[10px] uppercase tracking-wide text-neutral-500 flex items-center gap-1"><TrendingUp className="w-3 h-3" /> Max</div>
                  <div className="text-xs font-semibold tabular-nums mt-0.5">{compact(c.max)}</div>
                </div>
                <div className="bg-neutral-50 p-2">
                  <div className="text-[10px] uppercase tracking-wide text-neutral-500 flex items-center gap-1"><TrendingDown className="w-3 h-3" /> Min</div>
                  <div className="text-xs font-semibold tabular-nums mt-0.5">{compact(c.min)}</div>
                </div>
                <div className="bg-neutral-50 p-2">
                  <div className="text-[10px] uppercase tracking-wide text-neutral-500 flex items-center gap-1"><Activity className="w-3 h-3" /> Moy.</div>
                  <div className="text-xs font-semibold tabular-nums mt-0.5">{compact(c.moyenne)}</div>
                </div>
              </div>
              <div className="mt-2 text-[11px] text-neutral-400">{c.nb_jours} relevés · depuis {dateFr(c.premier_jour)}</div>
            </div>
          );
        })}
      </div>
    </Shell>
  );
}
