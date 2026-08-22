# Diagnostic de qualité des données — HelpDesk AI

> Document de référence sur la qualité du jeu de données (Phase 2 du [PLAN.md](PLAN.md)).
> Indicateurs calculés automatiquement par [`notebooks/data_quality_report.py`](notebooks/data_quality_report.py)
> → figures dans `notebooks/figures/` et rapport **`notebooks/figures/diagnostic_qualite_donnees.pdf`**.
> Dernière mise à jour : **2026-06-26**.

---

## 1. Résumé exécutif (verdict)

Le jeu de données est **exploitable et de bonne qualité structurelle** : aucune donnée manquante
sur les champs essentiels (texte et cible), **aucun ticket vide**, **aucune incohérence de label**,
et une longueur de texte homogène. Il est **prêt pour la modélisation**.

Trois points d'attention, tous **maîtrisables**, conditionnent la qualité du modèle :
1. **Déséquilibre des classes** (5,93×) — à traiter par rééchantillonnage/pondération.
2. **Redondance par types de tickets récurrents** — le corpus s'organise autour de **58 types de
   tickets** ré-instanciés ; il faut une **séparation train/test sans fuite** (déjà en place).
3. **Prétraitement actuel trop agressif** — il réduit fortement la diversité lexicale ; un nettoyage
   plus fin est recommandé pour améliorer la généralisation.

---

## 2. Indicateurs clés

| Indicateur | Valeur | Lecture |
|---|---|---|
| Lignes / colonnes | **1800 / 18** | Volume correct |
| Classes (cible `Catégorie`) | **8** | Multi-classes |
| Déséquilibre (max/min) | **5,93×** (Microsoft 409 → Backup 69) | ⚠️ à traiter |
| Tickets vides | **0** | ✅ |
| Doublons de ligne complète | **0** | ✅ |
| Descriptions uniques | **1535 / 1800** (85 %) | Bonne diversité au niveau description |
| Types de tickets (titres uniques) | **58** | Corpus organisé par scénarios récurrents |
| Cohérence des labels | **0 incohérence** | ✅ même type → même catégorie |
| Longueur description (mots) | min 23 · **médiane 33** · max 46 | Homogène |
| Champs manquants notables | Date résolution 73,6 % · CID 50,3 % · Résolution/Motif 5,9 % | Explicables |
| Tickets au statut « Résolu » | **476** (450 avec `Résolution/Motif` renseignée) | Sous-ensemble du corpus |
| Base de résolution (RAG) réellement indexée | **1357** (`data/splits/rag.csv`) | Voir §2.1 — définition |

> Figures : `dq_01_distribution_classes.png`, `dq_02_completude.png`, `dq_03_longueurs.png`,
> `dq_04_redondance.png`, `dq_05_statuts.png` (toutes regroupées dans le PDF).

### 2.1 Précision sur la taille de la base RAG (deux définitions à ne pas confondre)

Deux chiffres circulent dans le projet ; ils sont **tous deux exacts** mais ne mesurent pas la
même chose. À employer sans ambiguïté dans le mémoire :

| Définition | Valeur | Périmètre |
|---|---|---|
| Tickets au statut « Résolu » | 476 | Corpus complet (indicateur descriptif) |
| Tickets avec `Résolution/Motif` renseignée | 1693 | Corpus complet |
| **Base RAG effectivement indexée** (`data/splits/rag.csv`) | **1357** | **Train uniquement**, tous statuts confondus, `Résolution/Motif` renseignée |

Le moteur RAG n'indexe **pas** seulement les tickets « Résolu » : `src/pipeline/split.py` retient
tout ticket du jeu d'entraînement dont le champ `Résolution/Motif` est renseigné, quel que soit
son statut (Résolu 358, Rejeté 363, Problème 237, Prise en Charge 236, En attente 163). La
restriction au jeu d'entraînement est un choix **anti-fuite** délibéré : les résolutions des
tickets de test ne doivent pas être consultables par le RAG lors de l'évaluation.

**Chiffre à citer dans le mémoire pour la base de connaissances : 1357.**

---

## 3. Forces

- ✅ **Complétude des champs critiques** : `Description`, `Titre`, `Catégorie`, `knowledge Base`
  sans valeurs manquantes.
- ✅ **Aucun ticket vide ni doublon de ligne complète.**
- ✅ **Labels parfaitement cohérents** : un même type de ticket reçoit toujours la même catégorie
  (0 incohérence) — gage de fiabilité de l'annotation.
- ✅ **Texte homogène** (médiane 33 mots) : pas de tickets aberrants par la longueur.
- ✅ **Base de résolution suffisante** pour le moteur RAG (**1357 tickets** indexés, cf. §2.1).

---

## 4. Points d'attention et causes

### 4.1 Déséquilibre des classes (5,93×)
`Microsoft` (409) et `Réseau` (369) dominent ; `Sécurité` (73) et `Backup` (69) sont minoritaires.
**Impact** : risque de faible rappel sur les classes rares (`Sécurité`).
**Traitement** : pondération `class_weight`, rééchantillonnage (SMOTE), augmentation de données
ciblée, et **suivi du rappel par classe** (pas seulement l'exactitude globale).

### 4.2 Redondance par types de tickets récurrents
Le corpus comporte **58 types de tickets** (titres) instanciés plusieurs dizaines de fois chacun
avec des variations de surface (demandeur, dates, identifiants `CID-xxxx`). Les **descriptions**
restent diverses (1535 uniques), mais le **contenu informatif** se concentre sur un nombre limité
de scénarios.
**Impact** : si l'on découpe train/test au hasard, le **même type** se retrouve des deux côtés →
**fuite de données** et métriques trompeusement optimistes.
**Traitement** : **séparation sur textes uniques** (tous les tickets d'un même type dans le même
split) — **déjà implémentée** dans `03_modeling.ipynb`. C'est le bon réflexe à mettre en avant.

### 4.3 Prétraitement actuel trop agressif (cause de l'« uniformité » apparente)
Le nettoyage courant (`clean_text`) supprime accents, nombres, identifiants, mots courts **et une
longue liste de mots du domaine** (`probleme`, `systeme`, `service`, `demande`, `ticket`…). La
description passe en moyenne de ~33 mots à **~12 mots**, et la diversité lexicale **chute à ~125
motifs distincts**. Autrement dit, **l'uniformité observée est en grande partie produite par le
prétraitement**, pas par les données brutes.
**Traitement (recommandé)** :
- alléger la liste de mots vides du domaine (conserver les termes techniques discriminants) ;
- conserver certains nombres/codes utiles (ex. `error 80080300`, `office 365`) ;
- ajouter des **bi-grammes** (`ngram_range=(1,2)`) pour récupérer du signal (`salle serveur`,
  `tentatives connexion`) ;
- abaisser le seuil de longueur de token (`>= 2`).
**Bénéfice attendu** : plus de diversité → meilleure généralisation et réduction de l'écart
validation/test.

### 4.4 Champs manquants
`Date de résolution` (73,6 %) et `CID` (50,3 %) sont manquants **par nature** (seuls les tickets
résolus ont une date ; le CID n'est pas systématique) — **non bloquant**. `Résolution/Motif`
(5,9 %) est géré par un repli sur `knowledge Base` dans le moteur RAG.

---

## 5. Recommandations actionnables (priorisées)

| # | Recommandation | Phase | Priorité |
|---|---|---|---|
| 1 | Conserver la **séparation train/test sans fuite** (sur textes uniques) | 4–5 | Critique |
| 2 | **Suivre le rappel par classe** (focus `Sécurité`/`Backup`) en plus de l'exactitude | 4–5 | Critique |
| 3 | **Alléger le prétraitement** + bi-grammes (cf. 4.3) | 2–4 | Haute |
| 4 | **Rééquilibrage** (SMOTE / pondération) + augmentation ciblée des classes rares | 5 | Haute |
| 5 | Anonymiser les **données personnelles** (demandeur, filiale) — RGPD | 2 | Haute |
| 6 | Versionner données + traitements via **DVC** (reproductibilité) | 2/10 | Haute |
| 7 | Enrichir la **base de résolution** (1357 → +) pour les catégories rares | 6 | Moyenne |

---

## 6. Conclusion

Les données sont **fiables, complètes et cohérentes** : une base saine pour la suite du projet. Les
limites identifiées (déséquilibre, redondance par types récurrents, prétraitement trop agressif)
sont **classiques et traitables** ; les leviers correspondants (split sans fuite, suivi par classe,
nettoyage plus fin, rééquilibrage) sont intégrés au plan (Phases 2, 4 et 5 du [PLAN.md](PLAN.md)).
Le point le plus rentable à court terme est **l'allègement du prétraitement** (§4.3), qui augmente
directement la diversité exploitable par le modèle.
