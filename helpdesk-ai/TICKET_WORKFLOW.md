# Workflow des tickets — documentation

> Dernière mise à jour : **2026-07-29**. Décrit le comportement réel du code
> (`api/routers/tickets.py`, `frontend/.../admin/approval-queue`, `.../admin/ticket-detail`).

## Flux de statuts

```
┌─────────────────────────────────────────────────────────────┐
│                                                               │
│  Nouveau ticket (client)                                     │
│  ↓                                                            │
│  [En attente] ← statut initial                                │
│  ↓ (clic dans la file d'approbation → transition automatique) │
│  [Prise en Charge]                                             │
│  ↓                                                             │
│  ┌──────────────────────────────────────────┐                │
│  │ Traitement (écran de clôture)             │                │
│  ├──────────────────────────────────────────┤                │
│  │ ✅ Résolu    → [Résolu]     (terminal)     │                │
│  │ ❌ Rejeté     → [Rejeté]     (terminal)     │                │
│  │ ⚠️  Problème  → [Problème]                  │                │
│  │    ↓ → Prise en Charge, Résolu ou Rejeté   │                │
│  └──────────────────────────────────────────┘                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## Statuts disponibles

| Statut | Description | Transitions permises |
|---|---|---|
| **En attente** | Ticket créé, pas encore ouvert par un admin | → Prise en Charge, Rejeté |
| **Prise en Charge** | Un admin traite le ticket | → Résolu, Problème, Rejeté, En attente |
| **Problème** | Cas complexe, remis en traitement | → Prise en Charge, Résolu, Rejeté |
| **Résolu** | Clos, solution appliquée | *(terminal — mais reste éditable, voir plus bas)* |
| **Rejeté** | Clos, non valide | *(terminal — mais reste éditable, voir plus bas)* |

`Résolu`/`Rejeté` n'ont aucune transition **sortante**, mais un ticket dans ces statuts
reste **modifiable** (catégorie, priorité, classification, solution appliquée) : la
validation de transition n'exige un changement d'état permis que si le statut envoyé
diffère réellement du statut actuel (`api/routers/tickets.py::approve_ticket`).

## Réception d'un ticket — file d'approbation

`frontend/.../admin/approval-queue` liste les tickets **En attente**. Il n'y a **pas**
de formulaire de décision sur cet écran (message client / note interne / boutons
Valider-Rejeter ont été retirés) : un **simple clic** sur un ticket déclenche
automatiquement :

1. `PATCH /tickets/{id}/approve` avec `{"statut": "Prise en Charge"}`
2. Un message client standard est envoyé automatiquement (`AUTO_MESSAGE_PRISE_EN_CHARGE`)
   si aucun message n'est fourni
3. Le ticket est auto-assigné à l'admin qui vient de cliquer (`assigne_a`), s'il n'était
   pas déjà assigné
4. Redirection directe vers `/admin/tickets/{id}` — tout le traitement se fait sur cet
   écran, pas dans un popup dupliqué

## Traitement du ticket — écran en 2 étapes

`frontend/.../admin/ticket-detail` (`TicketDetail`, signal `step`) :

### Étape 1 — Revue (`step() === 'revue'`)
- **Résultat ML** : catégorie, priorité, classification et confiance affichés ensemble
  (seule la catégorie est une vraie prédiction ML ; priorité/classification sont des
  valeurs de départ — saisie client / défaut « Demande » — que l'admin confirme ou
  corrige, pas des sorties d'un modèle entraîné dédié)
- **Suggestion RAG** :
  - si `rag_score ≥ 0.50` (`NOVELTY_THRESHOLD`) : solution suggérée, avec source
  - sinon : panneau « Nouveau type de problème » — message explicite qu'aucun cas
    similaire n'est connu, invite à décrire la solution appliquée
- Pas de sélecteur de statut ici (il a été déplacé à l'étape 2 — voir plus bas pour la
  raison)
- Bouton **Suivant** → passe à l'étape de clôture

### Étape 2 — Clôture (`step() === 'cloture'`)
- **Nouveau statut** (`<select>`, statut actuel + transitions permises)
- **Catégorie finale**, **Priorité finale**, **Classification finale** — trois `<select>`
  pré-remplis par la prédiction/valeur de départ, modifiables par l'admin
- **Réponse au client** — pré-remplie avec le message automatique si le statut choisi est
  « Prise en Charge » et qu'aucun message n'a encore été saisi
- **Solution appliquée** (`commentaire_admin` en base) — jamais visible par le client,
  alimente ChromaDB. Obligatoire si le ticket est un « cas nouveau » et que le statut visé
  est « Résolu » (`400` sinon, côté serveur et côté client)
- Bouton **Enregistrer** → `PATCH /tickets/{id}/approve`

Les trois champs finaux et le statut sont regroupés **au même endroit**, à l'étape de
clôture — pas demandés en amont de la revue de la classification IA.

## Base de connaissances RAG — ChromaDB

Quand un ticket passe à **Résolu** (première fois ou correction ultérieure) :

1. `resolved_at` est fixé **une seule fois** (une correction plus tard ne réinitialise
   pas le « temps écoulé »)
2. `archive_resolved_ticket()` est planifiée en **tâche de fond** (`BackgroundTasks`,
   `api/db/vector_store.py`) — embedding `[titre + description + solution appliquée]`,
   stocké dans ChromaDB (mode embarqué, `data/chroma/`)
3. Cette collection est **interrogée en direct** à chaque nouvelle recommandation
   (`query_similar()` dans `api/services/ai_service.py`, fusionnée avec les résultats
   statiques FAISS/TF-IDF, tri par score décroissant) — une solution saisie par un admin
   devient donc exploitable par le RAG **dès le ticket suivant**, sans réentraînement ni
   redémarrage du serveur

## Endpoints API

### Tickets — client
```
POST   /tickets/                    # Créer un ticket
GET    /tickets/me                  # Lister mes tickets
GET    /tickets/{id}                # Détail d'un ticket
GET    /tickets/{id}/history        # Historique du ticket
```

### Tickets — admin
```
GET    /tickets/admin/all           # Lister tous les tickets
PATCH  /tickets/{id}/approve        # Changer statut / catégorie / priorité /
                                     # classification / commentaires
POST   /tickets/{id}/refresh-rag    # Recalculer la suggestion RAG
GET    /tickets/resolved/stats      # KPIs (ChromaDB) — total, par catégorie, par filiale
GET    /tickets/resolved/archive    # Tickets résolus archivés (ChromaDB)
```

## Modèle de données (`api/db/models.py::Ticket`)

```python
class Ticket:
    id: int
    titre: str
    description: str
    statut: str                     # En attente, Prise en Charge, Résolu, Rejeté, Problème
    categorie_predite: str          # Prédiction ML brute
    categorie_finale: str           # Corrigée par l'admin si besoin
    priorite_saisie: str            # Déclarée par le client à la création
    priorite_finale: str            # Confirmée/corrigée par l'admin
    classification_finale: str      # Demande / Incident / Problème / Changement
    confiance: float
    rag_score: float | None         # Score de la meilleure suggestion RAG (seuil 0.50)
    solution_rag: str               # Suggestion RAG (statique ou live ChromaDB)
    knowledge_rag: str
    commentaire_client: str         # Message visible par le client
    commentaire_admin: str          # "Solution appliquée" — jamais visible client, alimente ChromaDB
    assigne_a: str | None           # Admin en charge (auto-assigné à la prise en charge)
    created_at: datetime
    resolved_at: datetime | None    # Fixé une seule fois, à la première résolution
```

### TicketHistory
```python
class TicketHistory:
    id: int
    ticket_id: int
    champ_modifie: str
    ancienne_valeur: str | None
    nouvelle_valeur: str | None
    changed_by: int | None          # Admin ID (None = système)
    timestamp: datetime
```

## Bonnes pratiques

✅ **À faire :**
- Décrire la solution appliquée avec précision (diagnostic + action) — ce texte devient
  la base de connaissances RAG pour les prochains tickets similaires
- Vérifier l'historique avant de modifier un ticket déjà traité par un autre admin
- Utiliser « Problème » pour les cas nécessitant plus d'analyse plutôt que de forcer un
  « Résolu » prématuré

❌ **À éviter :**
- Marquer « Résolu » sans solution détaillée sur un cas nouveau (bloqué côté serveur de
  toute façon)
- Laisser le message client vide à la prise en charge (le message automatique s'en charge,
  mais un message personnalisé reste préférable pour les cas complexes)

## Exemple — cycle complet

```
1. [Client] Crée un ticket "Sage refuse de s'ouvrir, licence invalide"
   → Statut : En attente
   → Catégorie ML : Applicatifs (79% confiance)
   → rag_score : 0.48 → « Nouveau type de problème » (aucun cas similaire)

2. [Admin] Clique sur le ticket dans la file d'approbation
   → Statut passe automatiquement à Prise en Charge
   → Message client auto envoyé, admin auto-assigné
   → Redirection directe vers /admin/tickets/{id}

3. [Admin] Étape Revue : constate qu'aucune suggestion n'existe, clique Suivant

4. [Admin] Étape Clôture :
   → Statut = Résolu
   → Catégorie/Priorité/Classification finales confirmées
   → Solution appliquée (obligatoire, cas nouveau) : diagnostic + action détaillés
   → Enregistrer

5. [Backend] resolved_at fixé, embedding calculé en tâche de fond, archivé dans ChromaDB

6. [Client suivant] Ticket similaire créé
   → rag_score : 0.80 (le cas n'est plus "nouveau")
   → Suggestion RAG = la solution réellement appliquée à l'étape 4, pas une suggestion
     générique
```
