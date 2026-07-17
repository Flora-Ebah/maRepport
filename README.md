# MA2E — Pilote Trésorerie & Reporting

Pilote de digitalisation du **Point de Trésorerie**, des **rapprochements** et du
**reporting BCEAO** de la mutuelle MA2E (microfinance, zone UEMOA / BCEAO).

> **Stratégie** : quick-win sur les données Excel/PDF existantes, stack légère,
> sans dépendance à l'API Perfect-Vision (à intégrer en phase 2).

## Architecture (full-stack)
```
Frontend  Next.js 14 + React + Tailwind   (3 écrans, design bancaire carré)
   │  fetch (mode dégradé : repli sur données embarquées si API KO)
API       FastAPI                          (/api/tresorerie, /reversements, /bceao)
   │
Données   SQLite (ma2e.db)                 (cible production : PostgreSQL — db/schema.sql)
   ▲
Ingestion Scripts Python                   (parsing Excel/PDF existants + contrôle qualité)
```

## Structure
```
ma2e-pilote/
├── db/schema.sql                 # modèle canonique (cible PostgreSQL)
├── ingestion/                    # parsers (Trésorerie, SIVE, BCEAO) + dashboards
│   ├── parse_tresorerie.py       #   POINT RETRAIT → soldes propres + qualité
│   ├── parse_sive.py             #   POINT SIVE → écarts de reversement
│   ├── parse_bceao.py            #   SICSSFD + BALANCE → catalogue BCEAO
│   ├── generate_frontend_data.py #   → JSON embarqués (fallback)
│   └── generate_dashboard.py     #   dashboard HTML autonome
├── backend/                      # API
│   ├── load_db.py                #   construit ma2e.db depuis les données ingérées
│   ├── main.py                   #   FastAPI (3 endpoints)
│   └── requirements.txt
├── frontend/                     # application Next.js
│   ├── app/                      #   /, /reversements, /reporting-bceao, /copil.html
│   └── src/                      #   components, lib/api.ts, data (fallback)
├── docs/                         # Note de décision (Word) + deck COPIL (HTML)
└── output/                       # soldes_journaliers.csv + rapport_qualite.txt
```

## Lancer le système complet

**1. Ingestion (génère données + base)**
```bash
cd ingestion && pip install -r requirements.txt
python parse_tresorerie.py "../../POINT RETRAIT AU 12-06_2026.xlsx"
python parse_sive.py
python parse_bceao.py
python generate_frontend_data.py
cd ../backend && python load_db.py        # construit ma2e.db
```

**2. Backend API** (port 8000)
```bash
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**3. Frontend** (port 3000)
```bash
cd frontend && npm install && npm run dev
```

### Option : exécuter sur PostgreSQL (cible production)
```bash
docker compose up -d                 # Postgres sur le port 5435
cd backend && python load_pg.py      # charge les mêmes données dans Postgres
MA2E_DB=postgres uvicorn main:app --port 8000   # bascule l'API sur Postgres
```
L'API est **agnostique** : SQLite par défaut, PostgreSQL si `MA2E_DB=postgres`.
`GET /api/health` renvoie le moteur actif. Aucune autre modification requise.
→ http://localhost:3000 · badge « API en direct » si le backend répond, sinon « Mode dégradé ».

### Connexion (comptes de démonstration · mot de passe : `demo`)
| E-mail | Rôle | Accès |
|---|---|---|
| dg@ma2e.ci | Directeur Général | tous les écrans |
| dagf@ma2e.ci | DAGF | tous les écrans |
| treso@ma2e.ci | Trésorier | Trésorerie, Comptes, Rapprochements |
| ci@ma2e.ci | Contrôle Interne | Reporting BCEAO, Anomalies, Rapprochements |

> Pilote : auth applicative + RBAC. En production : Keycloak SSO + MFA, cookie httpOnly, vérification du jeton côté API.

## État d'avancement
- [x] Parsers d'ingestion + contrôle qualité (5 906 soldes, 13 anomalies détectées)
- [x] Base SQLite + API FastAPI (3 endpoints) — **données réelles**
- [x] Frontend Next.js : Point de Trésorerie, Rapprochements, Reporting BCEAO
- [x] Mode dégradé (repli automatique sur données embarquées)
- [x] Dossier décision : Note Word + deck COPIL
- [ ] Parser BCEAO chiffré (nécessite export Excel/CSV de la balance ou API Perfect-Vision)
- [ ] Connecteurs Perfect-Vision (conditionné au Sprint 0 / convention CAGECFI)
- [ ] Migration SQLite → PostgreSQL (production)
```
