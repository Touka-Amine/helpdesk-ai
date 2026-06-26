# PROJECT_STATUS.md — Avancement global

> Snapshot synthétique. **Source de vérité : [PLAN.md](PLAN.md)** (section 10 — Tableau de bord).
> Dernière mise à jour : *à la création*.

## Bandeau

| | |
|---|---|
| **Phase active** | Phase 1 — Cadrage scientifique & SRS |
| **Progression globale** | ~8 % (Phase 0 terminée) |
| **Périmètre** | Cœur rehaussé (Must) |
| **Durée** | Stage 6 mois · GPU local |
| **Prochaine étape** | Phase 1 : problématique → objectifs SMART → exigences |

## ✅ Terminé
- EDA + preprocessing (notebooks 01–02)
- Baseline ML TF-IDF + LogReg (F1-macro 0.77) — *référence*
- RAG lexical (TF-IDF + cosinus) — *à remplacer*
- Backend cœur (auth, tickets, approbation, historique)
- Documentation (cahier des charges, workflow)
- Système de pilotage documentaire (11 fichiers)

## 🟡 En cours
- Frontend Angular (non connecté au backend)
- Couches backend services/repositories/middleware (vides)

## 🔴 À faire (prioritaire)
- Phase 1 : cadrage scientifique & SRS
- Phase 2 : Data Engineering + RGPD + DVC
- Phases 5–7 : CamemBERT fine-tuné, RAG sémantique, évaluation RAGAS
- Phases 8–9 : durcissement backend + connexion frontend
- Phases 10–15 : MLOps, déploiement, tests, doc, soutenance

## Avancement par phase
| Phase | Avancement |
|---|---|
| 0 Initialisation | ✅ 100 % |
| 1 Cadrage & SRS | 🔴 0 % |
| 2 Data & RGPD | 🔴 0 % |
| 3 EDA | 🟡 ~80 % (à consolider) |
| 4 ML baseline | 🟡 ~70 % (à formaliser) |
| 5 Fine-Tuning | 🔴 0 % |
| 6 RAG sémantique | 🔴 0 % |
| 7 Éval RAG | 🔴 0 % |
| 8 Backend | 🟡 ~85 % |
| 9 Frontend | 🟡 ~65 % |
| 10 MLOps | 🔴 ~5 % |
| 11 Déploiement | 🔴 0 % |
| 12 Tests | 🔴 0 % |
| 13 Optimisation | 🔴 0 % |
| 14 Doc/mémoire | 🟡 ~10 % |
| 15 Soutenance | 🔴 0 % |
