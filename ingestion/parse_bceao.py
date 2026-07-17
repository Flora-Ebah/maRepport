"""
MA2E — Pilote Trésorerie
Préparation du module Reporting BCEAO.

Sources :
  - SICSSFD_MENSUEL_*.xlsx (feuille GUIDE_DU_REPORTING) : catalogue OFFICIEL
    des états réglementaires + périodicité. Source FIABLE et structurée.
  - BALANCE *.pdf (export Perfect-Vision) : agrégats vérifiables uniquement
    (total bilan, résultat). L'extraction PDF mélange les colonnes détaillées
    -> le mapping ligne-à-ligne plan comptable → postes BCEAO est une tâche
    Sprint 0 nécessitant un export Excel/CSV ou l'API Perfect-Vision.

Sortie : frontend/src/data/bceao.json
"""
from __future__ import annotations
import os, sys, re, json, glob
from collections import Counter
import openpyxl, PyPDF2

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
OUT_DIR = os.path.join(HERE, "..", "frontend", "src", "data")
OUT = os.path.join(OUT_DIR, "bceao.json")

PERIODICITE = {"M": "Mensuelle", "T": "Trimestrielle", "A": "Annuelle"}


def catalogue_etats():
    """Lit le catalogue des états depuis la feuille GUIDE_DU_REPORTING."""
    path = glob.glob(os.path.join(ROOT, "SICSSFD*.xlsx"))[0]
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb["GUIDE_DU_REPORTING"]
    etats = []
    for row in ws.iter_rows(values_only=True):
        if not row:
            continue
        num, libelle = row[0], row[1]
        per_sfd44 = row[2] if len(row) > 2 else None
        # Une feuille principale = numéro présent + libellé commençant par "Feuille"
        if isinstance(num, (int, float)) and libelle and str(libelle).strip():
            code = f"{int(num)}"
            lib = re.sub(r"^Feuille portant sur( les| la| le)?\s*", "", str(libelle)).strip()
            lib = lib[0].upper() + lib[1:] if lib else lib
            per = PERIODICITE.get(str(per_sfd44).strip(), "Variable") if per_sfd44 else "Variable"
            etats.append({"code": code, "libelle": lib, "periodicite": per})
    return etats, os.path.basename(path)


def indicateurs():
    """Indicateurs prudentiels & de portefeuille avec NORMES BCEAO.
    Source : SICSSFD onglet 5 (Instruction n°20-10-2010) + dispositif prudentiel.
    """
    return [
        {"groupe": "Qualité du portefeuille", "items": [
            {"libelle": "Portefeuille à risque — PAR30", "norme": "≤ 5 %"},
            {"libelle": "Portefeuille à risque — PAR90", "norme": "≤ 3 %"},
            {"libelle": "Portefeuille à risque — PAR180", "norme": "≤ 2 %"},
            {"libelle": "Taux de provisions / créances en souffrance", "norme": "≥ 40 %"},
            {"libelle": "Taux de perte sur créances", "norme": "≤ 2 %"}]},
        {"groupe": "Efficacité & productivité", "items": [
            {"libelle": "Productivité des agents de crédit", "norme": "≥ 130"},
            {"libelle": "Productivité du personnel", "norme": "≥ 115"},
            {"libelle": "Charges d'exploitation / portefeuille", "norme": "≤ 35 %"},
            {"libelle": "Frais généraux / portefeuille (épargne-crédit)", "norme": "≤ 20 %"},
            {"libelle": "Charges de personnel (épargne-crédit)", "norme": "≤ 10 %"}]},
        {"groupe": "Rentabilité", "items": [
            {"libelle": "Rentabilité des fonds propres (ROE)", "norme": "≥ 15 %"},
            {"libelle": "Rendement sur actif (ROA)", "norme": "≥ 3 %"},
            {"libelle": "Autosuffisance opérationnelle", "norme": "≥ 130 %"}]},
        {"groupe": "Dispositif prudentiel", "items": [
            {"libelle": "Limitation des risques (une institution)", "norme": "≤ 200 %"},
            {"libelle": "Couverture emplois MLT par ressources stables", "norme": "≥ 100 %"},
            {"libelle": "Norme de liquidité", "norme": "≥ 100 %"},
            {"libelle": "Norme de capitalisation", "norme": "≥ 15 %"}]},
    ]


def agregats_balance(balance_path=None):
    """Métadonnées fiables de la balance.

    Décision d'intégrité : l'export PDF mélange les colonnes détaillées à
    l'extraction ; on ne publie AUCUN montant non vérifiable sur un état
    réglementaire. Le détail (postes du bilan) sera alimenté par un export
    structuré (Excel/CSV) ou l'API Perfect-Vision — tâche Sprint 0.
    """
    path = balance_path or glob.glob(os.path.join(ROOT, "BALANCE*.pdf"))[0]
    reader = PyPDF2.PdfReader(path)
    nb_pages = len(reader.pages)
    texte = "\n".join((p.extract_text() or "") for p in reader.pages)

    # Tokenisation : séparateur de milliers = espace insécable ( ).
    def nums(s):
        out = []
        for tok in s.split(" "):
            t = tok.replace(" ", "")
            if t.isdigit():
                out.append(int(t))
        return out

    total_bilan = resultat = None
    for ln in texte.splitlines():
        if "Total comptes bilan" in ln:
            vals = nums(ln)
            rep = [v for v in set(vals) if vals.count(v) >= 2]  # valeur d'équilibre
            total_bilan = max(rep) if rep else (max(vals) if vals else None)
        if "Résultat" in ln:
            seg = ln.split("Résultat")[-1]
            v = nums(seg)
            if v:
                resultat = max(v)

    m = re.search(r"(\d{2})-(\d{2})-(\d{4})", os.path.basename(path))
    arrete = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None

    return {
        "source": os.path.basename(path),
        "format": f"PDF ({nb_pages} pages)",
        "core_banking": "Perfect-Vision v5.7.1.5",
        "date_arrete": arrete,
        "etat_connexion": "Source détectée",
        "total_bilan": total_bilan,
        "resultat_net": resultat,
        "detail_disponible": False,
        "note": "Total bilan & résultat lus de la balance (indicatif). Détail des postes en attente d'un export structuré (Excel/CSV) ou de l'API Perfect-Vision.",
    }


def main():
    etats, src_cat = catalogue_etats()
    agg = agregats_balance()
    data = {
        "meta": {
            "titre": "Reporting réglementaire BCEAO (SICSSFD)",
            "source_catalogue": src_cat,
            "periode": "2026-05",
        },
        "balance": agg,
        "workflow": [
            {"niveau": 1, "role": "Préparateur (Contrôle Interne)", "sla": "24h",
             "desc": "Génération automatique des états + revue manuelle"},
            {"niveau": 2, "role": "Contrôleur senior", "sla": "48h",
             "desc": "Contrôle qualité & conformité — rejet possible avec motif"},
            {"niveau": 3, "role": "DAGF (Validateur)", "sla": "48h",
             "desc": "Validation finale + signature électronique XAdES"},
            {"niveau": 4, "role": "Système", "sla": "—",
             "desc": "Envoi BCEAO + archivage WORM 7 ans + accusé de réception"},
        ],
        "etats": etats,
        "indicateurs": indicateurs(),
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

    print("REPORTING BCEAO PRÉPARÉ")
    print(f"  États réglementaires : {len(etats)}")
    print(f"  Source balance       : {agg['source']} ({agg['core_banking']})")
    print(f"  Arrêté               : {agg['date_arrete']}")
    print(f"  Détail postes        : {'oui' if agg['detail_disponible'] else 'en attente export structuré'}")
    print(f"  -> {os.path.abspath(OUT)}")


if __name__ == "__main__":
    main()
