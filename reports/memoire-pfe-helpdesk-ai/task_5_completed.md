# Tâche 5 — Rédaction du chapitre 3 « Sprint 1 : Données et gouvernance »

> Projet : mémoire PFE **HelpDesk AI** — Mohamed Amine Toukabri — OneTech Business Solutions
> Tâches précédentes : [`task_1`](task_1_completed.md) · [`task_2`](task_2_completed.md) · [`task_3`](task_3_completed.md) · [`task_4`](task_4_completed.md)
> Date : 2026-08-20 · Branche : `chore/gouvernance-pfe`

---

## 1. Sortie transmise dans le fil de conversation

Chapitre 3 rédigé, **14 pages** (p. 38 à 51), dans la cible de 14 à 16 pages fixée par
`PLAN_RAPPORT.md`. Sept sections numérotées, trois figures, huit tableaux.

Toutes les valeurs citées ont été recalculées sur `data/raw/HelpDesk1.csv` avant rédaction. Deux
d'entre elles corrigent des chiffres qui circulaient dans le projet.

Le chapitre porte deux constats qui n'étaient pas dans les documents de suivi :

- **Le champ `Date de création` mélange deux formats** : 828 lignes en ISO, 972 en `JJ/MM/AAAA`.
  Une lecture qui n'essaie qu'un format écarte silencieusement 54 % des dates. C'est ce qui
  explique la volumétrie de « ~60 tickets/mois » retenue dans une version antérieure de
  l'introduction : elle ne comptait que les 828 lignes ISO. La valeur exacte est **129 par mois**
  sur quatorze mois.
- **Le délai de traitement est mesurable**, contrairement à ce qui avait été conclu lors d'une
  session antérieure. 476 tickets portent les deux dates (26,4 %), délai médian **2 jours**. Le
  chapitre le rapporte avec son périmètre explicite : il ne décrit que les tickets menés à terme.

Le cœur du chapitre est la section 3.5.3–3.5.4 sur le découpage anti-fuite, et elle est écrite
sans complaisance : le découpage par groupe de titres **élimine bien la fuite** (0 titre commun
entre train et test), **et il laisse trois catégories sur huit hors du jeu de test**
(*Applicatifs*, *Communication*, *Backup*). Toute moyenne macro calculée sur ce jeu porte donc sur
5 classes. C'est l'explication du couple 0,685 / 0,5673 qui coexistait dans le dépôt. Le chapitre
l'énonce et renvoie au protocole stratifié du chapitre 4.

Compilation : **60 pages**, 0 erreur, 13 citations résolues, aucun débordement de boîte.

---

## 2. Objet de la tâche

Rédiger le chapitre 3 du mémoire selon la structure imposée par `PLAN_RAPPORT.md` (§ CHAPITRE 3,
lignes 113–155), en appliquant :

- la discipline de rédaction établie aux chapitres 1 et 2 (skill `humanize`) : pas d'antithèse
  « pas X mais Y », pas de triade annoncée, pas de tiret cadratin en prose, pas de superlatif vide ;
- les règles anti-invention du prompt de rédaction : aucun chiffre non vérifié (R1), limites
  énoncées explicitement (R3).

**Critères de réussite** : 14 à 16 pages ; sections conformes au plan ; chaque chiffre traçable à
une source du dépôt ; compilation sans erreur.

---

## 3. Déroulement

| # | Action | Résultat |
|---|---|---|
| 1 | Lecture du plan (`PLAN_RAPPORT.md` l. 113–155) | Structure 3.1 à 3.7 relevée |
| 2 | Lecture de `DIAGNOSTIC_QUALITE_DONNEES.md` | 139 lignes, indicateurs de référence |
| 3 | Recalcul de tous les indicateurs sur le CSV brut | Concordance avec le diagnostic, sauf dates |
| 4 | Découverte du double format de date | 828 ISO / 972 `JJ/MM/AAAA` |
| 5 | Recalcul de la volumétrie et du délai | 14 mois, 129/mois, délai médian 2 j sur 476 tickets |
| 6 | Lecture de `src/pipeline/split.py`, `src/data/preprocess.py`, `params.yaml`, `dvc.yaml` | Protocole et règles de nettoyage |
| 7 | Calcul de la composition des jeux par catégorie | 3 catégories absentes du test |
| 8 | Inspection du jeu externe `similar_helpdesk_dataset.csv` | 11 923 × 15, 10 891 titres uniques |
| 9 | Génération de `ch03_split_antifuite.png` | Deux essais : chevauchements corrigés au second |
| 10 | Import de deux figures du diagnostic | `dq_01` et `dq_04` renommées `ch03_*` |
| 11 | Rédaction de `chap_03.tex` | 7 sections, 3 figures, 8 tableaux |
| 12 | Ajout de l'entrée bibliographique du jeu public | `hfTickets` |
| 13 | Compilation, contrôle visuel page à page | 1 débordement de tableau détecté |
| 14 | Correction du tableau 3.8 et de deux césures | Recompilation propre |
| 15 | Détection d'une entrée bibliographique non citée | `wirth2000` (CRISP-DM) rattachée au ch. 1 |

---

## 4. Entrées et sorties

### Sources lues

| Fichier | Usage |
|---|---|
| `helpdesk-ai/PLAN_RAPPORT.md` | Structure imposée du chapitre |
| `helpdesk-ai/DIAGNOSTIC_QUALITE_DONNEES.md` | Indicateurs de qualité, définition de la base RAG |
| `helpdesk-ai/data/raw/HelpDesk1.csv` | Recalcul de tous les chiffres (1 800 × 18) |
| `helpdesk-ai/data/splits/{train,test,rag}.csv` | Composition des jeux |
| `helpdesk-ai/data/external/similar_helpdesk_dataset.csv` | Jeu public de comparaison |
| `helpdesk-ai/src/pipeline/split.py` | Protocole de découpage |
| `helpdesk-ai/src/data/preprocess.py` | Règles de nettoyage, listes de mots protégés |
| `helpdesk-ai/params.yaml`, `dvc.yaml` | Paramètres et étapes du pipeline |
| `helpdesk-ai/CHANGELOG.md`, `PLAN.md`, `CAHIER_DES_CHARGES.md` | Risque R-14, métriques enregistrées |

### Fichiers produits ou modifiés

| Fichier | Nature |
|---|---|
| `report/chap_03.tex` | **Créé** — 14 pages |
| `report/img/ch03_split_antifuite.png` | **Créé** — figure originale (matplotlib) |
| `report/img/ch03_distribution_categories.png` | Importée de `notebooks/figures/dq_01_*` |
| `report/img/ch03_redondance.png` | Importée de `notebooks/figures/dq_04_*` |
| `report/biblio.bib` | Entrée `hfTickets` ajoutée (13 entrées) |
| `report/chap_01.tex` | `\cite{wirth2000}` ajoutée sur CRISP-DM |
| `report/main.pdf` | Recompilé — 60 pages |

### Structure produite

```
Introduction
3.1 Objectifs du sprint                        tab:obj3
3.2 Le jeu de données
    3.2.1 Provenance et mode de collecte
    3.2.2 Schéma et variable cible             tab:schema
    3.2.3 Un jeu de données public             tab:bench
3.3 Analyse exploratoire
    3.3.1 Distribution des catégories          fig:distcat
    3.3.2 Complétude des champs                tab:completude
    3.3.3 Longueur des textes et cycle de vie  tab:statuts
    3.3.4 Redondance du corpus                 fig:redondance
3.4 Diagnostic de qualité des données
    3.4.1 Synthèse des indicateurs             tab:dq
    3.4.2 Risques identifiés et traitements    tab:risques
    3.4.3 Limite assumée : la représentativité
3.5 Préparation des données
    3.5.1 Nettoyage textuel
    3.5.2 Variables construites                tab:variables
    3.5.3 Séparation anti-fuite                fig:split
    3.5.4 Composition des jeux obtenus         tab:splits
3.6 Gouvernance et reproductibilité
    3.6.1 Versionnement des données et du pipeline
    3.6.2 Données personnelles : une limite non traitée
3.7 Bilan du sprint
Conclusion
```

---

## 5. Chiffres vérifiés (règle R2)

Tous recalculés sur le fichier source, aucun repris sur déclaration.

| Valeur | Mesure | Source |
|---|---|---|
| 1 800 lignes × 18 colonnes | `raw.shape` | `data/raw/HelpDesk1.csv` |
| Période : 01/01/2025 → 17/02/2026, 14 mois | `Date de création`, **deux formats parsés** | idem |
| 129 tickets/mois | 1 800 ÷ 14 | idem |
| 202 demandeurs, 11 assignés, 8 filiales | `nunique()` | idem |
| Formats de date : 828 ISO / 972 `JJ/MM/AAAA` | comptage par masque | idem |
| Microsoft 409 … Backup 69 ; ratio 5,93 | `value_counts()` | idem |
| 61 % dans les 3 premières catégories | 1 104 ÷ 1 800 | idem |
| Manquants : 73,6 / 50,3 / 5,9 / 5,6 / 3,4 / 3,1 % | `isna().mean()` | idem |
| Description : 23–46 mots, médiane 33, moyenne 33,1 | `str.split().str.len()` | idem |
| Titre : 2–8 mots, médiane 5 | idem | idem |
| Statuts : 476 / 464 / 328 / 321 / 211 | `value_counts()` | idem |
| Délai médian 2 j, max 4 j, sur 476 tickets | `Date de résolution − Date de création` | idem |
| 1 535 descriptions distinctes, 58 titres, 58 `knowledge Base` | `nunique()` | idem |
| 0 doublon, 0 ticket vide, 0 titre à deux catégories | `duplicated()`, `groupby.nunique()` | idem |
| train 1 444 / 46 titres · test 356 / 12 titres · RAG 1 357 | lecture des trois CSV | `data/splits/` |
| 0 titre commun train/test | intersection d'ensembles | idem |
| Test = 5/8 catégories ; Applicatifs, Communication, Backup à 0 | tableau croisé | idem |
| RAG : 363 rejetés / 358 résolus / 237 / 236 / 163 | `value_counts()` | `data/splits/rag.csv` |
| Jeu public : 11 923 × 15, 10 891 titres uniques (91 %) | `shape`, `nunique()` | `data/external/` |
| test_size 0,2 · random_state 42 · ngram (1,2) | lecture directe | `params.yaml` |
| 33 mots → ~12 mots, ~125 motifs (nettoyage agressif) | valeurs du diagnostic | `DIAGNOSTIC_QUALITE_DONNEES.md` §4.3 |

### Écarts avec des chiffres antérieurs du projet

| Chiffre antérieur | Valeur exacte | Cause |
|---|---|---|
| ~60 tickets/mois (intro, version antérieure) | **129/mois** | Seules les 828 lignes ISO étaient comptées |
| 52 tickets avec les deux dates, délai médian 119 j | **476 tickets, médiane 2 j** | Analyse antérieure faussée par le double format |
| Base RAG = 476 tickets « Résolu » | **1 357 tickets, tous statuts** | Confusion déjà signalée dans le diagnostic §2.1 |

Le premier écart n'a pas d'effet sur le mémoire : la mention « une soixantaine de tickets par
mois » avait disparu lors de la condensation de l'introduction générale à une page. Aucun chapitre
rédigé ne portait cette valeur.

---

## 6. Erreurs rencontrées et traitement

| Erreur | Diagnostic | Correction |
|---|---|---|
| `bash: unexpected EOF while looking for matching '` à l'écriture du chapitre par *heredoc* | Contenu LaTeX + français trop long pour un heredoc Git Bash | Écriture par l'outil `Write` |
| Figure `ch03_split_antifuite.png` : légendes superposées aux titres des boîtes, encadré RAG tronqué, flèche courbe illisible | Textes positionnés en absolu par-dessus les boîtes | Refonte : sous-titres passés en paramètre de la fonction `boite`, disposition en deux colonnes, flèche droite |
| Tableau 3.8 : `classification_simple` déborde sur la colonne voisine | Colonne à 3,4 cm, insuffisante pour 21 caractères en gras chasse fixe | Colonne portée à 4,4 cm |
| Tableau 3.2 : césures `Assigné` / `à` et `Chemin` / `d'accès` | Coupure sur l'espace | Espaces insécables `~` |
| `wirth2000` (CRISP-DM) présente dans `biblio.bib` mais jamais citée | Détection par comparaison `biblio.bib` / `main.aux` | `\cite{wirth2000}` ajoutée au chapitre 1 § 1.2 |
| Avertissement biblatex « Please (re)run BibTeX » persistant | Artefact du backend `bibtex` de biblatex | Sans effet : 13 citations résolues, vérifié dans le PDF |

---

## 7. Contrôle qualité

### Discipline de rédaction

| Fichier | Antithèses | Triades annoncées | Tirets en prose | « technicien » |
|---|---|---|---|---|
| `introduction.tex` | 0 | 0 | 0 | 0 |
| `chap_01.tex` | 1 * | 1 * | 0 | 0 |
| `chap_02.tex` | 0 | 0 | 0 | 0 |
| **`chap_03.tex`** | **0** | **0** | **0** ** | **0** |

\* Conservées volontairement : « nous ne le déduisons pas d'un entretien mais du fichier d'export »
porte l'argument de preuve ; « trois démarches candidates » est factuel, le tableau en compare
exactement trois.
\** L'unique `---` du fichier est celui du titre de chapitre, hors prose.

### Compilation

```
pdflatex → bibtex → pdflatex → pdflatex
erreurs           : 0
overfull > 15 pt  : 0
références non résolues : 0
citations         : 13 / 13
pages             : 60   (chapitre 3 : p. 38 à 51, soit 14 p.)
```

### Contrôle visuel

Pages 38 à 51 rendues en PNG et inspectées. Aucune page creuse, aucun tableau coupé au milieu
d'une phrase, aucune figure illisible. Les pages 52 à 56 et 58 restent quasi vides : ce sont les
amorces des chapitres 4 à 7, encore non rédigés.

---

## 8. Statut final

**Terminé.** Le chapitre 3 est rédigé, vérifié et intégré au document compilé.

### Livrables

- `report/chap_03.tex` — 14 pages, 7 sections, 3 figures, 8 tableaux
- `report/img/ch03_split_antifuite.png` — figure originale
- `report/main.pdf` — 60 pages, compilation propre

### Limites énoncées dans le chapitre

Conformément à la règle R3, trois limites sont écrites noir sur blanc plutôt que contournées :

1. **Représentativité** (§ 3.4.3) — le corpus s'organise en 58 scénarios récurrents ; 3 % de titres
   uniques contre 91 % dans le jeu public comparable. Le modèle apprend à reconnaître des familles
   de problèmes déjà rencontrées ; sa capacité sur un problème inédit n'est pas mesurable ici.
2. **Couverture du jeu de test** (§ 3.5.4) — 5 catégories sur 8. Toute moyenne macro sur ce jeu est
   mécaniquement supérieure à celle calculée sur 8 classes, et les deux ne sont pas comparables.
3. **Données personnelles** (§ 3.6.2) — 202 noms de collaborateurs en clair, anonymisation
   identifiée comme prioritaire et non réalisée.

### Points ouverts

- **Chapitres 4 à 7** non rédigés (amorces seulement).
- **Conclusion générale**, `annexes.tex`, résumés FR/EN (`tpl/resume.tex`) encore en `\todo`.
- **`CADRAGE_SRS.md` § 2** décrit trois personas là où le code n'en implémente que deux
  (`client`, `admin`). Signalé à plusieurs reprises, non tranché.
- **Cadence de suivi avec les encadrants** toujours inconnue ; conditionne la précision de la
  section 1.2, qui parle d'« itérations d'une durée comparable » sans pouvoir nommer de rythme.
- **Autorisation d'exploitation** des données réelles dans un mémoire soutenu publiquement :
  question posée à l'entreprise, sans réponse à ce jour.
