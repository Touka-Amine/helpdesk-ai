# ARCHITECTURE.md — Architecture détaillée

> Vue de référence (évolutive). Résumé dans [PLAN.md](PLAN.md) (section 3). Décisions dans
> [DECISIONS.md](DECISIONS.md). Dernière mise à jour : *à la création*.

## 1. Vue d'ensemble (C4 — niveau Conteneurs)

```mermaid
flowchart TB
  user([Client / Agent / Admin])
  user -->|HTTPS| front[Frontend Angular 21]
  front -->|REST /api/v1| api[API FastAPI]
  api --> ml[Service NLP\nCamemBERT + baseline]
  api --> rag[Service RAG sémantique]
  api --> db[(BDD\nSQLite -> PostgreSQL)]
  rag --> vdb[(Base vectorielle\nQdrant/Chroma/pgvector)]
  rag --> llm[LLM de génération\n+ guardrails]
  ml -.-> mlflow[(MLflow Registry)]
  subgraph MLOps
    dvc[DVC pipeline] --> mlflow
  end
```

## 2. Modules

| Module | Responsabilité | État | Emplacement cible |
|---|---|---|---|
| Frontend | UI client/admin, restitution confiance + sources, feedback | 🟡 | `frontend/` |
| API | Contrat REST, auth, orchestration | ✅🟡 | `api/` |
| Service NLP | Classification, résumé, NER, priorité, sentiment | ✅🔴 | `api/services/ai_service.py`, `src/models/` |
| Service RAG | Retrieval sémantique + génération | 🔴 | `src/rag/` (à refondre) |
| Base vectorielle | Index des embeddings | 🔴 | infra |
| BDD | Tickets, users, historique, feedback | ✅ | `api/db/` |
| MLOps | Reproductibilité, registre | 🔴 | `dvc.yaml`, `mlruns/` |
| Sécurité | JWT, RBAC, secrets | 🟡 | `api/services/auth_service.py`, middleware |

## 3. Flux de données (création d'un ticket)

```mermaid
sequenceDiagram
  participant C as Client (front)
  participant A as API FastAPI
  participant N as Service NLP
  participant R as Service RAG
  participant D as BDD
  C->>A: POST /tickets (titre, description)
  A->>N: prétraitement + classification (+ confiance)
  N-->>A: catégorie, confiance, entités, priorité
  A->>R: retrieval sémantique (query, filtre catégorie)
  R-->>A: top-k résolutions + citations
  A->>D: enregistrer ticket (statut=En attente)
  A-->>C: catégorie + suggestions + confiance
```

## 4. Modèle de données (domaine)

```mermaid
classDiagram
  class User { id; email; nom; prenom; role; filiale }
  class Ticket { id; titre; description; categorie_predite; categorie_finale; confiance; statut; solution_rag; created_at }
  class TicketHistory { id; champ_modifie; ancienne_valeur; nouvelle_valeur; timestamp }
  class Feedback { id; ticket_id; utile; correction_categorie; created_at }
  class KBDocument { id; texte; categorie; resolution; source }
  User "1" --> "*" Ticket
  Ticket "1" --> "*" TicketHistory
  Ticket "1" --> "*" Feedback
```

> `Feedback` et `KBDocument` sont **cibles** (à introduire en Phases 9 et 6).

## 5. Stack technique

| Couche | Technologies |
|---|---|
| Frontend | Angular 21, Angular Material, Chart.js, RxJS |
| API | FastAPI, Pydantic v2, Uvicorn |
| NLP/ML | scikit-learn, imbalanced-learn, NLTK, HuggingFace Transformers, PEFT/LoRA |
| RAG | sentence-transformers (FR), base vectorielle (ADR-004), RAGAS |
| Données | pandas, DVC |
| MLOps | DVC, MLflow |
| Persistance | SQLAlchemy, SQLite → PostgreSQL |
| Sécurité | python-jose (JWT), passlib/bcrypt |
| Déploiement | Docker, docker-compose, GitHub Actions |

## 6. Principes d'architecture
- **Monolithe modulaire** (pas de microservices pour le PFE — voir ADR-005).
- Séparation en couches : `routers` (HTTP) → `services` (métier) → `repositories` (données).
- Sans état côté API (scalabilité horizontale possible).
- Dégradation gracieuse : si le LLM est indisponible, repli sur retrieval sans génération.
