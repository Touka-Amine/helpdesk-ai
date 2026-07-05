# RISKS.md — Registre des risques

> Probabilité (P) et Impact (I) : Faible / Moyen / Élevé. Source de vérité : [PLAN.md](PLAN.md).
> Dernière mise à jour : *à la création*.

| ID | Risque | P | I | Mitigation | Statut |
|---|---|---|---|---|---|
| R-01 | **Redondance du corpus** (≈58 types de tickets récurrents) → risque de fuite de données et de généralisation limitée | Élevé | Élevé | Séparation train/test sans fuite ; prétraitement plus fin ; enrichissement des données ; évaluation sur test dé-dupliqué | Ouvert |
| R-02 | **Sur-apprentissage** (CV F1=1.0 vs test 0.77) | Élevé | Moyen | Régularisation, augmentation, validation honnête, métriques par classe | Ouvert |
| R-03 | **Classe *Sécurité* à faible rappel** (36,4 % mesuré Phase 12 sur `best_pipeline.pkl`, cible ≥ 0.70 ; le chiffre ~20 % était une estimation antérieure aux corrections FORCE_RULES v1.1) | Élevé | Moyen | Augmentation de données, focal loss, fine-tuning CamemBERT, heuristiques | Ouvert |
| R-04 | **Hallucinations LLM** dans la génération RAG | Moyen | Élevé | Guardrails, citations obligatoires, Faithfulness (RAGAS), fallback sans génération | Ouvert |
| R-05 | **Non-conformité RGPD** (données personnelles) | Moyen | Élevé | Anonymisation, registre de traitement, rétention (Phase 2) | Ouvert |
| R-06 | **Délai 6 mois** insuffisant pour tout le périmètre | Moyen | Élevé | MoSCoW strict, backlog, une tâche à la fois, jalons mensuels | Ouvert |
| R-07 | ~~Dette d'intégration front/back~~ (env vide, enum/modèle désalignés) | Élevé | Moyen | Corrigé Phase 9 (2026-07-04) : environment.ts, guards, contrat OpenAPI | **Clos** |
| R-08 | ~~`/ingest` cassé~~ | Élevé | Faible | Corrigé Phase 8 (2026-07-03) | **Clos** |
| R-09 | **Secrets exposés** (`SECRET_KEY=change-me`) | Moyen | Élevé | Gestion des secrets, `.env` hors git, rotation | Ouvert |
| R-10 | **Coût/temps GPU** pour le fine-tuning | Faible | Moyen | LoRA (léger), GPU local, runs courts | Ouvert |
| R-11 | **Dérive documentaire** (PLAN.md non maintenu) | Moyen | Moyen | Étape 7 du workflow obligatoire à chaque tâche | Ouvert |
| R-12 | **Panne de démo** à la soutenance | Faible | Élevé | Vidéo de secours, environnement figé Docker | Ouvert |
| R-13 | **Latence P95 > 300ms sous charge concurrente** (mesuré : 330ms séquentiel → 15s à 20 requêtes simultanées, 19% timeouts) — endpoint `/predict` synchrone/CPU-bound limité par le GIL et 2 workers uvicorn | Élevé | Moyen | Mesuré en Phase 12 (`metrics/load_test.json`) ; optimisation (workers, pipeline async, cache) prévue Phase 13 | Ouvert |
| R-14 | **Split de test non représentatif** : `data/splits/test.csv` (GroupShuffleSplit anti-fuite par Titre, 46 train/12 test Titres) ne contient **aucun exemple** des catégories *Backup* et *Communication* (0/356) — le F1-macro rapporté (ENF-03, 0.685) est calculé sur les classes réellement présentes, pas sur les 8 catégories du domaine ; risque de sur-interprétation déjà anticipé par PLAN.md Phase 12 (« sur-interprétation liée à la redondance du corpus ») | Élevé | Élevé | Découvert en construisant la matrice exigences→résultats (Phase 12, `CADRAGE_SRS.md` §5) ; nécessite un split stratifié (ex. `StratifiedGroupKFold`) ou plus de Titres uniques par catégorie rare avant de pouvoir mesurer un F1-macro fiable sur les 8 classes | Ouvert |

---
*Procédure : tout nouveau risque identifié en cours de tâche est ajouté ici + signalé dans le
résumé de la tâche.*
