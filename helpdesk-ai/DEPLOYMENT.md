# DEPLOYMENT.md — Déploiement & infrastructure

> **Phase 11 — complétée (2026-07-04).** Source de vérité : [PLAN.md](PLAN.md). Décisions :
> [DECISIONS.md](DECISIONS.md). Dernière mise à jour : **2026-07-04**.

---

## 1. Topologie cible (PFE)

```mermaid
flowchart LR
  subgraph docker-compose
    front["frontend :8081→80\nAngular / Nginx"]
    api["api :8000\nFastAPI / uvicorn"]
    dash["dashboard :8501\nStreamlit"]
    pg[(PostgreSQL)]
    chroma[(ChromaDB vol)]
  end

  Navigateur -->|HTTP :8081| front
  Navigateur -->|HTTP :8000| api
  front --> api
  dash --> api
  api --> pg
  api --> chroma
```

> **Port hôte 8081 (pas 80)** : sur Windows, le port 80 est souvent réservé (plage
> d'exclusion Hyper-V/WSL2 ou service système type IIS). 8081 évite ce conflit.

> **Pas de Kubernetes** (ADR-005 — hors périmètre PFE). `docker compose` suffit pour la démo
> et la soutenance.

---

## 2. Services & ports

| Service | Port | Image | Description |
|---|---|---|---|
| `api` | **8000** | `helpdesk-api:latest` | FastAPI + uvicorn (2 workers) |
| `frontend` | **8081** → 80 | `helpdesk-front:latest` | Angular build → Nginx |
| `dashboard` | **8501** | `helpdesk-dashboard:latest` | Streamlit |

---

## 3. Démarrage rapide

### Prérequis
- Docker Desktop ≥ 24 (ou Docker Engine + Compose v2)
- 4 Go RAM libres (sentence-transformers + FAISS chargés en mémoire)
- Premier build : téléchargement du modèle `paraphrase-multilingual-mpnet-base-v2` (~420 Mo)

### Étapes

```bash
# 1. Cloner et se placer dans le répertoire
cd helpdesk-ai

# 2. Créer le fichier d'environnement
cp .env.example .env
# Éditer .env : renseigner SECRET_KEY, ADMIN_EMAILS, INGEST_API_KEY

# 3. Lancer tous les services
docker compose -f docker/docker-compose.yml up --build

# Accès :
#   Frontend  → http://localhost:8081
#   API Swagger → http://localhost:8000/docs
#   Dashboard → http://localhost:8501
```

### Commandes utiles

```bash
# Démarrage en arrière-plan
docker compose -f docker/docker-compose.yml up -d --build

# Logs d'un service
docker compose -f docker/docker-compose.yml logs -f api

# Arrêt (avec suppression des conteneurs)
docker compose -f docker/docker-compose.yml down

# Arrêt + suppression des volumes (PostgreSQL + ChromaDB)
docker compose -f docker/docker-compose.yml down -v

# Rebuild forcé d'un seul service
docker compose -f docker/docker-compose.yml build api
docker compose -f docker/docker-compose.yml up -d api
```

---

## 4. Fichiers Docker

| Fichier | Rôle |
|---|---|
| `docker/Dockerfile.api` | Image API FastAPI (python:3.11-slim, NLTK + ST pré-téléchargés) |
| `docker/Dockerfile.front` | Image Angular multi-stage (node:20 build → nginx:1.27 serve) |
| `docker/Dockerfile.dashboard` | Image Streamlit (python:3.11-slim) |
| `docker/docker-compose.yml` | Orchestration multi-services + volumes PostgreSQL/ChromaDB + réseau interne |
| `docker/requirements-api.txt` | Dépendances Python runtime uniquement (sans dvc/mlflow/jupyter) |
| `docker/nginx.conf` | Config Nginx : SPA routing + cache assets + headers sécurité |
| `.dockerignore` | Exclut node_modules, venv, mlruns, camembert_lora (~2 Go) du contexte |

---

## 5. Variables d'environnement

Toutes les variables sont dans `.env` (copier depuis `.env.example`) :

| Variable | Description | Défaut |
|---|---|---|
| `SECRET_KEY` | Clé JWT (min 32 chars) | *(à changer)* |
| `ALGORITHM` | Algorithme JWT | `HS256` |
| `TOKEN_EXPIRE_MIN` | Durée token (minutes) | `480` |
| `DB_URL` | URL SQLAlchemy | `postgresql+psycopg2://helpdesk:helpdesk@postgres:5432/helpdesk` |
| `CONFIDENCE_THRESHOLD` | Seuil auto-routage | `0.40` |
| `ADMIN_EMAILS` | Emails admins (virgule) | — |
| `CORS_ORIGINS` | Origines CORS (virgule) | `http://localhost:8081,http://localhost:4200` |
| `INGEST_API_KEY` | Clé API `/ingest` | *(à changer)* |

---

## 6. Volumes & persistance

| Volume | Point de montage | Contenu |
|---|---|---|
| `api-data` | `/app/data` | Base de connaissances vectorielle ChromaDB `chroma/` (persistée entre redémarrages) |
| `postgres-data` | `/var/lib/postgresql/data` | Base opérationnelle PostgreSQL (utilisateurs, tickets, historique) |

Les modèles ML/RAG (`models/`) sont intégrés dans l'image API pour la démo. Pour mettre à jour
un modèle sans rebuild : monter `models/` en volume override dans `docker-compose.yml`.

---

## 7. CI/CD — GitHub Actions

Workflow : `.github/workflows/ci.yml`

| Job | Déclencheur | Étapes |
|---|---|---|
| `python-ci` | Push / PR | ruff lint + pytest (tests unitaires) |
| `angular-ci` | Push / PR | npm ci + ng build (production) |
| `docker-build` | Après python-ci + angular-ci | docker build API + docker build Frontend |

Les jobs `docker-build` ne publient pas d'image en registry (pas de DockerHub configuré). Pour
activer la publication : ajouter `docker/login-action` + `docker/build-push-action` dans le workflow.

---

## 8. Sécurité (minimal pour la démo PFE)

- **Secrets** : `SECRET_KEY` et `INGEST_API_KEY` dans `.env` (jamais committé).
- **CORS** : restreint aux origines listées dans `CORS_ORIGINS`.
- **Rate limiting** : login limité (FastAPI middleware) — voir `api/middleware/auth_middleware.py`.
- **Headers** : `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` via Nginx.
- **À faire (hors PFE)** : HTTPS/TLS, secrets manager, scan d'image (Trivy).

---

## 9. Observabilité minimale

- **Health check API** : `GET /api/v1/health` → `{"status": "ok", "model_loaded": true}`
- **Logs** : stdout/stderr collectés par Docker, consultables via `docker compose logs`
- **Métriques modèle** : `metrics/ml_eval.json` (DVC) et `mlruns/` (MLflow UI)
- **À faire (hors PFE)** : Prometheus + Grafana, alerting sur drift confiance.
