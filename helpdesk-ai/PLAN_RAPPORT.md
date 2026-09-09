# PLAN_RAPPORT.md — Plan détaillé du mémoire PFE

> Structure calquée sur les deux rapports de référence encadrés par M. Ahmed Dhouibi
> (Sarra Mzali / TEK-UP / PwC — 134 p. ; Hamad Wafa / ISET Rades / Tunisie Telecom — 119 p.),
> adaptée au contenu réel du projet HelpDesk AI.
> Organisation **par sprints** (et non par thèmes) conformément au format attendu.
> Volume cible : **110–135 pages**.
> Template : `latex-tekup/Rapport PFE TEKUP LATEX/`

---

---

## ÉTAT DE LA RÉDACTION — au 2026-09-08

> Suivi détaillé et figures restant à produire : [PFE_PROGRESS.md](PFE_PROGRESS.md).
> Sources LaTeX : `../report/`. Le document compile à **115 pages, sans erreur**.

| # | Chapitre | Pages | Cible | État |
|---|---|---|---|---|
| — | Introduction générale | 1 | 2–3 p. | 🟡 à étoffer en fin de rédaction |
| 1 | Contexte général du projet | 2–9 | 12–15 p. | 🟡 rédigé, sous la cible (bloqué sur les réponses OTBS) |
| 2 | Concepts fondamentaux et spécification | 10–25 | 15–18 p. | ✅ rédigé, repris le 2026-09-07 |
| 3 | Sprint 1 — Données et gouvernance | 26–39 | 14–16 p. | ✅ rédigé et vérifié |
| 4 | Sprint 2 — Modélisation IA | 40–55 | 16–18 p. | ✅ rédigé, corrigé après l'audit des règles |
| 5 | Sprint 3 — RAG et assistant LLM | 56–73 | 16–18 p. | ✅ rédigé et relu le 2026-09-08, 18 pages |
| 6 | Sprint 4 — Développement de l'application | 74–93 | 16–18 p. | ✅ rédigé le 2026-09-08, 20 p. (Conception en 6 p.) |
| 7 | Sprint 5 — Industrialisation et validation | 94 | 14–16 p. | 🔴 **prochain à rédiger** |
| — | Conclusion générale | 95 | 2–3 p. | 🔴 balises seules |
| — | Annexes | 98 | — | 🔴 balises seules |
| — | Résumés FR et EN | `global_config.tex` | 1 p. | 🔴 à rédiger en dernier |

**Écart à l'ordre initialement recommandé.** Les chapitres 1 et 2 ont été rédigés avant le
chapitre 5, contrairement à l'ordre proposé plus bas. Le chapitre 2 ayant servi à fixer le
vocabulaire réutilisé aux chapitres 3 et 4, l'écriture s'est faite dans l'ordre de lecture.
L'ordre restant est inchangé : 5, puis 6 et 7, puis l'introduction, la conclusion et les résumés.

**Conventions de rédaction en vigueur.** Style académique, « nous » de modestie, aucune métrique
inventée : toute valeur citée renvoie à un fichier du dépôt. En cas de doute, la valeur est
laissée entre crochets plutôt que devinée. Les limites du travail sont énoncées explicitement.

**Trame des chapitres de sprint**, alignée sur le rapport de référence de Rania Dridi
(`../exemple_de_rapport/Rania-DRIDI-22159-2.pdf`), appliquée depuis le chapitre 6 :

1. Objectifs du sprint (liste)
2. Backlog du sprint (tableau : référence, récit utilisateur, priorité, critère de recette)
3. Spécification des besoins fonctionnels (diagramme de cas d'utilisation du sprint)
4. Technologies utilisées (liste, nom en gras puis paragraphe de justification)
5. **Conception** : diagramme de contexte (C4 niveau 1), architecture générale (C4 niveau 2),
   diagramme de classes, diagramme de séquence, diagramme d'états
6. Réalisation
7. Bilan du sprint (tableau exigences → résultats)

## PAGES LIMINAIRES (`frontmatter`)

| Élément | Fichier LaTeX | État |
|---|---|---|
| Page de garde | `tpl/cover_page.tex` | ✅ renseignée via `global_config.tex` |
| Autorisations de dépôt / signatures | `tpl/signatures.tex` | 🟡 rédigée, **reste à faire signer** |
| Dédicaces | `dedicaces.tex` | ✅ rédigées |
| Remerciements | `remerciement.tex` | ✅ rédigés |
| Table des matières | auto | — |
| Liste des figures | auto | — |
| Liste des tableaux | auto | — |
| Liste des abréviations | `acronymes.tex` | ✅ rédigée |

**Titre proposé** : *Conception et développement d'une plateforme intelligente de
classification et d'assistance à la résolution de tickets informatiques par NLP et RAG*

---

## INTRODUCTION GÉNÉRALE (2–3 p.)

- Contexte de la transformation digitale et de la charge des services support IT
- Enjeu de l'automatisation assistée par IA
- Annonce de la problématique et des objectifs
- Annonce du plan du mémoire

---

## CHAPITRE 1 — CONTEXTE GÉNÉRAL DU PROJET (12–15 p.)

**Introduction**

## CHAPITRE 1 — CONTEXTE GÉNÉRAL ET CADRE DU PROJET (12–15 p.)

### Introduction

### 1.1  Présentation de l'organisme d'accueil
       1.1.1  Le groupe OneTech et sa filiale OTBS
       1.1.2  Le service support informatique
#### 1.2  Contexte et analyse de l'existant
       1.2.1  Le traitement des tickets au sein du service
       1.2.2  Les solutions de gestion de tickets du marché
       1.2.3  Limites de l'existant et problématique
### 1.3  Besoins et solution proposée
       1.3.1  Acteurs et besoins fonctionnels
       1.3.2  Contraintes et exigences non fonctionnelles
       1.3.3  Solution retenue et périmètre du projet
###  1.4  Méthodologie de travail
       1.4.1  Démarche retenue
       1.4.2  Organisation du projet


> Sources principales : `CAHIER_DES_CHARGES.md`, `CADRAGE_SRS.md` §1–4

## CHAPITRE 2 — CONCEPTS FONDAMENTAUX ET MÉTHODOLOGIE (15–18 p.)

**Introduction**

### 2.1 Traitement automatique du langage naturel (TALN)
- 2.1.1 Représentations classiques : sac de mots, TF-IDF
- 2.1.2 Représentations denses : word embeddings, phrase embeddings
- 2.1.3 Modèles transformers et BERT
- 2.1.4 CamemBERT — un transformer francophone
- 2.1.5 Fine-tuning et adaptation efficiente (PEFT / LoRA)

### 2.2 Classification supervisée et déséquilibre de classes
- 2.2.1 Algorithmes de référence (LogReg, SVM, Gradient Boosting)
- 2.2.2 Métriques adaptées au déséquilibre (F1-macro, rappel par classe)
- 2.2.3 Techniques de rééquilibrage (pondération, SMOTE)

### 2.3 Génération augmentée par récupération (RAG)
- 2.3.1 Principe et architecture d'un système RAG
- 2.3.2 Recherche lexicale vs recherche sémantique
- 2.3.3 Bases vectorielles (FAISS, ChromaDB)
- 2.3.4 Évaluation d'un système RAG (RAGAS : précision, MRR, fidélité)

### 2.4 Grands modèles de langage (LLM)
- 2.4.1 LLM open-source et exécution locale (on-premise)
- 2.4.2 Prompt engineering
- 2.4.3 Hallucinations et garde-fous
- 2.4.4 Enjeux de confidentialité des données

### 2.5 MLOps et industrialisation
- 2.5.1 Versionnement des données et des modèles (DVC)
- 2.5.2 Suivi d'expérimentations (MLflow)
- 2.5.3 Conteneurisation et CI/CD

### 2.6 Outils technologiques utilisés *(grand tableau : outil / rôle / justification)*

### 2.7 Méthodologie de travail
- 2.7.1 Comparaison des approches de conduite de projet (Cycle en V vs Agile)
- 2.7.2 Application de CRISP-DM au projet
- 2.7.3 Démarche hybride retenue
- 2.7.4 Organisation en releases et sprints *(tableau de planification)*
- 2.7.5 Acteurs et responsabilités

**Conclusion**

> Sources : `CADRAGE_SRS.md` §1.6, `DECISIONS.md`, `ARCHITECTURE.md`

---

## CHAPITRE 3 — SPRINT 1 : DONNÉES ET GOUVERNANCE (14–16 p.)

**Introduction**

### 3.1 Sprint Backlog *(tableau des user stories)*

### 3.2 Présentation du jeu de données
- 3.2.1 Provenance et mode de collecte
- 3.2.2 Schéma : 1 800 lignes × 18 colonnes *(tableau descriptif des champs)*
- 3.2.3 Variable cible : 8 catégories métier
- 3.2.4 Jeu de données externe de benchmark (11 923 lignes, anglophone)

### 3.3 Analyse exploratoire (EDA)
- 3.3.1 Distribution des classes → **déséquilibre 5,93×** (Microsoft 409 / Backup 69)
- 3.3.2 Complétude des champs
- 3.3.3 Distribution des longueurs de texte (médiane 33 mots)
- 3.3.4 Analyse des statuts et du cycle de vie
- 3.3.5 Analyse de la redondance → **58 types de tickets récurrents**

### 3.4 Diagnostic de qualité des données
- 3.4.1 Indicateurs clés *(tableau de synthèse)*
- 3.4.2 Forces : 0 valeur manquante critique, 0 doublon, 0 incohérence de label
- 3.4.3 Risques identifiés *(tableau : risque → impact → traitement)*
- 3.4.4 **Limite majeure assumée** : représentativité du corpus

### 3.5 Prétraitement et préparation
- 3.5.1 Règles de nettoyage textuel (normalisation, regex, stop-words)
- 3.5.2 Enrichissement des variables (`text_enriched`)
- 3.5.3 **Stratégie de séparation anti-fuite** : GroupShuffleSplit par titre
      (46 titres train / 12 test) — justification scientifique
- 3.5.4 Jeux résultants : train 1 444 / test 356 / RAG 1 357

### 3.6 Gouvernance et reproductibilité
- 3.6.1 Versionnement des données avec DVC
- 3.6.2 Considérations RGPD et anonymisation *(limite : non implémenté)*

### 3.7 Livrables et bilan du sprint

**Conclusion**

> Sources : `DIAGNOSTIC_QUALITE_DONNEES.md`, notebooks 01 et 02
> Figures : distribution des classes, complétude, longueurs, redondance, statuts

---

## CHAPITRE 4 — SPRINT 2 : MODÉLISATION IA (16–18 p.)

**Introduction**

### 4.1 Sprint Backlog

### 4.2 Protocole expérimental
- 4.2.1 Métrique retenue : F1-macro (justification vs exactitude)
- 4.2.2 Protocole d'entraînement et de validation
- 4.2.3 Modèle de référence plancher (Dummy)

### 4.3 Approche 1 — Baseline classique
- 4.3.1 Vectorisation TF-IDF
- 4.3.2 Modèles testés : LogReg+SMOTE, LinearSVC calibré, LightGBM, ensemble
- 4.3.3 Traitement du déséquilibre (`class_weight='balanced'`, SMOTE)
- 4.3.4 Résultats comparés *(tableau)*

### 4.4 Approche 2 — Heuristiques métier
- 4.4.1 Motivation : injection de connaissance experte
- 4.4.2 Règles implémentées (FORCE_RULES, mots-clés discriminants)
- 4.4.3 Gain mesuré

### 4.5 Approche 3 — Fine-tuning CamemBERT avec LoRA
- 4.5.1 Justification du choix de CamemBERT
- 4.5.2 Configuration LoRA (r=8, α=16, modules query/value) — contrainte GPU 2 Go
- 4.5.3 Hyperparamètres retenus *(tableau : valeur + justification)*
- 4.5.4 Déroulement de l'entraînement (courbes de perte, early stopping)
- 4.5.5 Résultats et matrice de confusion

### 4.6 Comparaison et analyse critique
- 4.6.1 Tableau comparatif final des 6 approches
- 4.6.2 **Analyse : pourquoi le transformer ne surpasse pas la baseline**
      → lien avec la redondance des 58 types (chap. 3)
- 4.6.3 Choix du modèle retenu pour la production et justification
- 4.6.4 Calibration de la confiance et seuil de routage automatique (HITL)

### 4.7 Livrables et bilan du sprint

**Conclusion**

> Sources : notebooks 03, 04, 05 · `models/camembert_metadata.json`
> Figures : matrice de confusion, distribution de confiance, benchmark comparatif

---

## CHAPITRE 5 — SPRINT 3 : SYSTÈME RAG ET ASSISTANT LLM (16–18 p.)

**Introduction**

### 5.1 Sprint Backlog

### 5.2 Constitution de la base de connaissances
- 5.2.1 Extraction des tickets résolus et de leurs solutions
- 5.2.2 Structuration et indexation

### 5.3 RAG lexical (version 1)
- 5.3.1 Similarité cosinus sur TF-IDF
- 5.3.2 Limites observées

### 5.4 RAG sémantique (version 2)
- 5.4.1 Choix du modèle d'embeddings francophone
- 5.4.2 Indexation FAISS par catégorie
- 5.4.3 Gain mesuré : score cosinus 0,93 vs 0,76

### 5.5 RAG hybride (version 3)
- 5.5.1 Pondération sémantique/lexical (0,5 / 0,5)
- 5.5.2 Résultats

### 5.6 Évaluation du système RAG
- 5.6.1 Protocole RAGAS
- 5.6.2 Résultats : P@3, MRR, Answer Relevancy, Faithfulness *(tableau)*
- 5.6.3 **Analyse critique** : Faithfulness = 1,0 vrai *par construction*
      (génération template-based, pas génération LLM libre)

### 5.7 Intégration d'un LLM local (Ollama)
- 5.7.1 Justification du choix on-premise (confidentialité des tickets)
- 5.7.2 Modèle retenu (llama3.2:3b) et contraintes matérielles
- 5.7.3 Conception des prompts
- 5.7.4 **Garde-fous anti-hallucination** (assainissement en entrée, rejet des ID inventés)
- 5.7.5 Optimisation de la latence : ~95 s à froid → ~19 s à chaud (`keep_alive`)
- 5.7.6 Mécanisme de repli automatique

### 5.8 Boucle d'apprentissage continu
- 5.8.1 Migration TinyDB → ChromaDB : d'un journal passif à une base interrogée en direct
- 5.8.2 Détection des « cas nouveaux » (seuil `rag_score` < 0,50)
- 5.8.3 Alimentation de la base par la solution réellement appliquée

### 5.9 Livrables et bilan du sprint

**Conclusion**

> Sources : notebooks 06, 07 · `src/rag/semantic_engine.py` · `api/services/llm_service.py`

---

## CHAPITRE 6 — SPRINT 4 : DÉVELOPPEMENT DE L'APPLICATION (16–18 p.)

**Introduction**

### 6.1 Sprint Backlog

### 6.2 Conception
- 6.2.1 Architecture générale (vue C4 — contexte et conteneurs)
- 6.2.2 Diagramme de cas d'utilisation
- 6.2.3 Modèle de données / diagramme de classes
- 6.2.4 Diagramme d'états du ticket
- 6.2.5 Diagramme de séquence (création → classification → RAG → validation)

### 6.3 Développement du backend (FastAPI)
- 6.3.1 Architecture en couches (routers / services / db)
- 6.3.2 API REST versionnée `/api/v1` *(tableau des endpoints)*
- 6.3.3 Authentification JWT et contrôle d'accès par rôle
- 6.3.4 Sécurité : hachage bcrypt, rate limiting, CORS
- 6.3.5 Intégration des services IA (classification + RAG + LLM)

### 6.4 Développement du frontend (Angular)
- 6.4.1 Choix technologiques (Angular standalone, signals, Tailwind)
- 6.4.2 Système de design Material 3 et thème sombre
- 6.4.3 Portail client — écrans et parcours
- 6.4.4 Console d'administration — écrans et parcours

### 6.5 Workflow métier du ticket
- 6.5.1 Cycle de vie complet et transitions de statut
- 6.5.2 File d'approbation
- 6.5.3 Clôture en deux étapes (revue → clôture)
- 6.5.4 **Human-in-the-loop** : validation obligatoire avant résolution
- 6.5.5 Différenciation de l'information client / admin

### 6.6 Livrables et bilan du sprint

**Conclusion**

> Sources : `ARCHITECTURE.md`, `TICKET_WORKFLOW.md`, code `api/` et `frontend/`

---

## CHAPITRE 7 — SPRINT 5 : INDUSTRIALISATION, TESTS ET VALIDATION (14–16 p.)

**Introduction**

### 7.1 Sprint Backlog

### 7.2 Infrastructure de persistance
- 7.2.1 Migration SQLite → PostgreSQL (justification, ADR)
- 7.2.2 Base vectorielle ChromaDB
- 7.2.3 Difficultés rencontrées et corrections (concurrence entre workers)

### 7.3 Conteneurisation et déploiement
- 7.3.1 Architecture Docker Compose — 5 services *(schéma de déploiement)*
- 7.3.2 Healthchecks, volumes et réseau interne
- 7.3.3 Variante GPU

### 7.4 Chaîne MLOps
- 7.4.1 Pipeline DVC (4 étapes)
- 7.4.2 Suivi MLflow et registre de modèles
- 7.4.3 Model cards
- 7.4.4 Intégration continue (lint, tests, build)

### 7.5 Stratégie de tests
- 7.5.1 Tests unitaires (41)
- 7.5.2 Tests d'intégration (18/18)
- 7.5.3 Tests de charge et latence
- 7.5.4 Tests de sécurité

### 7.6 Validation fonctionnelle
- 7.6.1 Matrice exigences → résultats mesurés
- 7.6.2 Étude utilisateur légère : méthodologie et limites
- 7.6.3 Anomalies détectées et corrigées
- 7.6.4 Bilan de conformité *(y compris ENF non conformes : latence P95)*

### 7.7 Livrables et bilan du sprint

**Conclusion**

> Sources : `DEPLOYMENT.md`, `TESTING.md`, `CADRAGE_SRS.md` §5–6, `DECISIONS.md`

---

## CONCLUSION GÉNÉRALE (3–4 p.)

- Rappel de la problématique et synthèse des contributions
- Bilan des résultats obtenus *(tableau de synthèse global)*
- **Limites du travail** (à assumer explicitement) :
  représentativité du corpus · RGPD non traité · latence P95 · pas d'augmentation
  de données · absence de mise en production réelle
- Perspectives d'évolution (backlog priorisé)
- Apport personnel et compétences acquises

---

## ÉLÉMENTS DE FIN

- **Webographie / Bibliographie** — `webo.tex` + `biblio.bib`
- **Annexes** — `annexes.tex` :
  - A. Contrat d'API (extrait OpenAPI)
  - B. Model card du modèle retenu
  - C. Data card
  - D. Journal des décisions techniques (ADR)
  - E. Résultats détaillés de l'évaluation RAG
  - F. Captures d'écran complémentaires
- **Résumé / Abstract** — `tpl/resume.tex` (français + anglais + mots-clés)

---

## ACRONYMES À DÉFINIR (`acronymes.tex`)

API · BERT · CI/CD · CRISP-DM · CRUD · DVC · EF/ENF · F1 · FAISS · HITL ·
IA · ITSM · JWT · LLM · LoRA · ML · MLOps · NLP/TALN · ORM · PEFT · RAG ·
RAGAS · REST · RGPD · SMOTE · SRS · TF-IDF · UML · VRAM

---

## INVENTAIRE DES FIGURES À PRODUIRE

**Chapitre 1** — organigramme OTBS · processus existant · diagramme de contexte
**Chapitre 2** — architecture transformer · principe LoRA · architecture RAG · cycle Scrum
**Chapitre 3** — distribution des classes · complétude · longueurs · redondance ·
              statuts · schéma du split anti-fuite
**Chapitre 4** — courbes d'entraînement · matrice de confusion · distribution de
              confiance · benchmark comparatif
**Chapitre 5** — architecture RAG · comparaison des scores · résultats RAGAS ·
              flux LLM avec garde-fous
**Chapitre 6** — C4 contexte/conteneurs · cas d'utilisation · classes · états ·
              séquence · captures d'écran client et admin
**Chapitre 7** — schéma de déploiement Docker · pipeline DVC · interface MLflow ·
              résultats des tests

---

## ORDRE DE RÉDACTION RECOMMANDÉ

1. **Chapitres 3 et 4** (matière la plus dense et déjà disponible)
2. **Chapitre 5** (RAG + LLM)
3. **Chapitres 6 et 7** (application + industrialisation)
4. **Chapitre 1** (contexte — nécessite des informations entreprise à collecter)
5. **Chapitre 2** (concepts — largement transposable depuis l'existant)
6. **Introduction et conclusion générales** (en dernier)
7. Pages liminaires, annexes, résumé

---

## POINTS À CORRIGER AVANT RÉDACTION — état au 2026-09-08

| # | Point | Statut |
|---|---|---|
| 1 | Deux protocoles d'évaluation coexistent | ✅ **Tranché** — voir ci-dessous. ⚠️ Chiffres actualisés après l'audit des règles du 2026-08-22 |
| 2 | Base RAG : 476 vs 1 357 tickets | ✅ **Tranché** — voir ci-dessous |
| 3 | Informations entreprise (effectif, organigramme, chiffres) | 🔴 Toujours en attente — voir [../report/QUESTIONS_ENTREPRISE.md](../report/QUESTIONS_ENTREPRISE.md). Le chapitre 1 reste sous sa cible tant que ces réponses manquent |
| 4 | Chiffres du RAG à citer au chapitre 5 | ✅ **Tranché en rédigeant** — voir ci-dessous |
| 5 | Scores de classification postérieurs à l'audit des règles | ✅ **Tranché** — voir ci-dessous |

### Point 1 — F1 baseline : deux protocoles, pas une erreur

Les deux chiffres sont exacts mais proviennent de **protocoles d'évaluation différents** :

| Protocole | Split | Classes couvertes | F1-macro TF-IDF + règles |
|---|---|---|---|
| Pipeline DVC (`metrics/ml_eval.json`) | `GroupShuffleSplit` par Titre, **non stratifié** | **5 / 8** | **0,5829** (0,685 avant l'audit) |
| Campagne du 2026-08-22 (notebooks 03 et 05) | `StratifiedShuffleSplit` sur les titres uniques | **8 / 8** | **0,5827** (0,7513 avant l'audit) |

Les deux valeurs sont aujourd'hui presque identiques, mais cette proximité est fortuite : elles ne
portent ni sur le même découpage ni sur le même nombre de catégories. Elle ne dispense pas de
préciser le protocole à chaque citation.

Le test du pipeline DVC ne contient **aucun exemple** d'*Applicatifs*, *Backup* et *Communication*
(0/356). Son F1-macro ne porte donc que sur 5 classes — dont les plus faciles — ce qui le rend
**mécaniquement supérieur** et **non comparable** au protocole stratifié.

**Règle de citation dans le mémoire :**
- Comparer TF-IDF et CamemBERT **à configuration égale**, c'est-à-dire tous deux avec les règles
  ou tous deux sans : sans règles **0,3753 contre 0,5685**, avec règles **0,5827 contre 0,8343**.
  Opposer TF-IDF *avec* règles à CamemBERT *sans* règles est la faute à ne pas commettre, puisque
  les règles s'appliquent indépendamment du modèle.
- Le chiffre du pipeline DVC (**0,5829**) se cite uniquement comme métrique de production,
  **toujours accompagné** de la mention « 5 catégories sur 8 » et d'un renvoi à R-14.
- Ne jamais citer un F1-macro sans son protocole : un jury qui ouvre `metrics/ml_eval.json` verra
  qu'il ne contient que 6 entrées `f1_*` pour 8 catégories.
- Les valeurs **0,685**, **0,7513**, **0,5673** et **0,9499** appartiennent à l'avant-audit. Elles
  ne se citent que pour documenter la correction, jamais comme résultats du travail.

### Point 2 — Base RAG : deux définitions, pas une erreur

| Définition | Valeur |
|---|---|
| Tickets au statut « Résolu » (corpus complet) | 476 |
| Tickets avec `Résolution/Motif` renseignée (corpus complet) | 1 693 |
| **Base RAG effectivement indexée** (`data/splits/rag.csv`) | **1 357** |

Le moteur RAG n'indexe pas que les tickets « Résolu » : `src/pipeline/split.py` retient tout
ticket **du jeu d'entraînement** dont `Résolution/Motif` est renseignée, quel que soit son statut
(Résolu 358, Rejeté 363, Problème 237, Prise en Charge 236, En attente 163). La restriction au
train est un choix **anti-fuite** délibéré, à valoriser dans le mémoire.

**Chiffre à citer pour la base de connaissances : 1 357.**

### Point 4 — Chiffres du RAG : ce qui est publiable et ce qui ne l'est pas

| Chiffre | Source | Verdict |
|---|---|---|
| Score cosinus **0,93 contre 0,76** (sémantique contre lexical) | `models/semantic_rag_metadata.json` | Mesuré sur un index de **476 documents**, alors que l'index servi en contient **1 357**. Le chiffre est daté, pas faux. À republier en précisant l'index de mesure, ou à rejouer sur l'index courant |
| `recall_at_3 = 0,0277` | `metrics/rag_eval.json` | **Ne pas citer comme une mesure de qualité.** C'est un artefact du protocole proxy « même catégorie = pertinent » (R-22). Le notebook d'origine `07_rag_evaluation.ipynb` n'a par ailleurs aucune sortie enregistrée |
| **P@3 = 0,354** (hybride) contre 0,292 (sémantique) et 0,154 (lexical) | campagne du 2026-08-22, [MLOPS.md](MLOPS.md) | **Chiffre à mettre en avant.** Première mesure du moteur réellement servi, protocole identique pour les trois moteurs |
| P@3 = 0,30 · MRR = 0,56 · AR = 0,58 · Faithfulness = 1,0 | RAGAS, Phase 7 | Citables, mais toujours avec la mention que le jeu annoté n'existe pas (R-22) |

**Règle de citation au chapitre 5** : toute métrique de pertinence RAG est présentée comme
indicative tant que le jeu annoté n'est pas constitué. La commande
`python src/pipeline/rag_eval.py --build-template` génère le gabarit d'annotation (80 requêtes).

### Point 5 — Scores de classification : les valeurs d'avant le 2026-08-22 sont périmées

L'audit des règles métier du 2026-08-22 (R-23) a retiré quatre mots-clés qui n'étaient attestés
dans aucun ticket d'entraînement et ne se déclenchaient que sur des tickets de test. Les scores
publiés avant cette date mesuraient donc en partie de la mémorisation.

| Système | Avant l'audit | **Valeur à citer** | Protocole |
|---|---|---|---|
| Hasard (`DummyClassifier`) | — | **0,1382** | stratifié, 8 classes |
| TF-IDF seul | 0,3753 | **0,3753** | stratifié, 8 classes |
| TF-IDF + règles | 0,7513 | **0,5827** | stratifié, 8 classes |
| CamemBERT seul | 0,5685 | **0,5685** | stratifié, 8 classes |
| **CamemBERT + règles** | 0,9499 | **0,8343** | stratifié, 8 classes |
| Pipeline servi (TF-IDF + règles) | 0,685 | **0,5829** | DVC, 5 classes sur 8 (R-14) |

Deux conséquences pour la rédaction. D'abord, **H1 est vérifiée** : à configuration égale,
CamemBERT devance TF-IDF de +0,193 sans les règles et de +0,252 avec. Ensuite, l'écart à
l'objectif ENF-03 n'est plus que de **0,016**, et il tient à une seule catégorie, *Microsoft*,
qui plafonne à 0,4463 quand elle devrait atteindre 0,5719.

Comparaison détaillée avant et après : [../reports/analyse-notebooks/COMPARAISON_AVANT_APRES.md](../reports/analyse-notebooks/COMPARAISON_AVANT_APRES.md).
