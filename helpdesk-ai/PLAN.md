# PLAN.md — Plan directeur du PFE `helpdesk-ai`

> **Source de vérité unique du projet.** Aucune fonctionnalité ne doit être développée sans être
> prévue ici. À chaque session : relire ce fichier → identifier la phase/tâche active → exécuter
> **une seule** tâche → tester → mettre à jour ce fichier → cocher → résumer → proposer la suite.
>
> **Méta** — Dernière mise à jour : **2026-07-29** · Phase active : **Phase 13** (Phases 0–12
> terminées, Phase 9 complétée rétroactivement le 2026-07-06 avec la refonte Stitch, corrections
> UX complémentaires le 2026-07-16 : sidebar noire, mode sombre, formulaire ticket, routing,
> expiration de session. Depuis, hors découpage strict des phases ML — boucle de feedback RAG
> (`rag_score`, détection de cas nouveau, archivage validé par l'admin), refonte complète du
> workflow de traitement des tickets (file d'approbation simplifiée, écran de clôture en 2 étapes,
> édition possible après clôture), et migration infrastructure SQLite→PostgreSQL /
> TinyDB→ChromaDB (ADR-004, ADR-006) — le RAG est maintenant interrogé en direct sur les
> résolutions admin, pas seulement archivé. Voir [CHANGELOG.md](CHANGELOG.md) pour le détail daté.
> · Périmètre : **Cœur rehaussé (Must)** · Durée : **stage 6 mois** · Compute : **GPU local**.
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
| Critère | Cible | Mesuré (2026-07-05) |
|---|---|---|
| F1-macro classification (test dé-dupliqué) | ≥ 0.85 | 0.685 (heuristiques) — 🔴 non atteint ; ⚠️ mesure non représentative (split sans exemples Backup/Communication, voir R-14) |
| Rappel classe *Sécurité* | ≥ 0.70 | 0.364 — 🔴 non atteint (matrice exigences, [CADRAGE_SRS.md](CADRAGE_SRS.md) §5) |
| RAG : Context Recall | ≥ 0.80 | 0.028 — 🔴 non atteint (RAGAS simplifié, Phase 7) |
| RAG : Faithfulness | ≥ 0.85 | 1.0 (template-based, Phase 7) — ✅ |
| Latence prédiction P95 | ≤ 300 ms | 330 ms séquentiel, 15022 ms à 20 req. concurrentes — 🔴 non atteint (`metrics/load_test.json`, cause identifiée, optimisation Phase 13) |
| Front ↔ back fonctionnel de bout en bout | Démo création→validation→résolution | ✅ Docker validé (Phase 11–12) |
| Conformité RGPD | Anonymisation + registre de traitement | 🔴 non fait (Phase 2 reliquat) |
| Mémoire + soutenance | Livrés dans les 6 mois | En cours |

---

## 2. État actuel du projet

Légende : ✅ Terminé · 🟡 En cours · 🔴 À faire

| État | Élément | Avancement | Qualité | Dette technique | Remarques |
|---|---|---|---|---|---|
| ✅ | EDA + preprocessing (notebooks 01–02) | 90 % | Bonne | Notebooks à figer en scripts | À consolider/documenter (Phase 3). |
| ✅ | Baseline ML TF-IDF + LogReg/LinearSVC | 100 % | F1-macro heuristiques **0.685** (protocole DVC) ⚠️ **5/8 classes** — R-14 ; **0.5673** sur protocole stratifié 8 classes | Sur-apprentissage (CV=1.0) lié à la redondance du corpus | Référence de comparaison ; pipeline DVC (Phase 10). Seul le 0.5673 est comparable à CamemBERT. |
| ✅ | RAG lexical (`src/rag/engine.py`) | 100 % | Bonne (fallback) | — | Conservé comme fallback du RAG hybride (Phase 13). |
| ✅ | Backend cœur (auth JWT, tickets, approbation, historique) | 100 % | Bonne | Couches services/repos minces mais fonctionnelles | Durci Phase 8 (CORS, rate limiting, OpenAPI /api/v1). |
| ✅ | Documentation (cahier des charges, workflow) | 85 % | Très bonne | — | Base solide pour le mémoire. |
| ✅ | Frontend Angular 21 | 100 % | Bonne | — | Connecté au backend (Phase 9) : auth, guards, pages détail, intercepteur JWT. Les 15 écrans redessinés (design Stitch, thème clair) avec données réelles (2026-07-06). |
| ✅ | Gestion des comptes / utilisateurs (admin) | 100 % | Bonne | — | CRUD admin-only (`api/routers/admin.py`), mot de passe temporaire auto-généré, `first_login` forcé via guards Angular jusqu'au changement de mot de passe (2026-07-06). |
| ✅ | Couches `services/`, `db/repositories/`, `middleware/` | 90 % | Bonne | Code mort supprimé (`api/db/__init__.py`, Phase 12) | Rate limiting via dépendance FastAPI. |
| ✅ | Endpoint `/ingest` | Fonctionnel | Bonne | — | Réécrit Phase 8 : API key, ORM, validation Pydantic. |
| ✅ | CamemBERT fine-tuné (LoRA) + benchmark | 100 % | F1=0.5685 | features enrichies | Phase 5 — à parité avec TF-IDF+heuristiques mais sans règles codées. Infrastructure/Sécurité à 0.00. |
| ✅ | RAG sémantique (embeddings FR + FAISS) | 100 % | Score cosinus 0.93 vs 0.76 lexical (+0.17) | FAISS local | Phase 6 terminée. |
| ✅ | RAG hybride (sémantique + lexical) | 100 % | score = 0.5×sém + 0.5×lex | Gain P@3/MRR à mesurer (notebook à ré-exécuter) | Phase 13 Semaine 2. Validé bout-en-bout en Docker (Phase 12, 2026-07-05). |
| ✅ | Évaluation RAG (RAGAS) + génération | 100 % | P@3 0.30 sém/0.42 lex, MRR 0.56/0.65 | RAGAS simplifié (template-based) | Phase 7 terminée. |
| 🔴 | RGPD / anonymisation | 0 % | — | Données personnelles non traitées | Phase 2 (reliquat). |
| ✅ | MLOps (DVC, registre de modèles, monitoring) | 100 % | F1-macro heuristiques 0.685 tracké ; **0.822 sur les 5 classes évaluables** | Model cards à enrichir ; aucun trafic de production pour alimenter les boucles (R-20) | Phase 10 : 8 stages DVC, registre avec promotion/rollback, deux boucles d'amélioration ([MLOPS.md](MLOPS.md)). |
| ✅ | Docker / CI-CD / monitoring | 100 % | `docker compose up` opérationnel | Pas de scan de sécurité d'image | Phase 11 : 3 services + CI 3 jobs. |
| ✅ | Tests automatisés + validation | 100 % | 41 tests unitaires + 18/18 tests d'intégration + test de charge + matrice exigences→résultats + étude utilisateur (couverture 74 % local / 22 % en CI) | Couverture non vérifiée par la CI (best_pipeline.pkl gitignoré) ; 2 régressions UX trouvées (R-15, R-16) | Phase 12 terminée (2026-07-05) ; matrice = [CADRAGE_SRS.md](CADRAGE_SRS.md) §5-6. |
| 🔴 | Mémoire PFE | 10 % | — | — | Phase 14 (continu). |

---

## 3. Architecture globale (résumé)

> Détail complet et diagrammes dans [ARCHITECTURE.md](ARCHITECTURE.md).

| Module | État | Stack cible |
|---|---|---|
| Frontend | 🟡 | Angular 21, Material, Chart.js |
| Backend / API | ✅🟡 | FastAPI, Pydantic, OpenAPI |
| Base de données | ✅ | PostgreSQL (+ ChromaDB pour la base de connaissances RAG) |
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
- **Risques** : non-conformité RGPD ; non-généralisation (redondance du corpus) — *à surveiller*.

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
- **Risques** : sur-interprétation liée à la redondance du corpus → le dire.

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

### Phase 0 — Initialisation ✅ (terminée 2026-06-26)
- [x] Créer les 11 fichiers de pilotage
- [x] Écrire/compléter `.gitignore` (node_modules, venv, *.pkl, data lourde, .env)
- [x] Figer l'environnement Python (`requirements.txt` vérifié / venv)
- [x] Initialiser et configurer DVC (déjà initialisé, vérifié)
- [x] Premier commit de la gouvernance (branche `chore/gouvernance-pfe`, 3 commits)
- [x] Vérifier la cohérence inter-fichiers (cycle workflow déroulé)

### Phase 1 — Cadrage & SRS 🟡 (v0.1 rédigée → `CADRAGE_SRS.md`, en validation)
- [x] Figer problématique + hypothèses + questions de recherche
- [x] Rédiger objectifs SMART
- [x] Synthétiser l'état de l'art (NLP FR, RAG, LLM)
- [x] Lister les exigences fonctionnelles (MoSCoW)
- [x] Lister les exigences non-fonctionnelles (perf, sécurité, RGPD, accessibilité)
- [x] Construire la matrice de traçabilité exigences ↔ tests
- [ ] **Validation par l'étudiant** des points 🟠 (entreprise, données réelles, RGPD, date, périmètre)

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
- [x] Construire le dataset HuggingFace
- [x] Tokenisation CamemBERT
- [x] Split anti-fuite (GroupShuffleSplit par Titre — 46 train / 12 test, overlap 0)
- [x] Configurer LoRA (r=8, alpha=16, modules query+value)
- [x] Entraînement GPU local (MX130, 10 epochs, FP32)
- [x] Features enrichies (`text_enriched` : type+priorité simplifiés + titre + description) → F1 0.5325 → 0.5685
- [x] Évaluation (F1-macro 0.5685 / Accuracy 0.6873, matrice de confusion `cam_01`)
- [x] Benchmark vs LogReg (CamemBERT 0.5685 ≈ TF-IDF+heuristiques 0.5673 — écart +0.0012 dans le bruit, mais sans règles codées)
- [x] Analyse confiance / HITL (seuil 0.4 → 91 % auto-route @ 70 % précision)
- [x] Sauvegarde de l'adaptateur (`models/camembert_lora_adapter/`)
- [x] Documenter (CHANGELOG, `camembert_metadata.json`)
- [ ] Calibration fine (température/Platt) — *renvoyée Phase 13*
- [ ] Log MLflow + model card — *renvoyé Phase 10 (MLOps)*

### Phase 6 — RAG sémantique
- [x] Choisir la base vectorielle (ADR-004 → FAISS local, sans serveur)
- [x] Choisir/charger les embeddings FR (`paraphrase-multilingual-mpnet-base-v2`, 768d)
- [x] Encoder la base de connaissance (476 tickets résolus → vecteurs FAISS IndexFlatIP)
- [x] Implémenter le retrieval (+ filtre catégorie via index FAISS dédié par classe)
- [x] Évaluation réaliste (query = titre+description ; score cosinus 0.93 sem vs 0.76 lex)
- [x] Sauvegarde `models/semantic_rag/` + `semantic_rag_metadata.json`
- [ ] Intégrer au service d'inférence backend — *renvoyé Phase 8 (Backend)*

### Phase 7 — Évaluation RAG + génération ✅ (terminée 2026-07-03)
- [x] Construire le jeu d'évaluation RAG (80 requêtes stratifiées, GT=même catégorie)
- [x] Mesurer Precision@k / Recall@k / MRR / nDCG (sémantique P@3=0.30, MRR=0.56 ; lexical P@3=0.42, MRR=0.65)
- [x] Mesurer Faithfulness / Answer Relevancy / Context Precision-Recall (RAGAS simplifié sans LLM externe)
- [x] Implémenter la génération de réponse avec citations (template-based, Faithfulness=1.0)
- [x] Comparatif lexical vs sémantique (sémantique : score moyen 0.69 vs 0.18 lexical ★)
- [ ] LLM-as-a-Judge (renvoyé BACKLOG — optionnel pour PFE, résultats suffisants)

### Phase 8 — Backend ✅ (terminée 2026-07-03)
- [x] Figer le contrat OpenAPI (`/api/v1`) — tous les routers préfixés sous `/api/v1`
- [x] Durcir la sécurité (CORS configurable, rate limiting login 429, anti-injection Pydantic, API key ingest)
- [x] Intégrer CamemBERT + RAG sémantique dans les services (`predictor.py` → SemanticRAGEngine FAISS, fallback lexical)
- [x] Réparer et enregistrer `/ingest` (`api/routers/ingest.py` — auth API key, ORM, validation, utilisateur système)
- [x] Refactor en couches (`ticket_service.py`, `rag_service.py`, `auth_middleware.py` remplis)
- [x] Tests d'intégration API (`tests/test_api_integration.py` — 18/18 passent depuis correctif bcrypt Phase 12)

### Phase 9 — Frontend ✅ (terminée 2026-07-06)
- [x] Configurer `environment.ts`
- [x] Aligner enum statuts + modèle `Ticket` sur le backend
- [x] Créer la page de détail ticket (+ routes)
- [x] Ajouter les guards d'auth/rôles + intercepteur HTTP
- [x] Afficher confiance + sources RAG (citations cliquables)
- [x] Capturer le feedback utilisateur (👍/👎 + correction) — persisté via `POST /tickets/{id}/feedback` (corrige R-15/EF-13)
- [x] Refonte des 15 écrans (client + admin) via maquettes Stitch, fabrications retirées au profit de données réelles
- [x] Module gestion des comptes : CRUD admin-only, mot de passe temporaire, `first_login` obligatoire

### Phase 10 — MLOps ✅ TERMINÉ (2026-08-22) — voir [MLOPS.md](MLOPS.md)
- [x] Pipeline DVC de bout en bout — **8 stages** : `preprocess → split → build_dataset →
      train → promote` (classification) et `rag_build / rag_semantic_build → rag_eval`
      (connaissances). Les deux chaînes partent de `split` et ne se rejoignent jamais
- [x] Registre de modèles avec promotion, rejet motivé et rollback
      (`src/registry/model_registry.py`). Le Model Registry MLflow fonctionne avec le store
      fichier du projet mais MLflow 3.6 le déclare déprécié : il est alimenté **en plus**,
      jamais à la place
- [x] Jeu de test **gelé** (`data/reference/`, empreinte SHA-256) — sans référence stable,
      comparer deux modèles ne mesure rien
- [x] Boucle de collecte des tickets validés avec qualification de la force de l'étiquette
- [x] Monitoring ML et RAG (`src/monitoring/`) + déclencheurs de réentraînement écrivant un
      rapport, jamais une action
- [x] Cycle de vie des connaissances RAG : contrôle qualité, statuts, versionnement, évaluation
- [ ] Model cards / data cards — non rédigées. Le lineage par version
      (`models/registry/v*/lineage.json`) en contient déjà la matière : dataset, jeu de test,
      métriques, run MLflow

### Phase 11 — Déploiement ✅ TERMINÉ (2026-07-04)
- [x] Dockerfile API + Dockerfile front
- [x] `docker-compose` multi-services
- [x] Pipeline CI/CD (lint, tests, build) — scan de sécurité d'image non fait (BACKLOG)
- [x] Observabilité de base (healthchecks + logs stdout/stderr)

### Phase 12 — Tests & validation ✅ TERMINÉ (2026-07-05)
- [x] Tests unitaires (NLP, RAG, services) — 41 tests : `test_preprocess.py`, `test_heuristics.py`, `test_rag_engine.py`, `test_hybrid_engine.py`
- [x] Tests d'intégration end-to-end (Phase 8 : `test_api_integration.py`, **18/18 passent** — non branché en CI, cf. note plus haut)
- [x] Test de charge (latence P95) — `scripts/load_test.py` + `metrics/load_test.json` : critère
      ≤300ms non atteint (330ms séquentiel → 15s à 20 req. concurrentes, 19% timeouts) ; cause
      identifiée (endpoint synchrone/CPU-bound, GIL, 2 workers) ; optimisation → Phase 13.
      A aussi révélé et corrigé un 4ᵉ bug de déploiement (healthcheck frontend `localhost`→IPv6).
- [x] **Test manuel navigateur** (connexion client réelle) — a révélé et corrigé un **5ᵉ bug** :
      seeding utilisateurs cassé par incompatibilité `bcrypt`/`passlib` (aucun compte jamais créé
      en base) → `bcrypt==4.0.1` épinglé, résout aussi la dette technique des 4 tests auth skippés.
- [x] **Matrice exigences → résultats** (`CADRAGE_SRS.md` §5) — 9/17 EF, 5/14 ENF pleinement
      atteints ; découverte critique R-14 (split de test sans exemples Backup/Communication)
- [x] **Étude utilisateur légère** (`CADRAGE_SRS.md` §6) — golden path Client→Admin→Client
      confirmé fonctionnel ; découverte R-15 (feedback client trompeur, à corriger avant démo
      jury) et R-16 (pas d'auto-routage réel par confiance)

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
| **Progression globale** | **~86 %** (Phases 0–12 terminées, Phase 9 complétée rétroactivement, Phase 13 partiellement avancée + travaux d'ingénierie hors-phases significatifs — voir ci-dessous) |
| **Phase actuelle** | Phase 9 — Frontend ✅ **terminée** (2026-07-06) · Phase 12 — Tests & validation ✅ **terminée** (2026-07-05) · travaux 2026-07-16→29 hors découpage strict (UX + boucle RAG + workflow tickets + infra) |
| **Tâche actuelle** | Aucune — prochaine étape à décider : activer ou non `split.strategy: stratified_group` (R-14), puis Phase 14 (mémoire PFE) |
| **Tâches terminées** | Phase 0 · Phase 1 (SRS v0.1) · Phase 3 (EDA) · Phase 4 (baseline ML) · Phase 5 (CamemBERT LoRA F1=0.5685) · Phase 6 (RAG sémantique FAISS score 0.93) · Phase 7 (RAGAS : AR=0.58, Faith=1.0) · Phase 8 (Backend API v1.1) · **Phase 9 (Frontend connecté + 15 écrans redessinés Stitch + module gestion des comptes, 2026-07-06)** · Phase 10 (MLOps DVC+MLflow, F1 heuristiques 0.685) · Phase 11 (Docker + CI/CD) · Phase 12 (tests, matrice exigences, étude utilisateur) · Phase 13 Semaines 1–2 (heuristiques + RAG hybride) · **Boucle de feedback RAG** (`rag_score`, détection cas nouveau, archivage validé admin, 2026-07-16) · **Refonte workflow tickets** (file d'approbation simplifiée, écran de clôture en 2 étapes avec catégorie/priorité/classification/statut regroupés, édition post-clôture, 2026-07-29) · **Migration PostgreSQL + ChromaDB** (ADR-004, ADR-006 — RAG interrogé en direct sur les résolutions admin, 2026-07-29) · **Industrialisation MLOps** (jeu de test gelé, registre de modèles avec porte de promotion et rollback, collecte des tickets validés, cycle de vie des connaissances RAG, monitoring — 2026-08-22, [MLOPS.md](MLOPS.md)) |
| **Tâches restantes** | Phase 13 Semaine 3 (conditionnelle) · Phases 14–15 · calibrage des seuils MLOps après mise en exploitation (R-20) · annotation du jeu d'évaluation RAG (R-22) |
| **Prochaine étape** | Trancher R-14 (référence de test à 5 ou 8 classes), puis démarrer Phase 14 (mémoire PFE) |
| **Risques ouverts** | F1 classification ML seul faible (zero-shot par Titre) · split de test sans exemples Applicatifs/Backup/Communication (R-14, atténué : test gelé + métrique sur classes évaluables) · boucles MLOps sans données réelles (R-20) · fuite par paraphrase non détectée (R-21) · jeu annoté RAG absent (R-22) · pas d'auto-routage par confiance (R-16) · RGPD non traité · délai 6 mois · latence P95 non conforme sous charge (R-13, voir [RISKS.md](RISKS.md)) — *R-15 (feedback client trompeur) clos le 2026-07-06* |
| **Dette technique** | RGPD à faire (Phase 2 reliquat) · `test_api_integration.py` non branché en CI (nécessite `models/best_pipeline.pkl`, ignoré par git ; sa collecte en local est en revanche réparée depuis le 2026-08-22) · model cards non rédigées · pas de scan sécurité d'image Docker · LLM-as-a-Judge BACKLOG · EF-14 « génération LLM » en réalité template-based (à nuancer au mémoire) · seuil 0.40 (routage bas niveau) et 0.50 (`NOVELTY_THRESHOLD`) codés en dur dans `tickets.py` · incohérence nommage `priorite`/`priorite_saisie` · priorité/classification affichées comme « Résultat ML » ne sont pas de vraies prédictions entraînées (valeurs de départ confirmées par l'admin — à nuancer au mémoire, même logique qu'EF-14) |
| **Fonctionnalités futures** | Voir [BACKLOG.md](BACKLOG.md) (LLM-as-a-Judge, QLoRA, hybrid search avancé, re-ranking, agents, K8s…) |

> **Calcul de la progression** : moyenne pondérée de l'avancement des 15 phases par leur priorité.
> Mis à jour à chaque fin de tâche.
