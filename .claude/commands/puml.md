---
description: Écrit ou met à jour un diagramme PlantUML du mémoire, le rend et vérifie le résultat
argument-hint: [nom-du-diagramme] [ce qu'il doit représenter]
allowed-tools: Bash(bash report/diagrams/render.sh:*), Read, Write, Edit, Glob, Grep
---

Diagramme demandé : **$ARGUMENTS**

Les sources PlantUML du mémoire vivent dans `report/diagrams/`, les images produites
dans `report/img/`. Chaque source inclut `_style.puml`, qui porte le langage visuel
commun au mémoire.

Marche à suivre :

1. Si un `.puml` de ce nom existe déjà, le lire avant de le modifier. Sinon en créer un,
   qui commence par `@startuml <nom>` puis `!include _style.puml`.
2. **N'inventer aucun fait.** Tout ce que le diagramme affirme — attributs, transitions,
   conteneurs, appels — doit être lu dans le code (`helpdesk-ai/api/`, `docker/`) ou dans
   un document de conception du dépôt. En cas de doute, poser la question plutôt que
   supposer, et citer en commentaire du `.puml` le fichier source des faits représentés.
3. Rendre avec `bash report/diagrams/render.sh <nom>`.
4. **Relire l'image produite** avec l'outil Read. Vérifier qu'aucun libellé n'est tronqué
   ni superposé, que les flèches partent et arrivent au bon endroit, et que le rapport
   largeur/hauteur reste proche de 1,2 pour tenir sur une page à `\textwidth`. Si le
   rendu est mauvais, corriger la source et rendre à nouveau.
5. Si le diagramme entre dans le mémoire, indiquer la ligne `\includegraphics` à ajouter,
   sans modifier le `.tex` sans y avoir été invité.

Rappels de mise en page PlantUML : `left to right direction` élargit un diagramme trop
haut, `hide circle` retire la pastille de classe, `skinparam nodesep` et `ranksep` règlent
les espacements, `together { }` regroupe des éléments que le moteur sépare.
