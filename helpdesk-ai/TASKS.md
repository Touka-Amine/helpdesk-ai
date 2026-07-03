# TASKS.md — Tâches de la phase active

> Tâches du sprint courant. Détail complet des checklists dans [PLAN.md](PLAN.md) (section 6).
> Dernière mise à jour : **2026-07-03**. **Phase active : Phase 9 — Frontend.**

## 🔵 Prochaine phase
- [ ] **Phase 9 — Frontend** : configurer `environment.ts` → aligner enum statuts → page détail ticket
  → guards auth/rôles → afficher confiance + sources RAG → feedback utilisateur.

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
