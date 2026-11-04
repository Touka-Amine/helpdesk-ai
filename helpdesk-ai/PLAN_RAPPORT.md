# PLAN_RAPPORT.md — Plan détaillé du mémoire PFE

> Structure calquée sur les deux rapports de référence encadrés par M. Ahmed Dhouibi
> (Sarra Mzali / TEK-UP / PwC — 134 p. ; Hamad Wafa / ISET Rades / Tunisie Telecom — 119 p.),
> adaptée au contenu réel du projet HelpDesk AI.
> Fil conducteur méthodologique : **CRISP-DM**, méthodologie officielle du projet depuis le
> 2026-09-15. Les sept chapitres gardent une organisation académique, et chacun est rattaché à la
> ou aux phases qu'il porte. Le développement logiciel n'est pas une phase distincte : il relève
> de la phase de déploiement et d'intégration, et des itérations successives du projet.
> L'ancien découpage par sprints est abandonné ; le mot « sprint » n'apparaît dans aucun `.tex`.
> Volume cible : **110–135 pages**.
> Template : `latex-tekup/Rapport PFE TEKUP LATEX/`
>
> **Plan de reference : [crisp-dm.md](crisp-dm.md).** Ce fichier-ci porte le suivi de
> redaction, les conventions et les points chiffres tranches. La structure chapitre par
> chapitre, avec le rattachement aux phases, vit dans `crisp-dm.md`.

---

---

## ÉTAT DE LA RÉDACTION — au 2026-09-15

> Suivi détaillé et figures restant à produire : [PFE_PROGRESS.md](PFE_PROGRESS.md).
> Sources LaTeX : `../report/`. Le document compile à **151 pages, sans erreur**,
> soit seize pages au-dessus de la cible haute.

| # | Chapitre | Pages | Cible | État |
|---|---|---|---|---|
| — | Introduction générale | 1 | 2–3 p. | ✅ rédigée ; annonce CRISP-DM comme fil conducteur |
| 1 | Contexte général du projet — *phase 1, compréhension du métier* | 2–19 | 12–15 p. | ✅ rédigé ; porte le choix et la justification de CRISP-DM |
| 2 | Concepts fondamentaux et spécification — *transversal* | 20–35 | 15–18 p. | ✅ rédigé ; sert toutes les phases, n'en porte aucune |
| 3 | Analyse et préparation des données — *phases 2 et 3* | 36–50 | 14–16 p. | ✅ rédigé ; compréhension puis préparation |
| 4 | Système de classification — *phases 4 et 5* | 51–67 | 16–18 p. | ✅ rédigé ; modélisation puis évaluation |
| 5 | Système RAG et assistant — *phases 4 et 5* | 68–89 | 16–18 p. | ✅ rédigé ; sections permutées le 2026-09-15 pour que la construction précède l'évaluation |
| 6 | Développement et intégration de la plateforme — *phase 6* | 90–112 | 16–18 p. | ✅ rédigé ; intègre les deux moteurs dans une plateforme utilisable |
| 7 | Industrialisation, tests et validation — *phases 5 et 6* | 113–139 | 14–16 p. | ✅ rédigé ; l'exposé suit l'ordre de mise en exploitation, la validation mesurant l'environnement conteneurisé |
| — | Conclusion générale | 147 | 1 p. | ✅ rédigée ; tient sur une page, sans tableau |
| — | Annexes | — | — | ⬜ supprimées le 2026-09-14 sur décision de l'auteur |
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
en V / Scrum / CRISP-DM, puis CRISP-DM retenue comme méthodologie officielle, avec la figure du
cycle, la figure de correspondance phases/chapitres et la règle du protocole arrêté avant
l'entraînement.
Le chapitre 2 ne comporte donc pas de §2.7. Symétriquement, la **spécification des besoins**
(acteurs, quinze exigences fonctionnelles, huit exigences non fonctionnelles) reste au
**chapitre 2**, là où le plan la situe en §1.3 : elle y suit immédiatement les concepts et les
outils dont elle dépend, et le chapitre 2 tient ainsi sa cible de 15 à 18 pages. Enfin, les points
§2.4.1 et §2.4.4 du plan sont traités dans une sous-section unique, l'exécution locale du modèle
de langage découlant directement de l'exigence de confidentialité.

**Conventions de rédaction appliquées à tous les chapitres**, alignées sur le rapport de
référence de Hichem Ben Salah (`../exemple_de_rapport/`) :

1. Une section s'ouvre toujours par un paragraphe, jamais directement sur un sous-titre
2. Une figure ou un tableau est annoncé par une phrase, puis relu par un paragraphe placé après
3. Un titre n'est jamais imprimé seul en bas de page (`needspace`, `commandes_locales.tex`)
4. La légende d'un tableau est au-dessus, celle d'une figure en dessous
5. Tout flottant est appelé au moins une fois par le texte
6. Chaque chapitre nomme dans son introduction la ou les phases CRISP-DM qu'il porte
7. Chaque conclusion de chapitre annonce ce que le chapitre suivant reprend

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

> Phase CRISP-DM portée : **1 — Compréhension du métier**

**Introduction**

### 1.1 Présentation de l'organisme d'accueil
- 1.1.1 Le groupe OneTech
- 1.1.2 OneTech Business Solutions
- 1.1.3 Organisation interne
- 1.1.4 Le cadre de confidentialité

### 1.2 Le service support et son fonctionnement
- 1.2.1 Le ticketing, socle organisationnel du support
- 1.2.2 Périmètre et acteurs du service
- 1.2.3 Volumétrie observée
- 1.2.4 L'outil de suivi et la qualité de ses données
- 1.2.5 Le cycle de vie du ticket
- 1.2.6 Répétitivité des résolutions
- 1.2.7 Limites du diagnostic

### 1.3 Problématique et solution proposée
- 1.3.1 Limites de l'existant et besoins associés
- 1.3.2 Les solutions du marché
- 1.3.3 Énoncé de la problématique
- 1.3.4 La solution proposée
- 1.3.5 Périmètre du travail

### 1.4 Méthodologie de travail
- 1.4.1 Comparaison des démarches envisagées
- 1.4.2 Démarche retenue : CRISP-DM


> Sources principales : `CAHIER_DES_CHARGES.md`, `CADRAGE_SRS.md` §1–4

## CHAPITRE 2 — CONCEPTS FONDAMENTAUX ET SPÉCIFICATION DES BESOINS (15–18 p.)

> **Chapitre transversal** — sert toutes les phases, n'en porte aucune

**Introduction**

### 2.1 Traitement automatique du langage naturel
- 2.1.1 Représentations classiques : sac de mots, TF-IDF
- 2.1.2 Représentations denses : word embeddings, phrase embeddings
- 2.1.3 Modèles transformers et BERT
- 2.1.4 CamemBERT — un transformer francophone
- 2.1.5 Fine-tuning et adaptation efficiente (PEFT / LoRA)

### 2.2 Classification supervisée et déséquilibre de classes
- 2.2.1 Algorithmes de référence (LogReg, SVM, Gradient Boosting)
- 2.2.2 Métriques adaptées au déséquilibre (F1-macro, rappel par classe)
- 2.2.3 Techniques de rééquilibrage (pondération, SMOTE)

### 2.3 Génération augmentée par récupération
- 2.3.1 Principe et architecture d'un système RAG
- 2.3.2 Recherche lexicale vs recherche sémantique
- 2.3.3 Bases vectorielles (FAISS, ChromaDB)
- 2.3.4 Évaluation d'un système RAG (RAGAS : précision, MRR, fidélité)

### 2.4 Grands modèles de langage
- 2.4.1 LLM open-source et exécution locale (on-premise)
- 2.4.2 Prompt engineering
- 2.4.3 Hallucinations et garde-fous
- 2.4.4 Enjeux de confidentialité des données

### 2.5 Industrialisation et MLOps
- 2.5.1 Versionnement des données et des modèles (DVC)
- 2.5.2 Suivi d'expérimentations (MLflow)
- 2.5.3 Conteneurisation et CI/CD

### 2.6 Positionnement du travail

### 2.7 Outils technologiques utilisés *(tableau : outil / rôle / justification)*

### 2.8 Spécification des besoins
- 2.8.1 Acteurs du système
- 2.8.2 Exigences fonctionnelles
- 2.8.3 Exigences non fonctionnelles
- 2.8.4 Traçabilité des exigences

*(La méthodologie n'est pas reprise ici : elle est traitée une seule fois, au chapitre 1, §1.4.)*

**Conclusion**

> Sources : `CADRAGE_SRS.md` §1.6, `DECISIONS.md`, `ARCHITECTURE.md`

---

## CHAPITRE 3 — ANALYSE ET PRÉPARATION DES DONNÉES (14–16 p.)

> Phases CRISP-DM portées : **2 — Compréhension des données** (3.1 et 3.2), puis
> **3 — Préparation des données** (3.3 à 3.6)

### 3.1 Présentation des données

- Sources des données
- Structure du corpus
- Variables disponibles
- Catégories de tickets
- Volume des données

### 3.2 Analyse exploratoire des données

- Distribution des catégories
- Analyse de la longueur des textes
- Analyse des titres et descriptions
- Qualité des données
- Déséquilibre des classes
- Redondance éventuelle

### 3.3 Préparation des données

- Nettoyage des données
- Normalisation
- Traitement des textes
- Gestion des valeurs problématiques
- Enrichissement du texte

### 3.4 Préparation du corpus pour la classification

- Définition de la variable cible
- Séparation entraînement / validation / test
- Prévention de la fuite de données
- Gestion du déséquilibre

### 3.5 Préparation des connaissances pour le RAG

- Sélection des informations pertinentes
- Nettoyage et structuration
- Constitution de la base de connaissances
- Différence entre dataset ML et base de connaissances

### 3.6 Gouvernance et reproductibilité

- Versionnement des données et du pipeline
- Données personnelles : une limite non traitée

## Conclusion du chapitre

---

## CHAPITRE 4 — DÉVELOPPEMENT ET ÉVALUATION DU SYSTÈME DE CLASSIFICATION (16–18 p.)

> Phases CRISP-DM portées : **4 — Modélisation** (4.1 à 4.4), puis **5 — Évaluation**
> (4.5 et 4.6)

## 4.1 Formulation du problème de classification

- Définition de la tâche
- Variable cible
- Classes considérées
- Métriques d’évaluation

### 4.2 Approche fondée sur TF-IDF

### 4.2.1 Vectorisation des textes

### 4.2.2 Modèles de classification testés

### 4.2.3 Évaluation des modèles

## 4.3 Amélioration par les heuristiques métier

- Motivation
- Principe des règles métier
- Règles appliquées
- Impact sur les performances

### 4.4 Approche fondée sur CamemBERT et LoRA

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

## CHAPITRE 5 — SYSTÈME RAG ET ASSISTANCE INTELLIGENTE (16–18 p.)

> Phases CRISP-DM portées : **4 — Modélisation** (5.1 à 5.4), puis **5 — Évaluation**
> (5.5). L'intégration du modèle de langage est passée avant l'évaluation le 2026-09-15 :
> la construction doit s'achever avant que la mesure commence.

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

## 5.4 Intégration du LLM

- Un modèle exécuté sur site
- Conception du prompt
- Garde-fous et repli

## 5.5 Évaluation du RAG

- Protocole et approximation de la pertinence
- Dimensions non couvertes par la campagne
- Résultats mesurés
- Le seuil que le moteur servi n'atteint jamais
- Une mesure ancienne à ne pas citer

## 5.6 Apprentissage continu

- Validation des tickets
- Enrichissement des connaissances
- Réutilisation des tickets validés
- Principe d’amélioration progressive du système

## Conclusion du chapitre
---

## CHAPITRE 6 — DÉVELOPPEMENT ET INTÉGRATION DE LA PLATEFORME (16–18 p.)

> Phase CRISP-DM portée : **6 — Déploiement**. Le développement logiciel n'est pas une
> activité à part : il intègre dans une plateforme utilisable les deux moteurs des
> chapitres 4 et 5.

### 6.1 Architecture applicative

- Découpage en couches, communication entre composants, choix technologiques

### 6.2 Conception et modélisation UML

- 6.2.1 Contexte et cas d'utilisation
- 6.2.2 Diagramme de classes
- 6.2.3 Diagramme de séquence : dépôt d'une demande
- 6.2.4 Diagramme de séquence : clôture d'un ticket
- 6.2.5 Traçabilité des états du ticket

### 6.3 Développement du backend

- Trois couches, contrat typé, contrôle d'accès par rôle

### 6.4 Développement du frontend

- 6.4.1 Accès à la plateforme
- 6.4.2 Portail du demandeur
- 6.4.3 Console d'administration et file d'approbation
- 6.4.4 Validation humaine et bouclage de la résolution

### 6.5 Workflow global de traitement d'un ticket

Le parcours complet, du dépôt à l'enrichissement de la base, avec la boucle de retour qui
ramène la résolution rédigée vers la recherche servant la demande suivante.

## Conclusion du chapitre
> Sources : `ARCHITECTURE.md`, `TICKET_WORKFLOW.md`, code `api/` et `frontend/`

---

## CHAPITRE 7 — INDUSTRIALISATION, TESTS ET VALIDATION (14–16 p.)

*Phases CRISP-DM 5 et 6 : évaluation du système, puis clôture du déploiement. L'exposé suit
l'ordre de la mise en exploitation, la validation mesurant l'environnement conteneurisé.*

**Introduction**

### 7.1 Conteneurisation et déploiement
- Quatre services : ollama, postgres, api, frontend
- Contrôles de santé, volumes nommés, réseau interne, configuration hors image
- Captures : état des services, encombrement des images

### 7.2 Chaîne d'apprentissage automatisé
- Pipeline DVC à huit étapes, en deux chaînes issues du même corpus
- Jeu de test gelé, suivi des expériences
- Porte de promotion et ses trois conditions, réentraînement contrôlé

### 7.3 Tests de la solution
- Périmètre de la suite, zones non couvertes, exécution automatique et couverture

### 7.4 Validation de la solution
- Le temps de réponse, exigence non tenue
- Bilan de conformité aux exigences

### 7.5 Limites du système

### 7.6 Perspectives

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
**Chapitre 2** — architecture transformer · principe LoRA · architecture RAG
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

## ORDRE DE RÉDACTION — historique

Tout est rédigé. L'ordre effectivement suivi a été : chapitres 3 et 4, puis 1 et 2, puis 5,
puis 6 et 7, enfin l'introduction et la conclusion générales. Le chapitre 2 a été écrit tôt
parce qu'il fixe le vocabulaire réutilisé aux chapitres 3 et 4.

Reste à produire : les résumés français et anglais (`tpl/resume.tex`) et la signature des
autorisations de dépôt.

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
