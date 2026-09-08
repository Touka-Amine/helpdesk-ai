# Progression du modèle — avant et après l'audit des règles

> Mesures du 2026-08-22. Deux campagnes : l'une avant le nettoyage des règles métier,
> l'autre après. Données brutes de la première : `helpdesk-ai/metrics/campagne_avant_nettoyage.json`.
> Les chiffres publiables sont ceux de la colonne « après ».

## Protocole unique

Toutes les configurations sont mesurées dans des conditions **identiques**.

| | |
|---|---|
| Découpage | `StratifiedShuffleSplit` sur les 58 titres uniques, graine 42 |
| Entraînement | 1 445 tickets, 46 scénarios |
| Test | 355 tickets, 12 scénarios, **8 catégories sur 8** |
| Fuite | aucune : aucun titre commun entre les deux jeux |
| Seuil de confiance | 0,60 (valeur de production) |

---

## 1. Avant et après l'audit

| Système | Avant (contaminé) | **Après (publiable)** | Écart |
|---|---|---|---|
| Référence plancher (hasard) | 0,1382 | 0,1382 | — |
| TF-IDF + LinearSVC seul | 0,3753 | 0,3753 | — |
| TF-IDF + règles métier | 0,7513 | **0,5827** | −0,169 |
| CamemBERT + LoRA seul | 0,5685 | 0,5685 | — |
| **CamemBERT + règles métier** | 0,9499 | **0,8343** | −0,116 |

Les modèles seuls ne bougent pas : l'audit ne portait que sur les règles.

---

## 2. Ce que l'audit a retiré

Quatre mots-clés des règles fermes, absents du jeu d'entraînement et actifs sur le seul
jeu de test :

| Mot-clé | Catégorie forcée | Tickets d'entraînement | Tickets de test touchés |
|---|---|---|---|
| `onedrive` | Microsoft | 0 | 45 |
| `san` | Infrastructure | 0 | 21 |
| `ids` | Sécurité | 0 | 12 |
| `acces non autorise` | Sécurité | 0 | redondant avec `ids` |

Le fichier `src/models/heuristics.py` portait un commentaire qui documentait
explicitement l'ajout de l'un d'eux à partir d'un titre du jeu de test.

Les règles fermes passent de **35 à 29 motifs**. Les règles souples sont inchangées.

**Nuance.** Ces quatre termes désignent des technologies dont la catégorie ne prête pas à
discussion. Le défaut tient au moment de leur introduction, pas à leur contenu. Ils
pourront être réintroduits si le service support les valide par écrit, indépendamment de
tout résultat de test.

---

## 3. Tableau de progression retenu

| Étape | Système | F1-macro | Exactitude | Tickets corrects |
|---|---|---|---|---|
| 0 | Référence plancher (hasard) | 0,1382 | 0,1887 | 67 / 355 |
| 1 | TF-IDF + LinearSVC seul | 0,3753 | 0,5803 | 206 / 355 |
| 2 | TF-IDF + règles métier | 0,5827 | 0,6620 | 235 / 355 |
| 3 | CamemBERT + LoRA seul | 0,5685 | 0,6873 | 244 / 355 |
| **4** | **CamemBERT + règles métier** | **0,8343** | 0,7887 | 280 / 355 |

**Progression totale : 0,1382 → 0,8343, soit un facteur 6,0.**

---

## 4. Ce que chaque étape a apporté

| Passage | Gain | Ce qui l'explique |
|---|---|---|
| Hasard → TF-IDF | **+0,237** | L'apprentissage statistique sur vecteurs lexicaux |
| TF-IDF → CamemBERT | **+0,193** | Représentation contextuelle d'un modèle de langue français |
| CamemBERT → CamemBERT + règles | **+0,266** | Injection de la connaissance métier du service |

Contribution supplémentaire mesurée séparément : l'enrichissement du texte d'entrée
(`text_enriched`) fait passer CamemBERT de **0,5325 à 0,5685**, soit **+0,036**.
Source : `models/camembert_metadata.json`.

---

## 5. La comparaison équitable

| Configuration | TF-IDF | CamemBERT | Écart |
|---|---|---|---|
| Sans règles | 0,3753 | 0,5685 | **+0,193** |
| Avec règles | 0,5827 | **0,8343** | **+0,252** |
| Apport des règles | +0,207 | +0,266 | |

CamemBERT devance la chaîne lexicale dans les deux configurations. **L'hypothèse H1 du
cahier des charges est vérifiée.** Les règles profitent davantage au transformer, ce qui
indique que les deux composants corrigent des erreurs différentes.

---

## 6. Détail par catégorie, configuration retenue

| Catégorie | Précision | Rappel | F1 | Support |
|---|---|---|---|---|
| Applicatifs | 1,0000 | 1,0000 | **1,0000** | 68 |
| Backup | 1,0000 | 1,0000 | **1,0000** | 15 |
| Infrastructure | 1,0000 | 1,0000 | **1,0000** | 21 |
| Système | 1,0000 | 1,0000 | **1,0000** | 29 |
| Sécurité | 1,0000 | 0,6000 | 0,7500 | 20 |
| Réseau | 0,5954 | 1,0000 | 0,7464 | 78 |
| Communication | 0,5882 | 0,9677 | 0,7317 | 31 |
| **Microsoft** | 0,9643 | **0,2903** | **0,4463** | 93 |

Quatre catégories à 1,00, six au-dessus de 0,74. Le point faible unique est
*Microsoft* : sa précision reste excellente à 0,96, son rappel tombe à 0,29 depuis le
retrait de `onedrive`.

**Il suffirait que *Microsoft* passe de 0,4463 à 0,5719 pour que le F1-macro atteigne
0,85.** Aucune autre catégorie n'aurait besoin de bouger.

---

## 7. Position par rapport au cahier des charges

| Exigence | Cible | Mesure | État |
|---|---|---|---|
| ENF-03 — F1-macro | ≥ 0,85 | **0,8343** | à 0,016 de la cible |
| ENF-04 — rappel *Sécurité* | ≥ 0,70 | **0,60** | non atteint |
| H1 — CamemBERT surpasse la baseline | — | +0,252 | **vérifiée** |

Sur ENF-04, la précision vaut 1,00 : chaque incident de sécurité annoncé en est bien un,
mais quatre sur dix échappent au système.

---

## 8. Métriques du modèle servi en production

Protocole du pipeline, non stratifié, 5 catégories seulement au test. **Non comparable
aux chiffres ci-dessus.**

| Indicateur | Avant audit | Après audit |
|---|---|---|
| F1-macro, modèle seul | 0,2708 | 0,2708 |
| F1-macro avec les règles | 0,6850 | **0,5829** |
| F1-macro sur les catégories évaluables | 0,8220 | **0,6995** |
| Exactitude | 0,8539 | **0,8202** |
| Rappel *Sécurité* | 0,3636 | **0,0000** |

Le rappel *Sécurité* passe de 0,3636 à zéro : les trois scénarios de sécurité tirés au
test relèvent tous de l'intrusion détectée, que le terme `ids` capturait. Le même système
atteint 0,40 de rappel sous le protocole stratifié, où d'autres scénarios sont tirés.

Cet écart de zéro à 0,40 pour un système inchangé illustre la réserve du chapitre 3 :
sur douze scénarios de test, une mesure par catégorie se déplace par paliers entiers.

---

## 9. Note sur une mesure intermédiaire écartée

Une première reconstruction des règles « d'avant contamination » avait donné 0,8198 pour
CamemBERT et 0,6440 pour TF-IDF. Elle remettait en outre `teams` dans les règles fermes
de *Microsoft*, ce que le nettoyage effectif ne fait pas : les 64 tickets d'entraînement
contenant `teams` sont tous classés *Communication* par le service, ce qui justifie de le
laisser en règle souple vers cette catégorie.

Les valeurs retenues sont donc **0,8343 et 0,5827**, mesurées sur l'état réellement
implémenté du module de règles.

---

## 10. Réserve de méthode

Le jeu de test compte 12 scénarios pour 8 catégories, soit une à trois situations par
catégorie. Une F1 par classe s'y déplace par paliers grossiers, et le résultat global
garde une incertitude large. Ce point est énoncé au chapitre 3 §3.5.4 et doit accompagner
tout chiffre de ce document.
