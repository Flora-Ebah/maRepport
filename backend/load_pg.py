"""
MA2E — Pilote Trésorerie · Backend
Charge la base PostgreSQL (cible production) avec les mêmes données.

Types alignés sur SQLite (TEXT / DOUBLE PRECISION / INTEGER) pour que
l'API reste strictement identique quel que soit le moteur.

Connexion via variables d'environnement (défauts : conteneur pilote) :
  PGHOST=localhost PGPORT=5435 PGDATABASE=ma2e PGUSER=ma2e PGPASSWORD=ma2e
"""
from __future__ import annotations
import os, sys, csv, json
import psycopg2, psycopg2.extras
from load_db import UTILISATEURS, PARAMETRES  # mêmes seeds (DRY)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "..", "output", "soldes_journaliers.csv")
REV = os.path.join(HERE, "..", "frontend", "src", "data", "reversements.json")
BCEAO = os.path.join(HERE, "..", "frontend", "src", "data", "bceao.json")

PG = dict(
    host=os.environ.get("PGHOST", "localhost"),
    port=int(os.environ.get("PGPORT", "5435")),
    dbname=os.environ.get("PGDATABASE", "ma2e"),
    user=os.environ.get("PGUSER", "ma2e"),
    password=os.environ.get("PGPASSWORD", "ma2e"),
)

DDL = """
DROP TABLE IF EXISTS fait_solde_journalier, fait_reversement, bceao_etat,
                     bceao_config, utilisateur, parametre CASCADE;

CREATE TABLE fait_solde_journalier (
  id SERIAL PRIMARY KEY,
  date_jour TEXT NOT NULL,
  code_compte TEXT NOT NULL,
  type_compte TEXT NOT NULL,
  montant DOUBLE PRECISION NOT NULL,
  source_onglet TEXT,
  source_ligne INTEGER,
  qualite_flag TEXT NOT NULL DEFAULT 'OK'
);
CREATE INDEX idx_solde_date ON fait_solde_journalier(date_jour);

CREATE TABLE fait_reversement (
  id SERIAL PRIMARY KEY,
  periode TEXT NOT NULL, iso TEXT,
  epargne DOUBLE PRECISION, pret DOUBLE PRECISION,
  droit_adhesion DOUBLE PRECISION, parts_sociales DOUBLE PRECISION,
  total_fichier DOUBLE PRECISION, montant_vir DOUBLE PRECISION,
  ecart DOUBLE PRECISION, regle INTEGER NOT NULL DEFAULT 0, observation TEXT
);

CREATE TABLE bceao_etat (code TEXT PRIMARY KEY, libelle TEXT NOT NULL, periodicite TEXT NOT NULL);
CREATE TABLE bceao_config (cle TEXT PRIMARY KEY, valeur TEXT);
CREATE TABLE utilisateur (email TEXT PRIMARY KEY, nom TEXT NOT NULL, role TEXT NOT NULL, mdp_hash TEXT NOT NULL);
CREATE TABLE parametre (cle TEXT PRIMARY KEY, libelle TEXT NOT NULL, valeur TEXT NOT NULL, unite TEXT, categorie TEXT);
"""


def main():
    con = psycopg2.connect(**PG)
    cur = con.cursor()
    cur.execute(DDL)

    # Soldes
    soldes = []
    with open(CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            soldes.append((r["date_jour"], r["code_compte"], r["type_compte"], float(r["montant"]),
                           r["source_onglet"], int(r["source_ligne"]) if r["source_ligne"] else None, r["qualite_flag"]))
    psycopg2.extras.execute_batch(cur,
        "INSERT INTO fait_solde_journalier(date_jour,code_compte,type_compte,montant,source_onglet,source_ligne,qualite_flag) VALUES(%s,%s,%s,%s,%s,%s,%s)", soldes)

    # Reversements
    rev = json.load(open(REV, encoding="utf-8"))
    for l in rev["lignes"]:
        cur.execute(
            "INSERT INTO fait_reversement(periode,iso,epargne,pret,droit_adhesion,parts_sociales,total_fichier,montant_vir,ecart,regle,observation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (l["periode"], l.get("iso"), l.get("epargne"), l.get("pret"), l.get("droit_adhesion"),
             l.get("parts_sociales"), l.get("total_fichier"), l.get("montant_vir"), l.get("ecart"),
             1 if l.get("regle") else 0, l.get("observation")))

    # BCEAO
    bc = json.load(open(BCEAO, encoding="utf-8"))
    for e in bc["etats"]:
        cur.execute("INSERT INTO bceao_etat(code,libelle,periodicite) VALUES(%s,%s,%s)", (e["code"], e["libelle"], e["periodicite"]))
    for cle in ("meta", "balance", "workflow", "indicateurs"):
        cur.execute("INSERT INTO bceao_config(cle,valeur) VALUES(%s,%s)", (cle, json.dumps(bc[cle], ensure_ascii=False)))

    # Utilisateurs + paramètres (mêmes seeds que SQLite)
    psycopg2.extras.execute_batch(cur, "INSERT INTO utilisateur(email,nom,role,mdp_hash) VALUES(%s,%s,%s,%s)", UTILISATEURS)
    psycopg2.extras.execute_batch(cur, "INSERT INTO parametre(cle,libelle,valeur,unite,categorie) VALUES(%s,%s,%s,%s,%s)", PARAMETRES)

    con.commit()
    cur.execute("SELECT COUNT(*) FROM fait_solde_journalier"); n = cur.fetchone()[0]
    con.close()
    print("BASE POSTGRESQL CHARGÉE")
    print(f"  Cible       : {PG['user']}@{PG['host']}:{PG['port']}/{PG['dbname']}")
    print(f"  Soldes      : {n:,}")
    print(f"  Reversements: {len(rev['lignes'])} · États: {len(bc['etats'])} · Users: {len(UTILISATEURS)} · Paramètres: {len(PARAMETRES)}")


if __name__ == "__main__":
    main()
