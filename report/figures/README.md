# Figures du chapitre 6

Scripts de génération des six diagrammes du chapitre 6, écrits avec matplotlib.
`style.py` porte le langage visuel commun : quatre familles de couleurs sémantiques,
tracé des connecteurs avant les nœuds, helpers de boîte, de note UML et d'acteur.

```bash
cd report/figures && for f in f*.py; do python "$f"; done
```

Chaque script écrit directement dans `report/img/` à 200 ppp.

| Script | Figure | Source des faits représentés |
|---|---|---|
| `f1_contexte.py` | `ch06_contexte.png` | périmètre du chapitre 1 |
| `f2_archi.py` | `ch06_architecture.png` | `docker/docker-compose.yml`, `api/db/vector_store.py` |
| `f3_cas.py` | `ch06_cas_utilisation.png` | backlog du sprint 4, `CADRAGE_SRS.md` |
| `f4_classes.py` | `ch06_classes.png` | `api/db/models.py` |
| `f5_sequence.py` | `ch06_sequence.png` | `api/routers/tickets.py` |
| `f6_etats.py` | `ch06_etats_ticket.png` | `api/routers/tickets.py:28` (`STATUS_TRANSITIONS`) |

Toute modification du code cité doit entraîner la régénération de la figure correspondante.

---

## Statut : superseded

Ces scripts ont produit la première version des six figures du chapitre 6. Le mémoire sert
désormais les figures décrites en PlantUML dans [../diagrams/](../diagrams/).

Leur sortie a été redirigée vers `../img/_matplotlib/` pour qu'ils ne puissent plus écraser
les figures servies au mémoire. Ils sont conservés pour deux raisons : ils gardent la trace
d'une mise en page à zéro croisement obtenue par placement manuel, et ils restent la
solution à reprendre si une figure future demande un contrôle que PlantUML ne donne pas.
