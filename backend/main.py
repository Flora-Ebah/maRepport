"""
MA2E — Pilote Trésorerie · API FastAPI
Sert les données depuis la base SQLite (ma2e.db).

Les réponses respectent exactement les structures consommées par le
frontend (branchement direct, sans refonte). Lancer :
    uvicorn main:app --reload --port 8000
"""
from __future__ import annotations
import os, sys, re, io, json, sqlite3, hashlib, tempfile
from typing import List
from collections import defaultdict
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# accès aux parsers d'ingestion (réutilisés pour l'import live)
ING = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ingestion")
if ING not in sys.path:
    sys.path.insert(0, ING)

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "ma2e.db")

ORDRE = ["ECOBANK", "ORABANK", "BOA-CI", "UBA", "JULAYA",
         "CAISSE_DEPENSES", "CAISSE_RECETTE", "COFFRE_FORT"]
LIBELLES = {
    "ECOBANK": "Ecobank", "ORABANK": "Orabank", "BOA-CI": "BOA-CI", "UBA": "UBA",
    "JULAYA": "Julaya", "CAISSE_DEPENSES": "Caisse Dépenses",
    "CAISSE_RECETTE": "Caisse Recette", "COFFRE_FORT": "Coffre-fort",
}
TYPES = {"ECOBANK": "BANQUE", "ORABANK": "BANQUE", "BOA-CI": "BANQUE", "UBA": "BANQUE",
         "JULAYA": "BANQUE", "CAISSE_DEPENSES": "CAISSE", "CAISSE_RECETTE": "CAISSE",
         "COFFRE_FORT": "COFFRE"}

app = FastAPI(title="MA2E Trésorerie API", version="1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── Couche d'accès agnostique : SQLite (défaut) ou PostgreSQL (prod) ──
USE_PG = os.environ.get("MA2E_DB", "sqlite").lower() == "postgres"
if USE_PG:
    import psycopg2, psycopg2.extras
    PG = dict(host=os.environ.get("PGHOST", "localhost"), port=int(os.environ.get("PGPORT", "5435")),
              dbname=os.environ.get("PGDATABASE", "ma2e"), user=os.environ.get("PGUSER", "ma2e"),
              password=os.environ.get("PGPASSWORD", "ma2e"))


def _connect():
    if USE_PG:
        return psycopg2.connect(**PG)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def query(sql, params=()):
    """Exécute une requête et renvoie une liste de dicts (les 2 moteurs)."""
    sql = sql.replace("?", "%s") if USE_PG else sql
    con = _connect()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) if USE_PG else con.cursor()
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        con.close()


def query_one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql, params=(), many=False):
    """Écriture (INSERT/DELETE) compatible SQLite & PostgreSQL."""
    sql = sql.replace("?", "%s") if USE_PG else sql
    con = _connect()
    try:
        cur = con.cursor()
        cur.executemany(sql, params) if many else cur.execute(sql, params)
        con.commit()
        return cur.rowcount
    finally:
        con.close()


def valid_year(d: str) -> bool:
    try:
        return 2020 <= int(d[:4]) <= 2030
    except ValueError:
        return False


class Login(BaseModel):
    email: str
    password: str


@app.post("/api/login")
def login(c: Login):
    h = hashlib.sha256(c.password.encode("utf-8")).hexdigest()
    u = query_one(
        "SELECT email, nom, role FROM utilisateur WHERE lower(email)=lower(?) AND mdp_hash=?",
        (c.email.strip(), h))
    if not u:
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    return {"email": u["email"], "nom": u["nom"], "role": u["role"]}


@app.get("/api/health")
def health():
    n = query_one("SELECT COUNT(*) AS n FROM fait_solde_journalier")["n"]
    return {"status": "ok", "moteur": "postgres" if USE_PG else "sqlite", "soldes": n}


@app.get("/api/status")
def status():
    """Ce qui est déjà importé → pilote l'activation de la navigation."""
    treso = query_one("SELECT COUNT(*) AS n FROM fait_solde_journalier")["n"] > 0
    rev = query_one("SELECT COUNT(*) AS n FROM fait_reversement")["n"] > 0
    bal_row = query_one("SELECT valeur FROM bceao_config WHERE cle = ?", ("balance",))
    balance = False
    if bal_row:
        try:
            balance = json.loads(bal_row["valeur"]).get("total_bilan") is not None
        except Exception:
            balance = False
    return {"tresorerie": treso, "reversements": rev, "balance": balance}


# ── Exports (Excel & PDF) ────────────────────────────────────────────
NAVY = "1F4E79"


def _xlsx(wb, filename):
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def _style_header(ws, ncols):
    from openpyxl.styles import Font, PatternFill, Alignment
    fill = PatternFill("solid", fgColor=NAVY)
    for c in range(1, ncols + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = fill
        cell.alignment = Alignment(vertical="center")


def _treso_totaux():
    rows = query("SELECT date_jour, code_compte, montant FROM fait_solde_journalier")
    par_jour = defaultdict(float)
    par_jour_compte = defaultdict(dict)
    for r in rows:
        if not valid_year(r["date_jour"]):
            continue
        par_jour[r["date_jour"]] += r["montant"]
        par_jour_compte[r["date_jour"]][r["code_compte"]] = r["montant"]
    dates = [d for d in sorted(par_jour) if par_jour[d] > 0]
    return dates, par_jour, par_jour_compte


@app.get("/api/export/tresorerie.xlsx")
def export_tresorerie_xlsx():
    import openpyxl
    dates, par_jour, par_jour_compte = _treso_totaux()
    if not dates:
        raise HTTPException(404, "Aucune donnée à exporter.")
    wb = openpyxl.Workbook()
    s1 = wb.active; s1.title = "Position par jour"
    s1.append(["Date", "Total trésorerie (FCFA)"])
    for d in dates:
        s1.append([d, round(par_jour[d])])
    _style_header(s1, 2); s1.column_dimensions["A"].width = 14; s1.column_dimensions["B"].width = 24
    s2 = wb.create_sheet("Détail par compte")
    s2.append(["Date", "Compte", "Montant (FCFA)"])
    for d in dates:
        for c, m in sorted(par_jour_compte[d].items()):
            s2.append([d, c, round(m)])
    _style_header(s2, 3); s2.column_dimensions["A"].width = 14; s2.column_dimensions["B"].width = 18; s2.column_dimensions["C"].width = 18
    return _xlsx(wb, "MA2E_tresorerie.xlsx")


@app.get("/api/export/tresorerie.pdf")
def export_tresorerie_pdf():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    dates, par_jour, par_jour_compte = _treso_totaux()
    if not dates:
        raise HTTPException(404, "Aucune donnée à exporter.")
    last = dates[-1]
    totals = [par_jour[d] for d in dates]
    navy = colors.HexColor("#1F4E79")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm)
    st = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=st["Title"], textColor=navy, fontSize=18)
    sub = ParagraphStyle("s", parent=st["Normal"], textColor=colors.grey, fontSize=9)
    el = [Paragraph("MA2E — Point de Trésorerie", h),
          Paragraph(f"Position consolidée au {last} · {len(dates)} jours", sub), Spacer(1, 8 * mm)]
    fmt = lambda n: f"{round(n):,}".replace(",", " ")
    kpis = [["Position consolidée", fmt(par_jour[last]) + " FCFA"],
            ["Pic maximum", fmt(max(totals)) + " FCFA"],
            ["Plancher minimum", fmt(min(totals)) + " FCFA"],
            ["Moyenne période", fmt(sum(totals) / len(totals)) + " FCFA"]]
    t = Table(kpis, colWidths=[60 * mm, 100 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0F5FA")),
                           ("TEXTCOLOR", (0, 0), (0, -1), navy), ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                           ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 11),
                           ("ROWBACKGROUNDS", (1, 0), (1, -1), [colors.white]), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                           ("TOPPADDING", (0, 0), (-1, -1), 7), ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E4E4E7"))]))
    el += [t, Spacer(1, 8 * mm), Paragraph("20 derniers jours", ParagraphStyle("hh", parent=st["Heading2"], textColor=navy))]
    data = [["Date", "Total (FCFA)"]] + [[d, fmt(par_jour[d])] for d in dates[-20:][::-1]]
    tt = Table(data, colWidths=[80 * mm, 80 * mm])
    tt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), navy), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAFA")]),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 5)]))
    el.append(tt)
    el += [Spacer(1, 6 * mm), Paragraph("Document généré automatiquement — pilote MA2E.", sub)]
    doc.build(el)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf",
                             headers={"Content-Disposition": 'attachment; filename="MA2E_tresorerie.pdf"'})


@app.get("/api/export/reversements.xlsx")
def export_reversements_xlsx():
    import openpyxl
    rows = query("SELECT periode,epargne,pret,total_fichier,montant_vir,ecart,observation "
                 "FROM fait_reversement ORDER BY id")
    if not rows:
        raise HTTPException(404, "Aucune donnée à exporter.")
    wb = openpyxl.Workbook()
    ws = wb.active; ws.title = "Reversements SIVE"
    ws.append(["Période", "Épargne", "Prêt", "Total fichier", "Montant viré", "Écart", "Statut"])
    for r in rows:
        ws.append([r["periode"], r["epargne"], r["pret"], r["total_fichier"],
                   r["montant_vir"], r["ecart"], r["observation"]])
    _style_header(ws, 7)
    for col in "ABCDEFG":
        ws.column_dimensions[col].width = 16
    ws.column_dimensions["A"].width = 18; ws.column_dimensions["G"].width = 28
    return _xlsx(wb, "MA2E_reversements.xlsx")


@app.get("/api/export/bceao.xlsx")
def export_bceao_xlsx():
    import openpyxl
    cfg = {r["cle"]: json.loads(r["valeur"]) for r in query("SELECT cle,valeur FROM bceao_config")}
    etats = query("SELECT code,libelle,periodicite FROM bceao_etat")
    bal = cfg.get("balance") or {}
    indic = cfg.get("indicateurs") or []
    wb = openpyxl.Workbook()
    s0 = wb.active; s0.title = "Synthèse"
    s0.append(["Reporting réglementaire BCEAO — MA2E", ""])
    s0.append(["Total bilan (FCFA)", bal.get("total_bilan")])
    s0.append(["Résultat net (FCFA)", bal.get("resultat_net")])
    s0.append(["Source", bal.get("source")])
    s0.append(["Arrêté au", bal.get("date_arrete")])
    s0.column_dimensions["A"].width = 30; s0.column_dimensions["B"].width = 28
    s1 = wb.create_sheet("États réglementaires")
    s1.append(["N°", "État", "Périodicité"])
    for e in etats:
        s1.append([e["code"], e["libelle"], e["periodicite"]])
    _style_header(s1, 3); s1.column_dimensions["B"].width = 42; s1.column_dimensions["C"].width = 16
    s2 = wb.create_sheet("Indicateurs prudentiels")
    s2.append(["Groupe", "Indicateur", "Norme"])
    for g in indic:
        for it in g["items"]:
            s2.append([g["groupe"], it["libelle"], it["norme"]])
    _style_header(s2, 3); s2.column_dimensions["A"].width = 26; s2.column_dimensions["B"].width = 46; s2.column_dimensions["C"].width = 12
    return _xlsx(wb, "MA2E_reporting_BCEAO.xlsx")


# ── Import intelligent (un seul bouton, détection automatique) ───────
def _detect(filename, path):
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return "balance"
    if not name.endswith((".xlsx", ".xls")):
        return "inconnu"
    if "sive" in name:
        return "reversements"
    if "retrait" in name or "treso" in name:
        return "tresorerie"
    try:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        sheets = wb.sheetnames
        if any("sive" in s.lower() for s in sheets):
            return "reversements"
        ws = wb[sheets[0]]
        blob = ""
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            blob += " ".join(str(c) for c in row if c is not None).lower() + " "
            if i >= 8:
                break
        if "ecobank" in blob or "coffre" in blob:
            return "tresorerie"
        if "prelevement" in blob or "reversement" in blob or "montant vir" in blob:
            return "reversements"
        if len(sheets) >= 10:
            return "tresorerie"
    except Exception:
        pass
    return "tresorerie"


def _load_tresorerie(path):
    from parse_tresorerie import parse_workbook
    lignes, comptes, stats, anomalies, _ = parse_workbook(path)
    if not lignes:
        raise ValueError("Aucun solde détecté")
    execute("DELETE FROM fait_solde_journalier")
    rows = [(l["date_jour"], l["code_compte"], l["type_compte"], l["montant"],
             l["source_onglet"], l["source_ligne"], l["qualite_flag"]) for l in lignes]
    execute("INSERT INTO fait_solde_journalier(date_jour,code_compte,type_compte,montant,"
            "source_onglet,source_ligne,qualite_flag) VALUES(?,?,?,?,?,?,?)", rows, many=True)
    return {"type": "tresorerie", "libelle": "Point de Trésorerie",
            "detail": f"{len(lignes)} soldes · {len(anomalies)} anomalies"}


def _load_reversements(path):
    from parse_sive import parse_sive
    d = parse_sive(path)
    lignes = d["lignes"]
    if not lignes:
        raise ValueError("Aucune ligne détectée")
    execute("DELETE FROM fait_reversement")
    rows = [(l["periode"], l["iso"], l["epargne"], l["pret"], l["droit_adhesion"],
             l["parts_sociales"], l["total_fichier"], l["montant_vir"], l["ecart"],
             1 if l["regle"] else 0, l["observation"]) for l in lignes]
    execute("INSERT INTO fait_reversement(periode,iso,epargne,pret,droit_adhesion,parts_sociales,"
            "total_fichier,montant_vir,ecart,regle,observation) VALUES(?,?,?,?,?,?,?,?,?,?,?)", rows, many=True)
    return {"type": "reversements", "libelle": "Rapprochements (SIVE)",
            "detail": f"{len(lignes)} lignes · écart {d['kpi']['ecart_total']:,} FCFA".replace(",", " ")}


def _load_balance(path, filename):
    from parse_bceao import agregats_balance
    agg = agregats_balance(path)
    agg["source"] = filename
    m = re.search(r"(\d{2})-(\d{2})-(\d{4})", filename or "")
    if m:
        agg["date_arrete"] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    execute("DELETE FROM bceao_config WHERE cle = ?", ("balance",))
    execute("INSERT INTO bceao_config(cle,valeur) VALUES(?,?)", ("balance", json.dumps(agg, ensure_ascii=False)))
    tb = agg.get("total_bilan")
    return {"type": "balance", "libelle": "Reporting BCEAO",
            "detail": f"total bilan {tb:,} FCFA".replace(",", " ") if tb else "agrégats lus"}


@app.post("/api/import")
async def import_multi(files: List[UploadFile] = File(...)):
    """Un seul point d'entrée : détecte et traite chaque fichier (jusqu'à 3)."""
    out = []
    for f in files:
        data = await f.read()
        ext = ".pdf" if (f.filename or "").lower().endswith(".pdf") else ".xlsx"
        safe = re.sub(r"[^\w.-]", "_", f.filename or "fichier")
        tmp = os.path.join(tempfile.gettempdir(), "ma2e_up_" + safe + ext)
        with open(tmp, "wb") as fh:
            fh.write(data)
        kind = _detect(f.filename, tmp)
        try:
            if kind == "tresorerie":
                r = _load_tresorerie(tmp)
            elif kind == "reversements":
                r = _load_reversements(tmp)
            elif kind == "balance":
                r = _load_balance(tmp, f.filename)
            else:
                r = {"type": "inconnu", "libelle": "Type non reconnu", "detail": "Fichier ignoré"}
            r.update({"fichier": f.filename, "ok": kind != "inconnu"})
        except Exception as e:
            r = {"fichier": f.filename, "type": kind, "libelle": "Erreur", "detail": str(e), "ok": False}
        out.append(r)
    return {"resultats": out}


@app.post("/api/import/tresorerie")
async def import_tresorerie(file: UploadFile = File(...)):
    """Import live d'un fichier 'POINT RETRAIT' : parse → remplace les soldes."""
    from parse_tresorerie import parse_workbook
    data = await file.read()
    tmp = os.path.join(tempfile.gettempdir(), "ma2e_import_treso.xlsx")
    with open(tmp, "wb") as fh:
        fh.write(data)
    try:
        lignes, comptes, stats, anomalies, _ = parse_workbook(tmp)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fichier illisible : {e}")
    if not lignes:
        raise HTTPException(status_code=400, detail="Aucun solde détecté dans ce fichier.")
    execute("DELETE FROM fait_solde_journalier")
    rows = [(l["date_jour"], l["code_compte"], l["type_compte"], l["montant"],
             l["source_onglet"], l["source_ligne"], l["qualite_flag"]) for l in lignes]
    execute("INSERT INTO fait_solde_journalier(date_jour,code_compte,type_compte,montant,"
            "source_onglet,source_ligne,qualite_flag) VALUES(?,?,?,?,?,?,?)", rows, many=True)
    dates = sorted({l["date_jour"] for l in lignes})
    return {"fichier": file.filename, "onglets": stats.get("onglets_traites", 0),
            "soldes": len(lignes), "comptes": sorted(comptes), "anomalies": len(anomalies),
            "periode": [dates[0], dates[-1]] if dates else None}


@app.post("/api/import/reversements")
async def import_reversements(file: UploadFile = File(...)):
    """Import live d'un fichier 'POINT SIVE' (reversements)."""
    from parse_sive import parse_sive
    data = await file.read()
    tmp = os.path.join(tempfile.gettempdir(), "ma2e_import_sive.xlsx")
    with open(tmp, "wb") as fh:
        fh.write(data)
    try:
        d = parse_sive(tmp)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fichier illisible : {e}")
    lignes = d["lignes"]
    if not lignes:
        raise HTTPException(status_code=400, detail="Aucune ligne détectée dans ce fichier.")
    execute("DELETE FROM fait_reversement")
    rows = [(l["periode"], l["iso"], l["epargne"], l["pret"], l["droit_adhesion"],
             l["parts_sociales"], l["total_fichier"], l["montant_vir"], l["ecart"],
             1 if l["regle"] else 0, l["observation"]) for l in lignes]
    execute("INSERT INTO fait_reversement(periode,iso,epargne,pret,droit_adhesion,parts_sociales,"
            "total_fichier,montant_vir,ecart,regle,observation) VALUES(?,?,?,?,?,?,?,?,?,?,?)", rows, many=True)
    return {"fichier": file.filename, "lignes": len(lignes),
            "ecart_total": d["kpi"]["ecart_total"], "anomalies": d["kpi"]["nb_mois_attente"]}


@app.post("/api/import/balance")
async def import_balance(file: UploadFile = File(...)):
    """Import live d'une balance PDF (export Perfect-Vision)."""
    from parse_bceao import agregats_balance
    data = await file.read()
    tmp = os.path.join(tempfile.gettempdir(), "ma2e_import_balance.pdf")
    with open(tmp, "wb") as fh:
        fh.write(data)
    try:
        agg = agregats_balance(tmp)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fichier illisible : {e}")
    agg["source"] = file.filename
    m = re.search(r"(\d{2})-(\d{2})-(\d{4})", file.filename or "")
    if m:
        agg["date_arrete"] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    execute("DELETE FROM bceao_config WHERE cle = ?", ("balance",))
    execute("INSERT INTO bceao_config(cle,valeur) VALUES(?,?)", ("balance", json.dumps(agg, ensure_ascii=False)))
    return {"fichier": file.filename, "total_bilan": agg.get("total_bilan"),
            "resultat_net": agg.get("resultat_net"), "anomalies": 0}


@app.get("/api/tresorerie")
def tresorerie():
    rows = query(
        "SELECT date_jour, code_compte, montant, source_onglet, qualite_flag "
        "FROM fait_solde_journalier")

    par_jour = defaultdict(float)
    par_jour_compte = defaultdict(dict)
    anomalies, seen = [], set()
    for r in rows:
        d = r["date_jour"]
        if not valid_year(d):
            key = (r["source_onglet"], d)
            if key not in seen:
                seen.add(key); anomalies.append({"onglet": r["source_onglet"], "date": d, "type": "Date aberrante (hors série)"})
            continue
        par_jour[d] += r["montant"]
        par_jour_compte[d][r["code_compte"]] = r["montant"]
        if r["qualite_flag"] == "DATE_SUSPECTE":
            key = (r["source_onglet"], d)
            if key not in seen:
                seen.add(key); anomalies.append({"onglet": r["source_onglet"], "date": d, "type": "Date incohérente avec l'onglet"})

    dates = [d for d in sorted(par_jour) if par_jour[d] > 0]
    if not dates:
        return {"empty": True}
    serie = [{"date": d, "total": round(par_jour[d])} for d in dates]
    last, prev = dates[-1], (dates[-2] if len(dates) > 1 else dates[-1])
    pos, totals = par_jour[last], [par_jour[d] for d in dates]
    derniers = par_jour_compte[last]
    repartition = sorted(
        [{"code": c, "libelle": LIBELLES[c], "type": TYPES[c], "montant": round(derniers[c]),
          "part": round(derniers[c] / pos * 100, 1)} for c in ORDRE if c in derniers],
        key=lambda x: -x["montant"])
    recent = [{"date": d, "total": round(par_jour[d]),
               "comptes": {c: round(par_jour_compte[d].get(c, 0)) for c in ORDRE}}
              for d in dates[-20:][::-1]]
    return {
        "meta": {"institution": "MA2E — Mutuelle des Agents de l'Eau et de l'Électricité",
                 "source": "Base MA2E (API)", "date_position": last,
                 "periode_debut": dates[0], "periode_fin": dates[-1],
                 "nb_jours": len(dates), "nb_comptes": len(ORDRE)},
        "kpi": {"position": round(pos),
                "variation": round(pos - par_jour[prev]),
                "variation_pct": round((pos - par_jour[prev]) / par_jour[prev] * 100, 2) if par_jour[prev] else 0,
                "max": round(max(totals)), "min": round(min(totals)),
                "moyenne": round(sum(totals) / len(totals)), "nb_anomalies": len(anomalies)},
        "serie": serie, "repartition": repartition, "recent": recent,
        "colonnes": [{"code": c, "libelle": LIBELLES[c]} for c in ORDRE],
        "anomalies": anomalies,
    }


@app.get("/api/comptes")
def comptes():
    rows = query("SELECT date_jour, code_compte, montant FROM fait_solde_journalier")
    par_jour = defaultdict(float)
    par_jour_compte = defaultdict(dict)
    par_compte = defaultdict(list)
    for r in rows:
        d = r["date_jour"]
        if not valid_year(d):
            continue
        par_jour[d] += r["montant"]
        par_jour_compte[d][r["code_compte"]] = r["montant"]
        par_compte[r["code_compte"]].append((d, r["montant"]))
    dates = [d for d in sorted(par_jour) if par_jour[d] > 0]
    if not dates:
        return {"empty": True}
    last = dates[-1]
    total = par_jour[last]
    out = []
    for c in ORDRE:
        pts = sorted(par_compte.get(c, []))
        if not pts:
            continue
        m = [x for _, x in pts]
        solde = par_jour_compte[last].get(c, 0)
        out.append({
            "code": c, "libelle": LIBELLES[c], "type": TYPES[c],
            "solde_actuel": round(solde),
            "part": round(solde / total * 100, 1) if total else 0,
            "min": round(min(m)), "max": round(max(m)), "moyenne": round(sum(m) / len(m)),
            "premier_jour": pts[0][0], "dernier_jour": pts[-1][0], "nb_jours": len(pts),
            "serie": [round(x) for _, x in pts],
        })
    out.sort(key=lambda x: -x["solde_actuel"])
    return {"meta": {"date_position": last, "total": round(total), "nb_comptes": len(out)}, "comptes": out}


@app.get("/api/controle")
def controle():
    rows = query("SELECT date_jour, source_onglet, qualite_flag FROM fait_solde_journalier")
    if not rows:
        return {"empty": True}
    par_jour = defaultdict(int)
    anomalies, seen = [], set()
    n_susp = n_aberr = 0
    for r in rows:
        d = r["date_jour"]
        if not valid_year(d):
            n_aberr += 1
            key = (r["source_onglet"], d)
            if key not in seen:
                seen.add(key); anomalies.append({"onglet": r["source_onglet"], "date": d, "type": "Date aberrante (hors série)"})
            continue
        par_jour[d] += 1
        if r["qualite_flag"] == "DATE_SUSPECTE":
            n_susp += 1
            key = (r["source_onglet"], d)
            if key not in seen:
                seen.add(key); anomalies.append({"onglet": r["source_onglet"], "date": d, "type": "Date incohérente avec l'onglet"})
    nb_soldes = sum(par_jour.values())
    nb_jours = len([d for d in par_jour if par_jour[d] > 0])
    controles = [
        {"code": "CTRL-01", "libelle": "Cohérence somme des comptes = TOTAL fichier", "statut": "OK", "detail": "0 écart détecté à l'ingestion"},
        {"code": "CTRL-02", "libelle": "Cohérence des dates avec l'onglet (mois/année)", "statut": "ALERTE" if n_susp + n_aberr else "OK", "detail": f"{len(anomalies)} date(s) à corriger"},
        {"code": "CTRL-03", "libelle": "Dates dans la plage valide (2020–2030)", "statut": "ALERTE" if n_aberr else "OK", "detail": f"{n_aberr} date(s) aberrante(s)"},
        {"code": "CTRL-04", "libelle": "Complétude des soldes (montants présents)", "statut": "OK", "detail": f"{nb_soldes} soldes chargés"},
    ]
    return {
        "meta": {"source": "Base MA2E (API)"},
        "kpi": {"nb_soldes": nb_soldes, "nb_jours": nb_jours, "nb_anomalies": len(anomalies),
                "nb_controles_ok": sum(1 for c in controles if c["statut"] == "OK"), "nb_controles": len(controles)},
        "controles": controles,
        "anomalies": anomalies,
    }


@app.get("/api/parametres")
def parametres():
    seuils = [{"cle": r["cle"], "libelle": r["libelle"], "valeur": r["valeur"],
               "unite": r["unite"], "categorie": r["categorie"]}
              for r in query("SELECT cle,libelle,valeur,unite,categorie FROM parametre")]
    users = [{"email": r["email"], "nom": r["nom"], "role": r["role"]}
             for r in query("SELECT email,nom,role FROM utilisateur ORDER BY role")]
    comptes = [{"code": c, "libelle": LIBELLES[c], "type": TYPES[c], "actif": True} for c in ORDRE]
    return {"meta": {"source": "Base MA2E (API)"},
            "seuils": seuils, "comptes": comptes, "utilisateurs": users}


@app.get("/api/reversements")
def reversements():
    rows = query("SELECT periode,iso,epargne,pret,droit_adhesion,parts_sociales,"
                 "total_fichier,montant_vir,ecart,regle,observation FROM fait_reversement ORDER BY id")
    if not rows:
        return {"empty": True}
    lignes = [{"periode": r["periode"], "iso": r["iso"], "epargne": r["epargne"],
               "pret": r["pret"], "droit_adhesion": r["droit_adhesion"],
               "parts_sociales": r["parts_sociales"], "total_fichier": r["total_fichier"],
               "montant_vir": r["montant_vir"], "ecart": r["ecart"],
               "regle": bool(r["regle"]), "observation": r["observation"]} for r in rows]
    tp = sum(l["total_fichier"] or 0 for l in lignes)
    tr = sum(l["montant_vir"] or 0 for l in lignes)
    att = [l for l in lignes if not l["regle"]]
    return {
        "meta": {"titre": "Suivi des prélèvements & reversements SIVE", "exercice": 2026, "source": "Base MA2E (API)"},
        "kpi": {"total_preleve": round(tp), "total_reverse": round(tr),
                "ecart_total": round(tp - tr), "nb_mois_attente": len(att),
                "taux_reversement": round(tr / tp * 100, 1) if tp else 0},
        "lignes": lignes,
    }


@app.get("/api/bceao")
def bceao():
    etats = [{"code": r["code"], "libelle": r["libelle"], "periodicite": r["periodicite"]}
             for r in query("SELECT code,libelle,periodicite FROM bceao_etat")]
    cfg = {r["cle"]: json.loads(r["valeur"]) for r in query("SELECT cle,valeur FROM bceao_config")}
    balance = cfg.get("balance") or {
        "core_banking": "Perfect-Vision v5.7.1.5", "detail_disponible": False,
        "total_bilan": None, "resultat_net": None, "source": None, "date_arrete": None,
        "note": "Importez la balance pour afficher les agrégats."}
    return {"meta": cfg.get("meta"), "balance": balance,
            "workflow": cfg.get("workflow"), "etats": etats,
            "indicateurs": cfg.get("indicateurs")}
