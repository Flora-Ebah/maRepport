# Backend FastAPI — MA2E Trésorerie
# Contexte de build : la racine du projet (ma2e-pilote/)
FROM python:3.12-slim

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY ingestion/ ingestion/
# bceao.json fournit le catalogue BCEAO + les normes (référentiel) pour l'init
COPY frontend/src/data/bceao.json frontend/src/data/bceao.json

WORKDIR /app/backend
EXPOSE 8000
# Initialise la base (référentiels, données vides) puis démarre l'API
CMD ["sh", "-c", "python init_db.py && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
