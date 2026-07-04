# TASKS.md — Tâches de la phase active

> Tâches du sprint courant. Détail complet des checklists dans [PLAN.md](PLAN.md) (section 6).
> Dernière mise à jour : **2026-07-04**. **Phase active : Phase 13 — Optimisation (plan d'amélioration).**

## 🟢 En cours — Phase 13 : Optimisation (plan d'amélioration expert)

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

## 🔵 Prochaine phase — Phase 11 (Déploiement Docker)

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
- Incompatibilité bcrypt 4.x + passlib 1.7.x → envisager `bcrypt<=3.2.2` ou migration argon2
- Tests auth (register/login/tickets) skippés en TestClient — couverts en tests manuels uvicorn
- `helpdesk-ai/HelpDesk1.csv` en double — à traiter Phase 2 (DVC)

---
*Règle : une seule grosse tâche à la fois. Cocher ici + dans PLAN.md + journaliser dans
[CHANGELOG.md](CHANGELOG.md) à chaque fin de tâche.*
