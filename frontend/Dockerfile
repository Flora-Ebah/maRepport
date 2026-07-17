# Frontend Next.js — MA2E Trésorerie
# Contexte de build : frontend/
FROM node:20-slim

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# URL publique de l'API, injectée dans le bundle client au build.
# En local : http://localhost:8000. En prod : l'adresse publique du backend.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
