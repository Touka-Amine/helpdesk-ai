# TASKS.md — Tâches de la phase active

> Tâches du sprint courant. Détail complet des checklists dans [PLAN.md](PLAN.md) (section 6).
> Dernière mise à jour : **2026-09-08**. **Phase active : Phase 14 — Rédaction du mémoire**
> (Phases 0–12 closes, Phase 13 aux Semaines 1–2). Tâche courante : chapitre 5 du mémoire —
> suivi dans [PFE_PROGRESS.md](PFE_PROGRESS.md).
>
> ⚠️ **Ce fichier est un journal.** Les entrées ci-dessous conservent les chiffres tels qu'ils
> étaient au moment de la tâche, y compris le F1-macro de **0.685** devenu **0.5829** après
> l'audit des règles du 2026-08-22 (R-23). Elles ne sont pas corrigées, pour ne pas réécrire
> l'historique. **Pour citer une métrique dans le mémoire, se reporter à
> [PROMPT_REDACTION_RAPPORT.md](PROMPT_REDACTION_RAPPORT.md) §R2**, qui fait foi.

## ✅ Terminé — Migration PostgreSQL + ChromaDB (2026-07-29, ADR-004 / ADR-006)
- [x] Base opérationnelle SQLite → PostgreSQL : service dédié dans `docker-compose.yml`,
      `DB_URL` par défaut mis à jour, migration de colonnes rendue agnostique SQLite/Postgres
      (`sqlalchemy.inspect()`/`text()` au lieu de `sqlite3` en dur)
- [x] Base de connaissances TinyDB → ChromaDB (`api/db/vector_store.py` remplace
      `api/db/nosql_store.py`) — mode embarqué, archivage en `BackgroundTasks` à la résolution
- [x] RAG interrogé **en direct** sur les résolutions admin (`query_similar()` fusionné aux
      résultats statiques dans `ai_service.py`) — contrairement à TinyDB, jamais relu par le RAG
      malgré le texte affiché à l'admin qui le promettait
- [x] Bug découvert et corrigé en vérification : course entre les 2 workers uvicorn sur
      `Base.metadata.create_all()` avec une base Postgres neuve (`duplicate key ... users_id_seq`)
- [x] Bug découvert et corrigé en vérification : collection Chroma mise en cache par processus —
      un worker ne voyait pas les écritures faites par l'autre (staleness inter-processus)
- [x] Vérifié en direct : cycle ticket → résolution détaillée → archivage Chroma confirmé
      (`/tickets/resolved/stats`) → ticket similaire suivant recevant la vraie solution admin
      (score 0.78) plutôt que la suggestion statique générique
- [x] Documentation mise à jour : ARCHITECTURE.md, DECISIONS.md (ADR-004 clos, ADR-006 ajouté),
      DEPLOYMENT.md, RAPPORT_TEMPLATE.md, BACKLOG.md

## ✅ Terminé — Refonte du workflow de traitement des tickets (2026-07-29)
- [x] Résultat ML unifié (catégorie + priorité + classification + confiance) sur un seul panneau,
      au lieu de la seule catégorie affichée jusque-là
- [x] Transitions de statut : `Rejeté` atteignable depuis `Prise en Charge` et `Problème` (pas
      seulement depuis `En attente`)
- [x] Message client automatique à la prise en charge + auto-assignation de l'admin
- [x] File d'approbation : popup de décision (message client/note interne/Valider/Rejeter) retiré,
      remplacé par un clic simple → prise en charge automatique → redirection directe vers le détail
- [x] Écran de détail admin restructuré en 2 étapes : revue (classification + RAG, pas de statut
      visible) puis clôture (statut + catégorie/priorité/classification finales + solution, tous
      regroupés et modifiables ensemble)
- [x] Consigne « Solution appliquée » renforcée (diagnostic + action détaillés) — texte qui
      alimente directement ChromaDB
- [x] Liste des tickets admin reformatée sur le schéma du corpus d'entraînement (STATUT/Titre/
      Demandeur/Classification/Catégorie/Temps écoulé/CID/Filiale/Priorité/Assigné à/
      Résolution-Motif)
- [x] Bug découvert et corrigé en vérification : un ticket Résolu/Rejeté ne pouvait plus jamais
      être modifié (la validation de transition rejetait `new_status == current_status`) —
      contredisait l'exigence explicite que chaque ticket reste éditable après clôture

## ✅ Terminé — Login redessiné + retrait teaser IA (2026-07-16)
- [x] Page de login en deux colonnes : logo OneTech B.S. recréé en CSS/SVG (pas d'asset image
      fourni), formulaire de connexion inchangé à droite
- [x] Teaser « IA Copilote » décoratif retiré (contenu marketing non représentatif du produit)
- [x] Option « Saisie libre » retirée du sélecteur d'exemples du formulaire Nouveau ticket

## ✅ Terminé — Boucle admin → base de connaissances RAG (2026-07-16)
- [x] `rag_score` persisté sur le ticket + exposé par l'API (jusque-là calculé mais jamais transmis)
- [x] Détection de « cas nouveau » (score < 0.50) : écran admin affiche « Nouveau type de problème »,
      champ « Solution appliquée » obligatoire avant *Résolu* (validé serveur + client)
- [x] `archive_resolved_ticket()` utilise la solution réellement tapée par l'admin en priorité
      (repli sur la suggestion IA non validée seulement si l'admin n'a rien saisi)
- [x] Bug préexistant corrigé : migration `ALTER TABLE` non tolérante aux 2 workers uvicorn
      concurrents (`duplicate column name` non intercepté, révélé par l'ajout de `rag_score`)
- [x] Bug préexistant corrigé : `ticket-detail.ts` (client+admin) ne rafraîchissait pas les données
      en changeant de ticket sans rechargement complet (`route.snapshot` → `route.paramMap`)
- [x] Vérifié en direct (curl + navigateur) : cas nouveau bloqué sans solution puis résolu et
      archivé avec la vraie solution ; cas connu résolu librement et archivé avec la suggestion IA

## ✅ Terminé — Corrections UX post-Phase 9 (2026-07-16)
- [x] Sidebar noire (admin + client) + mode sombre app entière (`ThemeService`, toggle persisté)
- [x] Formulaire Nouveau ticket (client) reconstruit selon spec produit (exemples pré-remplis + questions guidées)
- [x] Routing racine/wildcard → `auth/login` (au lieu de `client/my-tickets` sans verif d'auth) ; login redirige immédiatement par rôle si session déjà valide
- [x] Expiration de session par inactivité (20 min) + déconnexion automatique sur 401 backend

## ✅ Terminé — Phase 9 : Frontend — refonte Stitch + gestion des comptes (2026-07-06/07)
- [x] Refonte des 15 écrans (client + admin) via maquettes Stitch — thème clair Tailwind,
      fabrications de la maquette systématiquement remplacées par des données réelles (voir
      détail dans [CHANGELOG.md](CHANGELOG.md))
- [x] Module **gestion des comptes** (spécification produit fournie) : `api/routers/admin.py`
      réécrit (CRUD admin-only, mot de passe temporaire auto-généré), `User.first_login`
      (migration additive) + guards Angular forçant `/auth/change-password` tant que le mot de
      passe temporaire n'a pas été changé — vérifié en direct (création → login → redirection
      forcée → changement → accès débloqué)
- [x] `POST /tickets/{id}/feedback` persisté (corrige **R-15/EF-13**, feedback client trompeur)
- [x] 3 bugs préexistants trouvés et corrigés en testant en direct : admin `GET /tickets/{id}`
      404 pour les tickets d'autrui, `approve()` envoyait un statut invalide (`Validé`), badge de
      rôle invisible (syntaxe opacité Tailwind v3 vs v4)
- [x] **Bugfix** : déconnexion client redirigeait vers `client/my-tickets` au lieu de
      `/auth/login` — `client-layout.ts` appelait un `router.navigate(['/login'])` redondant et
      mal typé après que `AuthService.logout()` ait déjà navigué correctement ; supprimé, guards
      client et admin revérifiés en direct

## ✅ Terminé — Phase 12 : Tests & validation (2026-07-05)
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
- [x] **Matrice exigences → résultats** — [CADRAGE_SRS.md](CADRAGE_SRS.md) §5 : 17 EF + 14 ENF évalués
      individuellement (9/17 EF atteints, 3 partiels, 4 non faits, 1 backlog ·
      5/14 ENF atteints, 5 partiels, 4 non atteints). Mesures recalculées à neuf :
      rappel *Sécurité* = **0.364** (cible ≥0.70), couverture de tests = **74 % en local mais
      22 % seulement en CI** (`test_api_integration.py` exclu, `best_pipeline.pkl` gitignoré).
      **Découverte critique en construisant la matrice** : `data/splits/test.csv` ne contient
      **aucun exemple** des catégories *Backup* et *Communication* (0/356) — le F1-macro=0.685
      rapporté n'est donc pas représentatif des 8 catégories du domaine. Ajouté comme risque
      **R-14** dans [RISKS.md](RISKS.md) (Ouvert, P=Élevé/I=Élevé). Autre clarification actée :
      EF-14 (« génération LLM ») est en réalité template-based, pas un vrai appel LLM — à nuancer
      explicitement dans le mémoire. `TESTING.md` mis à jour (checkboxes reflètent l'état réel).
- [x] **Étude utilisateur légère** — [CADRAGE_SRS.md](CADRAGE_SRS.md) §6 : parcours golden path
      (Client→Admin→Client) rejoué au niveau API (extension Chrome indisponible cette session)
      + revue de code des templates Angular. Golden path EF-01/02/03/04/06/07/08 confirmé
      fonctionnel de bout en bout. **2 découvertes ont corrigé des entrées trop optimistes de la
      matrice §5** : EF-05 (aucun routage réel par confiance, tout ticket suit la même file
      "En attente") et **EF-13 (feedback client trompeur : l'UI confirme "Merci pour votre
      retour !" mais `submitFeedbackComment()` ne fait qu'un `console.log()`, rien n'est
      persisté)**. Ajoutées comme risques **R-15** (feedback trompeur, Ouvert, I=Élevé — à
      corriger avant démo jury) et **R-16** (pas d'auto-routage, Ouvert) dans
      [RISKS.md](RISKS.md). 2 incohérences mineures notées (nommage `priorite`/`priorite_saisie`,
      seuil 0.40 obsolète codé en dur dans `tickets.py`).

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
