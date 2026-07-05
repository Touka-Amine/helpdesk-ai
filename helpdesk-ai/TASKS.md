# TASKS.md — Tâches de la phase active

> Tâches du sprint courant. Détail complet des checklists dans [PLAN.md](PLAN.md) (section 6).
> Dernière mise à jour : **2026-07-04**. **Phase active : Phase 12 — Tests & validation.**

## 🟢 En cours — Phase 12 : Tests & validation
- [x] Tests unitaires NLP — `tests/test_preprocess.py` (16 tests : clean_text, simplify_*, build_text_*)
- [x] Tests unitaires heuristiques — `tests/test_heuristics.py` (8 tests : FORCE/SOFT_RULES, word boundary)
- [x] Tests unitaires RAG lexical — `tests/test_rag_engine.py` (8 tests : filtre catégorie, seuil, fallback, dédup)
- [x] Tests unitaires RAG hybride — `tests/test_hybrid_engine.py` (9 tests : fusion de scores, save/restore sous-moteurs)
- [x] Corrigé `tests/test_preprocess.py` cassé (`basic_clean` inexistant → `clean_text`)
- [x] Corrigé 6 lints ruff préexistants (imports morts) + supprimé code mort `api/db/__init__.py::init_db` (bug F821 `User`/`pwd_ctx` non définis, jamais appelé — doublon mort de `api/db/database.py::init_db`)
- [x] CI : `ci.yml` exécute désormais toute la suite unitaire (hors `test_api_integration.py`, qui nécessite `models/best_pipeline.pkl` absent du checkout car ignoré par git)
- [x] **Test bout-en-bout via Docker réel** (`docker compose up`) — a révélé 3 bugs de déploiement corrigés :
      1. `docker/requirements-api.txt` manquait `pyarrow` (requis par `pandas.read_parquet` dans `SemanticRAGEngine.load()`) → RAG tombait en fallback lexical silencieux
      2. Port hôte `80` réservé par Windows (plage d'exclusion Hyper-V/WSL2 + service système) → `docker-compose.yml` frontend remappé sur `8081:80`
      3. **Bug critique** `src/rag/semantic_engine.py::save()` : noms de fichiers FAISS par catégorie accentuée (`index_cat_Réseau.faiss`) mal encodés par l'API C++ FAISS sous Windows (mojibake `RÃ©seau`) — invisible sur Windows (écriture/lecture symétriquement corrompues) mais cassait tout sous Linux/Docker (`metadata.json` référence le nom propre, absent du disque). Corrigé avec `unidecode()` pour des noms de fichiers 100% ASCII. Artefacts `models/semantic_rag/` régénérés via nouveau script `src/pipeline/rag_semantic_build.py` avec les 1357 tickets actuels (au lieu de 476, obsolètes depuis Phase 10).
      Validé : `docker compose up` → `GET /health` (rag_loaded=true), `/predict` → RAG hybride actif (1357 tickets), frontend + dashboard répondent 200.
- [x] **Tests d'intégration end-to-end** (Phase 8 : `test_api_integration.py`) — **18/18 passent** (auparavant 14/18, 4 skip bcrypt). Voir bug bcrypt ci-dessous.
- [x] **5ᵉ bug — auth cassée en conditions réelles** : test manuel de connexion client dans le navigateur (`http://localhost:8081`) → `"Email ou mot de passe incorrect"` pour les comptes seed. Logs conteneur : `AttributeError: module 'bcrypt' has no attribute '__about__'` → le seeding des utilisateurs (`_seed_users()`) échouait silencieusement à **chaque démarrage**, aucun compte (client/admin/système) n'était jamais créé en base. Cause : `passlib==1.7.4` lit `bcrypt.__about__.__version__`, supprimé depuis `bcrypt>=4.1`. Corrigé en épinglant `bcrypt==4.0.1` dans `requirements.txt` et `docker/requirements-api.txt`. Résout aussi la dette technique documentée (4 tests auth auparavant skippés → passent tous désormais).
      Validé : `POST /auth/login` réussit pour `aminetoukabri@gmail.com` (client) et
      `mohamedaminetoukabri089@gmail.com` (admin), tokens JWT corrects.
      Note mineure (non bloquante) : `Dockerfile.api` lance `uvicorn --workers 2`, donc
      `_seed_users()` s'exécute en parallèle dans les 2 processus au démarrage → un
      avertissement bénin `UNIQUE constraint failed` apparaît dans les logs (l'un des deux
      workers "perd" la course), rattrapé par le `try/except` existant sans conséquence sur
      l'état final de la base.
- [x] **Test de charge (latence P95)** — `scripts/load_test.py`, résultats dans `metrics/load_test.json` :
      | Concurrence | P95 | Erreurs |
      |---|---|---|
      | 1 (séquentiel) | 330 ms | 0% |
      | 5 | 1068 ms | 0% |
      | 20 | 15022 ms | 19% (timeouts) |
      **Critère PFE (P95≤300ms) NON ATTEINT**, y compris en séquentiel (330ms, proche).
      Cause : endpoint `/predict` synchrone + CPU-bound (encodage sentence-transformers,
      `predict_proba`, recherche FAISS), limité par le GIL et 2 workers uvicorn seulement.
      **4ᵉ bug corrigé au passage** : healthcheck `Dockerfile.front` utilisait `localhost`
      (résout en `::1` IPv6 dans le conteneur) au lieu de `127.0.0.1` → Nginx (IPv4 only)
      jamais joignable, conteneur signalé "unhealthy" en permanence.
      **Optimisation renvoyée à la Phase 13** (augmenter workers, revoir pipeline d'inférence).
- [ ] Matrice exigences → résultats
- [ ] Étude utilisateur légère

## 🟡 En pause — Phase 13 : Optimisation (plan d'amélioration expert)

### Semaine 1 — Quick wins ✅ TERMINÉ
- [x] Corriger `FORCE_RULES` : `"teams"` retiré de Microsoft → Communication ; `"san"` + `"ids"` + `"acces non autorise"` ajoutés en FORCE_RULES Infrastructure/Sécurité
- [x] Seuil de confiance ML : 0.40 → **0.60** (`params.yaml`, `model_metadata.json`, `predictor.py`)
- [x] Seuil RAG : 0.30 → **0.50** (`semantic_engine.py`, `engine.py`, `params.yaml`) — filtre les suggestions peu pertinentes
- [x] SOFT_RULES enrichies : `"compte bloque"` → Sécurité, `"teams"` → Communication

### Semaine 2 — Hybrid Search ✅ TERMINÉ
- [x] `src/rag/hybrid_engine.py` — `HybridRAGEngine` : score = 0.5×sémantique + 0.5×lexical
- [x] `api/predictor.py` — intégration du moteur hybride (priorité : Hybride > Sémantique > Lexical)
- [x] `api/services/rag_service.py` — `rag_engine_info()` mis à jour pour exposer `hybrid_active`
- [ ] **À faire** : ré-exécuter `07_rag_evaluation.ipynb` avec le moteur hybride → mesurer gain P@3/MRR

### Semaine 3 — Données (conditionnel)
- [ ] Collecter 50+ vrais tickets par classe rare (Infrastructure, Sécurité) auprès de l'entreprise
- [ ] Re-train pipeline ML avec nouvelles données → benchmark F1 avant/après
- [ ] Ré-évaluer RAGAS après enrichissement base RAG

## ✅ Terminé — Phase 10 (MLOps léger, 2026-07-04)
- [x] `src/pipeline/preprocess.py` — stage 1 : raw → processed (UTF-8-sig)
- [x] `src/pipeline/split.py` — stage 2 : GroupShuffleSplit anti-fuite par Titre
- [x] `src/pipeline/train.py` — stage 3 : LinearSVC + MLflow logging
- [x] `src/pipeline/rag_build.py` — stage 4 : RAGEngine lexical → `models/rag_engine.pkl`
- [x] `dvc.yaml` — 4 stages déclarés ; `dvc repro --dry` OK
- [x] `metrics/ml_eval.json` — F1-macro heuristiques=**0.685** (vs 0.567 avant corrections)
- [x] MLflow runs dans `mlruns/` (experiment : `helpdesk-ai-classification`)
- [ ] (optionnel) Monitoring drift sur confiance — reporté Phase 12

## ✅ Terminé — Phase 11 (Déploiement Docker, 2026-07-04)
- [x] `.dockerignore` — exclut venv, node_modules, mlruns, camembert_lora (~2 Go)
- [x] `docker/requirements-api.txt` — dépendances runtime uniquement (sans dvc/mlflow/jupyter)
- [x] `docker/Dockerfile.api` — python:3.11-slim, NLTK + sentence-transformers pré-téléchargés, healthcheck curl
- [x] `docker/Dockerfile.front` — multi-stage : node:20 build → nginx:1.27 serve
- [x] `docker/nginx.conf` — SPA routing, cache assets, headers sécurité
- [x] `docker/docker-compose.yml` — 3 services (api, frontend, dashboard), volume SQLite, réseau interne, healthchecks
- [x] `.github/workflows/ci.yml` — 3 jobs : ruff+pytest / ng build / docker build
- [x] `DEPLOYMENT.md` — guide complet (démarrage rapide, variables env, CI/CD, sécurité)

## ✅ Terminé — Phase 9 (Frontend connexion, 2026-07-04)
- [x] `environment.ts` / `environment.development.ts` — `apiUrl` configuré
- [x] Modèles TypeScript alignés sur backend : `auth.models.ts`, `ticket.models.ts`
- [x] `AuthApiService.login()` → `application/x-www-form-urlencoded` (OAuth2)
- [x] `AuthService` session manager (`setSession`, `logout`, `isAdmin`, `getToken`)
- [x] Intercepteur HTTP (`auth.interceptor.ts`) — injecte `Authorization: Bearer <token>`
- [x] Guards fonctionnels : `auth.guard.ts` (auth requise) + `admin.guard.ts` (rôle admin)
- [x] `app.config.ts` — `provideHttpClient(withInterceptors([authInterceptor]))`
- [x] `app.routes.ts` — routes auth/client/admin avec guards, lazy-load des détails
- [x] Composant login (`features/auth/login/`) — form réactif, redirection par rôle
- [x] Composant register (`features/auth/register/`) — inscription + auto-login
- [x] Page détail ticket client (`features/client/ticket-detail/`) — confiance, RAG, feedback
- [x] Page détail ticket admin (`features/admin/ticket-detail/`) — formulaire traitement, historique, refresh RAG
- [x] Build Angular propre (0 erreur)

## ⚪ À faire (Phase 2 — reliquat Data Engineering & RGPD)
- [ ] Anonymisation des PII + registre de traitement RGPD
- [ ] Écrire les stages DVC (preprocess → split → rag)
- [ ] Dictionnaire de données + data card

## ✅ Terminé — Phase 8 (Backend, 2026-07-03)
- [x] Contrat OpenAPI versionné `/api/v1` (tous les routers préfixés)
- [x] Sécurité : `CORS_ORIGINS` + `INGEST_API_KEY` configurables via `.env` ; rate limiting login (429)
- [x] SemanticRAGEngine (FAISS) intégré dans `predictor.py` + `ai_service.py` — fallback lexical si indisponible
- [x] `/ingest` réparé et réécrit (`api/routers/ingest.py`) — authentification API key, ORM, validation Pydantic
- [x] Refactor couches : `ticket_service.py` (sérialisation), `rag_service.py` (dispatch FAISS/TF-IDF),
      `auth_middleware.py` (rate limiter en dépendance FastAPI)
- [x] Tests d'intégration : `tests/test_api_integration.py` — 14/18 passent, 4 skippés
      (incompatibilité bcrypt 4.x + passlib 1.7.x dans le venv — ignorée, auth fonctionne via uvicorn)

## ✅ Terminé — Phase 7 (Évaluation RAG RAGAS, 2026-07-03)
- [x] Jeu d'évaluation 80 requêtes stratifiées (10/catégorie)
- [x] P@3=0.30 sém / 0.42 lex, MRR=0.56/0.65 ; Score moyen sémantique **0.69 vs 0.18** lexical
- [x] RAGAS simplifié : Answer Relevancy=0.58, Faithfulness=1.0 (template-based)
- [x] Figures + `metrics/rag_eval.json` + audit (3 bugs corrigés)

## ✅ Terminé — Phase 6 (RAG sémantique FAISS, 2026-06-27)
- [x] `src/rag/semantic_engine.py` — FAISS + `paraphrase-multilingual-mpnet-base-v2`
- [x] Score cosinus top-1 : **0.93 sémantique vs 0.76 lexical (+0.17)**

## ✅ Terminé — Phase 5 (CamemBERT LoRA, 2026-06-27)
- [x] Fine-tuning CamemBERT-base + LoRA — **F1-macro 0.5685**

## ✅ Terminé — Phase 1 (SRS v0.1, 2026-06-26) · Phase 0 (gouvernance, 2026-06-26)

## 📌 Dette technique
- ~~Incompatibilité bcrypt 4.x + passlib 1.7.x~~ **Corrigé Phase 12 (2026-07-05)** : `bcrypt==4.0.1` épinglé
- ~~Tests auth skippés en TestClient~~ **Résolu** : 18/18 tests passent depuis le pin bcrypt
- ~~`helpdesk-ai/HelpDesk1.csv` en double~~ **Supprimé (2026-07-05)** : identique octet pour octet à `data/raw/HelpDesk1.csv` (géré par DVC) ; aucune référence de code ne pointait dessus en premier choix (fallback inutilisé dans `notebooks/data_quality_report.py`)

---
*Règle : une seule grosse tâche à la fois. Cocher ici + dans PLAN.md + journaliser dans
[CHANGELOG.md](CHANGELOG.md) à chaque fin de tâche.*
