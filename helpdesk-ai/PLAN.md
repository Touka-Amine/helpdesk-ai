# PLAN.md — Plan directeur du PFE `helpdesk-ai`

> **Source de vérité unique du projet.** Aucune fonctionnalité ne doit être développée sans être
> prévue ici. À chaque session : relire ce fichier → identifier la phase/tâche active → exécuter
> **une seule** tâche → tester → mettre à jour ce fichier → cocher → résumer → proposer la suite.
>
> **Méta** — Dernière mise à jour : *à la création* · Phase active : **Phase 0** · Périmètre :
> **Cœur rehaussé (Must)** · Durée : **stage 6 mois** · Compute : **GPU local**.
>
> **Documents liés** : [CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md) ·
> [ARCHITECTURE.md](ARCHITECTURE.md) · [DECISIONS.md](DECISIONS.md) · [RISKS.md](RISKS.md) ·
> [TESTING.md](TESTING.md) · [DEPLOYMENT.md](DEPLOYMENT.md) · [BACKLOG.md](BACKLOG.md) ·
> [TASKS.md](TASKS.md) · [CHANGELOG.md](CHANGELOG.md) · [PROJECT_STATUS.md](PROJECT_STATUS.md) ·
> [PFE_PROGRESS.md](PFE_PROGRESS.md) · [TICKET_WORKFLOW.md](TICKET_WORKFLOW.md)

---

## 1. Vision du projet

### 1.1 Objectif global
Concevoir une **plateforme intelligente** d'analyse, de classification et d'assistance à la
résolution de **tickets informatiques francophones**, combinant NLP (classification, résumé,
extraction d'entités, priorité, sentiment), **RAG sémantique** d'assistance, le tout exposé via une
**API FastAPI** et une **interface web Angular**, industrialisé (MLOps, Docker) et évalué
scientifiquement.

### 1.2 Problématique
*Comment classer automatiquement et de manière fiable des tickets IT courts, déséquilibrés et
bruités en français, et proposer une assistance à la résolution pertinente et vérifiable, tout en
gardant l'humain dans la boucle ?*

### 1.3 Valeur ajoutée
Réduire le temps de traitement d'un ticket de **30–45 min → 5–10 min**, fiabiliser le routage,
capitaliser sur les résolutions passées, et fournir un journal d'audit complet.

### 1.4 Contributions scientifiques
- Benchmark rigoureux **baseline (TF-IDF + LogReg) → transformer francophone (CamemBERT fine-tuné
  LoRA)** sur classification de tickets courts déséquilibrés.
- **Évaluation quantitative d'un système RAG** (RAGAS : Precision@k, Recall@k, MRR, nDCG,
  Faithfulness, Answer Relevancy, Context Precision/Recall, Hallucination Rate).
- Stratégie de **calibration de confiance** et de **human-in-the-loop** pour le routage.

### 1.5 Contributions techniques
Architecture modulaire, pipeline reproductible (DVC), registre de modèles (MLflow), API durcie
(sécurité, RGPD), conteneurisation Docker, CI/CD et observabilité IA.

### 1.6 Critères de réussite (mesurables)
| Critère | Cible |
|---|---|
| F1-macro classification (test dé-dupliqué) | ≥ 0.85 |
| Rappel classe *Sécurité* | ≥ 0.70 |
| RAG : Context Recall | ≥ 0.80 |
| RAG : Faithfulness | ≥ 0.85 |
| Latence prédiction P95 | ≤ 300 ms |
| Front ↔ back fonctionnel de bout en bout | Démo création→validation→résolution |
| Conformité RGPD | Anonymisation + registre de traitement |
| Mémoire + soutenance | Livrés dans les 6 mois |

---

## 2. État actuel du projet

Légende : ✅ Terminé · 🟡 En cours · 🔴 À faire

| État | Élément | Avancement | Qualité | Dette technique | Remarques |
|---|---|---|---|---|---|
| ✅ | EDA + preprocessing (notebooks 01–02) | 90 % | Bonne | Notebooks à figer en scripts | À consolider/documenter (Phase 3). |
| ✅ | Baseline ML TF-IDF + LogReg | 100 % | F1-macro **0.77** | Sur-apprentissage (CV=1.0) sur données synthétiques | Devient la **référence** de comparaison. |
| ✅ | RAG lexical (`src/rag/engine.py`) | 100 % | Faible (lexical) | Pas sémantique, pas de métriques | À **remplacer** (Phases 6–7). |
| ✅ | Backend cœur (auth JWT, tickets, approbation, historique) | 85 % | Bonne | Couches services/repos vides | ENF + sécurité à durcir (Phase 8). |
| ✅ | Documentation (cahier des charges, workflow) | 80 % | Très bonne | — | Base solide pour le mémoire. |
| 🟡 | Frontend Angular 21 | 65 % | Moyenne | `environment.ts` vide, enum/`Ticket` désalignés, page détail absente, pas de guards | **Non connecté** au backend (Phase 9). |
| 🟡 | Couches `services/`, `db/repositories/`, `middleware/` | 10 % | — | Squelettes vides, logique dans routers | À implémenter ou assumer (Phase 8). |
| 🔴 | Endpoint `/ingest` | Cassé | — | Import `datetime` manquant, mauvais appel, non enregistré | À réparer (Phase 8). |
| 🔴 | CamemBERT fine-tuné (LoRA) + benchmark | 0 % | — | — | Phase 5. |
| 🔴 | RAG sémantique (embeddings FR + vector DB) + RAGAS | 0 % | — | — | Phases 6–7. |
| 🔴 | RGPD / anonymisation | 0 % | — | Données personnelles non traitées | Phase 2. |
| 🔴 | MLOps (pipeline DVC, MLflow registry) | 5 % | — | `dvc.yaml` vide | Phase 10. |
| 🔴 | Docker / CI-CD / monitoring | 0 % | — | — | Phases 10–11. |
| 🔴 | Tests automatisés | 0 % | — | Aucun test | Phase 12. |
| 🔴 | Mémoire PFE | 10 % | — | — | Phase 14 (continu). |

---

## 3. Architecture globale (résumé)

> Détail complet et diagrammes dans [ARCHITECTURE.md](ARCHITECTURE.md).

| Module | État | Stack cible |
|---|---|---|
| Frontend | 🟡 | Angular 21, Material, Chart.js |
| Backend / API | ✅🟡 | FastAPI, Pydantic, OpenAPI |
| Base de données | ✅ | SQLite (dev) → PostgreSQL (cible) |
| Pipeline NLP | ✅🔴 | NLTK, scikit-learn, HuggingFace Transformers |
| Pipeline ML (baseline) | ✅ | TF-IDF + LogisticRegression + SMOTE |
| Pipeline Fine-Tuning | 🔴 | CamemBERT + PEFT/LoRA (GPU local) |
| Pipeline RAG | 🔴 | embeddings FR + vector DB + retrieval |
| Vector Database | 🔴 | Qdrant ou Chroma ou pgvector (ADR-004) |
| Embeddings | 🔴 | modèle FR (e5-multilingual / Solon / Sentence-CamemBERT) |
| LLM | 🔴 | génération de réponse (léger, avec citations) |
| Prompt Engineering | 🔴 | templates versionnés, sortie contrainte |
| MLOps | 🔴 | DVC, MLflow |
| LLMOps | 🔴 (backlog partiel) | prompt versioning, traçage |
| CI/CD | 🔴 | GitHub Actions |
| Monitoring | 🔴 | logs structurés + métriques IA |
| Déploiement | 🔴 | Docker, docker-compose |
| Sécurité | 🟡 | JWT, RBAC, secrets, anti-injection |
| RGPD | 🔴 | anonymisation, rétention, registre |
| Documentation | ✅🟡 | markdown + mémoire |
| Tests | 🔴 | pytest, tests RAG, charge |

---

## 4. Découpage en phases

> **Note** : *Deep Learning* et *Fine-Tuning* fusionnés (Phase 5) — l'unique activité DL du projet
> est le fine-tuning CamemBERT. La phase libérée devient **Phase 7 = Évaluation RAG (RAGAS)**.

| Phase | Titre | Priorité | Calendrier |
|---|---|---|---|
| 0 | Initialisation & gouvernance projet | Critique | Mois 1 |
| 1 | Cadrage scientifique & SRS | Critique | Mois 1 |
| 2 | Data Engineering & gouvernance (RGPD) | Haute | Mois 1–2 |
| 3 | Analyse exploratoire (consolidation) | Moyenne | Mois 2 |
| 4 | ML baseline (formalisation + calibration + XAI) | Haute | Mois 2 |
| 5 | Deep Learning & Fine-Tuning (CamemBERT + LoRA) | Critique | Mois 2–3 |
| 6 | RAG sémantique | Critique | Mois 3–4 |
| 7 | Évaluation RAG (RAGAS) + génération | Critique | Mois 4 |
| 8 | Backend (durcissement + intégration) | Haute | Mois 4 |
| 9 | Frontend (connexion + finalisation) | Haute | Mois 5 |
| 10 | MLOps léger | Haute | Mois 5 |
| 11 | Déploiement (Docker, CI/CD) | Moyenne | Mois 5 |
| 12 | Tests & validation | Haute | Mois 6 |
| 13 | Optimisation | Moyenne | Mois 6 |
| 14 | Documentation & mémoire PFE | Critique | Mois 6 (continu) |
| 15 | Préparation soutenance | Critique | Mois 6 |

---

## 5. Détail par phase

> Format : Objectif · Prérequis · Livrables · Critères de validation · Dépendances · Estimation ·
> Priorité · Risques.

### Phase 0 — Initialisation & gouvernance projet
- **Objectif** : mettre en place la gouvernance documentaire et l'environnement de travail.
- **Prérequis** : dépôt git existant.
- **Livrables** : 11 fichiers de pilotage ; `.gitignore` propre ; environnement Python figé ;
  DVC initialisé.
- **Critères** : tous les fichiers présents et cohérents ; `git status` propre ; `dvc` opérationnel.
- **Dépendances** : aucune.
- **Estimation** : 2–3 sessions.
- **Priorité** : Critique.
- **Risques** : dérive documentaire si non maintenu → règle de MAJ systématique.

### Phase 1 — Cadrage scientifique & SRS
- **Objectif** : transformer le cahier des charges en exigences exécutables.
- **Prérequis** : Phase 0 ; [CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md).
- **Livrables** : problématique/hypothèses figées, objectifs SMART, état de l'art synthétisé,
  exigences fonctionnelles (MoSCoW) + non-fonctionnelles, matrice de traçabilité.
- **Critères** : chaque exigence a un critère d'acceptation + un moyen de vérification.
- **Dépendances** : Phase 0.
- **Estimation** : 3–4 sessions.
- **Priorité** : Critique.
- **Risques** : périmètre flou → MoSCoW strict.

### Phase 2 — Data Engineering & gouvernance (RGPD)
- **Objectif** : données propres, conformes, versionnées, reproductibles.
- **Prérequis** : Phase 1.
- **Livrables** : audit qualité, **anonymisation/pseudonymisation RGPD**, registre de traitement,
  pipeline **DVC** (raw → processed → splits), dictionnaire de données, stratégie d'acquisition de
  données réelles.
- **Critères** : `dvc repro` reproductible ; PII anonymisées ; data card rédigée.
- **Dépendances** : Phase 1.
- **Estimation** : 4–5 sessions.
- **Priorité** : Haute.
- **Risques** : non-conformité RGPD ; non-généralisation (données synthétiques) — *assumée*.

### Phase 3 — Analyse exploratoire (consolidation)
- **Objectif** : figer l'EDA et la documenter pour le mémoire.
- **Prérequis** : Phase 2.
- **Livrables** : notebook 01 nettoyé, figures finales, rapport d'audit consolidé.
- **Critères** : EDA reproductible, figures exportées, insights documentés.
- **Dépendances** : Phase 2.
- **Estimation** : 2 sessions.
- **Priorité** : Moyenne.
- **Risques** : faible.

### Phase 4 — ML baseline (formalisation + calibration + XAI)
- **Objectif** : ériger TF-IDF+LogReg en **référence scientifique** propre.
- **Prérequis** : Phase 2.
- **Livrables** : pipeline baseline scripté, **calibration** (Platt/température), **XAI**
  (SHAP/LIME), rapport d'éval baseline, model card.
- **Critères** : métriques reproductibles, courbe de calibration (ECE), explications par classe.
- **Dépendances** : Phase 2.
- **Estimation** : 3 sessions.
- **Priorité** : Haute.
- **Risques** : seuil de confiance non justifié → calibrer.

### Phase 5 — Deep Learning & Fine-Tuning (CamemBERT + LoRA)
- **Objectif** : surpasser la baseline avec un transformer francophone.
- **Prérequis** : Phases 2 & 4 ; GPU local.
- **Livrables** : dataset HF, entraînement **LoRA**, adaptateur sauvegardé, **benchmark vs
  baseline**, model card, log MLflow.
- **Critères** : F1-macro ≥ 0.85 et rappel *Sécurité* ≥ 0.70 sur test dé-dupliqué ; benchmark
  documenté.
- **Dépendances** : Phases 2, 4.
- **Estimation** : 5–6 sessions.
- **Priorité** : Critique.
- **Risques** : sur-apprentissage, données limitées, temps GPU → augmentation/régularisation.

### Phase 6 — RAG sémantique
- **Objectif** : remplacer le RAG lexical par un RAG sémantique.
- **Prérequis** : Phase 2.
- **Livrables** : chunking de la base de connaissance, **embeddings FR**, **base vectorielle**,
  module de retrieval, intégration avec la catégorie prédite.
- **Critères** : retrieval fonctionnel, index versionné, top-k pertinent qualitativement.
- **Dépendances** : Phases 2 (, 5 pour le filtrage par catégorie).
- **Estimation** : 5 sessions.
- **Priorité** : Critique.
- **Risques** : choix vector DB (ADR-004), qualité des embeddings FR.

### Phase 7 — Évaluation RAG (RAGAS) + génération
- **Objectif** : prouver scientifiquement la qualité du RAG + générer une réponse avec citations.
- **Prérequis** : Phase 6.
- **Livrables** : jeu d'éval RAG, **métriques RAGAS** (Precision@k, Recall@k, MRR, nDCG,
  Faithfulness, Answer Relevancy, Context Precision/Recall, Hallucination Rate), génération de
  réponse légère **avec citations**, **LLM-as-a-Judge**, comparatif lexical vs sémantique.
- **Critères** : Context Recall ≥ 0.80, Faithfulness ≥ 0.85 ; tableau comparatif produit.
- **Dépendances** : Phase 6.
- **Estimation** : 4 sessions.
- **Priorité** : Critique.
- **Risques** : hallucinations, coût/latence → guardrails, fallback.

### Phase 8 — Backend (durcissement + intégration)
- **Objectif** : industrialiser l'API et y intégrer le nouveau modèle + RAG.
- **Prérequis** : Phases 5, 7.
- **Livrables** : contrat OpenAPI versionné, sécurité (RBAC, secrets, rate limiting,
  anti-injection), intégration CamemBERT+RAG sémantique, **fix `/ingest`**, séparation en couches.
- **Critères** : endpoints conformes au contrat, tests d'intégration verts, secrets non exposés.
- **Dépendances** : Phases 5, 7.
- **Estimation** : 4 sessions.
- **Priorité** : Haute.
- **Risques** : régressions → tests d'intégration.

### Phase 9 — Frontend (connexion + finalisation)
- **Objectif** : rendre l'application fonctionnelle de bout en bout.
- **Prérequis** : Phase 8.
- **Livrables** : `environment.ts` configuré, **alignement enum statuts + modèle `Ticket`**, page
  de détail, **guards** d'auth/rôles, restitution **confiance + sources RAG (citations)**, capture
  de **feedback** utilisateur.
- **Critères** : parcours client + admin complets en démo ; pas d'appel API en échec.
- **Dépendances** : Phase 8.
- **Estimation** : 5 sessions.
- **Priorité** : Haute.
- **Risques** : désalignement contrat → s'appuyer sur OpenAPI.

### Phase 10 — MLOps léger
- **Objectif** : reproductibilité et traçabilité du cycle de vie modèles.
- **Prérequis** : Phases 5, 6.
- **Livrables** : pipeline **DVC** complet (preprocess→split→train→eval), **MLflow registry**,
  model/data cards, monitoring minimal (métriques IA).
- **Critères** : `dvc repro` de bout en bout ; modèles versionnés et comparables.
- **Dépendances** : Phases 5, 6.
- **Estimation** : 4 sessions.
- **Priorité** : Haute.
- **Risques** : dette MLOps → garder léger.

### Phase 11 — Déploiement (Docker, CI/CD)
- **Objectif** : packager et automatiser.
- **Prérequis** : Phases 8, 9.
- **Livrables** : Dockerfiles, `docker-compose` multi-services, **CI/CD** (lint, tests, build,
  scan), observabilité de base.
- **Critères** : `docker-compose up` lance tout ; pipeline CI vert.
- **Dépendances** : Phases 8, 9.
- **Estimation** : 3–4 sessions.
- **Priorité** : Moyenne.
- **Risques** : sur-dimensionnement (pas de K8s) → compose suffit.

### Phase 12 — Tests & validation
- **Objectif** : prouver la qualité et l'atteinte des exigences.
- **Prérequis** : Phases 8–11.
- **Livrables** : tests unitaires/intégration, test de charge, **matrice exigences→résultats**,
  étude utilisateur légère.
- **Critères** : couverture cible atteinte, ENF validées (P95), exigences tracées.
- **Dépendances** : Phases 8–11.
- **Estimation** : 4 sessions.
- **Priorité** : Haute.
- **Risques** : sur-interprétation sur données synthétiques → le dire.

### Phase 13 — Optimisation
- **Objectif** : améliorer performance et coût.
- **Prérequis** : Phase 12.
- **Livrables** : optimisations latence, calibration finale, mesure coût d'inférence.
- **Critères** : cibles ENF tenues, coût documenté.
- **Dépendances** : Phase 12.
- **Estimation** : 2–3 sessions.
- **Priorité** : Moyenne.
- **Risques** : faible.

### Phase 14 — Documentation & mémoire PFE
- **Objectif** : produire le mémoire et les livrables académiques.
- **Prérequis** : transverse, alimenté en continu.
- **Livrables** : mémoire (chapitres alignés sur le cahier des charges), diagrammes, model/data
  cards, annexes. Suivi dans [PFE_PROGRESS.md](PFE_PROGRESS.md).
- **Critères** : tous les chapitres rédigés et relus.
- **Dépendances** : toutes phases.
- **Estimation** : continu, intensif Mois 6.
- **Priorité** : Critique.
- **Risques** : rédaction repoussée → écrire au fil de l'eau.

### Phase 15 — Préparation soutenance
- **Objectif** : réussir la défense.
- **Prérequis** : Phase 14.
- **Livrables** : slides, **démo répétée**, anticipation des questions du jury.
- **Critères** : démo fluide, timing maîtrisé.
- **Dépendances** : Phase 14.
- **Estimation** : 3 sessions.
- **Priorité** : Critique.
- **Risques** : panne de démo → enregistrer une vidéo de secours.

---

## 6. Checklists par phase

> Chaque tâche est atomique (réalisable en 1 session). On coche au fil de l'eau.

### Phase 0 — Initialisation
- [ ] Créer les 11 fichiers de pilotage
- [ ] Écrire/compléter `.gitignore` (node_modules, venv, *.pkl, data lourde, .env)
- [ ] Figer l'environnement Python (`requirements.txt` vérifié / venv)
- [ ] Initialiser et configurer DVC
- [ ] Premier commit de la gouvernance (sur une branche)
- [ ] Vérifier la cohérence inter-fichiers (cycle workflow à blanc)

### Phase 1 — Cadrage & SRS
- [ ] Figer problématique + hypothèses + questions de recherche
- [ ] Rédiger objectifs SMART
- [ ] Synthétiser l'état de l'art (NLP FR, RAG, LLM)
- [ ] Lister les exigences fonctionnelles (MoSCoW)
- [ ] Lister les exigences non-fonctionnelles (perf, sécurité, RGPD, accessibilité)
- [ ] Construire la matrice de traçabilité exigences ↔ tests

### Phase 2 — Data Engineering & RGPD
- [ ] Audit qualité (doublons, NaN, déséquilibre, fuite)
- [ ] Définir et appliquer l'anonymisation (PII : demandeur, filiale…)
- [ ] Rédiger le registre de traitement RGPD
- [ ] Écrire les stages DVC (preprocess → split → rag)
- [ ] Rédiger le dictionnaire de données + data card
- [ ] Documenter la stratégie d'acquisition de données réelles

### Phase 3 — EDA
- [ ] Nettoyer le notebook 01
- [ ] Régénérer les figures finales
- [ ] Consolider le rapport d'audit

### Phase 4 — ML baseline
- [ ] Scripter le pipeline baseline (hors notebook)
- [ ] Calibrer la confiance (Platt/température) + courbe ECE
- [ ] Ajouter XAI (SHAP/LIME)
- [ ] Rédiger le rapport d'éval baseline + model card

### Phase 5 — Fine-Tuning CamemBERT
- [ ] Construire le dataset HuggingFace
- [ ] Tokenisation CamemBERT
- [ ] Split anti-fuite (textes uniques)
- [ ] Configurer LoRA (r, alpha, dropout)
- [ ] Entraînement GPU local
- [ ] Évaluation (F1-macro, rappel Sécurité, matrice de confusion)
- [ ] Benchmark vs LogReg
- [ ] Calibration
- [ ] Log MLflow + model card
- [ ] Sauvegarde de l'adaptateur
- [ ] Documenter

### Phase 6 — RAG sémantique
- [ ] Choisir la base vectorielle (ADR-004)
- [ ] Chunking de la base de connaissance
- [ ] Choisir/charger les embeddings FR
- [ ] Indexer la base
- [ ] Implémenter le retrieval (+ filtre catégorie)
- [ ] Intégrer au service d'inférence

### Phase 7 — Évaluation RAG + génération
- [ ] Construire le jeu d'évaluation RAG (requêtes + vérités terrain)
- [ ] Mesurer Precision@k / Recall@k / MRR / nDCG
- [ ] Mesurer Faithfulness / Answer Relevancy / Context Precision-Recall (RAGAS)
- [ ] Implémenter la génération de réponse avec citations
- [ ] Mettre en place LLM-as-a-Judge
- [ ] Comparatif lexical vs sémantique

### Phase 8 — Backend
- [ ] Figer le contrat OpenAPI (`/api/v1`)
- [ ] Durcir la sécurité (RBAC, secrets, rate limiting, anti-injection)
- [ ] Intégrer CamemBERT + RAG sémantique dans les services
- [ ] Réparer et enregistrer `/ingest`
- [ ] Refactor en couches (services/repositories)
- [ ] Tests d'intégration API

### Phase 9 — Frontend
- [ ] Configurer `environment.ts`
- [ ] Aligner enum statuts + modèle `Ticket` sur le backend
- [ ] Créer la page de détail ticket (+ routes)
- [ ] Ajouter les guards d'auth/rôles + intercepteur HTTP
- [ ] Afficher confiance + sources RAG (citations cliquables)
- [ ] Capturer le feedback utilisateur (👍/👎 + correction)

### Phase 10 — MLOps
- [ ] Compléter le pipeline DVC de bout en bout
- [ ] Mettre en place MLflow Registry
- [ ] Rédiger model cards / data cards
- [ ] Monitoring minimal (métriques IA)

### Phase 11 — Déploiement
- [ ] Dockerfile API + Dockerfile front
- [ ] `docker-compose` multi-services
- [ ] Pipeline CI/CD (lint, tests, build, scan)
- [ ] Observabilité de base (logs structurés)

### Phase 12 — Tests & validation
- [ ] Tests unitaires (NLP, RAG, services)
- [ ] Tests d'intégration end-to-end
- [ ] Test de charge (latence P95)
- [ ] Matrice exigences → résultats
- [ ] Étude utilisateur légère

### Phase 13 — Optimisation
- [ ] Optimiser la latence d'inférence
- [ ] Calibration finale
- [ ] Mesurer le coût d'inférence

### Phase 14 — Documentation & mémoire
- [ ] Rédiger les chapitres (voir PFE_PROGRESS.md)
- [ ] Produire les diagrammes
- [ ] Finaliser annexes (cards, ADR, OpenAPI)

### Phase 15 — Soutenance
- [ ] Préparer les slides
- [ ] Répéter la démo (+ vidéo de secours)
- [ ] Préparer les Q/R du jury

---

## 7. Workflow obligatoire (10 étapes)

1. **Relire** PLAN.md.
2. **Identifier** la phase active.
3. **Identifier** la prochaine tâche.
4. **Vérifier** les dépendances.
5. **Développer uniquement** cette tâche.
6. **Tester**.
7. **Mettre à jour** PLAN.md (+ TASKS.md, CHANGELOG.md).
8. **Marquer** la tâche comme terminée (cocher).
9. **Résumer** les modifications.
10. **Proposer** la prochaine tâche.

> Ne jamais sauter une étape.

---

## 8. Règles de travail

- Une seule **grosse** tâche à la fois ; jamais plusieurs en parallèle.
- Toujours **terminer** complètement une tâche avant la suivante.
- Toujours **mettre à jour** PLAN.md après chaque tâche.
- Toujours vérifier la **cohérence avec l'architecture** ([ARCHITECTURE.md](ARCHITECTURE.md)).
- Toujours vérifier la **cohérence avec les objectifs du PFE**.
- Toujours **signaler la dette technique** (la consigner ici + RISKS.md).
- Toujours **proposer** des améliorations possibles **sans les implémenter** (→ BACKLOG.md).

---

## 9. Définition de « Terminé » (DoD)

Une tâche n'est *terminée* que si **tous** ces points sont vrais :
- [ ] Le code fonctionne.
- [ ] Les tests passent.
- [ ] La documentation est à jour.
- [ ] Le code est propre.
- [ ] Les fichiers concernés sont identifiés.
- [ ] Les critères d'acceptation sont validés.
- [ ] Aucune régression n'a été introduite.

---

## 10. Tableau de bord

| Indicateur | Valeur |
|---|---|
| **Progression globale** | **~5 %** (gouvernance en place) |
| **Phase actuelle** | Phase 0 — Initialisation |
| **Tâche actuelle** | Créer les 11 fichiers de pilotage |
| **Tâches terminées** | Création du système documentaire (en cours) |
| **Tâches restantes** | Phases 1 → 15 |
| **Prochaine étape** | `.gitignore` + figer l'environnement + init DVC |
| **Risques ouverts** | Données synthétiques · RGPD · délai 6 mois · dette intégration front/back (voir [RISKS.md](RISKS.md)) |
| **Dette technique** | Couches backend vides · `/ingest` cassé · front non connecté |
| **Fonctionnalités futures** | Voir [BACKLOG.md](BACKLOG.md) (QLoRA, hybrid search, re-ranking, agents, K8s…) |

> **Calcul de la progression** : moyenne pondérée de l'avancement des 15 phases par leur priorité.
> Mis à jour à chaque fin de tâche.
