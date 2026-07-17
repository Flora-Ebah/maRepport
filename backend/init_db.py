"""
MA2E — Initialisation de la base pour le DÉPLOIEMENT.
Crée le schéma + les référentiels (utilisateurs de démo, catalogue BCEAO,
normes, paramètres) SANS aucune donnée métier : l'application démarre VIDE,
tout s'enrichit à l'import.

Engine via MA2E_DB (sqlite par défaut, postgres sinon).
"""
from __future__ import annotations
import os, sys, json, hashlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
BCEAO_JSON = os.path.join(HERE, "..", "frontend", "src", "data", "bceao.json")
USE_PG = os.environ.get("MA2E_DB", "sqlite").lower() == "postgres"


def _h(p):
    return hashlib.sha256(p.encode("utf-8")).hexdigest()


UTILISATEURS = [
    ("dg@ma2e.ci", "Directeur Général", "DG", _h("demo")),
    ("dagf@ma2e.ci", "Directrice DAGF", "DAGF", _h("demo")),
    ("treso@ma2e.ci", "Trésorier", "TRESORIER", _h("demo")),
    ("ci@ma2e.ci", "Contrôle Interne", "CONTROLE_INTERNE", _h("demo")),
]
PARAMETRES = [
    ("plancher_tresorerie", "Plancher d'alerte trésorerie", "100000000", "FCFA", "Trésorerie"),
    ("ecart_tresorerie_pct", "Écart trésorerie vs prévision", "5", "%", "Trésorerie"),
    ("ecart_tresorerie_abs", "Écart théorique/constaté (TIF-CP-13)", "100000", "FCFA", "Trésorerie"),
    ("ecart_reversement", "Écart de reversement toléré", "0", "FCFA", "Rapprochements"),
    ("sla_suspens_alerte", "Alerte suspens", "7", "jours", "Rapprochements"),
    ("sla_suspens_escalade", "Escalade suspens", "30", "jours", "Rapprochements"),
    ("retention_audit", "Rétention des journaux d'audit (BCEAO)", "7", "ans", "Conformité"),
]
EMPTY_BALANCE = {
    "core_banking": "Perfect-Vision v5.7.1.5", "detail_disponible": False,
    "total_bilan": None, "resultat_net": None, "source": None, "date_arrete": None,
    "note": "Importez la balance pour afficher les agrégats.",
}

SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS fait_solde_journalier (id INTEGER PRIMARY KEY AUTOINCREMENT, date_jour TEXT NOT NULL, code_compte TEXT NOT NULL, type_compte TEXT NOT NULL, montant REAL NOT NULL, source_onglet TEXT, source_ligne INTEGER, qualite_flag TEXT NOT NULL DEFAULT 'OK');
CREATE TABLE IF NOT EXISTS fait_reversement (id INTEGER PRIMARY KEY AUTOINCREMENT, periode TEXT NOT NULL, iso TEXT, epargne REAL, pret REAL, droit_adhesion REAL, parts_sociales REAL, total_fichier REAL, montant_vir REAL, ecart REAL, regle INTEGER NOT NULL DEFAULT 0, observation TEXT);
CREATE TABLE IF NOT EXISTS bceao_etat (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, periodicite TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS bceao_config (cle TEXT PRIMARY KEY, valeur TEXT);
CREATE TABLE IF NOT EXISTS utilisateur (email TEXT PRIMARY KEY, nom TEXT NOT NULL, role TEXT NOT NULL, mdp_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS parametre (cle TEXT PRIMARY KEY, libelle TEXT NOT NULL, valeur TEXT NOT NULL, unite TEXT, categorie TEXT);
"""
SCHEMA_PG = SCHEMA_SQLITE.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY").replace("REAL", "DOUBLE PRECISION")


def main():
    bc = json.load(open(BCEAO_JSON, encoding="utf-8"))
    if USE_PG:
        import psycopg2
        con = psycopg2.connect(host=os.environ.get("PGHOST", "localhost"), port=int(os.environ.get("PGPORT", "5432")),
                               dbname=os.environ.get("PGDATABASE", "ma2e"), user=os.environ.get("PGUSER", "ma2e"),
                               password=os.environ.get("PGPASSWORD", "ma2e"))
        ph, schema = "%s", SCHEMA_PG
    else:
        import sqlite3
        con = sqlite3.connect(os.path.join(HERE, "ma2e.db"))
        ph, schema = "?", SCHEMA_SQLITE
    cur = con.cursor()
    for stmt in schema.strip().split(";"):
        if stmt.strip():
            cur.execute(stmt)
    ins = lambda sql, rows: [cur.execute(sql, r) for r in rows]
    # référentiels (idempotent : on nettoie puis on réinsère)
    for t in ("utilisateur", "parametre", "bceao_etat", "bceao_config"):
        cur.execute(f"DELETE FROM {t}")
    ins(f"INSERT INTO utilisateur(email,nom,role,mdp_hash) VALUES({ph},{ph},{ph},{ph})", UTILISATEURS)
    ins(f"INSERT INTO parametre(cle,libelle,valeur,unite,categorie) VALUES({ph},{ph},{ph},{ph},{ph})", PARAMETRES)
    ins(f"INSERT INTO bceao_etat(code,libelle,periodicite) VALUES({ph},{ph},{ph})",
        [(e["code"], e["libelle"], e["periodicite"]) for e in bc["etats"]])
    cfg = [(k, json.dumps(bc[k], ensure_ascii=False)) for k in ("meta", "workflow", "indicateurs")]
    cfg.append(("balance", json.dumps(EMPTY_BALANCE, ensure_ascii=False)))
    ins(f"INSERT INTO bceao_config(cle,valeur) VALUES({ph},{ph})", cfg)
    con.commit()
    con.close()
    print(f"Base initialisée ({'postgres' if USE_PG else 'sqlite'}) — référentiels chargés, données VIDES.")


if __name__ == "__main__":
    main()
