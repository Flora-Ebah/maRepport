# Déploiement — MA2E Pilote Trésorerie

Frontend (Next.js) + Backend (FastAPI) déployés **ensemble** via Docker Compose.
Base **SQLite** par défaut (aucun service de base à gérer). L'application démarre
**vide** : les données s'enrichissent uniquement à l'import.

## Prérequis
- Docker + Docker Compose sur le serveur.

## Déploiement local (test)
```bash
docker compose up --build
```
- Frontend : http://localhost:3000
- Backend  : http://localhost:8000
- Connexion : `dg@ma2e.ci` / `demo`

## Déploiement sur un serveur (accessible en ligne)
Le frontend appelle le backend **depuis le navigateur** : il faut donc lui donner
l'**URL publique** du backend au build.

```bash
# Remplacer par l'IP ou le domaine public du serveur
NEXT_PUBLIC_API_URL=http://mon-serveur.exemple:8000 docker compose up --build -d
```

Puis exposer les ports 3000 (frontend) et 8000 (backend) — idéalement derrière un
reverse-proxy HTTPS (Nginx / Caddy / Traefik).

## Comptes de démonstration (mot de passe : `demo`)
| E-mail | Rôle |
|---|---|
| dg@ma2e.ci | Directeur Général (accès complet) |
| dagf@ma2e.ci | DAGF |
| treso@ma2e.ci | Trésorier |
| ci@ma2e.ci | Contrôle Interne |

## Persistance des données
Par défaut, les données importées vivent le temps du conteneur backend. Pour les
**conserver** entre redémarrages, monter un volume sur `backend/ma2e.db` (à ajouter
dans `docker-compose.yml`), ou passer sur **PostgreSQL** (`MA2E_DB=postgres` + variables `PG*`).

## Sécurité / production (à faire avant un vrai déploiement)
- Mettre le dépôt Git en **privé** (données sensibles).
- Remplacer l'auth de démo par **Keycloak SSO + MFA** (cf. CDC).
- Cookie de session **httpOnly**, HTTPS obligatoire.
- Changer les mots de passe de démonstration.

> ⚠️ Ces fichiers Docker sont fournis prêts à l'emploi mais **n'ont pas été testés
> à l'exécution** dans l'environnement de développement (Docker indisponible au moment
> de leur écriture). À valider au premier `docker compose up --build`.
