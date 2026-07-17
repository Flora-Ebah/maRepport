"""
MA2E — Pilote Trésorerie
Génère un dashboard HTML autonome à partir de soldes_journaliers.csv.

Aucune dépendance externe à installer, aucun serveur : le fichier HTML
s'ouvre directement dans un navigateur. Sert de démonstration de valeur
avant l'industrialisation (FastAPI + PostgreSQL).

Usage : python generate_dashboard.py
"""
from __future__ import annotations
import os, csv, json, datetime as dt
from collections import defaultdict

try:
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "..", "output", "soldes_journaliers.csv")
HTML_PATH = os.path.join(HERE, "..", "output", "dashboard_tresorerie.html")

LIBELLES = {
    "ECOBANK": "Ecobank", "ORABANK": "Orabank", "BOA-CI": "BOA-CI",
    "UBA": "UBA", "JULAYA": "Julaya", "CAISSE_DEPENSES": "Caisse Dépenses",
    "CAISSE_RECETTE": "Caisse Recette", "COFFRE_FORT": "Coffre-fort",
}


def fmt_fcfa(n):
    return f"{n:,.0f}".replace(",", " ") + " F"


def main():
    par_jour = defaultdict(float)                 # date -> total
    par_jour_compte = defaultdict(dict)           # date -> {compte: montant}
    nb_anomalies = 0
    comptes = set()

    with open(CSV_PATH, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            d = row["date_jour"]
            # on écarte les dates aberrantes (typos année) des graphiques
            try:
                an = int(d[:4])
            except ValueError:
                continue
            if an < 2020 or an > 2030:
                nb_anomalies += 1
                continue
            if row["qualite_flag"] != "OK":
                nb_anomalies += 1
            montant = float(row["montant"])
            par_jour[d] += montant
            par_jour_compte[d][row["code_compte"]] = montant
            comptes.add(row["code_compte"])

    # jours sans saisie réelle (total nul) = exclus de la série
    dates = [d for d in sorted(par_jour) if par_jour[d] > 0]
    serie_totale = [round(par_jour[d]) for d in dates]

    # Dernière position connue par compte
    derniere_date = dates[-1]
    derniers = par_jour_compte[derniere_date]
    position_actuelle = sum(derniers.values())

    # Variation vs jour précédent disponible
    prev_total = par_jour[dates[-2]] if len(dates) > 1 else position_actuelle
    variation = position_actuelle - prev_total
    var_pct = (variation / prev_total * 100) if prev_total else 0

    # Min / max / moyenne sur la période
    pos_min = min(serie_totale)
    pos_max = max(serie_totale)
    pos_moy = sum(serie_totale) / len(serie_totale)

    # Répartition actuelle par compte (pour le donut)
    repartition = sorted(derniers.items(), key=lambda kv: -kv[1])

    data = {
        "dates": dates,
        "serie_totale": serie_totale,
        "repartition_labels": [LIBELLES.get(c, c) for c, _ in repartition],
        "repartition_values": [round(v) for _, v in repartition],
    }

    kpi = {
        "position": fmt_fcfa(position_actuelle),
        "date": derniere_date,
        "variation": ("+" if variation >= 0 else "") + fmt_fcfa(variation),
        "var_pct": f"{var_pct:+.2f} %",
        "var_pos": variation >= 0,
        "max": fmt_fcfa(pos_max),
        "min": fmt_fcfa(pos_min),
        "moy": fmt_fcfa(pos_moy),
        "nb_jours": len(dates),
        "periode": f"{dates[0]} → {dates[-1]}",
        "nb_anomalies": nb_anomalies,
        "nb_comptes": len(comptes),
    }

    rows_rep = "".join(
        f"<tr><td>{LIBELLES.get(c,c)}</td><td class='num'>{fmt_fcfa(v)}</td>"
        f"<td class='num'>{v/position_actuelle*100:.1f} %</td></tr>"
        for c, v in repartition)

    html = HTML_TEMPLATE.replace("__DATA__", json.dumps(data)) \
                        .replace("__KPI__", json.dumps(kpi)) \
                        .replace("__ROWS_REP__", rows_rep) \
                        .replace("__POSITION__", kpi["position"]) \
                        .replace("__DATE__", kpi["date"]) \
                        .replace("__VARIATION__", kpi["variation"]) \
                        .replace("__VARPCT__", kpi["var_pct"]) \
                        .replace("__VARCLASS__", "up" if kpi["var_pos"] else "down") \
                        .replace("__MAXP__", kpi["max"]) \
                        .replace("__MINP__", kpi["min"]) \
                        .replace("__MOYP__", kpi["moy"]) \
                        .replace("__NBJOURS__", str(kpi["nb_jours"])) \
                        .replace("__PERIODE__", kpi["periode"]) \
                        .replace("__NBANO__", str(kpi["nb_anomalies"])) \
                        .replace("__NBCOMPTES__", str(kpi["nb_comptes"]))

    with open(HTML_PATH, "w", encoding="utf-8") as fh:
        fh.write(html)

    print("DASHBOARD GÉNÉRÉ")
    print(f"  Position au {kpi['date']} : {kpi['position']}")
    print(f"  Variation veille         : {kpi['variation']} ({kpi['var_pct']})")
    print(f"  Période                  : {kpi['periode']} ({kpi['nb_jours']} jours)")
    print(f"  Max / Min / Moy          : {kpi['max']} / {kpi['min']} / {kpi['moy']}")
    print(f"  -> {os.path.abspath(HTML_PATH)}")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>MA2E — Point de Trésorerie</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root{--bg:#0f172a;--card:#1e293b;--ink:#e2e8f0;--mut:#94a3b8;--acc:#38bdf8;--up:#34d399;--down:#f87171;--brd:#334155;}
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--ink);font-family:system-ui,Segoe UI,Roboto,sans-serif;padding:24px;}
  header{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px;margin-bottom:20px}
  h1{font-size:20px;font-weight:700}h1 small{color:var(--mut);font-weight:400;font-size:13px}
  .sub{color:var(--mut);font-size:13px}
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin-bottom:18px}
  .card{background:var(--card);border:1px solid var(--brd);border-radius:14px;padding:16px}
  .card .lbl{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
  .card .val{font-size:22px;font-weight:700;margin-top:6px}
  .card .val.small{font-size:17px}
  .up{color:var(--up)}.down{color:var(--down)}
  .charts{display:grid;grid-template-columns:2fr 1fr;gap:14px;margin-bottom:18px}
  @media(max-width:820px){.charts{grid-template-columns:1fr}}
  .chartbox{background:var(--card);border:1px solid var(--brd);border-radius:14px;padding:16px}
  .chartbox h2{font-size:14px;margin-bottom:10px;font-weight:600}
  table{width:100%;border-collapse:collapse;font-size:14px}
  th,td{padding:9px 10px;border-bottom:1px solid var(--brd);text-align:left}
  th{color:var(--mut);font-weight:500;font-size:12px;text-transform:uppercase}
  td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
  footer{color:var(--mut);font-size:12px;margin-top:18px;border-top:1px solid var(--brd);padding-top:12px}
  .pill{display:inline-block;background:#422006;color:#fbbf24;border:1px solid #854d0e;border-radius:999px;padding:2px 10px;font-size:12px}
</style></head><body>

<header>
  <div><h1>MA2E — Point de Trésorerie <small>Mutuelle des Agents de l'Eau et de l'Électricité</small></h1>
  <div class="sub">Position consolidée au <b>__DATE__</b> · source : POINT RETRAIT (ingestion automatisée)</div></div>
  <span class="pill">⚠ __NBANO__ anomalies de saisie détectées</span>
</header>

<div class="grid">
  <div class="card"><div class="lbl">Position consolidée</div><div class="val">__POSITION__</div></div>
  <div class="card"><div class="lbl">Variation / veille</div><div class="val __VARCLASS__">__VARIATION__ <span style="font-size:14px">(__VARPCT__)</span></div></div>
  <div class="card"><div class="lbl">Pic max période</div><div class="val small">__MAXP__</div></div>
  <div class="card"><div class="lbl">Plancher min période</div><div class="val small">__MINP__</div></div>
  <div class="card"><div class="lbl">Moyenne période</div><div class="val small">__MOYP__</div></div>
  <div class="card"><div class="lbl">Profondeur historique</div><div class="val small">__NBJOURS__ jours</div><div class="sub">__PERIODE__</div></div>
</div>

<div class="charts">
  <div class="chartbox"><h2>Évolution de la trésorerie consolidée</h2><canvas id="ligne" height="120"></canvas></div>
  <div class="chartbox"><h2>Répartition actuelle par compte</h2><canvas id="donut" height="120"></canvas></div>
</div>

<div class="chartbox">
  <h2>Détail des positions au __DATE__</h2>
  <table><thead><tr><th>Compte</th><th class="num">Solde</th><th class="num">Part</th></tr></thead>
  <tbody>__ROWS_REP__</tbody></table>
</div>

<footer>Dashboard généré automatiquement depuis les données existantes — pilote MA2E.
Démonstration : aucune ressaisie, aucune consolidation manuelle. Données fraîches dès l'ingestion.</footer>

<script>
const DATA = __DATA__;
const palette = ['#38bdf8','#34d399','#fbbf24','#f87171','#a78bfa','#fb923c','#22d3ee','#e879f9'];
const fF = v => (v/1e6).toLocaleString('fr-FR',{maximumFractionDigits:0})+' M';

new Chart(document.getElementById('ligne'), {
  type:'line',
  data:{labels:DATA.dates, datasets:[{data:DATA.serie_totale, borderColor:'#38bdf8',
    backgroundColor:'rgba(56,189,248,.12)', fill:true, pointRadius:0, borderWidth:2, tension:.25}]},
  options:{plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>fF(c.parsed.y)+' FCFA'}}},
    scales:{x:{ticks:{color:'#94a3b8',maxTicksLimit:12},grid:{display:false}},
            y:{ticks:{color:'#94a3b8',callback:fF},grid:{color:'#334155'}}}}
});

new Chart(document.getElementById('donut'), {
  type:'doughnut',
  data:{labels:DATA.repartition_labels, datasets:[{data:DATA.repartition_values, backgroundColor:palette, borderColor:'#1e293b', borderWidth:2}]},
  options:{plugins:{legend:{position:'bottom',labels:{color:'#94a3b8',boxWidth:12,font:{size:11}}},
    tooltip:{callbacks:{label:c=>c.label+': '+fF(c.parsed)+' FCFA'}}}}
});
</script>
</body></html>"""

if __name__ == "__main__":
    main()
