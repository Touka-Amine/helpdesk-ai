# Tâche 3 — Détection et suppression des marqueurs de rédaction automatique (chapitre 1)

> Projet : mémoire PFE **HelpDesk AI** — Mohamed Amine Toukabri — OneTech Business Solutions
> Tâches précédentes : [`task_1_completed.md`](task_1_completed.md) · [`task_2_completed.md`](task_2_completed.md)
> Date : 2026-08-20 · Branche : `chore/gouvernance-pfe`

---

## 1. Sortie transmise dans le fil de conversation

Chapitre réécrit. Les faits, les chiffres, les quatre tableaux et les deux figures sont inchangés —
seule la prose a bougé.

**Les antithèses « pas X, mais Y »** passent de huit à zéro. Elles étaient le tic le plus visible :
« ne consiste pas à… mais », « n'a pas pour objet de… mais », « traduit non pas… mais ». Chacune
devient une affirmation directe. *« Qualifier un ticket, c'est décider qui va le traiter »* dit la
même chose et frappe plus fort.

**Les triades annoncées** passent de sept à deux. Le lecteur voyait « Trois tâches… », « Trois
démarches… », « Trois acteurs… » revenir page après page. Les listes restent, l'annonce disparaît.

**Une généralisation devient une preuve.** L'ancienne version affirmait que « les problèmes vraiment
inédits sont rares » — une opinion. La nouvelle l'appuie sur le corpus : sur 1 800 tickets, la
colonne des gestes de résolution ne compte que **58 valeurs distinctes**. Le chiffre existait déjà
dans les données. C'est le gain le plus utile de cette passe : un jury ne discute pas un chiffre
vérifiable.

**Les tirets cadratins en prose** tombent à zéro. Les six phases de CRISP-DM et les trois conditions
du marché sont rendues en syntaxe française ordinaire.

**Le registre commercial** disparaît, **les connecteurs vides** sont supprimés, **les annonces
d'importance** sont remplacées par des affirmations. Le vocabulaire est stabilisé : *ticket* et
*demande* pour l'objet, *demandeur* pour la personne, *démarche* pour la méthode.

Compilation propre : 32 pages, zéro erreur, zéro référence non résolue, chapitre à 8 pages.

---

## 2. Objet de la tâche

### Demande

Deux temps successifs demandés par l'auteur :

1. Installer la skill `humanize` depuis le dépôt `smykla-skalski/sai`
2. L'exécuter en mode diagnostic sur `report/chap_01.tex`, puis appliquer les corrections
3. Réécrire le chapitre 1 en traitant les marqueurs restants

### Critères de réussite

- Aucune donnée chiffrée modifiée ou perdue
- Structure du chapitre inchangée : `Introduction` / `1.1` / `1.2` / `Conclusion`
- Tableaux, figures, `\label` et `\ref` préservés
- Compilation sans erreur ni référence non résolue

### Enjeu

Un mémoire dont la prose porte les marqueurs d'une génération automatique perd en crédibilité, quelle
que soit la qualité du travail technique sous-jacent. Le risque n'est pas lexical — aucun terme
suspect n'était présent — mais **rythmique** : des figures de style répétées d'un paragraphe à
l'autre finissent par se remarquer.

---

## 3. Déroulement

| # | Action | Résultat |
|---|---|---|
| 1 | `npx --yes skillfish add smykla-skalski/sai humanize` | Échec — `504 Gateway Timeout` sur l'API GitHub |
| 2 | Nouvelle tentative de la même commande | Succès — skill installée pour 4 agents |
| 3 | Vérification de `~/.claude/skills/humanize/` | `SKILL.md` (10 430 octets) + `references/` présents |
| 4 | `/humanize report/chap_01.tex --score-only` | 13 patterns détectés, sévérité **Moderate**, aucun fichier modifié |
| 5 | `/humanize` sans argument | Application des corrections sur `chap_01.tex` et `introduction.tex`, sauvegarde préalable |
| 6 | Relecture du fichier modifié | Corrections de la skill conservées, patterns résiduels identifiés |
| 7 | Réécriture complète de `chap_01.tex` | Traitement des 9 patterns restants |
| 8 | Compilation 4 passes + contrôle métrique | 0 erreur, 8 pages, flottants en place |

### Répartition du travail entre la skill et la réécriture

La skill a traité les marqueurs **mécaniquement détectables** : gras superflus, tirets cadratins,
participes en apposition, doublons de phrases entre l'introduction générale et le chapitre 1.

La réécriture a traité ceux qui exigent de **reformuler l'argument** : antithèses, triades annoncées,
généralisations non sourcées, registre promotionnel, annonces d'importance. Une machine peut
compter les « ne… pas… mais » ; elle ne peut pas décider par quelle affirmation les remplacer sans
altérer le sens.

---

## 4. Entrées et sorties

### Diagnostic initial — 13 patterns

| Sévérité | Pattern | Occurrences |
|---|---|---|
| Glaring | P09 Antithèses « pas X, mais Y » | 8 |
| Glaring | P10 Triades annoncées | 7 |
| Clear | P14 Gras excessif en prose | 9 |
| Clear | P13 Tirets cadratins | 5 paires |
| Clear | P15 Liste à en-têtes gras déguisée en prose | 1 |
| Clear | P08 Évitement de la copule | 2 |
| Clear | P05 Attribution vague | 2 |
| Clear | P04 Registre promotionnel | 2 |
| Clear | P22 Connecteurs de remplissage | 11 |
| Faint | P01 Inflation de l'importance | 3 |
| Faint | P03 Participe en apposition | 2 |
| Faint | P11 Alternance de synonymes | 3 séries |
| Faint | P20 Écho de limitation de connaissance | 2 |

**Non détectés** : vocabulaire d'IA, complaisance, artefacts de dialogue, hedging excessif,
conclusion générique, guillemets courbes, emoji, casse de titre. Le diagnostic notait que le texte se
situait « bien au-dessus de la ligne de base habituelle ».

### Métriques avant / après

| Indicateur | Avant | Après |
|---|---|---|
| Antithèses « ne… pas… mais » | 8 | **0** |
| Occurrences de « trois » annonçant une liste | 7 | **2** (les deux factuelles) |
| `\textbf` en prose | 9 | **1** (`HelpDesk AI`, première mention) |
| `\textbf` total (en-têtes de tableaux inclus) | 20 | 12 |
| Tirets cadratins en prose | 15 | **0** |
| « par ailleurs / en effet / au demeurant / quant à lui » | 4 | **0** |
| « donc » | 6 | 3 |
| Mots (hors tableaux) | ~2 170 | 1 989 |
| Tableaux · figures | 4 · 2 | 4 · 2 |

### Fichiers modifiés

| Fichier | Nature |
|---|---|
| `report/chap_01.tex` | Réécrit intégralement — prose seule, structure et données inchangées |
| `report/introduction.tex` | Modifié par la skill : 7 ordinaux dégras, doublons avec le chapitre 1 reformulés |
| `report/main.pdf` | Régénéré — 32 pages |

Sauvegarde des deux fichiers avant intervention de la skill, dans le répertoire de travail
temporaire (`humanize-backup/`).

### Correction de fond apportée à la rédaction

Le diagnostic signalait deux affirmations non sourcées sur le caractère répétitif du support. Elles
ont été remplacées par une mesure tirée du corpus :

> Sur 1 800 tickets, la colonne consacrée aux gestes de résolution ne compte que 58 valeurs
> distinctes.

Ce chiffre était déjà connu — il apparaît dans l'analyse de `HelpDesk1.csv` menée en tâche 1 — mais
n'était pas exploité au chapitre 1. Il transforme une opinion en fait vérifiable et prépare
l'analyse de la redondance du corpus au chapitre 3.

---

## 5. Erreurs rencontrées et traitement

### Échec d'installation

```
Error: Failed to download https://api.github.com/repos/smykla-skalski/sai/tarball/main:
504 Gateway Timeout
```

**Cause.** Indisponibilité temporaire de l'API GitHub. Le dépôt avait pourtant été résolu
correctement à l'étape précédente : 42 skills listées, dont `Humanize`.

**Traitement.** Nouvelle exécution de la commande, sans modification. L'installation a abouti.
Aucune action corrective nécessaire.

### Faux positifs écartés du diagnostic

Trois signalements de la skill n'ont pas été suivis, chacun pour une raison précise.

**Les comptages factuels.** « trois métiers », « cinq sprints », « six domaines » décrivent des
réalités vérifiables. Les supprimer aurait dégradé l'exactitude au profit du style.

**Les sections `Introduction` et `Conclusion` de chapitre.** Signalées comme structure formulaïque,
elles sont imposées par la convention du mémoire de PFE français et figurent dans les trois rapports
de référence.

**Les tirets dans les cellules de tableau.** Comptés comme tirets cadratins par la skill, ils servent
de séparateur dans la colonne « Chapitre ». Ils ont néanmoins été remplacés par des deux-points, par
cohérence typographique.

### Vérification de non-régression

Le risque principal d'une réécriture stylistique est la perte silencieuse d'une donnée. Contrôles
effectués après compilation :

- Tous les chiffres présents avant réécriture le sont après : 4 500, 50, 325, 150, 300, 11, 202, 8,
  1 800, 464, 476, 58
- Les 4 `\label` et les 6 `\ref` résolvent : aucun avertissement `Reference undefined`
- La citation `\cite{otbs-site}` résout
- Placement des flottants inchangé : Figure 1.1 et Tableau 1.1 p. 6, Figure 1.2 p. 7, Tableaux 1.2 à
  1.4 p. 8 à 10

---

## 6. État final

### Contrôles de compilation

```
Erreurs                     0
Références non résolues     0
Citations non résolues      0
Pages                      32
Chapitre 1                  8 pages
Tableaux · figures          4 · 2
```

### Critères de réussite

| Critère | État |
|---|---|
| Aucune donnée chiffrée modifiée ou perdue | Atteint — 12 valeurs vérifiées une à une |
| Structure du chapitre inchangée | Atteint — sommaire identique |
| Tableaux, figures, labels préservés | Atteint |
| Compilation sans erreur | Atteint |
| Marqueurs de rédaction automatique traités | Atteint — 13 patterns sur 13 |

### Points ouverts

1. **Méthodologie** — la section 1.2 décrit une démarche hybride, agile dans son pilotage et inspirée
   de CRISP-DM. Elle ne revendique pas Scrum, faute d'artefacts correspondants dans le dépôt
   (`PLAN.md` décrit 16 phases numérotées, aucun sprint backlog ni rétrospective). Si des rituels de
   suivi à cadence fixe ont réellement existé, la section devra être ajustée.
2. **Spécification des besoins** — le passage à une structure en deux sections a retiré du chapitre 1
   les tableaux d'acteurs, d'exigences fonctionnelles et non fonctionnelles, ainsi que la matrice de
   traçabilité. `PLAN_RAPPORT.md` ne leur assigne aucun autre chapitre. À replacer, au chapitre 2 ou
   en annexe.
3. **Autorisation OTBS** — l'exploitation des données de tickets dans un mémoire soutenu publiquement
   reste à formaliser (report des tâches 1 et 2).
4. **Chapitre 1 en attente de validation** avant passage au chapitre 2.

### Documents liés

- Tâches précédentes : `reports/memoire-pfe-helpdesk-ai/task_1_completed.md`, `task_2_completed.md`
- Plan du mémoire : `helpdesk-ai/PLAN_RAPPORT.md`
- Questions entreprise restantes : `report/QUESTIONS_ENTREPRISE.md`
- Skill utilisée : `~/.claude/skills/humanize/SKILL.md`
