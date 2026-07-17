"""
MA2E — Pilote Trésorerie
Génère le fichier de données consommé par le frontend Next.js
à partir de output/soldes_journaliers.csv.

Sortie : frontend/src/data/tresorerie.json
(Étape transitoire : sera remplacé par l'API FastAPI en industrialisation.)
"""
from __future__ import annotations
import os, csv, json, sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "..", "output", "soldes_journaliers.csv")
OUT_DIR = os.path.join(HERE, "..", "frontend", "src", "data")
OUT_PATH = os.path.join(OUT_DIR, "tresorerie.json")

ORDRE = ["ECOBANK", "ORABANK", "BOA-CI", "UBA", "JULAYA",
         "CAISSE_DEPENSES", "CAISSE_RECETTE", "COFFRE_FORT"]
LIBELLES = {
    "ECOBANK": "Ecobank", "ORABANK": "Orabank", "BOA-CI": "BOA-CI",
    "UBA": "UBA", "JULAYA": "Julaya", "CAISSE_DEPENSES": "Caisse Dépenses",
    "CAISSE_RECETTE": "Caisse Recette", "COFFRE_FORT": "Coffre-fort",
}
TYPES = {
    "ECOBANK": "BANQUE", "ORABANK": "BANQUE", "BOA-CI": "BANQUE", "UBA": "BANQUE",
    "JULAYA": "BANQUE", "CAISSE_DEPENSES": "CAISSE", "CAISSE_RECETTE": "CAISSE",
    "COFFRE_FORT": "COFFRE",
}


def main():
    par_jour = defaultdict(float)
    par_jour_compte = defaultdict(dict)
    anomalies = []
    seen_ano = set()

    with open(CSV_PATH, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            d = row["date_jour"]
            try:
                an = int(d[:4])
            except ValueError:
                continue
            if an < 2020 or an > 2030:
                key = (row["source_onglet"], d)
                if key not in seen_ano:
                    seen_ano.add(key)
                    anomalies.append({"onglet": row["source_onglet"], "date": d,
                                      "type": "Date aberrante (hors série)"})
                continue
            montant = float(row["montant"])
            par_jour[d] += montant
            par_jour_compte[d][row["code_compte"]] = montant
            if row["qualite_flag"] == "DATE_SUSPECTE":
                key = (row["source_onglet"], d)
                if key not in seen_ano:
                    seen_ano.add(key)
                    anomalies.append({"onglet": row["source_onglet"], "date": d,
                                      "type": "Date incohérente avec l'onglet"})

    dates = [d for d in sorted(par_jour) if par_jour[d] > 0]
    serie = [{"date": d, "total": round(par_jour[d])} for d in dates]

    last = dates[-1]
    prev = dates[-2] if len(dates) > 1 else last
    pos = par_jour[last]
    var = pos - par_jour[prev]
    totals = [par_jour[d] for d in dates]

    derniers = par_jour_compte[last]
    repartition = [
        {"code": c, "libelle": LIBELLES[c], "type": TYPES[c],
         "montant": round(derniers[c]), "part": round(derniers[c] / pos * 100, 1)}
        for c in ORDRE if c in derniers
    ]
    repartition.sort(key=lambda r: -r["montant"])

    # Tableau : 20 derniers jours, détail par compte
    recent = []
    for d in dates[-20:][::-1]:
        comptes = par_jour_compte[d]
        recent.append({
            "date": d,
            "total": round(par_jour[d]),
            "comptes": {c: round(comptes.get(c, 0)) for c in ORDRE},
        })

    data = {
        "meta": {
            "institution": "MA2E — Mutuelle des Agents de l'Eau et de l'Électricité",
            "source": "POINT RETRAIT (ingestion automatisée)",
            "date_position": last,
            "periode_debut": dates[0],
            "periode_fin": dates[-1],
            "nb_jours": len(dates),
            "nb_comptes": len(ORDRE),
        },
        "kpi": {
            "position": round(pos),
            "variation": round(var),
            "variation_pct": round(var / par_jour[prev] * 100, 2) if par_jour[prev] else 0,
            "max": round(max(totals)),
            "min": round(min(totals)),
            "moyenne": round(sum(totals) / len(totals)),
            "nb_anomalies": len(anomalies),
        },
        "serie": serie,
        "repartition": repartition,
        "recent": recent,
        "colonnes": [{"code": c, "libelle": LIBELLES[c]} for c in ORDRE],
        "anomalies": anomalies,
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

    print("DONNÉES FRONTEND GÉNÉRÉES")
    print(f"  Position {last} : {pos:,.0f} FCFA")
    print(f"  Série : {len(serie)} points · Répartition : {len(repartition)} comptes")
    print(f"  Anomalies : {len(anomalies)}")
    print(f"  -> {os.path.abspath(OUT_PATH)}")


if __name__ == "__main__":
    main()
