# PROJECT_STATUS.md — Avancement global

> Résumé concis. **Source de vérité : [PLAN.md](PLAN.md)** (section 10 — Tableau de bord).
> Dernière mise à jour : **2026-06-27** (clôture Phase 5 — CamemBERT LoRA).

## Bandeau

| | |
|---|---|
| **Phase active** | Phase 6 — RAG sémantique |
| **Progression globale** | ~32 % (Phases 0–1, 3–5 terminées) |
| **Périmètre** | Cœur rehaussé (Must) |
| **Durée** | Stage 6 mois · GPU local |
| **Prochaine étape** | Phase 6 : embeddings FR → base vectorielle → retrieval |

## ✅ Terminé
- EDA + preprocessing (notebooks 01–02) + features enrichies (`text_enriched`)
- Baseline ML TF-IDF (F1-macro honnête 0.38 seul / 0.57 avec heuristiques, split anti-fuite) — *référence*
- **CamemBERT-base + LoRA — F1-macro 0.5685** (à parité avec TF-IDF+heuristiques 0.5673, sans règles codées)
- Benchmark externe public (Tobi-Bueck : TYPE F1=0.83 / QUEUE F1=0.48)
- RAG lexical (TF-IDF + cosinus) — *à remplacer (Phase 6)*
- Backend cœur (auth, tickets, approbation, historique) + NoSQL TinyDB
- Documentation (cahier des charges, workflow)
- Système de pilotage documentaire (11 fichiers)

## 🟡 En cours
- Frontend Angular (non connecté au backend)
- Couches backend services/repositories/middleware (vides)

## 🔴 À faire (prioritaire)
- Phase 6 : RAG sémantique (embeddings FR + base vectorielle + retrieval)
- Phase 7 : évaluation RAG (RAGAS) + génération avec citations
- Phase 2 (reliquat) : RGPD / anonymisation + pipeline DVC
- Phases 8–9 : durcissement backend + connexion frontend
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
| 6 RAG sémantique | 🔴 0 % |
| 7 Éval RAG | 🔴 0 % |
| 8 Backend | 🟡 ~88 % (NoSQL TinyDB ajouté pour tickets résolus) |
| 9 Frontend | 🟡 ~65 % |
| 10 MLOps | 🔴 ~5 % |
| 11 Déploiement | 🔴 0 % |
| 12 Tests | 🔴 0 % |
| 13 Optimisation | 🔴 0 % |
| 14 Doc/mémoire | 🟡 ~15 % |
| 15 Soutenance | 🔴 0 % |
