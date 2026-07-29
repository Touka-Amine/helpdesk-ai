# DECISIONS.md — Journal des décisions techniques (ADR)

> Une décision = un ADR : Contexte · Décision · Conséquences · Statut. Source de vérité :
> [PLAN.md](PLAN.md). Dernière mise à jour : *à la création*.

---

## ADR-001 — Périmètre « Cœur rehaussé (Must) »
- **Statut** : Accepté.
- **Contexte** : PFE de 6 mois, besoin d'un niveau ingénieur sans sur-dimensionnement.
- **Décision** : se concentrer sur CamemBERT fine-tuné, RAG sémantique évalué (RAGAS), MLOps léger,
  backend+front finalisés, Docker. Le reste va en [BACKLOG.md](BACKLOG.md).
- **Conséquences** : profondeur scientifique sur le cœur ; innovations avancées documentées en
  perspectives.

## ADR-002 — Fine-tuning sur GPU local
- **Statut** : Accepté.
- **Contexte** : GPU local disponible.
- **Décision** : entraîner CamemBERT + LoRA en local (PEFT), versionner les adaptateurs.
- **Conséquences** : itérations confortables ; reproductibilité à garantir (seeds, environnement).

## ADR-003 — CamemBERT comme modèle francophone
- **Statut** : Accepté.
- **Contexte** : données **en français** (catégories, résolutions). Les modèles anglophones
  généralistes sous-performent.
- **Décision** : CamemBERT/CamemBERTa fine-tuné pour la classification ; embeddings FR pour le RAG.
- **Conséquences** : meilleure adéquation linguistique ; dépendance HuggingFace.

## ADR-004 — Choix de la base vectorielle *(tranché 2026-07-29)*
- **Statut** : Accepté.
- **Contexte** : besoin d'un stockage/recherche d'embeddings pour la base de connaissances
  des tickets résolus, interrogée en direct par le RAG (voir `api/services/ai_service.py`).
- **Options** : **Qdrant** (riche, serveur), **Chroma** (simple, embarqué), **pgvector** (réutilise
  PostgreSQL).
- **Décision** : **ChromaDB**, en mode embarqué (`PersistentClient`, pas de service serveur
  séparé) — cohérent avec le choix monolithe modulaire (ADR-005) et évite d'ajouter un service
  d'infrastructure supplémentaire alors que PostgreSQL (ADR-006) suffit déjà pour
  la base opérationnelle. `pgvector` était l'alternative la plus proche mais aurait couplé le
  schéma vectoriel à la base relationnelle ; Chroma garde les deux préoccupations séparées
  (intégrité transactionnelle vs recherche sémantique) sans complexité opérationnelle
  supplémentaire (pas de conteneur en plus, stockage fichier dans le volume `api-data` existant).
- **Conséquences** : `api/db/vector_store.py` remplace l'ancien `api/db/nosql_store.py`
  (TinyDB) ; la collection Chroma est interrogée à chaque recommandation RAG
  (`query_similar()`), pas seulement en archive passive comme l'était TinyDB.

## ADR-005 — Monolithe modulaire vs microservices
- **Statut** : Accepté.
- **Contexte** : équipe = 1 stagiaire, PFE.
- **Décision** : **monolithe modulaire** bien découpé (routers/services/repositories). Microservices
  en perspective.
- **Conséquences** : simplicité de déploiement (docker-compose) ; bonne séparation logique.

## ADR-006 — SQLite → PostgreSQL *(tranché 2026-07-29)*
- **Statut** : Accepté.
- **Contexte** : SQLite convient pour un MVP mono-fichier, mais un incident réel a déjà été
  rencontré (crash `duplicate column name` lors d'une migration `ALTER TABLE` exécutée en
  parallèle par les 2 workers uvicorn — corrigé côté code, mais symptomatique des limites de
  SQLite en écriture concurrente). PostgreSQL est le standard attendu pour une base
  opérationnelle transactionnelle (utilisateurs, tickets, historique).
- **Options** : rester sur SQLite (simplicité, zéro dépendance) vs migrer vers PostgreSQL
  (robustesse concurrente, standard en production).
- **Décision** : **PostgreSQL**, ajouté comme service dédié dans `docker-compose.yml`
  (`postgres:16-alpine`), connexion via SQLAlchemy (`DB_URL=postgresql+psycopg2://...`).
  Le code de migration de colonnes (`api/db/database.py::_migrate_columns`) reste compatible
  SQLite pour un usage local hors Docker sans serveur Postgres (bascule automatique via
  `DB_URL`).
- **Conséquences** : un service supplémentaire à orchestrer (healthcheck, `depends_on` sur
  l'API) ; en contrepartie, écritures concurrentes fiables et un chemin plus direct vers un
  déploiement de production si le projet est repris au-delà du PFE.

---
*Template pour un nouvel ADR :*
```
## ADR-00X — Titre
- Statut : Proposé | Accepté | Déprécié | Remplacé par ADR-00Y
- Contexte :
- Décision :
- Conséquences :
```
