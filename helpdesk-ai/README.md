# HelpDesk AI

Plateforme de classification automatique et d'assistance à la résolution de tickets
informatiques francophones, développée chez **OneTech Business Solutions** dans le cadre d'un
Projet de Fin d'Études en Data Science et Intelligence Artificielle (TEK-UP).

Un ticket entrant est classé dans l'une de huit catégories, puis rapproché des résolutions
passées par recherche sémantique ; un modèle de langage local reformule ces résolutions en
français professionnel à l'intention de l'administrateur, qui reste seul décideur.

**Aucune donnée ne sort de l'infrastructure.** Le modèle de langage tourne en local via Ollama,
sans appel à un service externe. Cette contrainte vient du service support et a orienté
l'ensemble des choix techniques.

## Démarrage

```bash
docker compose -f docker/docker-compose.yml up --build
```

| Service | Adresse |
|---|---|
| Frontend Angular | http://localhost:8081 |
| API FastAPI (Swagger) | http://localhost:8000/docs |
| Tableau de bord | http://localhost:8501 |

Détail de la configuration, des variables d'environnement et de l'exploitation :
[DEPLOYMENT.md](DEPLOYMENT.md).

## Tests

```bash
python -m pytest tests/ -q
```

**133 tests** au 2026-09-08. Pour une exécution rapide pendant le développement,
`pytest -m "not slow"` exclut ceux qui chargent les modèles. Stratégie complète :
[TESTING.md](TESTING.md).

## Reproduire la chaîne de traitement

```bash
dvc repro
```

Huit étapes : `preprocess`, `split`, `build_dataset`, `train`, `promote`, `rag_build`,
`rag_semantic_build`, `rag_eval`. Le paramétrage est dans `params.yaml`.

`promote` est le **seul** écrivain de `models/best_pipeline.pkl` : un modèle candidat ne
remplace le modèle servi qu'après avoir passé trois conditions, et le modèle précédent reste
restaurable. Voir [MLOPS.md](MLOPS.md).

## Organisation du dépôt

| Répertoire | Contenu |
|---|---|
| `api/` | API FastAPI — `routers` (HTTP), `services` (métier), `db` (persistance et base vectorielle) |
| `frontend/` | Application Angular (espaces client et administrateur) |
| `src/` | Traitement des données, modèles, RAG, registre, chaîne MLOps, supervision |
| `notebooks/` | Exploration, entraînement et évaluation — voir la cartographie critique dans `../reports/analyse-notebooks/` |
| `tests/` | Suite pytest |
| `data/`, `models/`, `metrics/` | Artefacts versionnés par DVC |
| `docker/` | Images et orchestration |
| `../report/` | Sources LaTeX du mémoire |

## Documentation

**Pilotage**
[PLAN.md](PLAN.md) est la source de vérité du projet : phases, tâches, tableau de bord.
[PROJECT_STATUS.md](PROJECT_STATUS.md) en donne le résumé, [TASKS.md](TASKS.md) le journal des
tâches, [CHANGELOG.md](CHANGELOG.md) l'historique daté, [RISKS.md](RISKS.md) le registre des
risques, [DECISIONS.md](DECISIONS.md) les décisions d'architecture, [BACKLOG.md](BACKLOG.md) ce
qui est hors périmètre.

**Conception**
[CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md) et [CADRAGE_SRS.md](CADRAGE_SRS.md) portent les
exigences et la matrice de traçabilité. [ARCHITECTURE.md](ARCHITECTURE.md) décrit les modules et
les flux, [TICKET_WORKFLOW.md](TICKET_WORKFLOW.md) le parcours d'un ticket,
[MLOPS.md](MLOPS.md) les deux boucles d'amélioration, [DEPLOYMENT.md](DEPLOYMENT.md)
l'infrastructure et [TESTING.md](TESTING.md) la stratégie de tests.
[DIAGNOSTIC_QUALITE_DONNEES.md](DIAGNOSTIC_QUALITE_DONNEES.md) documente les limites du corpus.

**Mémoire**
[PLAN_RAPPORT.md](PLAN_RAPPORT.md) porte le plan détaillé en 7 chapitres et les règles de
citation des chiffres. [PFE_PROGRESS.md](PFE_PROGRESS.md) suit l'avancement de la rédaction.
[PROMPT_REDACTION_RAPPORT.md](PROMPT_REDACTION_RAPPORT.md) fixe les conventions d'écriture et,
en section R2, **la liste des valeurs exactes à citer** — c'est ce tableau qui fait foi, pas les
chiffres dispersés dans les autres fichiers.

## Limites connues

Elles sont documentées plutôt que masquées, et détaillées dans [RISKS.md](RISKS.md).

- Le corpus compte 1800 tickets pour seulement **58 scénarios distincts** : la redondance limite
  ce qu'un modèle peut apprendre, et le découpage train/test est fait par titre pour éviter
  qu'un même scénario se retrouve des deux côtés.
- Le jeu de test du pipeline ne couvre que **5 catégories sur 8** (R-14). Tout F1-macro doit
  donc être cité avec son protocole.
- **CamemBERT n'est pas industrialisé** : la meilleure combinaison mesurée (CamemBERT + règles,
  F1-macro 0,8343) n'est pas celle que sert l'API, qui utilise le pipeline TF-IDF + règles.
- Les deux boucles MLOps sont démontrées de bout en bout mais **n'ont pas encore de trafic
  réel** : leurs seuils restent à calibrer (R-20).
- Le RGPD n'est pas traité, et la latence P95 n'est pas conforme sous charge concurrente (R-13).

## Auteur

Mohamed Amine Toukabri — TEK-UP, Data Science et Intelligence Artificielle, 2025–2026.
Encadrement : Madame Rahma Oueslati (OneTech Business Solutions), Monsieur Ahmed Dhouibi (TEK-UP).
