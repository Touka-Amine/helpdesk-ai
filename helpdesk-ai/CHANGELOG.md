# CHANGELOG.md — Historique des modifications

> Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/). Types : `Ajouté`,
> `Modifié`, `Corrigé`, `Supprimé`, `Sécurité`, `Déprécié`. Source de vérité : [PLAN.md](PLAN.md).

## [Non publié] — branche `chore/gouvernance-pfe`

### Phase 12 — Nettoyage : doublon `HelpDesk1.csv` à la racine (2026-07-05)

- `Supprimé` : `helpdesk-ai/HelpDesk1.csv` — copie non suivie par git, identique octet pour octet
  à `data/raw/HelpDesk1.csv` (donnée gérée par DVC, `data/raw/*` gitignoré). Dette technique
  notée depuis la Phase 0, traitée par anticipation plutôt qu'en Phase 2 : rien ne pointait sur
  cette copie en priorité (`notebooks/data_quality_report.py` teste `data/raw/` en premier).

---

### Phase 12 — Authentification cassée en Docker : incompatibilité bcrypt/passlib (2026-07-05)

Test manuel de connexion client dans le navigateur (`http://localhost:8081`) → échec avec
les identifiants seed documentés. Logs du conteneur API :
`AttributeError: module 'bcrypt' has no attribute '__about__'`.

- `Corrigé` : `requirements.txt` et `docker/requirements-api.txt` — épinglé `bcrypt==4.0.1`.
  `passlib==1.7.4` (dernière release, non maintenue depuis 2020) lit
  `bcrypt.__about__.__version__` pour détecter la version du backend ; cet attribut a été
  retiré à partir de `bcrypt>=4.1`. Sans ce pin, `passlib[bcrypt]>=1.7.4` installe la
  dernière version de `bcrypt` (5.0.0 constaté), rendant **tout hachage de mot de passe
  défaillant** : `_seed_users()` échouait silencieusement à chaque démarrage du conteneur
  (aucun compte démo/admin/système jamais créé en base), et l'inscription via `/auth/register`
  aurait échoué de la même façon pour tout nouvel utilisateur.
- `Résolu` : dette technique documentée de longue date (4 tests d'authentification skippés
  dans `test_api_integration.py` faute de bcrypt fonctionnel dans l'environnement de test).
  **18/18 tests passent désormais** (contre 14/18 + 4 skip auparavant).

---

### Phase 12 — Test de charge : critère P95 non atteint, cause identifiée (2026-07-05)

- `Ajouté` : `scripts/load_test.py` — outil de test de charge autonome (requêtes concurrentes
  via `ThreadPoolExecutor`, mesure P50/P95/P99, comparaison au critère PFE ≤300ms).
- `Ajouté` : `metrics/load_test.json` — résultats de 3 scénarios (concurrence 1/5/20) contre
  l'API Docker réelle. **Critère P95≤300ms non atteint** dans les 3 cas : 330ms (séquentiel,
  proche) → 1068ms (concurrence 5) → 15022ms + 19% timeouts (concurrence 20). Cause
  identifiée : endpoint `POST /api/v1/predict` synchrone (`def`, pas `async def`) et
  CPU-bound (encodage sentence-transformers + `predict_proba` sklearn + recherche FAISS),
  limité par le GIL Python et seulement 2 workers uvicorn (`Dockerfile.api`). Optimisation
  (workers, pipeline d'inférence) renvoyée à la Phase 13, conformément à son périmètre.
- `Corrigé` : `docker/Dockerfile.front` — healthcheck utilisait `wget http://localhost/`,
  qui résout en `::1` (IPv6) dans le conteneur ; Nginx n'écoute qu'en IPv4 (`0.0.0.0:80`),
  causant un échec systématique (`Connection refused`) et un statut "unhealthy" permanent
  malgré un frontend fonctionnel. Remplacé par `http://127.0.0.1/`.
- `Ajouté` : `requests>=2.31.0` dans `requirements.txt` — dépendance directe de
  `scripts/load_test.py` (auparavant disponible seulement de façon transitive).

---

### Phase 12 — Test bout-en-bout Docker : 3 bugs de déploiement corrigés (2026-07-05)

Premier lancement réel de `docker compose up --build` en conditions de connexion lente —
a révélé des bugs invisibles en développement local (venv Windows).

#### Bug 1 — RAG sémantique en fallback silencieux (dépendance manquante)
- `Corrigé` : `docker/requirements-api.txt` — ajout de `pyarrow>=14.0.0`, requis par
  `pandas.read_parquet()` dans `SemanticRAGEngine.load()`. Absent de l'image API car
  installé seulement de façon transitive (via `streamlit`/`mlflow`) dans le venv de
  développement, jamais déclaré explicitement.
- `Corrigé` : `requirements.txt` — même ajout, pour ne pas dépendre d'une installation
  transitive fragile en dehors de Docker.

#### Bug 2 — Port 80 réservé par Windows
- `Modifié` : `docker/docker-compose.yml` — le service `frontend` est remappé sur le port
  hôte `8081` (`8081:80`) au lieu de `80:80`. Le port 80 est dans la plage d'exclusion
  Hyper-V/WSL2 de Windows et/ou occupé par un service système (HTTP.sys), rendant le bind
  impossible (`Ports are not available`).
- `Modifié` : `CORS_ORIGINS` (docker-compose.yml) et `DEPLOYMENT.md` mis à jour en conséquence.

#### Bug 3 — Noms de fichiers FAISS corrompus (mojibake Windows→Linux)
- `Corrigé` : `src/rag/semantic_engine.py::save()` — les noms de fichiers d'index FAISS par
  catégorie accentuée (ex. `index_cat_Réseau.faiss`) étaient mal encodés par l'API C++ de
  FAISS sous Windows, produisant des fichiers physiques nommés en mojibake
  (`index_cat_RÃ©seau.faiss`) alors que `metadata.json` référence le nom propre. Ce bug
  était invisible en développement (écriture et lecture symétriquement corrompues sur la
  même machine Windows) mais cassait totalement le chargement du RAG sémantique une fois
  le dépôt cloné sous Linux (Docker) : `FileIOReader ... No such file or directory`, avec
  fallback silencieux vers le RAG lexical. Fix : translittération ASCII via `unidecode()`
  avant construction du nom de fichier — le nom de catégorie affiché (accentué) reste
  inchangé partout ailleurs (metadata, logique applicative).
- `Ajouté` : `src/pipeline/rag_semantic_build.py` — script de reconstruction du RAG
  sémantique (miroir de `rag_build.py` pour le lexical), documenté comme processus manuel
  (hors `dvc.yaml`, nécessite le modèle sentence-transformers).
- `Corrigé` : artefacts `models/semantic_rag/` régénérés à partir des **1357 tickets**
  actuels de `data/splits/rag.csv` (les anciens artefacts dataient d'avant la Phase 10 et
  ne couvraient que 476 tickets — désynchronisés du RAG lexical).

#### Validation
- `docker compose up` (3 services) → tous healthy ; `GET /api/v1/health` → `rag_loaded: true` ;
  `POST /api/v1/predict` → RAG **hybride** actif (1357 tickets, alpha=0.5) ; frontend et
  dashboard répondent 200.

---

### Phase 12 — Tests & validation (2026-07-04)

#### Tests unitaires (41 nouveaux tests)
- `Ajouté` : `tests/test_heuristics.py` — 8 tests : FORCE_RULES (override, no-op si déjà
  correct, limites de mots avec `\b`), SOFT_RULES (seuil de confiance), plancher de
  confiance à 0.80.
- `Ajouté` : `tests/test_rag_engine.py` — 8 tests : recommandation avant `fit()`, requête
  vide, correspondance exacte, filtre catégorie, seuil + fallback, déduplication des
  résolutions identiques (base de connaissance en mémoire, scores TF-IDF vérifiés).
- `Ajouté` : `tests/test_hybrid_engine.py` — 9 tests : validation `alpha`, fusion de
  scores (`0.5×sém + 0.5×lex`), limite `top_k`, sauvegarde/restauration de l'état des
  sous-moteurs partagés (régression du Bug 1 de Phase 13), fallback hybride. Sous-moteurs
  remplacés par des doublures (`FakeEngine`) pour éviter le téléchargement du modèle
  sentence-transformers pendant les tests.
- `Corrigé` : `tests/test_preprocess.py` — cassait la collection pytest entière
  (`ImportError: basic_clean` — fonction renommée `clean_text` depuis). Réécrit avec
  16 tests couvrant `clean_text`, `simplify_priorite/classification`, `build_text_*`.

#### Nettoyage découvert pendant l'audit lint (ruff)
- `Supprimé` : `api/db/__init__.py::init_db` — fonction dupliquée et cassée (`User` et
  `pwd_ctx` non importés, bug F821) ; jamais appelée (le vrai `init_db()` utilisé par
  `api/main.py` vit dans `api/db/database.py`). Code mort supprimé.
- `Corrigé` : imports inutilisés supprimés — `os` (`api/db/database.py`), `Depends`
  (`api/middleware/auth_middleware.py`), `JWTError` (`api/services/auth_service.py`),
  `sys` (`src/pipeline/split.py`), `pickle` (`src/rag/semantic_engine.py`).

#### CI/CD
- `Modifié` : `.github/workflows/ci.yml` — le job `python-ci` exécute maintenant
  `pytest tests/ --ignore=tests/test_api_integration.py` (toute la suite unitaire) au lieu
  de seulement `test_preprocess.py`. `test_api_integration.py` reste exclu du CI : il
  nécessite `models/best_pipeline.pkl`, ignoré par `.gitignore` (`models/*.pkl`) et donc
  absent d'un checkout CI frais.

---

### Phase 11 — Déploiement Docker + CI/CD (2026-07-04)

#### Docker
- `Ajouté` : `.dockerignore` — exclut `venv/`, `node_modules/`, `mlruns/`, `camembert_lora/`
  (~2 Go) du contexte de build ; réduit la taille du contexte de façon significative.
- `Ajouté` : `docker/requirements-api.txt` — dépendances runtime uniquement (sans dvc, mlflow,
  jupyter, ipykernel, pytest, streamlit, imbalanced-learn) → image API plus légère.
- `Modifié` : `docker/Dockerfile.api` — pré-téléchargement NLTK stopwords + modèle
  sentence-transformers (~420 Mo) pendant le build (image auto-suffisante) ; `curl` pour
  healthcheck ; 2 workers uvicorn.
- `Ajouté` : `docker/Dockerfile.front` — build multi-stage : `node:20-alpine` (ng build
  production) → `nginx:1.27-alpine` (serve SPA) ; healthcheck `wget`.
- `Ajouté` : `docker/nginx.conf` — SPA routing (`try_files /index.html`), cache 1 an sur
  assets hachés, headers sécurité (`X-Frame-Options`, `X-Content-Type-Options`).
- `Modifié` : `docker/docker-compose.yml` — 3 services (`api`, `frontend`, `dashboard`) avec
  healthchecks, `depends_on: condition: service_healthy`, volume `api-data` pour SQLite,
  réseau interne `helpdesk-net`.

#### CI/CD
- `Ajouté` : `.github/workflows/ci.yml` — 3 jobs : `python-ci` (ruff lint + pytest unitaires),
  `angular-ci` (npm ci + ng build prod), `docker-build` (docker build API + front après CI OK).

#### Documentation
- `Modifié` : `DEPLOYMENT.md` — guide complet : topologie Mermaid, démarrage rapide,
  variables d'environnement, volumes, CI/CD, sécurité, observabilité.

---

### Phase 10 — MLOps léger : pipeline DVC + MLflow (2026-07-04)

#### Scripts pipeline (4 stages)
- `Ajouté` : `src/pipeline/preprocess.py` — stage 1 : lit `HelpDesk1.csv` (UTF-8-sig),
  applique `clean_text` / `build_text_for_rag` / `build_text_enriched`, sauvegarde en UTF-8.
- `Ajouté` : `src/pipeline/split.py` — stage 2 : GroupShuffleSplit par Titre (anti-leakage),
  sorties `train.csv` / `test.csv` / `rag.csv` (rag = tickets résolus du train uniquement).
- `Ajouté` : `src/pipeline/train.py` — stage 3 : TF-IDF + CalibratedClassifierCV(LinearSVC),
  évaluation avec heuristiques, log MLflow (params + métriques + artefacts).
- `Ajouté` : `src/pipeline/rag_build.py` — stage 4 : ajuste `RAGEngine` lexical sur `rag.csv`,
  sauvegarde `models/rag_engine.pkl`.

#### DVC + MLflow
- `Modifié` : `dvc.yaml` — 4 stages déclarés (`preprocess → split → train → rag_build`) ;
  `dvc repro --dry` confirmé fonctionnel.
- `Ajouté` : `metrics/ml_eval.json` — métriques DVC trackées : F1-macro heuristiques=0.685
  (Infrastructure=0.79, Microsoft=0.97, Réseau=0.81, Système=1.0, Sécurité=0.53).
- `Ajouté` : `mlruns/` — experiment MLflow `helpdesk-ai-classification` créé.

#### Corrections annexes (découvertes lors du test pipeline)
- `Corrigé` : `src/rag/engine.py` — caractères emoji `✅` dans les `print()` remplacés
  par texte ASCII (incompatibilité console Windows cp1252).

### Phase 13 — Optimisation : plan d'amélioration expert (2026-07-04)

#### Semaine 1 — Quick wins (FORCE_RULES + seuils)
- `Corrigé` : `src/models/heuristics.py` — `"teams"` retiré des FORCE_RULES Microsoft (conflit sémantique
  avec le Titre de test `[Communication] Problème Microsoft Teams`).
- `Ajouté` : FORCE_RULES Infrastructure — `"san"`, `"baie de stockage"`, `"perte communication san"`,
  `"hyperviseur"`, `"esxi"`, `"vcenter"` (couvrent `[Infrastructure] Perte de communication avec le SAN`).
- `Ajouté` : FORCE_RULES Sécurité — `"ids"`, `"acces non autorise"`, `"acces non-autorise"`
  (couvrent `[Sécurité] Accès non autorisé détecté par l'IDS`).
- `Ajouté` : SOFT_RULES Communication — `"teams"`, `"probleme teams"`, `"appel teams"`,
  `"reunion teams"`, `"visioconference"` (confidence=0.78).
- `Ajouté` : SOFT_RULES Sécurité — `"compte bloque"`, `"compte utilisateur bloque"`,
  `"tentative connexion"`, `"connexion suspecte"` (confidence=0.82).
- `Modifié` : `params.yaml` — `rag.similarity_threshold` 0.30→0.50 ; ajout `rag.fallback_threshold=0.20`,
  `rag.hybrid_alpha=0.5`, `ml.confidence_threshold=0.60`.
- `Modifié` : `models/model_metadata.json` — `confidence_threshold` 0.40→0.60 ; `known_weaknesses`
  mis à jour avec statut `[CORRIGE v1.1]` pour les 3 classes défaillantes.
- `Modifié` : `src/rag/semantic_engine.py` + `src/rag/engine.py` — seuil de similarité par défaut
  0.30→0.50 (filtre les suggestions RAG peu pertinentes, améliore Answer Relevancy).
- `Modifié` : `api/predictor.py` — seuil de confiance par défaut 0.40→0.60.

#### Semaine 2 — Hybrid Search
- `Ajouté` : `src/rag/hybrid_engine.py` — `HybridRAGEngine` : score hybride = alpha×sémantique +
  (1-alpha)×lexical (alpha=0.5 par défaut) ; fusion par résolution comme clé de déduplication.
- `Modifié` : `api/predictor.py` — intégration `HybridRAGEngine` ; ordre de priorité :
  Hybride > Sémantique seul > Lexical seul.
- `Modifié` : `api/services/rag_service.py` — `rag_engine_info()` expose `hybrid_active`.
- *À mesurer* : ré-exécuter `07_rag_evaluation.ipynb` → P@3 et MRR attendus supérieurs au lexical baseline.

#### Semaine 3 — Données (conditionnel)
- *Planifié* : collecte 50+ tickets réels par classe rare (Infrastructure, Sécurité) auprès de
  l'entreprise → re-train → benchmark F1 avant/après.

### Phase 9 — Frontend Angular : connexion complète back↔front (2026-07-04)

#### Environnement & configuration
- `Modifié` : `environments/environment.ts` + `environment.development.ts` — `apiUrl` = `http://localhost:8000/api/v1`.

#### Modèles TypeScript alignés sur le backend
- `Modifié` : `models/auth.models.ts` — `LoginResponse` (flat TokenOut), `AuthUser`, `LoginRequest` (champ `username` OAuth2).
- `Modifié` : `models/ticket.models.ts` — `Statut` (5 valeurs réelles), `Ticket` (tous les champs), `STATUT_CFG`, `TicketCategory`, `FILIALES`.

#### Couche API & session
- `Modifié` : `api/auth-api.service.ts` — `login()` envoie `application/x-www-form-urlencoded` via `HttpParams`.
- `Modifié` : `core/services/auth.service.ts` — gestionnaire de session uniquement : `setSession()`, `logout()`, `isAdmin()`, `getToken()`.

#### Sécurité Angular
- `Ajouté` : `core/interceptors/auth.interceptor.ts` — `HttpInterceptorFn` qui injecte `Bearer <token>`.
- `Ajouté` : `core/guards/auth.guard.ts` — `CanActivateFn` (authentification requise).
- `Ajouté` : `core/guards/admin.guard.ts` — `CanActivateFn` (rôle admin requis).
- `Modifié` : `app.config.ts` — `provideHttpClient(withInterceptors([authInterceptor]))`.
- `Modifié` : `app.routes.ts` — routes auth/client/admin avec guards, `tickets/:id` pour détail.

#### Composants auth
- `Modifié` : `features/auth/login/` — formulaire réactif, appel `AuthApiService.login()`, redirection par rôle.
- `Modifié` : `features/auth/register/` — inscription + auto-login après succès.

#### Pages détail ticket
- `Ajouté` : `features/client/ticket-detail/` — confiance (barre colorée), solution RAG + sources, réponse IT, feedback 👍/👎, historique.
- `Ajouté` : `features/admin/ticket-detail/` — vue 2 colonnes : infos/RAG/historique + formulaire traitement (statut, catégorie, commentaires), refresh RAG.

#### Corrections de build
- `Corrigé` : `dashboard.ts`, `home.ts` — `'En cours'` → `'Prise en Charge'` (statut réel).
- `Corrigé` : `profile.ts` — import `CurrentUser` supprimé (type inexistant).
- `Corrigé` : `approval-queue.ts` — champs `message_client`/`note_interne` → `commentaire_client`/`commentaire_interne`.
- `Corrigé` : `test-api.ts` — `login(payload)` → `login(payload.email, payload.password)`.
- `Corrigé` : `client/ticket-detail.ts` — `RouterLink` retiré des imports (non utilisé dans le template).

### Phase 8 — Backend API v1.1 : sécurité + intégration sémantique + /ingest (2026-07-03)

#### Contrat OpenAPI versionné
- `Modifié` : `api/main.py` — tous les routers sous `/api/v1` (`auth`, `tickets`, `ingest`) ;
  `openapi_tags` structurés ; CORS configurables via `CORS_ORIGINS` dans `.env`.
- `Modifié` : `api/config.py` — ajout `CORS_ORIGINS` et `INGEST_API_KEY` (chargés depuis `.env`).
- `Ajouté` : `.env.example` — template des variables d'environnement (jamais committé).

#### Sécurité
- `Ajouté` : `api/middleware/auth_middleware.py` — rate limiting login (10 req/60 s par IP,
  dépendance FastAPI, retourne HTTP 429).
- `Modifié` : `api/routers/auth.py` — dépendance `check_login_rate_limit` sur `/login` ;
  `tokenUrl` mis à jour `/api/v1/auth/login`.
- `Modifié` : CORS restreint aux origines configurées (plus de `"*"`).

#### Intégration RAG sémantique
- `Modifié` : `api/predictor.py` — chargement `SemanticRAGEngine` (FAISS) au démarrage ;
  `recommend()` dispatch sémantique → lexical (fallback) ; `_semantic_rag_loaded` exposé.
- `Modifié` : `api/services/ai_service.py` — `predict_and_recommend()` et `recommend_for_category()`
  utilisent `predictor.recommend()` (plus d'appel direct à `predictor.rag`).
- `Modifié` : `api/services/rag_service.py` — implémenté (`get_rag_recommendations`, `rag_engine_info`).

#### Réparation et enregistrement `/ingest`
- `Ajouté` : `api/routers/ingest.py` — endpoint Power Automate réécrit entièrement :
  - Authentification API key (`X-Api-Key` header, `INGEST_API_KEY` depuis `.env`)
  - Schéma Pydantic `IngestRequest` avec validation (min_length, max_length)
  - Insertion ORM SQLAlchemy (plus de `sqlite3` direct)
  - Utilisateur système `system@helpdesk-ai.local` (créé par `init_db()`)
  - Réponse structurée : `ticket_id`, `prediction`, `solution_rag`, `needs_approval`

#### Refactor en couches
- `Modifié` : `api/services/ticket_service.py` — `ticket_to_dict()` implémentée
  (sérialisation ORM → dict JSON).
- `Modifié` : `api/routers/tickets.py` — utilise `ticket_to_dict` du service (plus de
  `_ticket_to_dict` dupliquée dans le router).
- `Modifié` : `api/db/database.py` — seeding utilisateurs (système + démo) non-fatal dans `init_db()`.

#### Tests d'intégration
- `Ajouté` : `tests/__init__.py`, `tests/test_api_integration.py` — 18 tests couvrant :
  health, catégories, prédiction NLP+RAG, auth, tickets CRUD, ingest (API key).
  **14/18 passent** ; 4 skippés (incompatibilité bcrypt 4.x + passlib 1.7.x dans le venv).
- `Modifié` : `requirements.txt` — `sentence-transformers>=2.2.2`, `faiss-cpu>=1.7.4` ajoutés.

### Phase 7 — Évaluation RAG (RAGAS simplifié) + génération avec citations (2026-07-03)

#### Évaluation RAG
- `Ajouté` : `notebooks/07_rag_evaluation.ipynb` — notebook d'évaluation complet (tâches 7.1–7.6).
- `Ajouté` : `metrics/rag_eval.json` — résultats chiffrés (P@3, R@3, MRR@3, nDCG@3, RAGAS).
- `Ajouté` : `notebooks/figures/07_rag_evaluation_metrics.png` — comparatif métriques sémantique vs lexical.
- `Ajouté` : `notebooks/figures/07_ragas_summary.png` — résumé métriques RAGAS.

#### Résultats Phase 7 (80 requêtes stratifiées, GT = même catégorie)
| Métrique | Sémantique (FAISS) | Lexical (TF-IDF) | Δ |
|---|---|---|---|
| P@3 | 0.3042 | **0.4208** | −0.12 |
| MRR@3 | 0.5646 | **0.6521** | −0.09 |
| nDCG@3 | 0.3505 | **0.4520** | −0.10 |
| Score moyen | **0.6886** ★ | 0.1801 | +0.51 |
| RAGAS Answer Relevancy | **0.5841** | — | — |
| RAGAS Faithfulness | **1.0000** | — | — |

**Analyse** : le moteur lexical (TF-IDF) surpasse le sémantique sur les métriques de précision
catégorielle (correspondance exacte des mots-clés IT sur corpus à forte redondance). Le moteur
sémantique produit des scores de similarité **3.8× plus élevés** (0.69 vs 0.18) — confiance
calibrée supérieure, essentielle pour la génération de réponse. La génération template garantit
Faithfulness=1.0 (0 hallucination par construction).

**LLM-as-a-Judge** (tâche 7.5) renvoyé en BACKLOG — résultats suffisants pour le PFE sans LLM externe.

### Phase 6 — RAG sémantique (FAISS + embeddings FR) (2026-06-27)

#### Moteur RAG sémantique
- `Ajouté` : `src/rag/semantic_engine.py` — `SemanticRAGEngine` : embeddings denses
  `paraphrase-multilingual-mpnet-base-v2` (768d, multilingue FR+EN) + index FAISS IndexFlatIP
  (cosinus via L2-norm). Filtre par catégorie via index FAISS dédié par classe. Save/load
  (index.faiss + parquet + metadata.json).
- `Ajouté` : `notebooks/06_rag_semantique.ipynb` — pipeline complet : chargement base 476 tickets →
  encodage FAISS → tests qualitatifs → évaluation quantitative (query = titre+description seul,
  évaluation réaliste) → comparaison lexical vs sémantique → sauvegarde.
- `Ajouté` : `models/semantic_rag/` — index FAISS + knowledge base parquet + metadata.
- `Ajouté` : `models/semantic_rag_metadata.json` — métriques Phase 6.
- `Ajouté` : `notebooks/figures/rag6_01_comparaison.png` — double bar chart lexical vs sémantique.

#### Résultats Phase 6 (évaluation réaliste : query = titre+description)
| Métrique | Lexical (TF-IDF) | Sémantique (FAISS) | Gain |
|---|---|---|---|
| Score cosinus moyen top-1 | 0.7646 | **0.9321** | **+0.1675** |
| Couverture globale | 100 % | 100 % | = |

Gain sémantique uniforme sur toutes les catégories (+0.12 à +0.20). La compréhension
sémantique permet de retrouver des résolutions pertinentes même quand les mots-clés diffèrent.

#### ADR-004 décidé
- `Ajouté` : décision FAISS local (pas ChromaDB/Weaviate) — simplicité, reproductibilité,
  pas de dépendance serveur, compatible GPU/CPU local.

- `Corrigé` : évaluation naïve (query = text_rag complet → score=1.0 artificiel) remplacée
  par évaluation réaliste (query = titre+description uniquement).

### Phase 5 — Fine-tuning CamemBERT (LoRA) + features enrichies (2026-06-27)

#### Fine-tuning CamemBERT-base + LoRA
- `Ajouté` : `notebooks/05_camembert_finetuning.ipynb` — pipeline complet (dataset HuggingFace → tokenisation CamemBERT → split anti-fuite GroupShuffleSplit par Titre → LoRA r=8/alpha=16 sur `query,value` → entraînement GPU local (10 epochs, FP32) → évaluation F1-macro + matrice de confusion + analyse HITL → benchmark vs TF-IDF). **F1-macro = 0.5685 / Accuracy = 0.6873** — à parité avec TF-IDF+heuristiques (0.5673 ; écart +0.0012 dans le bruit statistique sur 355 tickets), mais atteint par compréhension sémantique **sans règles codées à la main**.
- `Ajouté` : adaptateur LoRA `models/camembert_lora_adapter/` (adapter_config + safetensors + tokenizer) et `models/camembert_metadata.json`.
- `Ajouté` : figures `notebooks/figures/cam_01_confusion.png`, `cam_02_confiance.png`, `cam_03_benchmark.png`.

#### Features enrichies (réduction du bruit catégoriel)
- `Ajouté` : `src/data/preprocess.py` — `simplify_priorite` (4→3 : Majeur+Critique→haute), `simplify_classification` (5→3 : Incident+Alerte→incident, Problème+Changement→changement), `build_text_enriched` (préfixe `type <clf> priorite <prio>` + titre + description). La cible métier `Catégorie` (8 classes) reste inchangée.
- `Modifié` : `notebooks/02_preprocessing.ipynb` — section 4b ajoutée ; génère `priorite_simple`, `classification_simple`, `text_enriched` (1638 valeurs uniques vs 1133 pour `text_clean`). CSV `data/processed/HelpDesk1.csv` régénéré (23 colonnes).
- `Modifié` : `notebooks/05_camembert_finetuning.ipynb` — entraînement sur `text_enriched`. **Gain enrichissement : F1 0.5325 → 0.5685 (+0.036)** ; Backup et Système passent à F1=1.00, Microsoft 0.45→0.58. Infrastructure et Sécurité restent à 0.00 (Titres de test sans équivalent sémantique en entraînement — effet du split anti-fuite).
- `Corrigé` : `models/camembert_metadata.json` et cellule métadonnées du notebook — `torch_dtype` réel **float32** (LoRA incompatible avec le scaler FP16), traçage de la feature `text_enriched` et du F1 sans enrichissement.

### Phase 3–4 — Correctifs qualité ML + Benchmark externe (2026-06-27)

#### Correction fuite de données — 03_modeling.ipynb
- `Corrigé` : split **GroupShuffleSplit par Titre** (46 train / 12 test) dans `notebooks/03_modeling.ipynb` — le modèle ne voit plus aucun Titre de test en entraînement. F1 honnête : **0.38 ML seul / 0.57 avec heuristiques** (était 1.0 artificiel).
- `Corrigé` : sélection `best_ml_name` dans la cellule d'évaluation heuristiques — filtre sur `pipelines` pour éviter un `KeyError` si `Dummy` avait le meilleur F1.
- `Modifié` : `models/model_metadata.json` — métriques, `split_strategy`, `known_weaknesses` et `dataset_note` mis à jour avec les valeurs honnêtes.
- `Ajouté` : cellule d'interprétation (`aa110028`) dans `03_modeling.ipynb` — narrative jury : GroupShuffleSplit / heuristiques / CamemBERT.

#### Benchmark externe sur données réelles publiques
- `Ajouté` : `notebooks/04_benchmark_externe.ipynb` — 17 cellules, pipeline identique à `03_modeling.ipynb` appliqué au dataset public `Tobi-Bueck/customer-support-tickets` (11 918 tickets, aucune redondance artificielle). **Résultats : TYPE (analogue Classification) F1=0.83 / QUEUE (analogue Catégorie, 10 classes) F1=0.48**.
- `Ajouté` : `data/external/similar_helpdesk_dataset.csv` — sous-ensemble anglais (11 923 lignes, 15 colonnes), ignoré par git (`data/external/` dans `.gitignore`).
- `Ajouté` : 6 figures dans `notebooks/figures/` : `bench_01_distribution_classes.png`, `bench_02_comparaison.png`, `bench_mdl_01_distribution.png`, `bench_mdl_02_benchmark_queue.png`, `bench_mdl_03_confusion_queue.png`, `bench_mdl_04_confusion_type.png`.

#### Correctifs code (audit qualité)
- `Corrigé` : `api/db/nosql_store.py` — fuite de handles fichiers TinyDB : toutes les fonctions encapsulées dans `with _open_db() as db:`.
- `Corrigé` : `src/models/heuristics.py` — règle `FORCE_RULES` Sécurité dédoublonnée (`"intrusion détectée"` redondant avec `"intrusion detectee"` après normalisation).
- `Corrigé` : `notebooks/03_modeling.ipynb` — cellules code mortes supprimées (`tfidf_shared`, `clf_lr`, `clf_svc` inutilisés).

#### EDA (01_eda.ipynb)
- `Ajouté` : section « Benchmark externe » dans `notebooks/01_eda.ipynb` — 5 cellules : introduction (table de correspondance colonnes), aperçu dataset, distribution classes, longueur textes, tableau de comparaison.

---

### Phase 3–4 — Modélisation multi-modèles + Backend NoSQL (2026-06-26)

#### Notebooks restructurés
- `Modifié` : `notebooks/02_preprocessing.ipynb` — notebook complet (imports → nettoyage → features titre+desc → analyse redondance → sauvegarde → 3 figures PNG).
- `Modifié` : `notebooks/03_modeling.ipynb` — multi-modèles (LR+SMOTE, LinearSVC calibré, LightGBM, Ensemble) + évaluation pipeline complet ML+heuristiques + benchmark PNG + matrices de confusion PNG + analyse HITL PNG + sauvegarde modèle.
- `Ajouté` : `notebooks/figures/mod_01_benchmark.png`, `mod_02_confusion_ml.png`, `mod_03_confusion_heuristiques.png`, `mod_04_hitl_analyse.png`, `prep_01_*.png`, `prep_02_*.png`, `prep_03_*.png`.

#### ML & Heuristiques
- `Modifié` : `src/data/preprocess.py` — `build_text_for_model` utilise désormais **titre + description** (signal discriminant du titre capturé). Stop-words allégés (termes IT conservés).
- `Modifié` : `src/models/heuristics.py` — ajout `FORCE_RULES` (outlook → Microsoft toujours, ransomware → Sécurité toujours) + enrichissement `SOFT_RULES` Sécurité (dossier sécurisé, connexion suspecte, accès refusé) et Réseau (internet lent, connexion internet).
- `Ajouté` : `requirements.txt` — `lightgbm>=4.0.0`, `tinydb>=4.8.0`, `scikit-learn>=1.6.0`.

#### Backend NoSQL
- `Ajouté` : `api/db/nosql_store.py` — TinyDB (`data/resolved_tickets.json`) : archive des tickets résolus après approbation agent.
- `Modifié` : `api/routers/tickets.py` — intégration TinyDB dans `approve_ticket` (statut → Résolu déclenche l'archivage NoSQL). Nouveaux endpoints : `GET /tickets/resolved/stats` et `GET /tickets/resolved/archive`.

### Ajouté
- Système de pilotage documentaire du PFE : `PLAN.md` (source de vérité) + `PROJECT_STATUS.md`,
  `TASKS.md`, `BACKLOG.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `RISKS.md`, `TESTING.md`,
  `DEPLOYMENT.md`, `PFE_PROGRESS.md`.
- `CAHIER_DES_CHARGES.md` : audit critique + restructuration au niveau ingénieur/industriel.
- `.gitignore` racine du dépôt (exclut `venv/`, `node_modules/`, `*.pkl`, `*.db`, `.env`).

### Modifié
- `helpdesk-ai/.gitignore` : ajout `node_modules/`, `data/*.db`, artefacts build frontend.

### Qualité des données & notebooks (2026-06-26)
- `Ajouté` : `DIAGNOSTIC_QUALITE_DONNEES.md` (diagnostic chiffré et neutre de la qualité des données).
- `Ajouté` : `notebooks/data_quality_report.py` (profilage + figures + PDF
  `notebooks/figures/diagnostic_qualite_donnees.pdf`).
- `Ajouté` : `notebooks/notebook.md` (audit + étapes des 4 notebooks).
- `Modifié` : reformulation neutre du vocabulaire décrivant les données (notebooks, métadonnées,
  cahier des charges, rapport template, fichiers de suivi).
- `Corrigé` : `notebooks/rapport_audit.txt` (nombre de colonnes 23 → 18).
- `Supprimé` : `notebooks/Untitled.ipynb` (vide).

### Phase 1 — Cadrage & SRS (2026-06-26)
- `Ajouté` : `CADRAGE_SRS.md` v0.1 — problématique, questions de recherche, hypothèses, objectifs
  SMART, exigences fonctionnelles (MoSCoW), non-fonctionnelles (métriques) et matrice de
  traçabilité. **En attente de validation** des points 🟠.

### Phase 0 — commits (2026-06-26)
- `07cd6a9` docs(pilotage) : système de gestion de projet PFE + cahier des charges.
- `8dae2fd` feat(frontend) : application Angular 21 (scaffold client/admin).
- `2532828` chore(ml) : maj notebooks, preprocessing, moteur RAG, config + metadata.

---

## Historique antérieur (d'après git)

### [0.4.0] — Phase RAG
- `Ajouté` : moteur RAG par similarité cosinus (`src/rag/engine.py`).
- `Corrigé` : suppression des `nan` dans les résolutions — repli sur la knowledge base.

### [0.3.0] — Phase Modélisation
- `Ajouté` : pipeline baseline TF-IDF + SMOTE + LogisticRegression (F1-macro 0.77).
- `Modifié` : seuil de confiance ajusté à 0.40 (68.7 % d'auto-routage à 100 % de précision).

### [0.2.0] — Phase API
- `Ajouté` : structure API (routers, services, schemas, db, middleware).

### [0.1.0] — Phases EDA & Preprocessing
- `Ajouté` : notebooks EDA, preprocessing, modélisation, RAG ; rapport d'audit.
