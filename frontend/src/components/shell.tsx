"use client";

import { ReactNode, useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard, Wallet, FileBarChart, ArrowLeftRight,
  ShieldAlert, Settings, LogOut, UploadCloud, Lock,
} from "lucide-react";
import { getSession, clearSession, canSee, ROLE_LABEL, API, type Session } from "@/lib/auth";

type Status = { tresorerie: boolean; reversements: boolean; balance: boolean };

// need = clé d'import requise pour activer l'onglet (null = toujours actif)
const NAV = [
  { label: "Trésorerie", icon: LayoutDashboard, href: "/", need: "tresorerie" as const },
  { label: "Soldes & Comptes", icon: Wallet, href: "/comptes", need: "tresorerie" as const },
  { label: "Rapprochements", icon: ArrowLeftRight, href: "/reversements", need: "reversements" as const },
  { label: "Reporting BCEAO", icon: FileBarChart, href: "/reporting-bceao", need: "balance" as const },
  { label: "Anomalies", icon: ShieldAlert, href: "/controle", need: "tresorerie" as const },
  { label: "Paramètres", icon: Settings, href: "/parametres", need: null },
];

function initials(nom: string) {
  return nom.split(" ").map((w) => w[0]).filter(Boolean).slice(0, 2).join("").toUpperCase();
}

export function Shell({ children, title, subtitle, right }: {
  children: ReactNode; title: string; subtitle?: string; right?: ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [session, setSession] = useState<Session | null | undefined>(undefined);
  const [status, setStatus] = useState<Status>({ tresorerie: false, reversements: false, balance: false });

  const loadStatus = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/status`, { cache: "no-store" });
      if (r.ok) setStatus(await r.json());
    } catch { /* API indisponible : tout reste inactif */ }
  }, []);

  useEffect(() => {
    const s = getSession();
    if (!s) { router.replace("/login"); setSession(null); return; }
    // Garde RBAC : rôle non habilité sur une route → retour à l'import.
    if (pathname && pathname !== "/" && pathname !== "/import" && !canSee(s.role, pathname)) {
      router.replace("/import");
    }
    setSession(s);
    loadStatus();
    const onImport = () => loadStatus();
    window.addEventListener("ma2e:imported", onImport);
    return () => window.removeEventListener("ma2e:imported", onImport);
  }, [router, loadStatus, pathname]);

  if (session === undefined || session === null) return null;

  const isActive = (href: string) => (href === "/" ? pathname === "/" : pathname.startsWith(href));
  const enabled = (need: string | null) => need === null || status[need as keyof Status];

  function logout() { clearSession(); router.replace("/login"); }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* ─── Navbar ───────────────────────────────────────── */}
      <nav className="bg-primary-800 text-white flex items-center h-14 px-4 gap-1 shrink-0 sticky top-0 z-20">
        <Link href="/import" className="flex items-center gap-2 pr-4 shrink-0">
          <div className="w-8 h-8 bg-white flex items-center justify-center">
            <span className="text-primary-800 font-extrabold text-base">M</span>
          </div>
          <span className="font-bold tracking-tight hidden sm:block">MA2E <span className="font-normal text-primary-200">Trésorerie</span></span>
        </Link>

        <div className="flex items-center gap-0.5 overflow-x-auto flex-1">
          {NAV.filter((n) => canSee(session.role, n.href)).map(({ label, icon: Icon, href, need }) => {
            const on = enabled(need);
            const active = isActive(href);
            const cls = `flex items-center gap-2 px-3 h-9 text-sm whitespace-nowrap transition-colors ${
              active ? "bg-primary-600 text-white font-medium"
              : on ? "text-primary-100 hover:bg-primary-700"
              : "text-primary-400 cursor-not-allowed"}`;
            return on ? (
              <Link key={href} href={href} className={cls}>
                <Icon className="w-4 h-4 shrink-0" /> {label}
              </Link>
            ) : (
              <span key={href} className={cls} title="Importez le document requis pour activer cet écran">
                <Lock className="w-3.5 h-3.5 shrink-0" /> {label}
              </span>
            );
          })}
        </div>

        {/* droite : import + user */}
        <div className="flex items-center gap-2 shrink-0 pl-2">
          {canSee(session.role, "/import") && (
            <Link href="/import"
              className={`h-9 px-3 text-sm font-medium flex items-center gap-2 transition-colors ${
                isActive("/import") ? "bg-white text-primary-800" : "bg-primary-600 hover:bg-primary-500 text-white"}`}>
              <UploadCloud className="w-4 h-4" /> <span className="hidden sm:inline">Importer</span>
            </Link>
          )}
          <div className="w-8 h-8 bg-primary-600 flex items-center justify-center text-xs font-bold shrink-0" title={`${session.nom} · ${ROLE_LABEL[session.role] || session.role}`}>
            {initials(session.nom)}
          </div>
          <button onClick={logout} title="Déconnexion" className="text-primary-200 hover:text-white p-1">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </nav>

      {/* ─── En-tête de page ──────────────────────────────── */}
      <header className="bg-white h-14 px-6 flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-lg font-bold leading-tight">{title}</h1>
          {subtitle && <div className="text-xs text-neutral-500">{subtitle}</div>}
        </div>
        {right}
      </header>

      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
