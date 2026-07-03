# PROJECT_STATUS.md — Avancement global

> Résumé concis. **Source de vérité : [PLAN.md](PLAN.md)** (section 10 — Tableau de bord).
> Dernière mise à jour : **2026-07-03** (clôture Phase 7 — Évaluation RAG).

## Bandeau

| | |
|---|---|
| **Phase active** | Phase 8 — Backend (durcissement + intégration) |
| **Progression globale** | ~44 % (Phases 0–1, 3–7 terminées) |
| **Périmètre** | Cœur rehaussé (Must) |
| **Durée** | Stage 6 mois · GPU local |
| **Prochaine étape** | Phase 8 : sécurité API + intégration CamemBERT + RAG + fix `/ingest` |

## ✅ Terminé
- EDA + preprocessing (notebooks 01–02) + features enrichies (`text_enriched`)
- Baseline ML TF-IDF (F1-macro honnête 0.38 seul / 0.57 avec heuristiques, split anti-fuite) — *référence*
- **CamemBERT-base + LoRA — F1-macro 0.5685** (à parité avec TF-IDF+heuristiques, sans règles codées)
- Benchmark externe public (Tobi-Bueck : TYPE F1=0.83 / QUEUE F1=0.48)
- RAG lexical (TF-IDF + cosinus) — *conservé comme baseline*
- **RAG sémantique FAISS** — `paraphrase-multilingual-mpnet-base-v2`, score cosinus **0.93 vs 0.76** lexical (+0.17)
- **Évaluation RAG (Phase 7)** — P@3=0.30 sém/0.42 lex, MRR=0.56/0.65, **Score moyen 0.69 sém vs 0.18 lex** ; RAGAS : Answer Relevancy=0.58, Faithfulness=1.0 ; génération template avec citations
- Backend cœur (auth, tickets, approbation, historique) + NoSQL TinyDB
- Documentation (cahier des charges, workflow)
- Système de pilotage documentaire (11 fichiers)

## 🟡 En cours
- Frontend Angular (non connecté au backend)
- Couches backend services/repositories/middleware (vides)

## 🔴 À faire (prioritaire)
- **Phase 8** : durcissement sécurité API + intégration CamemBERT + RAG sémantique + fix `/ingest`
- Phase 2 (reliquat) : RGPD / anonymisation + pipeline DVC
- Phase 9 : connexion frontend ↔ backend
- Phases 10–15 : MLOps, déploiement, tests, doc, soutenance

## Avancement par phase
| Phase | Avancement |
|---|---|
| 0 Initialisation | ✅ 100 % |
| 1 Cadrage & SRS | ✅ 100 % (SRS v0.1) |
| 2 Data & RGPD | 🟡 ~45 % (diagnostic qualité + features enrichies faits, RGPD à faire) |
| 3 EDA | ✅ ~90 % (consolidé + benchmark externe) |
| 4 ML baseline | ✅ 100 % (multi-modèles + heuristiques, F1 honnête 0.57) |
| 5 Fine-Tuning | ✅ 100 % (CamemBERT LoRA, F1=0.5685) |
| 6 RAG sémantique | ✅ 100 % (FAISS + paraphrase-multilingual, score 0.93) |
| 7 Éval RAG | ✅ 100 % (P@3=0.30 sém, MRR=0.56, AR=0.58, Faith=1.0 ; génération template) |
| 8 Backend | 🟡 ~88 % (NoSQL TinyDB ajouté pour tickets résolus) |
| 9 Frontend | 🟡 ~65 % |
| 10 MLOps | 🔴 ~5 % |
| 11 Déploiement | 🔴 0 % |
| 12 Tests | 🔴 0 % |
| 13 Optimisation | 🔴 0 % |
| 14 Doc/mémoire | 🟡 ~15 % |
| 15 Soutenance | 🔴 0 % |
