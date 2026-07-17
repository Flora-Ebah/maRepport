// Couche d'accès aux données.
// Consomme l'API FastAPI. IMPORTANT : aucune donnée métier « en dur » affichée
// par défaut — si l'API est indisponible, les écrans de données renvoient
// l'état VIDE (jamais des chiffres embarqués). Les fichiers JSON ne servent
// plus que de GABARIT DE TYPE, jamais de source affichée pour ces écrans.
// Seuls les référentiels (catalogue BCEAO, utilisateurs/paramètres) gardent un
// repli, car ce sont de la configuration, pas des données fictives.

import tresoShape from "@/data/tresorerie.json";
import revShape from "@/data/reversements.json";
import comptesShape from "@/data/comptes.json";
import controleShape from "@/data/controle.json";
import bceaoFallback from "@/data/bceao.json";
import parametresFallback from "@/data/parametres.json";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function get<T>(path: string, shape: T, emptyOnFail = true): Promise<{ data: T; live: boolean }> {
  try {
    const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
    if (!res.ok) throw new Error(String(res.status));
    return { data: (await res.json()) as T, live: true };
  } catch {
    // Données métier → état VIDE. Référentiels → repli config.
    return { data: (emptyOnFail ? ({ empty: true } as unknown as T) : shape), live: false };
  }
}

// Données métier → VIDE par défaut (le JSON ne sert qu'au typage).
export const getTresorerie = () => get("/api/tresorerie", tresoShape);
export const getReversements = () => get("/api/reversements", revShape);
export const getComptes = () => get("/api/comptes", comptesShape);
export const getControle = () => get("/api/controle", controleShape);

// Référentiels (configuration) → repli conservé.
export const getBceao = () => get("/api/bceao", bceaoFallback, false);
export const getParametres = () => get("/api/parametres", parametresFallback, false);
