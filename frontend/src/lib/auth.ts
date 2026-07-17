// Authentification & RBAC (pilote).
// Session stockée en cookie côté client. En production : Keycloak SSO + MFA,
// cookie httpOnly et vérification du jeton côté API.

export type Session = { email: string; nom: string; role: string };

const COOKIE = "ma2e_session";
export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const ROLE_LABEL: Record<string, string> = {
  DG: "Directeur Général", DAGF: "DAGF",
  TRESORIER: "Trésorier", CONTROLE_INTERNE: "Contrôle Interne",
};

// Séparation des accès par rôle (principe RBAC du CDC).
export const ROLE_MODULES: Record<string, string[] | "*"> = {
  DG: "*",
  DAGF: "*",
  TRESORIER: ["/", "/comptes", "/reversements", "/import"],
  CONTROLE_INTERNE: ["/reporting-bceao", "/controle", "/reversements", "/import"],
};

export function canSee(role: string, href: string): boolean {
  const m = ROLE_MODULES[role];
  if (!m) return false;
  return m === "*" || m.includes(href);
}

export function getSession(): Session | null {
  if (typeof document === "undefined") return null;
  const raw = document.cookie.split("; ").find((c) => c.startsWith(COOKIE + "="));
  if (!raw) return null;
  try {
    return JSON.parse(decodeURIComponent(raw.split("=").slice(1).join("=")));
  } catch {
    return null;
  }
}

export function setSession(s: Session) {
  document.cookie = `${COOKIE}=${encodeURIComponent(JSON.stringify(s))}; path=/; max-age=28800; samesite=lax`;
}

export function clearSession() {
  document.cookie = `${COOKIE}=; path=/; max-age=0; samesite=lax`;
}

export async function login(email: string, password: string): Promise<Session> {
  const res = await fetch(`${API}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error("Identifiants invalides");
  return (await res.json()) as Session;
}
