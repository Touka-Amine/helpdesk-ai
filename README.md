# HelpDesk AI

Classification automatique et assistance à la résolution de tickets informatiques
francophones. Projet de Fin d'Études en Data Science et Intelligence Artificielle,
réalisé chez **OneTech Business Solutions** et soutenu à **TEK-UP**.

Le service support traitait quatorze mois de tickets sans jamais réutiliser les
résolutions passées. La plateforme transforme cet historique en aide au traitement :
une demande déposée en texte libre reçoit une catégorie proposée par un modèle,
accompagnée des tickets déjà résolus les plus proches. L'administrateur corrige,
traite, et rédige la solution appliquée, qui rejoint la base interrogée par la demande
suivante.

**Aucune donnée ne sort de l'infrastructure.** Le modèle de langage tourne en local via
Ollama, sans appel à un service externe. La contrainte vient du service support et a
orienté tous les choix techniques.

## Ce que le système fait, et ce qu'il ne fait pas

Il qualifie, retrouve et suggère. Il ne clôt aucun ticket. Une prédiction sous le seuil
de confiance part en file d'approbation humaine, et la décision reste au consultant.

## Résultats mesurés

| Mesure | Valeur |
|---|---|
| Corpus | 1 800 tickets, 8 catégories, 58 scénarios distincts |
| Découpage | 1 444 entraînement, 356 test, 1 357 indexés pour la recherche |
| F1-macro, hasard stratifié | 0,1382 |
| F1-macro, TF-IDF seul | 0,3753 |
| F1-macro, TF-IDF et règles métier | 0,5827 |
| F1-macro, CamemBERT LoRA seul | 0,5685 |
| F1-macro, CamemBERT LoRA et règles métier | **0,8343** |
| F1-macro du pipeline réellement servi | 0,5829 |
| Précision à trois passages, recherche hybride | 0,3542 |
| Précision à trois passages, sémantique seule | 0,2917 |
| Précision à trois passages, lexicale seule | 0,1542 |
| Latence d'inférence, TF-IDF | 5,0 ms |
| Latence d'inférence, CamemBERT sur processeur | 325,8 ms |
| Latence d'inférence, CamemBERT sur carte graphique | 58,7 ms |
| Temps de réponse, 95e centile en séquentiel | 330 ms |
| Suite de tests | 150 tests, 132 en intégration continue, 44 % de couverture |

La combinaison la plus performante n'est pas celle que sert l'API. CamemBERT coûte
325,8 ms par ticket sur processeur, davantage à lui seul que le budget de latence
entier, donc la version servie repose sur la chaîne lexicale plus légère. Servir le
transformer redevient défendable dès que la machine hôte dispose d'une carte graphique.

## Architecture

```
Angular 17  ──►  FastAPI  ──►  PostgreSQL          état des tickets
                    │
                    ├──────►  TF-IDF + règles      catégorie proposée
                    ├──────►  FAISS + ChromaDB     résolutions proches
                    └──────►  Ollama (llama3.2)    reformulation locale
```

| Couche | Technologies |
|---|---|
| Interface | Angular 17, composants autonomes, Tailwind v4, 17 écrans |
| Service | FastAPI, Python 3.11, SQLAlchemy, JWT |
| Persistance | PostgreSQL 16, ChromaDB pour la base de connaissances vivante |
| Modèles | scikit-learn, CamemBERT adapté par LoRA, sentence-transformers |
| Recherche | FAISS pour l'index figé, hybride lexical et sémantique |
| Génération | Ollama, llama3.2:3b, entièrement local |
| Industrialisation | Docker Compose, DVC, MLflow, pytest, GitHub Actions |

## Démarrage

```bash
docker compose -f helpdesk-ai/docker/docker-compose.yml up --build
```

Quatre conteneurs : `ollama`, `postgres`, `api`, `frontend`. L'interface répond sur
http://localhost:8081 et la documentation de l'API sur http://localhost:8000/docs.

Copier `helpdesk-ai/.env.example` vers `.env` et renseigner les trois valeurs marquées
`REMPLACER__` avant tout démarrage. Le service refuse de se lancer tant qu'elles sont
inchangées.

## Les données ne sont pas distribuées

Le corpus est un export réel du service support. Il porte des noms de demandeurs, des
consultants nommés, des codes de filiale, des identifiants clients et le chemin interne
du site qui l'héberge. Rien de tout cela ne figure dans ce dépôt, ni dans son
historique, et les sorties des notebooks ont été vidées pour la même raison.

Ce qui reste local : `data/raw/`, `models/semantic_rag/knowledge_base.parquet`,
`data/reference/test_reference.csv` et tous les jeux dérivés. Un clone frais exécute la
suite de tests et démarre l'API. Il ne peut ni rejouer `dvc repro`, ni servir de
recommandations, faute de corpus.

## Limites connues

Elles sont documentées plutôt que masquées.

Le corpus compte 1 800 tickets pour 58 scénarios distincts seulement. Cette redondance
plafonne ce qu'un modèle peut apprendre, et le découpage entraînement/test se fait par
titre pour éviter qu'un même scénario se retrouve des deux côtés. Le jeu de test gelé ne
couvre que cinq des huit catégories, si bien que tout F1-macro doit être cité avec son
protocole.

Deux exigences chiffrées ne sont pas tenues. Le temps de réponse atteint 330 ms au 95e
centile pour un budget de 300, et le rappel sur la catégorie *Sécurité* plafonne à 0,60
pour une cible de 0,70.

Trois réserves subsistent. La conformité au règlement sur les données personnelles
attend un arbitrage écrit du service. L'interface n'est couverte par aucun test
automatique. La valeur d'usage n'a pas été mesurée auprès des consultants.

## Organisation du dépôt

| Répertoire | Contenu |
|---|---|
| `helpdesk-ai/api/` | API FastAPI : `routers` HTTP, `services` métier, `db` persistance |
| `helpdesk-ai/frontend/` | Application Angular, espaces demandeur et administrateur |
| `helpdesk-ai/src/` | Traitement des données, modèles, RAG, registre, chaîne MLOps |
| `helpdesk-ai/notebooks/` | Exploration, entraînement, évaluation |
| `helpdesk-ai/tests/` | Suite pytest |
| `helpdesk-ai/docker/` | Images et orchestration |
| `report/` | Sources LaTeX du mémoire, 137 pages |
| `report/diagrams/` | Sources PlantUML des diagrammes UML |

La documentation d'ingénierie vit dans `helpdesk-ai/` : cahier des charges, cadrage des
exigences, architecture, stratégie de tests, boucles MLOps, registre des risques,
décisions d'architecture. Le [README du projet](helpdesk-ai/README.md) en donne l'index.

## Droits

Aucune licence n'est accordée à ce stade. Le travail a été réalisé dans le cadre d'un
stage de fin d'études, et la répartition des droits entre l'auteur, TEK-UP et OneTech
Business Solutions n'a pas été arrêtée par écrit.

## Auteur

Mohamed Amine Toukabri, TEK-UP, Data Science et Intelligence Artificielle, 2025-2026.

Encadrement : Madame Rahma Oueslati (OneTech Business Solutions), Monsieur Ahmed Dhouibi
(TEK-UP).
