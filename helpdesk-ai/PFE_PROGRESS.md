# PFE_PROGRESS.md — Suivi de la rédaction du mémoire

> Suivi des livrables académiques : mémoire LaTeX, figures, soutenance.
> Structure alignée sur [PLAN_RAPPORT.md](PLAN_RAPPORT.md), qui fait foi pour le plan détaillé.
> Source de vérité projet : [PLAN.md](PLAN.md). Sources LaTeX : `../report/`.
> Dernière mise à jour : **2026-09-08** (chapitre 5 rédigé).

## 1. Où en est le mémoire

| | |
|---|---|
| **Compilation** | 96 pages, 0 erreur, 0 référence non résolue (`pdflatex` x2 + `bibtex` + `pdflatex`) |
| **Chapitres rédigés** | 5 sur 7, plus l'introduction générale |
| **Volume rédigé** | pages 1 à 73 du corps, sur une cible de 110 à 135 pages |
| **Figures intégrées** | 11 |
| **Tableaux intégrés** | 36 |
| **Prochain chapitre** | Chapitre 6 — Sprint 4, développement de l'application |

## 2. Avancement chapitre par chapitre

État : ✅ rédigé et relu · 🟡 partiel · 🔴 non commencé.

| # | Chapitre | Fichier | Pages | Fig. | Tab. | Cible | État |
|---|---|---|---|---|---|---|---|
| — | Introduction générale | `introduction.tex` | 1 | 0 | 0 | 2–3 p. | 🟡 à étoffer en fin de rédaction |
| 1 | Contexte général du projet | `chap_01.tex` | 2–9 | 2 | 4 | 12–15 p. | 🟡 rédigé, sous la cible — bloqué sur les réponses OTBS |
| 2 | Concepts fondamentaux et spécification | `chap_02.tex` | 10–25 | 1 | 5 | 15–18 p. | ✅ repris le 2026-09-07 |
| 3 | Sprint 1 — Données et gouvernance | `chap_03.tex` | 26–39 | 3 | 9 | 14–16 p. | ✅ vérifié et corrigé |
| 4 | Sprint 2 — Modélisation IA | `chap_04.tex` | 40–55 | 3 | 10 | 16–18 p. | ✅ corrigé après l'audit des règles |
| 5 | Sprint 3 — RAG et assistant LLM | `chap_05.tex` | 56–73 | 2 | 8 | 16–18 p. | ✅ rédigé et relu le 2026-09-08 |
| 6 | Sprint 4 — Développement de l'application | `chap_06.tex` | 74 | 0 | 0 | 16–18 p. | 🔴 **prochain à rédiger** |
| 7 | Sprint 5 — Industrialisation et validation | `chap_07.tex` | 75 | 0 | 0 | 14–16 p. | 🔴 squelette |
| — | Conclusion générale | `conclusion.tex` | 76 | — | — | 2–3 p. | 🔴 balises seules |
| — | Annexes | `annexes.tex` | 79 | — | — | — | 🔴 balises seules |

**Lecture** : les trois chapitres restants décrivent du travail déjà réalisé et testé dans le
dépôt. Il s'agit de le documenter, pas de le construire. Le chapitre 1 est le seul dont
l'avancement dépend d'un tiers.

## 3. Pages liminaires

| Élément | Fichier | État |
|---|---|---|
| Page de garde | `tpl/cover_page.tex` | ✅ renseignée via `global_config.tex` |
| Autorisations de dépôt | `tpl/signatures.tex` | 🟡 rédigée, **reste à faire signer** |
| Dédicaces | `dedicaces.tex` | ✅ |
| Remerciements | `remerciement.tex` | ✅ |
| Liste des abréviations | `acronymes.tex` | ✅ |
| Table des matières, listes des figures et tableaux | auto | ✅ |
| Résumé français | `global_config.tex` | 🔴 `\todo` — à rédiger en dernier |
| Abstract anglais | `global_config.tex` | 🔴 `\todo` — à rédiger en dernier |

## 4. Figures produites

| Figure | Fichier | Chapitre | Source |
|---|---|---|---|
| Processus de traitement existant | `img/ch01_processus_existant.png` | 1 | schéma rédigé |
| Vue d'ensemble de la solution | `img/ch01_vue_solution.png` | 1 | schéma rédigé |
| Principe de la génération augmentée par récupération | `img/ch02_principe_rag.png` | 2 | schéma rédigé, refait le 2026-09-07 |
| Distribution des catégories | `img/ch03_distribution_categories.png` | 3 | notebook 01 |
| Redondance du corpus | `img/ch03_redondance.png` | 3 | notebook 01 |
| Découpage anti-fuite | `img/ch03_split_antifuite.png` | 3 | `src/pipeline/split.py` |
| Comparaison des sept approches | `img/ch04_benchmark.png` | 4 | campagne du 2026-08-22 |
| Matrice de confusion CamemBERT | `img/ch04_confusion_camembert.png` | 4 | notebook 05 |
| Distribution de la confiance | `img/ch04_confiance.png` | 4 | notebook 05 |
| Comparaison des trois moteurs de recherche | `img/ch05_moteurs.png` | 5 | `metrics/rag_eval.json` |
| Chaîne RAG servie et boucle d'alimentation | `img/ch05_chaine_rag.png` | 5 | schéma rédigé |

**Restant à produire** (voir PLAN_RAPPORT.md §Figures) : C4, cas d'utilisation, classes, états,
séquence et captures d'écran (ch. 6) ; déploiement Docker, pipeline DVC, interface MLflow et
résultats de tests (ch. 7).

## 5. Points tranchés au chapitre 5

| # | Point | Décision retenue |
|---|---|---|
| 1 | La comparaison « 0,93 contre 0,76 » provient de `models/semantic_rag_metadata.json`, qui décrit un index de **476 documents** quand l'index servi en contient **1 357** | ✅ Citée en §5.5.4 avec son index de mesure, et accompagnée de la précision qu'elle porte sur la similarité du **meilleur** passage, non sur les trois retenus. La campagne du 2026-08-22 sert de référence unique |
| 2 | `metrics/rag_eval.json` ne publie plus de rappel : le champ vaut `null` et porte une note expliquant qu'en protocole approché l'ensemble des pertinents est la catégorie entière | ✅ Le chapitre explique pourquoi le rappel n'est pas publié plutôt que de le citer |
| 3 | Campagne du 2026-08-22 : P@3 **0,3542** hybride, 0,2917 sémantique, 0,1542 lexical | ✅ Référence unique du chapitre, protocole identique pour les trois moteurs |
| 4 | **Trouvé en rédigeant** : le taux de repli du moteur hybride vaut **1,000**. Son score moyen (0,3551) n'atteint jamais le seuil de 0,50, calibré sur l'échelle du moteur sémantique | ✅ Analysé au chapitre. Conséquence : tout ticket est traité comme un cas nouveau. Deux corrections possibles, non tranchées faute de trafic réel (R-20) |
| 5 | **Trouvé en relecture** : la base de connaissances contient 1 357 tickets mais seulement **46 résolutions distinctes**, une par scénario, réinstanciée 31 fois en médiane | ✅ Chiffré au chapitre, avec la répartition par catégorie (4 à 8 réponses selon la catégorie) |
| 6 | **Trouvé en relecture** : les 58 scénarios se répartissent en deux ensembles **disjoints**, 46 dans la base et 12 au jeu de test. **Aucune des 356 requêtes d'évaluation n'a sa réponse dans la base** | ✅ Les valeurs mesurées sont présentées comme un plancher. C'est aussi la raison pour laquelle le protocole approché est le seul mesurable : une définition stricte de la pertinence donnerait zéro pour les trois moteurs |

## 6. Écarts à assumer explicitement dans le mémoire

Ces points ne sont pas des défauts à cacher, ce sont des limites qu'un jury valorise si elles
sont énoncées avant qu'il ne les trouve.

- **CamemBERT n'est pas industrialisé.** Le chapitre 4 mesure CamemBERT + règles à **0,8343**,
  mais l'API sert le pipeline TF-IDF + règles, à **0,5829** sur le protocole DVC. À expliciter
  au chapitre 7.
- **Deux protocoles d'évaluation coexistent** (R-14). Toute citation d'un F1-macro doit préciser
  lequel et combien de catégories il couvre.
- **EF-14 « génération LLM »** repose sur un modèle 3B local reformulant des résolutions
  existantes, pas sur une génération libre.
- **La priorité et la classification affichées comme « Résultat ML »** sont des valeurs de départ
  confirmées par l'administrateur, pas des prédictions entraînées.
- **Les deux boucles MLOps n'ont pas encore de trafic réel** (R-20) : elles sont démontrées de
  bout en bout sur une base simulée, leurs seuils restent à calibrer.
- **Les 129 motifs des règles métier n'ont pas été validés par OTBS** (R-24).

## 7. Livrables jury

- [ ] Mémoire PDF complet
- [x] Cahier des charges ([CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md))
- [x] Code source et suite de tests (**133 tests**)
- [ ] Démonstration en direct plus vidéo de secours
- [ ] Diaporama de soutenance
- [ ] Annexes : model card, data card, décisions d'architecture, contrat OpenAPI, liste des
      mots-clés des règles métier signée par le support

## 8. Blocages externes

| Blocage | Impact | Interlocuteur |
|---|---|---|
| Réponses au questionnaire OTBS ([../report/QUESTIONS_ENTREPRISE.md](../report/QUESTIONS_ENTREPRISE.md)) | Chapitre 1 sous sa cible, introduction et conclusion incomplètes | Encadrant professionnel |
| Signature des autorisations de dépôt | Dépôt du mémoire | Encadrants professionnel et académique |
| Validation écrite des mots-clés des règles (R-24) | Annexe, et condition de réintroduction des quatre termes retirés | Responsable du support |
