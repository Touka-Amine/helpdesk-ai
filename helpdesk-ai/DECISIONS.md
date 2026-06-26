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

## ADR-004 — Choix de la base vectorielle *(à trancher en Phase 6)*
- **Statut** : Proposé.
- **Contexte** : besoin d'un stockage/recherche d'embeddings.
- **Options** : **Qdrant** (riche, serveur), **Chroma** (simple, embarqué), **pgvector** (réutilise
  PostgreSQL).
- **Décision** : *à figer* — recommandation initiale : Chroma pour démarrer (simplicité), migration
  pgvector si PostgreSQL adopté.
- **Conséquences** : impacte le déploiement (service supplémentaire ou non).

## ADR-005 — Monolithe modulaire vs microservices
- **Statut** : Accepté.
- **Contexte** : équipe = 1 stagiaire, PFE.
- **Décision** : **monolithe modulaire** bien découpé (routers/services/repositories). Microservices
  en perspective.
- **Conséquences** : simplicité de déploiement (docker-compose) ; bonne séparation logique.

---
*Template pour un nouvel ADR :*
```
## ADR-00X — Titre
- Statut : Proposé | Accepté | Déprécié | Remplacé par ADR-00Y
- Contexte :
- Décision :
- Conséquences :
```
