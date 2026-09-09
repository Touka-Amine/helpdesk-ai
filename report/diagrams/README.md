# Diagrammes PlantUML

Sources UML du mémoire. Le rendu va dans `../img/`, à 200 ppp.

## Les six diagrammes du chapitre 6

| Source | Figure | Type | Faits représentés, et où les vérifier |
|---|---|---|---|
| `ch06_contexte.puml` | 6.2 | C4 niveau 1 | Périmètre du chapitre 1 ; absence d'annuaire, `api/routers/auth.py` |
| `ch06_architecture.puml` | 6.3 | C4 niveau 2 + composants | `docker/docker-compose.yml` (cinq services) ; `api/db/vector_store.py:93` (ChromaDB embarqué) ; `params.yaml` |
| `ch06_cas_utilisation.puml` | 6.1 | Cas d'utilisation | Backlog du chapitre 2 ; deux rôles, `api/db/models.py` |
| `ch06_classes.puml` | 6.4 | Classes | `api/db/models.py`, les 27 attributs de `Ticket` |
| `ch06_sequence.puml` | 6.5 | Séquence | `api/routers/tickets.py`, chemin de création |
| `ch06_etats_ticket.puml` | 6.6 | États | `api/routers/tickets.py:28`, `STATUS_TRANSITIONS` |

Les deux vues d'architecture utilisent **C4-PlantUML**, fourni avec le jar sous
`<C4/C4_Context>` et `<C4/C4_Component>`. Les autres diagrammes incluent `_style.puml`,
qui porte le langage visuel commun.

Chaque source cite en commentaire d'en-tête le fichier de code dont elle tire ses faits.
Toute modification de ce code doit entraîner la régénération de la figure.

## Installation

PlantUML est un fichier `.jar` unique. Java 21 est déjà présent sur le poste, et le jar
embarque son propre Graphviz : **aucune installation système n'est nécessaire**.

```bash
mkdir -p "$LOCALAPPDATA/PlantUML" && curl -L -o "$LOCALAPPDATA/PlantUML/plantuml.jar" https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar
```

Version installée : **1.2026.8**, Graphviz embarqué 2.44.1, C4-PlantUML 2.13.0.
Le chemin du jar est lu dans `PLANTUML_JAR`, renseignée dans `.claude/settings.local.json` ;
à défaut, `render.sh` cherche aux emplacements usuels.

## Rendu

```bash
bash report/diagrams/render.sh
```

| Commande | Effet |
|---|---|
| `render.sh` | tous les diagrammes, en PNG 200 ppp |
| `render.sh ch06_classes` | un seul diagramme |
| `render.sh -f pdf` | en PDF vectoriel |

Formats vérifiés : `png`, `svg`, `pdf`, `eps`. Le jeu de caractères est forcé à UTF-8,
les accents français sont rendus correctement.

## Dans Claude Code

`/puml <nom> <description>` écrit ou met à jour un diagramme, le rend, puis relit l'image
produite pour vérifier qu'aucun libellé n'est tronqué. La commande impose aussi de citer
le fichier de code d'où viennent les faits représentés.

## Conventions apprises à l'usage

**La mise en page n'est pas pilotable.** PlantUML décide, on l'oriente. Les leviers qui
ont servi ici, par ordre d'efficacité :

- `left to right direction` redresse un diagramme d'états ou de cas d'utilisation qui sort
  en portrait. Le diagramme d'états est passé d'illisible à une bande large sans croisement ;
- raccourcir le texte des boîtes réduit la largeur et augmente d'autant la taille relative
  du texte une fois la figure mise à `\textwidth` ;
- `skinparam wrapWidth`, `nodesep` et `ranksep` resserrent l'ensemble ;
- les variantes directionnelles de C4 (`Rel_R`, `Rel_D`) se contredisent facilement et
  produisent alors une disposition pire que le placement automatique. Les avoir toutes
  retirées a suffi à corriger la vue des conteneurs.

**Ne pas dupliquer la prose dans la figure.** Les notes et légendes qui répétaient mot pour
mot le paragraphe voisin ont été retirées du diagramme d'états et du diagramme de cas :
elles consommaient de la largeur et rendaient tout le reste plus petit.

**Vérifier la figure rendue, pas seulement la source.** Un `<<extend>>` syntaxiquement
correct entre « Qualifier » et « Consulter l'historique » a été retiré parce qu'il était
faux sur le fond, et il déformait au passage la mise en page.

## Les scripts matplotlib de `../figures/`

Ils ont produit la première version de ces six figures et sont conservés à titre de trace.
Leur sortie a été redirigée vers `../img/_matplotlib/` pour qu'ils ne puissent plus écraser
les figures servies au mémoire. Ils donnent un contrôle complet des positions, au prix de
plusieurs centaines de lignes par figure ; PlantUML donne la notation UML juste en quelques
dizaines de lignes, sans contrôle de la mise en page.
