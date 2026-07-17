import {
  SlidersHorizontal, Landmark, Users, ShieldCheck, Wallet, Vault, Building2,
} from "lucide-react";
import { Shell } from "@/components/shell";
import { getParametres } from "@/lib/api";
import { ROLE_LABEL } from "@/lib/auth";

const TYPE_ICON: Record<string, typeof Landmark> = { BANQUE: Landmark, CAISSE: Wallet, COFFRE: Vault };
const ROLE_BADGE: Record<string, string> = {
  DG: "badge-info", DAGF: "badge-info", TRESORIER: "badge-neutral", CONTROLE_INTERNE: "badge-warning",
};

function fmtVal(valeur: string, unite: string | null) {
  const n = Number(valeur);
  if (unite === "FCFA" && !Number.isNaN(n)) return n.toLocaleString("fr-FR") + " FCFA";
  return `${valeur}${unite ? " " + unite : ""}`;
}

export default async function Page() {
  const { data } = await getParametres();
  const { seuils, comptes, utilisateurs } = data;

  return (
    <Shell title="Paramètres" subtitle="Administration — référentiels, seuils & habilitations">
      {/* ─── Seuils & règles d'alerte ─────────────────────── */}
      <div className="card mb-px">
        <div className="section-title"><SlidersHorizontal className="w-3.5 h-3.5" /> Seuils & règles d'alerte</div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead><tr><th>Paramètre</th><th>Catégorie</th><th className="num">Valeur</th></tr></thead>
            <tbody>
              {seuils.map((s) => (
                <tr key={s.cle}>
                  <td className="font-medium">{s.libelle}</td>
                  <td><span className="badge badge-neutral">{s.categorie}</span></td>
                  <td className="num font-semibold tabular-nums">{fmtVal(s.valeur, s.unite)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-3 text-xs text-neutral-500">
          Ces seuils pilotent les alertes (trésorerie, suspens) et la rétention réglementaire. Modification réservée à l'administrateur (validation à 4 yeux en production).
        </div>
      </div>

      {/* ─── Référentiel des comptes ──────────────────────── */}
      <div className="card mb-px">
        <div className="section-title"><Landmark className="w-3.5 h-3.5" /> Référentiel des comptes de trésorerie</div>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-px bg-neutral-200">
          {comptes.map((c) => {
            const Icon = TYPE_ICON[c.type] || Building2;
            return (
              <div key={c.code} className="bg-white p-3 flex items-center gap-3">
                <div className="w-8 h-8 bg-primary-600 flex items-center justify-center shrink-0">
                  <Icon className="w-4 h-4 text-white" />
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-medium text-neutral-800 truncate">{c.libelle}</div>
                  <div className="text-[11px] text-neutral-500">{c.type} · {c.actif ? "actif" : "inactif"}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ─── Utilisateurs & habilitations ─────────────────── */}
      <div className="card">
        <div className="section-title"><Users className="w-3.5 h-3.5" /> Utilisateurs & habilitations (RBAC)</div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead><tr><th>Nom</th><th>E-mail</th><th>Rôle</th></tr></thead>
            <tbody>
              {utilisateurs.map((u) => (
                <tr key={u.email}>
                  <td className="font-medium">{u.nom}</td>
                  <td className="tabular-nums text-neutral-600">{u.email}</td>
                  <td><span className={`badge ${ROLE_BADGE[u.role] || "badge-neutral"}`}>{ROLE_LABEL[u.role] || u.role}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-3 flex items-center gap-2 text-xs text-neutral-500">
          <ShieldCheck className="w-3.5 h-3.5" /> Pilote : 4 rôles. En production : 15+ rôles, SSO + MFA (Keycloak), séparation des pouvoirs.
        </div>
      </div>
    </Shell>
  );
}
