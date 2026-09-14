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

**Écarts assumés au plan, arbitrés le 2026-09-09.** Le plan cite la méthodologie de travail
deux fois, au chapitre 1 (§1.4) et au chapitre 2 (§2.7). Elle n'est rédigée qu'une seule fois, au
**chapitre 1** (`../report/chap_01.tex`, section « Méthodologie de travail ») : comparaison cycle
en V / Scrum / CRISP-DM, démarche hybride retenue, découpage en cinq sprints et acteurs du projet.
Le chapitre 2 ne comporte donc pas de §2.7. Symétriquement, la **spécification des besoins**
(acteurs, quinze exigences fonctionnelles, huit exigences non fonctionnelles) reste au
**chapitre 2**, là où le plan la situe en §1.3 : elle y suit immédiatement les concepts et les
outils dont elle dépend, et le chapitre 2 tient ainsi sa cible de 15 à 18 pages. Enfin, les points
§2.4.1 et §2.4.4 du plan sont traités dans une sous-section unique, l'exécution locale du modèle
de langage découlant directement de l'exigence de confidentialité.

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

## Chapitre 3 — Analyse et préparation des données

## 3.1 Présentation des données

- Sources des données
- Structure du corpus
- Variables disponibles
- Catégories de tickets
- Volume des données

## 3.2 Analyse exploratoire des données

- Distribution des catégories
- Analyse de la longueur des textes
- Analyse des titres et descriptions
- Qualité des données
- Déséquilibre des classes
- Redondance éventuelle

## 3.3 Préparation des données

- Nettoyage des données
- Normalisation
- Traitement des textes
- Gestion des valeurs problématiques
- Enrichissement du texte

## 3.4 Préparation du corpus pour la classification

- Définition de la variable cible
- Séparation entraînement / validation / test
- Prévention de la fuite de données
- Gestion du déséquilibre

## 3.5 Préparation des connaissances pour le RAG

- Sélection des informations pertinentes
- Nettoyage et structuration
- Constitution de la base de connaissances
- Différence entre dataset ML et base de connaissances

## Conclusion du chapitre

---

# Chapitre 4 — Développement et évaluation du système de classification

## 4.1 Formulation du problème de classification

- Définition de la tâche
- Variable cible
- Classes considérées
- Métriques d’évaluation

## 4.2 Approche basée sur TF-IDF

### 4.2.1 Vectorisation des textes

### 4.2.2 Modèles de classification testés

### 4.2.3 Évaluation des modèles

## 4.3 Amélioration par les heuristiques métier

- Motivation
- Principe des règles métier
- Règles appliquées
- Impact sur les performances

## 4.4 Approche basée sur CamemBERT et LoRA

### 4.4.1 Justification du choix de CamemBERT

### 4.4.2 Principe de LoRA

### 4.4.3 Configuration de l’entraînement

### 4.4.4 Résultats obtenus

## 4.5 Comparaison des approches

- Comparaison des performances
- Analyse des résultats
- Avantages et limites de chaque approche

Présenter les résultats principaux dans un tableau comparatif.

## 4.6 Sélection du modèle final

- Critères de sélection
- Modèle retenu
- Justification du choix
- Gestion de la confiance de prédiction
- Routage automatique et validation humaine

## Conclusion du chapitre

---
---

# Chapitre 5 — Système RAG et assistance intelligente

## 5.1 Présentation du système RAG

- Objectif du RAG dans la plateforme
- Principe général
- Flux de recherche et de génération

## 5.2 Construction de la base de connaissances

- Sources utilisées
- Préparation des connaissances
- Indexation
- Gestion des connaissances historiques et dynamiques

## 5.3 Mise en œuvre de la recherche

### 5.3.1 Recherche lexicale

### 5.3.2 Recherche sémantique

### 5.3.3 Recherche hybride

### 5.3.4 Comparaison des approches

## 5.4 Évaluation du RAG

- Protocole d’évaluation
- Critères et métriques
- Résultats
- Analyse des résultats
- Limites de l’évaluation

## 5.5 Intégration du LLM

- Rôle du LLM
- Modèle utilisé
- Construction du prompt
- Génération de la solution
- Contrôle du contexte fourni au modèle
- Gestion des hallucinations

## 5.6 Apprentissage continu

- Validation des tickets
- Enrichissement des connaissances
- Réutilisation des tickets validés
- Principe d’amélioration progressive du système

## Conclusion du chapitre
---

# Chapitre 6 — Développement et intégration de la plateforme

## 6.1 Architecture applicative

- Organisation du backend
- Organisation du frontend
- Base de données
- Services IA
- Communication entre les composants

## 6.2 Développement du backend

- API REST
- Gestion des tickets
- Gestion des utilisateurs
- Intégration du modèle de classification
- Intégration du RAG
- Intégration du LLM

## 6.3 Développement du frontend

- Interface de création des tickets
- Interface de consultation
- Interface de suivi
- Interface de validation
- Interface d’administration

## 6.4 Workflow de traitement d’un ticket

Présenter le workflow global :

**Création du ticket  
→ Classification  
→ Recherche de connaissances  
→ Proposition de solution  
→ Validation humaine  
→ Résolution  
→ Archivage / enrichissement**

## 6.5 Intégration des composants

- Intégration du pipeline IA
- Intégration de la base de données
- Intégration des services externes
- Communication entre les différents composants

## 6.6 Exemple complet de traitement

Présenter un exemple réel ou représentatif montrant le parcours d’un ticket dans la plateforme.

## Conclusion du chapitre
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
