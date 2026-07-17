"""
MA2E — Pilote Trésorerie
Vide les données importables (soldes, reversements, agrégats balance) tout en
conservant les référentiels (utilisateurs, catalogue BCEAO, normes, paramètres).

L'application démarre ainsi VIDE : chaque page invite à importer son fichier.
Engine via MA2E_DB (sqlite par défaut, postgres sinon).
"""
from __future__ import annotations
import os, sys, json

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
USE_PG = os.environ.get("MA2E_DB", "sqlite").lower() == "postgres"

EMPTY_BALANCE = {
    "core_banking": "Perfect-Vision v5.7.1.5", "detail_disponible": False,
    "total_bilan": None, "resultat_net": None, "source": None, "date_arrete": None,
    "note": "Importez la balance pour afficher les agrégats.",
}

if USE_PG:
    import psycopg2
    con = psycopg2.connect(host=os.environ.get("PGHOST", "localhost"),
                           port=int(os.environ.get("PGPORT", "5435")),
                           dbname=os.environ.get("PGDATABASE", "ma2e"),
                           user=os.environ.get("PGUSER", "ma2e"),
                           password=os.environ.get("PGPASSWORD", "ma2e"))
    ph = "%s"
else:
    import sqlite3
    con = sqlite3.connect(os.path.join(HERE, "ma2e.db"))
    ph = "?"

cur = con.cursor()
cur.execute("DELETE FROM fait_solde_journalier")
cur.execute("DELETE FROM fait_reversement")
cur.execute(f"DELETE FROM bceao_config WHERE cle = {ph}", ("balance",))
cur.execute(f"INSERT INTO bceao_config(cle, valeur) VALUES ({ph}, {ph})",
            ("balance", json.dumps(EMPTY_BALANCE, ensure_ascii=False)))
con.commit()
con.close()
print(f"Base vidée ({'postgres' if USE_PG else 'sqlite'}) — prête pour l'import.")
