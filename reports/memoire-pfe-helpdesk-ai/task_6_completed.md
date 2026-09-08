# Tâche 6 — Audit des règles métier et correction du chapitre 4

**Date** : 2026-09-07
**Périmètre** : `helpdesk-ai/src/models/heuristics.py`, `helpdesk-ai/tests/`, `report/chap_04.tex`,
fichiers de suivi
**Statut** : terminé, non commité

---

## 1. Sortie remise dans le fil de discussion

> J'ai relu mon travail et trouvé sept erreurs, toutes de mon fait. Corrigées.
>
> **Cinq erreurs factuelles dans le chapitre 4.** La plus grave : j'avais écrit « faire remonter
> *Microsoft* à 0,13 suffirait à franchir la barre ». C'est faux et absurde, *Microsoft* est à
> 0,4463, donc 0,13 serait une régression. J'avais confondu l'incrément nécessaire (+0,126) avec la
> cible. Le bon chiffre est 0,5719. Les quatre autres : *Microsoft* décrit comme nul alors qu'il
> vaut 0,4463 ; « cinq catégories au-dessus de 0,74 et trois à 1,00 » au lieu de six et quatre ;
> *Backup* crédité de huit scénarios au lieu de six ; un F1 de 0,75 attribué au modèle servi alors
> qu'il appartient à CamemBERT.
>
> **Une confusion de métrique.** ENF-04 porte sur le rappel, pas sur le F1. En recalculant :
> CamemBERT + règles 0,60, TF-IDF + règles 0,40 en stratifié et 0,00 en pipeline. ENF-04 n'est
> atteint dans aucune configuration, la conclusion est nette et non ambiguë.
>
> **Un document livré devenu faux.** `COMPARAISON_AVANT_APRES.md` contenait 0,8198 et 0,6440,
> issus d'une reconstruction où j'avais aussi remis `teams` dans les règles fermes de *Microsoft*.
> Le nettoyage effectif ne le fait pas. Les valeurs réelles sont 0,8343 et 0,5827.
>
> **Un décompte périmé par ma propre modification.** Le chapitre disait « 135 motifs ». Après
> retrait des quatre mots-clés, il y en a 129.
>
> **Documents de suivi resynchronisés** : CADRAGE_SRS, RISKS (R-23 clos, R-24 ouvert), MLOPS,
> PROJECT_STATUS, CHANGELOG.
>
> Chaque chiffre du chapitre 4 trace désormais à sa source, contrôlé programmatiquement.
> 133 tests passent. Compilation à 76 pages, 0 erreur, 0 boîte débordante, 0 référence non résolue.
> Rien n'a été commité.

---

## 2. Vue d'ensemble de la tâche

### Contexte

Le chapitre 4 du mémoire, rédigé plus tôt dans la même session, rapportait un F1-macro de 0,5673
pour la chaîne TF-IDF accompagnée des règles métier et concluait que l'objectif ENF-03 de 0,85
n'était pas atteint, avec un écart de 0,28.

Deux anomalies ont motivé cette tâche.

**La première** : les règles métier avaient été corrigées après l'exécution du notebook 03, si bien
que le chiffre publié était périmé.

**La seconde** : le chapitre comparait une chaîne lexicale *avec* règles à un transformer *sans*
règles, comparaison asymétrique dont aucune conclusion valide ne pouvait être tirée.

### Objectifs

1. Mesurer les quatre configurations dans des conditions identiques
2. Vérifier que les règles métier n'ont pas été ajustées sur le jeu de test
3. Assainir les règles si nécessaire
4. Corriger le chapitre 4 avec les valeurs réelles
5. Resynchroniser les fichiers de suivi

### Critères de réussite

- Chaque chiffre du chapitre tracé à une source du dépôt
- Aucune règle non attestée dans le jeu d'entraînement et active sur le test
- Suite de tests au vert
- Compilation du mémoire sans erreur ni référence non résolue

---

## 3. Déroulement

| # | Action | Résultat |
|---|---|---|
| 1 | Mesure de CamemBERT accompagné des règles, jamais faite | **0,9499** contre 0,5685 seul |
| 2 | Lecture de `heuristics.py` avant publication du chiffre | Commentaire ligne 41 : `« acces non autorise » ajouté : test title "Accès non autorisé détecté par l'IDS"` |
| 3 | Confrontation de chaque mot-clé au jeu d'entraînement | 4 mots-clés absents du train, actifs sur le seul test |
| 4 | Audit complet des 35 motifs fermes | Script d'audit initial fautif : il omettait les frontières de mot et signalait `san` comme contredit. Corrigé |
| 5 | Mesure de deux options d'assainissement | Option A (stricte) 0,8343 ; option B (produits conservés) 0,9499 |
| 6 | Décision de l'utilisateur | **Option A** retenue |
| 7 | Modification de `heuristics.py` | 35 → 29 motifs fermes, note méthodologique en tête |
| 8 | Suite de tests | 1 échec : `test_force_rule_word_boundary_matches_standalone_keyword` utilisait `ids` |
| 9 | Réécriture des tests | 2 tests réécrits avec `esxi` et `sage erp`, 1 test de non-régression ajouté |
| 10 | `train.py` puis `promote.py` | Métriques du pipeline régénérées, candidat v4 rejeté par la porte |
| 11 | Mesure du tableau final | 5 configurations, protocole stratifié 8 catégories |
| 12 | Régénération de `ch04_benchmark.png` | 7 barres, 4 paliers |
| 13 | Réécriture du chapitre 4 | Introduction, objectifs, §4.4.3, 2 sections nouvelles, §4.6.4, production, bilan, conclusion |
| 14 | **Relecture critique de mon propre travail** | **5 erreurs factuelles trouvées** |
| 15 | Correction des 5 erreurs | Voir §5 |
| 16 | Contrôle programmatique des chiffres | 20 valeurs tracées à leur source |
| 17 | Resynchronisation des fichiers de suivi | 5 fichiers |
| 18 | Compilation finale | 76 pages, propre |

---

## 4. Entrées et sorties

### Entrées

| Source | Usage |
|---|---|
| `data/processed/HelpDesk1.csv` | corpus, 1 800 lignes, 23 colonnes |
| `models/camembert_lora_adapter/` | adaptateur LoRA, chargé pour l'inférence |
| `models/best_pipeline.pkl` | chaîne TF-IDF servie |
| `metrics/ml_eval.json` | métriques du pipeline |
| `src/models/heuristics.py` | règles métier, avant modification |
| `CADRAGE_SRS.md` §5 | exigences ENF-03 et ENF-04 |

### Sorties — code

| Fichier | Modification |
|---|---|
| `src/models/heuristics.py` | 4 mots-clés retirés, note méthodologique de 25 lignes ajoutée en tête |
| `tests/test_heuristics.py` | 2 tests réécrits, 1 test de non-régression ajouté |

### Sorties — mémoire

| Fichier | Modification |
|---|---|
| `report/chap_04.tex` | 9 passages réécrits, 2 sections et 2 tableaux créés |
| `report/img/ch04_benchmark.png` | régénérée avec les 7 approches |
| `report/main.pdf` | 74 → 76 pages |

### Sorties — artefacts régénérés

`metrics/ml_eval.json`, `metrics/ml_eval_candidate.json`,
`metrics/confusion_matrix_candidate.json` et `.png`, `metrics/promotion_decision.json`,
`models/candidate_pipeline.pkl`, `models/candidate_metadata.json`, `models/registry/v4/`

### Sorties — documentation

| Fichier | Modification |
|---|---|
| `reports/analyse-notebooks/COMPARAISON_AVANT_APRES.md` | créé puis réécrit avec les valeurs implémentées |
| `metrics/campagne_avant_nettoyage.json` | créé, campagne figée avant nettoyage |
| `CHANGELOG.md` | 2 entrées datées |
| `CADRAGE_SRS.md` | ENF-03 et ENF-04 réécrits |
| `RISKS.md` | R-23 ajouté et clos, R-24 ouvert |
| `MLOPS.md` | métrique de promotion actualisée |
| `PROJECT_STATUS.md` | bandeau, acquis, tableau des phases |

---

## 5. Erreurs rencontrées et traitement

### 5.1 La fuite méthodologique — défaut principal

**Constat.** Quatre mots-clés des règles fermes n'étaient attestés dans aucun ticket
d'entraînement et ne se déclenchaient que sur des tickets de test.

| Mot-clé | Catégorie forcée | Tickets train | Tickets test |
|---|---|---|---|
| `onedrive` | Microsoft | 0 | 45 |
| `san` | Infrastructure | 0 | 21 |
| `ids` | Sécurité | 0 | 12 |
| `acces non autorise` | Sécurité | 0 | redondant |

**Impact.** Le score mesurait en partie de la mémorisation. Part non généralisable : **0,116** sur
CamemBERT accompagné des règles, **0,169** sur la chaîne lexicale.

**Traitement.** Retrait des quatre termes. Règle méthodologique inscrite en tête du module : un
mot-clé n'est admis que s'il est attesté à l'entraînement, ou s'il reste sans effet sur le test.
Test de non-régression ajouté.

**Réserve.** Ces termes désignent des technologies dont la catégorie est exacte. Leur
réintroduction reste possible après validation écrite du service support, indépendante de tout
résultat de test. Risque R-24 ouvert à ce titre.

### 5.2 Cinq erreurs factuelles introduites par moi dans le chapitre

Trouvées en relecture de mon propre travail, après une première compilation réussie.

| # | Erreur écrite | Valeur réelle |
|---|---|---|
| 1 | « faire remonter *Microsoft* à 0,13 suffirait » | **0,5719**. J'avais confondu l'incrément (+0,126) avec la cible. Écrire 0,13 revenait à demander une régression depuis 0,4463 |
| 2 | « Une seule reste à zéro, *Microsoft* » | *Microsoft* vaut **0,4463**. Aucune catégorie n'est nulle dans cette configuration |
| 3 | « Cinq catégories dépassent 0,74 et trois atteignent 1,00 » | **six** et **quatre** |
| 4 | « ses huit scénarios » (*Backup*) | **six** scénarios |
| 5 | « La même catégorie atteint 0,75 sous le protocole stratifié » | 0,75 appartient à CamemBERT. Le modèle servi donne **0,5714** de F1 et **0,40** de rappel |

### 5.3 Confusion entre F1 et rappel sur ENF-04

**Constat.** L'exigence ENF-04 porte sur le **rappel**, et je comparais des F1. La formulation
« ce qui interdit de conclure dans un sens comme dans l'autre » masquait un résultat net.

**Rappels réels sur *Sécurité*** :

| Configuration | Rappel | Précision |
|---|---|---|
| CamemBERT + règles, stratifié | **0,60** | 1,00 |
| TF-IDF + règles, stratifié | 0,40 | 1,00 |
| TF-IDF + règles, pipeline | 0,00 | 0,00 |

**Traitement.** ENF-04 déclaré non atteint dans toutes les configurations, avec la précision de
1,00 mentionnée : aucune fausse alerte, mais quatre incidents sur dix échappent au système.

### 5.4 Document livré devenu faux

`COMPARAISON_AVANT_APRES.md`, remis à l'utilisateur, portait 0,8198 et 0,6440. Ces valeurs
venaient d'une reconstruction où `teams` avait été remis dans les règles fermes de *Microsoft*, ce
que le nettoyage effectif ne fait pas : les 64 tickets d'entraînement contenant `teams` sont tous
classés *Communication*. Document réécrit avec 0,8343 et 0,5827, et une section §9 qui explique
l'écart.

### 5.5 Décompte périmé par ma propre modification

Le chapitre annonçait « 135 motifs ». Après retrait, 129. Corrigé, et vérifié qu'aucune autre
occurrence ne subsiste dans le mémoire ni dans les fichiers de suivi.

### 5.6 Script d'audit fautif

Mon premier script d'audit signalait `san` comme contredit dans l'entraînement, réparti sur trois
catégories. Vérification faite, `apply_heuristics` utilise des frontières de mot (`\b`) et `san` ne
correspond donc pas à « sans ». C'était mon script qui omettait ces frontières. Corrigé avant toute
conclusion.

### 5.7 Test cassé par la modification

`test_force_rule_word_boundary_matches_standalone_keyword` s'appuyait sur `ids`. Son objet est de
vérifier la correspondance sur mot entier, pas ce mot-clé. Réécrit avec `esxi` pour le cas positif
et `sage erp` contre « usage erp » pour le cas négatif.

---

## 6. Résultats

### Tableau final, protocole stratifié 8 catégories

| Système | F1-macro | Exactitude | Corrects |
|---|---|---|---|
| Référence plancher | 0,1382 | 0,1887 | 67 / 355 |
| TF-IDF seul | 0,3753 | 0,5803 | 206 / 355 |
| TF-IDF + règles | 0,5827 | 0,6620 | 235 / 355 |
| CamemBERT seul | 0,5685 | 0,6873 | 244 / 355 |
| **CamemBERT + règles** | **0,8343** | 0,7887 | 280 / 355 |

### Comparaison à configuration égale

| Configuration | TF-IDF | CamemBERT | Écart |
|---|---|---|---|
| Sans règles | 0,3753 | 0,5685 | +0,193 |
| Avec règles | 0,5827 | **0,8343** | +0,252 |

**L'hypothèse H1 du cahier des charges est vérifiée.** Le mémoire la donnait pour infirmée.

### Position par rapport aux exigences

| Exigence | Cible | Mesure | État |
|---|---|---|---|
| ENF-03 — F1-macro | ≥ 0,85 | 0,8343 | écart de **0,016** |
| ENF-04 — rappel *Sécurité* | ≥ 0,70 | 0,60 | non atteint |
| H1 — CamemBERT surpasse la baseline | — | +0,252 | **vérifiée** |

---

## 7. Statut final

### Critères de réussite

| Critère | État |
|---|---|
| Chaque chiffre tracé à une source | ✅ 20 valeurs contrôlées programmatiquement |
| Aucune règle ajustée sur le test | ✅ 4 retirées, test de non-régression |
| Suite de tests au vert | ✅ **133 tests** |
| Compilation propre | ✅ 76 pages, 0 erreur, 0 boîte > 20 pt, 0 référence non résolue |

### Limites connues

**Le jeu de test compte 12 scénarios pour 8 catégories.** Une F1 par classe s'y déplace par paliers
entiers. Le rappel sur *Sécurité* passe de 0,00 à 0,40 pour un système inchangé, selon les
scénarios tirés. Cette réserve accompagne tout chiffre du chapitre.

**Le modèle servi reste la chaîne TF-IDF**, choisie quand les deux approches semblaient
équivalentes. L'écart de 0,252 invite à rouvrir cet arbitrage ; l'exigence de latence ENF-01 reste
l'obstacle réel. Porté aux perspectives.

**Le référentiel de mots-clés n'est validé par personne.** Les 129 motifs ont été écrits par
l'équipe projet à partir de l'examen des données. Risque R-24.

### Suites à donner

1. Committer l'ensemble, non fait à ce stade
2. Faire valider les 4 mots-clés retirés par le service support, condition de leur réintroduction
3. Traiter *Microsoft*, seul obstacle à ENF-03 : de 0,4463 à 0,5719
4. Chapitre 5, dont les chiffres RAG proviennent de notebooks sans sorties enregistrées et dont la
   comparaison « 0,93 contre 0,76 » porte sur un index périmé de 476 tickets

### Documents liés

- [COMPARAISON_AVANT_APRES.md](../analyse-notebooks/COMPARAISON_AVANT_APRES.md)
- [ANALYSE_NOTEBOOKS.md](../analyse-notebooks/ANALYSE_NOTEBOOKS.md)
- `helpdesk-ai/metrics/campagne_avant_nettoyage.json`
- `helpdesk-ai/CHANGELOG.md`, entrées du 2026-08-22
- `helpdesk-ai/RISKS.md`, R-23 et R-24
