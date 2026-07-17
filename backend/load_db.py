"""
MA2E — Pilote Trésorerie · Backend
Charge la base SQLite (ma2e.db) à partir des données déjà ingérées.

SQLite est utilisé pour le pilote (zéro installation). La cible de
production reste PostgreSQL (cf. db/schema.sql) — le modèle est identique.

Sources :
  - ../output/soldes_journaliers.csv         (parser trésorerie)
  - ../frontend/src/data/reversements.json   (parser SIVE)
  - ../frontend/src/data/bceao.json          (parser BCEAO)
"""
from __future__ import annotations
import os, sys, csv, json, sqlite3

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "ma2e.db")
CSV = os.path.join(HERE, "..", "output", "soldes_journaliers.csv")
REV = os.path.join(HERE, "..", "frontend", "src", "data", "reversements.json")
BCEAO = os.path.join(HERE, "..", "frontend", "src", "data", "bceao.json")

SCHEMA = """
DROP TABLE IF EXISTS fait_solde_journalier;
DROP TABLE IF EXISTS fait_reversement;
DROP TABLE IF EXISTS bceao_etat;
DROP TABLE IF EXISTS bceao_config;

CREATE TABLE fait_solde_journalier (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date_jour TEXT NOT NULL,
  code_compte TEXT NOT NULL,
  type_compte TEXT NOT NULL,
  montant REAL NOT NULL,
  source_onglet TEXT,
  source_ligne INTEGER,
  qualite_flag TEXT NOT NULL DEFAULT 'OK'
);
CREATE INDEX idx_solde_date ON fait_solde_journalier(date_jour);

CREATE TABLE fait_reversement (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  periode TEXT NOT NULL,
  iso TEXT,
  epargne REAL, pret REAL, droit_adhesion REAL, parts_sociales REAL,
  total_fichier REAL, montant_vir REAL, ecart REAL,
  regle INTEGER NOT NULL DEFAULT 0,
  observation TEXT
);

CREATE TABLE bceao_etat (
  code TEXT PRIMARY KEY,
  libelle TEXT NOT NULL,
  periodicite TEXT NOT NULL
);

CREATE TABLE bceao_config (cle TEXT PRIMARY KEY, valeur TEXT);

DROP TABLE IF EXISTS utilisateur;
CREATE TABLE utilisateur (
  email TEXT PRIMARY KEY,
  nom TEXT NOT NULL,
  role TEXT NOT NULL,
  mdp_hash TEXT NOT NULL
);

DROP TABLE IF EXISTS parametre;
CREATE TABLE parametre (
  cle TEXT PRIMARY KEY,
  libelle TEXT NOT NULL,
  valeur TEXT NOT NULL,
  unite TEXT,
  categorie TEXT
);
"""

# Seuils & règles d'alerte (paramétrables — module M5 Administration).
PARAMETRES = [
    ("plancher_tresorerie", "Plancher d'alerte trésorerie", "100000000", "FCFA", "Trésorerie"),
    ("ecart_tresorerie_pct", "Écart trésorerie vs prévision", "5", "%", "Trésorerie"),
    ("ecart_tresorerie_abs", "Écart théorique/constaté (TIF-CP-13)", "100000", "FCFA", "Trésorerie"),
    ("ecart_reversement", "Écart de reversement toléré", "0", "FCFA", "Rapprochements"),
    ("sla_suspens_alerte", "Alerte suspens", "7", "jours", "Rapprochements"),
    ("sla_suspens_escalade", "Escalade suspens", "30", "jours", "Rapprochements"),
    ("retention_audit", "Rétention des journaux d'audit (BCEAO)", "7", "ans", "Conformité"),
]

# Comptes de démonstration (pilote). En production : Keycloak SSO + MFA.
import hashlib
def _h(p): return hashlib.sha256(p.encode("utf-8")).hexdigest()
UTILISATEURS = [
    ("dg@ma2e.ci",    "Directeur Général",   "DG",               _h("demo")),
    ("dagf@ma2e.ci",  "Directrice DAGF",     "DAGF",             _h("demo")),
    ("treso@ma2e.ci", "Trésorier",           "TRESORIER",        _h("demo")),
    ("ci@ma2e.ci",    "Contrôle Interne",    "CONTROLE_INTERNE", _h("demo")),
]


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.executescript(SCHEMA)

    # ── Soldes journaliers ──
    n = 0
    with open(CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            cur.execute(
                "INSERT INTO fait_solde_journalier(date_jour,code_compte,type_compte,montant,source_onglet,source_ligne,qualite_flag) VALUES(?,?,?,?,?,?,?)",
                (r["date_jour"], r["code_compte"], r["type_compte"], float(r["montant"]),
                 r["source_onglet"], int(r["source_ligne"]) if r["source_ligne"] else None, r["qualite_flag"]))
            n += 1

    # ── Reversements ──
    rev = json.load(open(REV, encoding="utf-8"))
    for l in rev["lignes"]:
        cur.execute(
            "INSERT INTO fait_reversement(periode,iso,epargne,pret,droit_adhesion,parts_sociales,total_fichier,montant_vir,ecart,regle,observation) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (l["periode"], l.get("iso"), l.get("epargne"), l.get("pret"), l.get("droit_adhesion"),
             l.get("parts_sociales"), l.get("total_fichier"), l.get("montant_vir"), l.get("ecart"),
             1 if l.get("regle") else 0, l.get("observation")))

    # ── BCEAO (catalogue + config) ──
    bc = json.load(open(BCEAO, encoding="utf-8"))
    for e in bc["etats"]:
        cur.execute("INSERT INTO bceao_etat(code,libelle,periodicite) VALUES(?,?,?)",
                    (e["code"], e["libelle"], e["periodicite"]))
    for cle in ("meta", "balance", "workflow", "indicateurs"):
        cur.execute("INSERT INTO bceao_config(cle,valeur) VALUES(?,?)",
                    (cle, json.dumps(bc[cle], ensure_ascii=False)))

    # ── Utilisateurs ──
    cur.executemany("INSERT INTO utilisateur(email,nom,role,mdp_hash) VALUES(?,?,?,?)", UTILISATEURS)
    # ── Paramètres ──
    cur.executemany("INSERT INTO parametre(cle,libelle,valeur,unite,categorie) VALUES(?,?,?,?,?)", PARAMETRES)

    con.commit()
    nb_rev = cur.execute("SELECT COUNT(*) FROM fait_reversement").fetchone()[0]
    nb_et = cur.execute("SELECT COUNT(*) FROM bceao_etat").fetchone()[0]
    con.close()

    print("BASE SQLITE CHARGÉE")
    print(f"  Soldes journaliers : {n:,}")
    print(f"  Reversements       : {nb_rev}")
    print(f"  États BCEAO        : {nb_et}")
    print(f"  Utilisateurs       : {len(UTILISATEURS)}")
    print(f"  -> {DB}")


if __name__ == "__main__":
    main()
