# Tâche 2 — Finalisation de la page de garde

> Projet : mémoire PFE **HelpDesk AI** — Mohamed Amine Toukabri — OneTech Business Solutions
> Spécification parente : `helpdesk-ai/PROMPT_REDACTION_RAPPORT.md`
> Tâche précédente : [`task_1_completed.md`](task_1_completed.md)
> Date : 2026-08-18 · Branche : `chore/gouvernance-pfe`

---

## 1. Sortie transmise dans le fil de conversation

### Premier échange — placement du logo

Logo OTBS placé en haut à droite, en vis-à-vis du logo TEK-UP.

Deux conséquences de ce déplacement, tranchées sans attendre :

**L'emblème national a été retiré.** Il occupait cette place ; les deux ne tiennent pas côte à côte
sans surcharger l'en-tête. Il peut être remis entre le logo TEK-UP et le bloc de texte central si
l'auteur le souhaite.

**Le logo en bas de page a été supprimé.** Il aurait fait doublon. La mention *« Projet réalisé au
sein de OneTech Business Solutions »* reste, en italique au-dessus de l'année universitaire — elle
nomme l'entreprise sans répéter l'image.

Compilation propre : 44 pages, zéro erreur.

### Second échange — fonctions des encadrants

Fonctions ajoutées et alignement corrigé.

```
Encadrant professionnel :   Madame Rahma OUESLATI     Consultante SI
Encadrant académique :      Monsieur Ahmed DHOUIBI    Enseignant
```

Les trois colonnes étaient composées en `minipage` centrées verticalement, ce qui décalait la
fonction par rapport au nom — visible sur la version précédente où « Enseignant » flottait entre
les deux lignes. Elles ont été remplacées par un vrai tableau à trois colonnes : chaque ligne
aligne désormais le libellé, le nom et la fonction sur la même base.

**Un point sur l'orthographe du prénom.** L'auteur avait écrit « Rahama » la première fois,
« rahma » la seconde. La forme **Rahma** a été retenue, qui est aussi celle enregistrée dans le
fichier de tickets d'OTBS. Sur une couverture de mémoire, autant être sûr — confirmation demandée.

Compilation propre : 44 pages, zéro erreur.

---

## 2. Objet de la tâche

### Demandes de l'auteur

Deux demandes successives, portant toutes deux sur la page de garde :

1. « pour la page de garde, mettre le logo dans la partie droite en haut »
2. « ajouter à Rahma Oueslati *Consultante SI* et à Ahmed Dhouibi *Enseignant* ; ajuster le rôle de
   chaque enseignant »

### Contexte

La tâche 1 avait aligné la page de garde sur celle du rapport de référence
`exemple_de_rapport/Rapport_PFE_VFinale (2).pdf`, qui place l'emblème national tunisien en haut à
droite et le logo de l'entreprise en bas de page. L'auteur revient sur ce choix et préfère la
disposition d'origine du template TEK-UP : logo école à gauche, logo entreprise à droite.

### Critères de réussite

- Logo OTBS en haut à droite, à la même hauteur que le logo TEK-UP
- Pas de doublon visuel du logo sur la page
- Fonctions des deux encadrants affichées et alignées avec les noms correspondants
- Compilation sans erreur

---

## 3. Déroulement

| # | Action | Résultat |
|---|---|---|
| 1 | Édition 1 de `tpl/cover_page.tex` : `armoiries_tunisie.png` → `logoSociete.png` dans la minipage haut-droite | Logo OTBS positionné, largeur `1.15\columnwidth` |
| 2 | Édition 2 : suppression du `\includegraphics` du bloc bas de page | Doublon éliminé, mention textuelle conservée |
| 3 | Compilation 4 passes | 44 pages, 0 erreur, 786 506 octets |
| 4 | Rendu de la page 1 à 105 dpi, contrôle visuel | Disposition validée ; désalignement de la colonne « fonction » repéré |
| 5 | Édition de `global_config.tex` : `\proFramerName` et `\proFramerSpeciality` | « Madame Rahma OUESLATI » · « Consultante SI » |
| 6 | Édition 3 de `tpl/cover_page.tex` : 3 `minipage` → un `tabular` à 3 colonnes | Alignement par ligne garanti |
| 7 | Compilation 4 passes | 44 pages, 0 erreur, 787 599 octets |
| 8 | Rendu de la page 1 à 115 dpi, contrôle visuel | Alignement conforme |

### Décision de conception — pourquoi un tableau plutôt que trois minipages

Le template composait le bloc des encadrants en trois `minipage[c]` juxtaposées. L'alignement
vertical `[c]` centre chaque bloc indépendamment sur sa propre hauteur. Les noms étant en
`\textbf` à la taille `\large` et les fonctions en corps normal, les deux colonnes n'avaient pas la
même hauteur totale : la colonne des fonctions se retrouvait décalée d'environ une demi-ligne.

Le passage à un `tabular` à trois colonnes de largeurs fixes résout le problème par construction :
les cellules d'une même ligne partagent la même ligne de base, quelle que soit leur mise en forme.
Le `\setlength{\tabcolsep}{0pt}` et les séparateurs `@{}` suppriment les marges internes de
colonne, pour reproduire l'espacement du template d'origine.

### Arbitrage sur l'orthographe du prénom

Trois occurrences, deux graphies :

| Source | Graphie |
|---|---|
| Message de l'auteur, premier envoi | Rahama |
| Message de l'auteur, second envoi | rahma |
| `HelpDesk1.csv`, champ `Assigné à` | Rahma Oueslati |

**Rahma** a été retenue : elle est majoritaire, et surtout elle provient du système d'information
de l'entreprise elle-même. La divergence est signalée à l'auteur plutôt que résolue silencieusement,
s'agissant du nom d'une personne sur une couverture de mémoire.

---

## 4. Entrées et sorties

### Fichiers modifiés

| Fichier | Modification |
|---|---|
| `report/tpl/cover_page.tex` | 3 éditions : image haut-droite, suppression du logo bas de page, bloc encadrants en `tabular` |
| `report/global_config.tex` | `\proFramerName{Madame Rahma OUESLATI}` · `\proFramerSpeciality{Consultante SI}` |
| `report/main.pdf` | Régénéré deux fois — état final 44 pages, 787 599 octets |

### Code final du bloc encadrants

```latex
\setlength{\tabcolsep}{0pt}
\begin{tabular}{@{}p{0.30\columnwidth}@{}p{0.42\columnwidth}@{}p{0.28\columnwidth}@{}}
Encadrant professionnel : & \textbf{\@proFramerName} & \@proFramerSpeciality \\[2mm]
Encadrant académique :    & \textbf{\@academicFramerName} & \@academicFramerSpeciality \\
\end{tabular}
```

### Ressource devenue inutilisée

`report/img/armoiries_tunisie.png` (36 039 octets) n'est plus référencée. Le fichier est conservé
dans le dépôt : l'auteur peut vouloir réintroduire l'emblème, et sa réextraction depuis le PDF de
référence coûterait une manipulation inutile.

---

## 5. Erreurs rencontrées et traitement

**Aucune erreur de compilation** sur les deux passes de cette tâche.

### Défaut visuel détecté au contrôle, non signalé par LaTeX

Le désalignement de la colonne des fonctions n'a produit **ni erreur ni avertissement** : du point
de vue de LaTeX, trois minipages centrées côte à côte constituent une composition parfaitement
valide. Le défaut n'est apparu qu'au rendu de la page en image.

Ce cas confirme l'utilité du contrôle visuel systématique après chaque modification de mise en
page. Les indicateurs de compilation — zéro erreur, zéro référence non résolue — ne disent rien de
l'alignement, de l'équilibre des blancs ou de la lisibilité.

### Régression évitée

La suppression de l'emblème et celle du logo en bas de page n'avaient pas été demandées
explicitement. Elles découlent mécaniquement de la demande principale : deux images ne tiennent pas
dans le même emplacement, et un logo affiché deux fois sur une couverture est un défaut. Les deux
décisions ont été prises, puis **annoncées à l'auteur avec la possibilité de revenir en arrière**,
plutôt que d'interrompre le travail pour une question de détail.

---

## 6. État final

### Contrôles de compilation

```
Erreurs                     0
Références non résolues     0
Citations non résolues      0
Overfull hbox               4   (toutes dans tpl/cover_page.tex — minipages de l'en-tête)
Pages                      44
Taille                     787 599 octets
```

Les quatre débordements résiduels sont ceux du gabarit d'en-tête du template TEK-UP. Ils existent
dans tout mémoire bâti sur cette classe, y compris le rapport de référence.

### Composition finale de la page de garde

| Zone | Contenu |
|---|---|
| Haut gauche | Logo TEK-UP |
| Haut centre | République Tunisienne · Ministère · École · TEK-UP |
| Haut droite | Logo OneTech B.S |
| Corps | Rapport de PFE · Diplôme · Spécialité *Data Science & Intelligence Artificielle* · Auteur |
| Encadré | Titre du mémoire |
| Sous l'encadré | Encadrants, noms et fonctions, sur trois colonnes alignées |
| Bas | *Projet réalisé au sein de OneTech Business Solutions* |
| Pied de page | Année Universitaire 2025 – 2026 |

### Critères de réussite

| Critère | État |
|---|---|
| Logo OTBS en haut à droite | Atteint |
| Aucun doublon visuel | Atteint |
| Fonctions affichées et alignées | Atteint |
| Compilation sans erreur | Atteint |

### Points ouverts

1. **Orthographe du prénom** — « Rahma » retenue ; confirmation attendue.
2. **Emblème national** — retiré ; peut être réintroduit sur demande.
3. **Volume du chapitre 1** — 19 pages contre 12–15 au plan ; réduction toujours à arbitrer
   (report de la tâche 1).
4. **Autorisation OTBS** — exploitation des données de tickets à formaliser (report de la tâche 1).
5. **Chapitre 1 en attente de validation** — le protocole impose l'accord de l'auteur avant le
   chapitre 2.

### Documents liés

- Tâche précédente : `reports/memoire-pfe-helpdesk-ai/task_1_completed.md`
- Plan du mémoire : `helpdesk-ai/PLAN_RAPPORT.md`
- Questions entreprise restantes : `report/QUESTIONS_ENTREPRISE.md`
- Script de compilation : `report/compiler.bat`
