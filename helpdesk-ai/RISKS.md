# RISKS.md — Registre des risques

> Probabilité (P) et Impact (I) : Faible / Moyen / Élevé. Source de vérité : [PLAN.md](PLAN.md).
> Dernière mise à jour : *à la création*.

| ID | Risque | P | I | Mitigation | Statut |
|---|---|---|---|---|---|
| R-01 | **Redondance du corpus** (≈58 types de tickets récurrents) → risque de fuite de données et de généralisation limitée | Élevé | Élevé | Séparation train/test sans fuite ; prétraitement plus fin ; enrichissement des données ; évaluation sur test dé-dupliqué | Ouvert |
| R-02 | **Sur-apprentissage** (CV F1=1.0 vs test 0.77) | Élevé | Moyen | Régularisation, augmentation, validation honnête, métriques par classe | Ouvert |
| R-03 | **Classe *Sécurité* à faible rappel** (~20 %) | Élevé | Moyen | Augmentation de données, focal loss, fine-tuning CamemBERT, heuristiques | Ouvert |
| R-04 | **Hallucinations LLM** dans la génération RAG | Moyen | Élevé | Guardrails, citations obligatoires, Faithfulness (RAGAS), fallback sans génération | Ouvert |
| R-05 | **Non-conformité RGPD** (données personnelles) | Moyen | Élevé | Anonymisation, registre de traitement, rétention (Phase 2) | Ouvert |
| R-06 | **Délai 6 mois** insuffisant pour tout le périmètre | Moyen | Élevé | MoSCoW strict, backlog, une tâche à la fois, jalons mensuels | Ouvert |
| R-07 | **Dette d'intégration front/back** (env vide, enum/modèle désalignés) | Élevé | Moyen | Contrat OpenAPI, Phase 9 dédiée | Ouvert |
| R-08 | **`/ingest` cassé** | Élevé | Faible | Correction en Phase 8 | Ouvert |
| R-09 | **Secrets exposés** (`SECRET_KEY=change-me`) | Moyen | Élevé | Gestion des secrets, `.env` hors git, rotation | Ouvert |
| R-10 | **Coût/temps GPU** pour le fine-tuning | Faible | Moyen | LoRA (léger), GPU local, runs courts | Ouvert |
| R-11 | **Dérive documentaire** (PLAN.md non maintenu) | Moyen | Moyen | Étape 7 du workflow obligatoire à chaque tâche | Ouvert |
| R-12 | **Panne de démo** à la soutenance | Faible | Élevé | Vidéo de secours, environnement figé Docker | Ouvert |

---
*Procédure : tout nouveau risque identifié en cours de tâche est ajouté ici + signalé dans le
résumé de la tâche.*
