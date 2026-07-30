# Workflow des tickets — documentation

> Dernière mise à jour : **2026-07-30**. Décrit le comportement réel du code
> (`api/routers/tickets.py`, `frontend/.../admin/approval-queue`, `.../admin/ticket-detail`,
> `.../admin/ticket-list`, `.../client/ticket-detail`).

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

## Traitement du ticket — écran en 3 sous-étapes (revue → champs → solution)

`frontend/.../admin/ticket-detail` (`TicketDetail`, signal `step` + `showSolutionModal`) :

### Étape 1 — Revue (`step() === 'revue'`)
- **Résultat ML** : catégorie, priorité, classification et confiance affichés ensemble
  (seule la catégorie est une vraie prédiction ML ; priorité/classification sont des
  valeurs de départ — saisie client / défaut « Demande » — que l'admin confirme ou
  corrige, pas des sorties d'un modèle entraîné dédié)
- **Suggestion RAG** :
  - si `rag_score ≥ 0.50` (`NOVELTY_THRESHOLD`) : solution suggérée, avec source
  - sinon : panneau « Nouveau type de problème » — message explicite qu'aucun cas
    similaire n'est connu, invite à décrire la solution appliquée
- Pas de sélecteur de statut ici (il a été déplacé à la fin du parcours — voir plus bas)
- Bouton **Suivant** → passe à l'étape de clôture

### Étape 2 — Champs de clôture (`step() === 'cloture'`)
- **Catégorie finale**, **Priorité finale**, **Classification finale** — trois `<select>`
  pré-remplis par la prédiction/valeur de départ, modifiables par l'admin
- **Réponse au client** — message libre visible par le client
- Bouton **Suivant** → ouvre le popup dédié « Solution appliquée » (pas de sélecteur de
  statut ni de champ solution sur cet écran)

### Étape 3 — Popup « Solution appliquée » (`showSolutionModal()`, retour utilisateur)
Champ isolé dans un grand popup dédié (`max-w-2xl`, textarea de 12 lignes) plutôt que
noyé dans la colonne étroite avec les autres champs — l'admin doit pouvoir rédiger le
diagnostic à l'aise, ce texte alimentant directement ChromaDB.
- **Solution appliquée** (`commentaire_interne` / `commentaire_admin` en base) — jamais
  visible par le client. Obligatoire si le ticket est un « cas nouveau » et que le statut
  final choisi est « Résolu » (`400` côté serveur, même règle côté client)
- Bouton **Enregistrer** — **toujours pas de sélecteur de statut dans le formulaire.** Le
  clic ouvre une modale « Quel est le nouveau statut de ce ticket ? » listant les
  transitions valides depuis le statut actuel (`availableStatuts()`) ; l'admin choisit le
  statut réel là, une fois tous les autres champs déjà fixés. Un choix « Résolu » sur un
  cas nouveau sans solution appliquée **referme la modale de statut et rouvre ce popup**
  avec le message d'erreur affiché directement au-dessus du champ concerné (plutôt que
  dans la petite modale de statut, loin du champ à corriger). Le message client
  automatique adapté (`AUTO_MESSAGE_PRISE_EN_CHARGE`/`AUTO_MESSAGE_RESOLU`) est appliqué
  côté serveur si le champ « Réponse au client » est resté vide ou inchangé. Après
  enregistrement, redirection vers la liste de tous les tickets.
  - **Ticket déjà terminal** (Résolu/Rejeté, aucune transition possible) : le clic sur
    Enregistrer (dans ce popup) sauvegarde directement les autres champs, sans modale de
    statut (rien à choisir).
- Bouton **Retour** → referme le popup sans enregistrer, retour aux champs de l'étape 2.

Le parcours complet est donc **Suivant → Suivant → Enregistrer** : catégorie/priorité/
classification/réponse client d'abord, puis la solution appliquée seule dans son grand
popup, la décision du statut restant la toute dernière action.

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

## Assistant de triage IA — synthèse RAG (Ollama, 100% on-premise)

`GET /tickets/{id}/rag-synthesis` (admin) reformule les tickets similaires réellement
archivés (ChromaDB, avec leur vrai ID) en français professionnel via un LLM local
(`api/services/llm_service.py`, service Docker `ollama`, modèle `llama3.2:3b`) : le RAG ne
recrache plus la résolution brute d'un seul cas (parfois mal écrite). La réponse liste
chaque ticket similaire à puces (`Ticket #<id> (Score : <score>% - <catégorie>) : <résumé>`)
et termine en demandant l'ID du cas le plus pertinent. Un exemple concret (few-shot) est
injecté dans l'historique de conversation envoyé au LLM pour ancrer le format exact — un
modèle de cette taille (3B) suit un exemple complet beaucoup plus fidèlement que des règles
abstraites seules. Si Ollama est indisponible ou trop lent (`OLLAMA_TIMEOUT`, 90s par
défaut — l'inférence CPU peut prendre 20 à 60s selon la longueur du prompt), repli
automatique sur un récapitulatif brut non reformulé (`source: "fallback"` dans la réponse,
vs `"ollama"` en fonctionnement normal, `"none"` si aucun cas similaire n'existe).

**Affichage par défaut (2026-07-30, retour utilisateur)** : le panneau « Solution suggérée »
de l'étape Revue déclenche cette synthèse **automatiquement** dès l'ouverture d'un ticket
ayant un cas connu (`!isNovelCase()`), avec un état de chargement visible — ce n'est plus
une action optionnelle séparée en dessous d'une résolution brute. L'admin voit directement
la reformulation professionnelle, jamais le texte brut d'un cas archivé, sauf repli
explicite (`source: "fallback"`, avertissement affiché) ou si la meilleure correspondance
provient uniquement du corpus statique d'entraînement (pas d'ID de ticket réel à
synthétiser/explorer — dans ce cas, la suggestion brute `solution_rag` reste affichée,
c'est la seule situation où du texte non reformulé apparaît encore par défaut). Le bouton
« Rafraîchir » recalcule le score RAG **et** relance la synthèse. Le champ pour explorer la
procédure complète d'un ticket cité (en tapant son ID) n'apparaît que si une synthèse réelle
(`ollama`/`fallback`) est disponible.

## Endpoints API

### Tickets — client
```
POST   /tickets/                    # Créer un ticket
GET    /tickets/me                  # Lister mes tickets
GET    /tickets/{id}                # Détail d'un ticket
GET    /tickets/{id}/history        # Historique du ticket
GET    /tickets/{id}/similar-titles # Titres de cas similaires (sans solution ni score)
```

### Tickets — admin
```
GET    /tickets/admin/all           # Lister tous les tickets
POST   /tickets/admin-create        # Créer un ticket (client existant ou saisie libre)
PATCH  /tickets/{id}/approve        # Changer statut / catégorie / priorité /
                                     # classification / commentaires
DELETE /tickets/{id}                # Suppression définitive (+ historique lié)
POST   /tickets/{id}/refresh-rag    # Recalculer la suggestion RAG
GET    /tickets/{id}/rag-synthesis  # Synthèse IA des tickets similaires (LLM local)
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
   → Catégorie/Priorité/Classification finales confirmées
   → Solution appliquée (obligatoire, cas nouveau) : diagnostic + action détaillés
   → Enregistrer → modale « Quel est le nouveau statut ? » → choix « Résolu »

5. [Backend] resolved_at fixé, embedding calculé en tâche de fond, archivé dans ChromaDB

6. [Client suivant] Ticket similaire créé
   → rag_score : 0.80 (le cas n'est plus "nouveau")
   → Suggestion RAG = la solution réellement appliquée à l'étape 4, pas une suggestion
     générique
```
