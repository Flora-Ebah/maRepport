"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LogIn, ShieldCheck, Loader2, AlertCircle } from "lucide-react";
import { login, setSession, ROLE_LABEL } from "@/lib/auth";

const DEMO = [
  { email: "dg@ma2e.ci", role: "DG" },
  { email: "dagf@ma2e.ci", role: "DAGF" },
  { email: "treso@ma2e.ci", role: "TRESORIER" },
  { email: "ci@ma2e.ci", role: "CONTROLE_INTERNE" },
];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      const s = await login(email, password);
      setSession(s);
      router.replace("/import");
    } catch {
      setErr("Identifiants invalides. Vérifiez l'e-mail et le mot de passe.");
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* ─── Panneau marque (gauche) ───────────────────── */}
      <div className="hidden lg:flex w-1/2 bg-primary-800 text-white flex-col justify-between p-12">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white flex items-center justify-center">
            <span className="text-primary-800 font-extrabold text-xl">M</span>
          </div>
          <div className="font-bold text-lg">MA2E <span className="font-normal text-primary-200">Trésorerie</span></div>
        </div>
        <div>
          <h1 className="text-4xl font-extrabold leading-tight">Pilotage financier digitalisé</h1>
          <p className="text-primary-200 mt-4 text-lg leading-relaxed">
            Point de trésorerie, rapprochements et reporting BCEAO — fiables, en temps réel,
            conformes aux exigences réglementaires.
          </p>
        </div>
        <div className="text-primary-300 text-sm">Mutuelle des Agents de l'Eau et de l'Électricité · UEMOA</div>
      </div>

      {/* ─── Formulaire (droite) ───────────────────────── */}
      <div className="flex-1 flex items-center justify-center bg-neutral-100 p-6">
        <div className="w-full max-w-sm">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-9 h-9 bg-primary-800 flex items-center justify-center">
              <span className="text-white font-extrabold">M</span>
            </div>
            <div className="font-bold">MA2E Trésorerie</div>
          </div>

          <h2 className="text-2xl font-bold text-neutral-900">Connexion</h2>
          <p className="text-sm text-neutral-500 mt-1 mb-6">Accédez à votre espace de pilotage.</p>

          {err && (
            <div className="bg-danger-light text-danger-dark text-sm px-3 py-2.5 mb-4 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" /> {err}
            </div>
          )}

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1.5">Adresse e-mail</label>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="prenom@ma2e.ci"
                className="block w-full h-11 px-3 bg-white text-sm outline-none focus:ring-2 focus:ring-primary-600 placeholder:text-neutral-400" />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1.5">Mot de passe</label>
              <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="block w-full h-11 px-3 bg-white text-sm outline-none focus:ring-2 focus:ring-primary-600 placeholder:text-neutral-400" />
            </div>
            <button type="submit" disabled={busy}
              className="w-full h-11 bg-primary-600 text-white font-medium flex items-center justify-center gap-2 hover:bg-primary-700 disabled:opacity-60 transition-colors">
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogIn className="w-4 h-4" />}
              {busy ? "Connexion…" : "Se connecter"}
            </button>
          </form>

          {/* Comptes de démonstration */}
          <div className="mt-8 bg-white p-4">
            <div className="text-[11px] uppercase tracking-wider text-neutral-500 font-semibold mb-2">Comptes de démonstration · mot de passe : demo</div>
            <div className="grid grid-cols-1 gap-px bg-neutral-200">
              {DEMO.map((d) => (
                <button key={d.email} onClick={() => { setEmail(d.email); setPassword("demo"); }}
                  className="bg-neutral-50 hover:bg-primary-50 px-3 py-2 text-left text-sm flex items-center justify-between transition-colors">
                  <span className="tabular-nums text-neutral-700">{d.email}</span>
                  <span className="badge badge-neutral">{ROLE_LABEL[d.role]}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="mt-6 flex items-center gap-2 text-xs text-neutral-400">
            <ShieldCheck className="w-3.5 h-3.5" /> Pilote — en production : SSO + MFA (Keycloak), conforme BCEAO.
          </div>
        </div>
      </div>
    </div>
  );
}
