# 🎫 Workflow des Tickets - Documentation

## Flux de Statuts

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Nouveau Ticket (Client)                                   │
│  ↓                                                          │
│  [En attente] ← Initial status                             │
│  ↓                                                          │
│  Admin ouvre le ticket                                     │
│  ↓                                                          │
│  [Prise en Charge] ← Admin assigned                        │
│  ↓                                                          │
│  ┌────────────────────────────────────┐                    │
│  │ Traitement du problème par l'IT    │                    │
│  ├────────────────────────────────────┤                    │
│  │ ✅ Résolu        → [Résolu]        │                    │
│  │ ❌ Rejeté         → [Rejeté]        │                    │
│  │ ⚠️  Compliqué     → [Problème]      │                    │
│  │    ↓              → retour à       │                    │
│  │                     [Prise en      │                    │
│  │                      Charge]       │                    │
│  └────────────────────────────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Statuts Disponibles

| Statut | Icône | Description | Transitions Permises |
|--------|-------|-------------|----------------------|
| **En attente** | ⏳ | Ticket créé, en attente d'assignment | → Prise en Charge, Rejeté |
| **Prise en Charge** | 🔧 | Admin traite le ticket | → Résolu, Problème, En attente |
| **Problème** | ⚠️ | Problème complexe / long | → Prise en Charge, Résolu |
| **Résolu** | ✅ | Ticket résolu | (terminal) |
| **Rejeté** | ❌ | Ticket rejeté | (terminal) |

## Amélioration du Workflow

### 1️⃣ Initiation du Ticket
- Client soumet un ticket (titre, description, équipement, filiale)
- Statut: **En attente**
- Système: Prédiction ML + Heuristiques + RAG en arrière-plan

### 2️⃣ Approbation par l'Admin
- Admin voit le ticket dans la file d'attente
- Admin change le statut à **Prise en Charge**
- Admin peut:
  - Corriger la catégorie ML
  - Ajouter des commentaires (réponse IT)
  - Actualiser la solution RAG

### 3️⃣ Résolution ou Escalade
- **Résolu**: Ticket fermé avec solution
  - `resolved_at` est enregistré
  - Client voit la solution via l'interface
- **Problème**: Ticket escaladé pour analyse approfondie
  - Retour à "Prise en Charge" pour rétenter
- **Rejeté**: Ticket invalide / dupliqué

### 4️⃣ Suivi Client
- Client voir la **timeline** de progression
- Client voir l'**historique** de tous les changements
- Client voir la **solution proposée** dès qu'elle est disponible

## API Endpoints

### Tickets Client

```
POST   /tickets/                    # Créer un ticket
GET    /tickets/me                   # Lister mes tickets
GET    /tickets/{id}                 # Détail d'un ticket
GET    /tickets/{id}/history         # Historique du ticket
```

### Tickets Admin

```
GET    /tickets/admin/all            # Lister tous les tickets
PATCH  /tickets/{id}/approve         # Approuver/modifier un ticket
POST   /tickets/{id}/refresh-rag     # Actualiser la solution RAG
```

## Structures de Données

### Ticket Model
```python
class Ticket:
    id: int
    titre: str
    description: str
    statut: str                    # En attente, Prise en Charge, Résolu, Rejeté, Problème
    categorie_predite: str         # Catégorie ML brute
    categorie_finale: str          # Catégorie finale (après admin correction)
    confiance: float               # Confiance de la prédiction
    solution_rag: str              # Solution proposée via RAG
    commentaire_client: str        # Réponse IT pour le client
    commentaire_admin: str         # Notes internes de l'IT
    created_at: datetime
    resolved_at: datetime          # Set quand statut = "Résolu"
```

### TicketHistory Model
```python
class TicketHistory:
    id: int
    ticket_id: int
    champ_modifie: str             # Quel champ a changé
    ancienne_valeur: str           # Ancienne valeur
    nouvelle_valeur: str           # Nouvelle valeur
    changed_by: int                # Admin ID
    timestamp: datetime
```

## Interface Client - Détail Ticket

### Sections Affichées:
1. **📋 Progression** - Timeline visuelle des statuts
2. **📝 Votre demande** - Description du ticket
3. **💡 Solution proposée** - Réponse de l'IT (ou "en attente")
4. **📊 Historique** - Tous les changements avec timestamps
5. **ℹ️ Informations** - Classification AI, confiance, dates

### Actions Disponibles:
- Retour à la liste de mes tickets
- Consultation de l'historique complet
- Suivi en temps réel du statut

## Interface Admin - Approval Queue (existant)

### Sections Affichées:
1. **Model Proposal** - Classification AI + confiance
2. **RAG Solution** - Solution proposée par RAG
3. **IT Decision** - Form pour approuver/modifier
   - Changer le statut
   - Corriger la catégorie
   - Ajouter la réponse IT (commentaire_client)
   - Ajouter les notes internes (commentaire_admin)
4. **Refresh RAG** - Bouton pour re-calculer la solution

## Bonnes Pratiques

✅ **DO:**
- Toujours changer le statut en "Prise en Charge" quand vous commencez à traiter
- Ajouter un commentaire client avant de marquer comme "Résolu"
- Utiliser "Problème" pour les tickets complexes nécessitant plus d'analyse
- Vérifier l'historique pour comprendre les changements précédents

❌ **DON'T:**
- Passer directement de "En attente" à "Résolu" sans review
- Modifier plusieurs statuts rapidement
- Oublier d'ajouter un commentaire de résolution

## Exemple: Workflow Complet

```
1. [Client] Crée ticket "VPN ne fonctionne pas"
   → Statut: En attente
   → Catégorie ML: Microsoft (MAUVAISE)
   → Solution RAG: "Réinstaller Office"

2. [Admin] Ouvre l'approval queue
   → Voit: VPN → Microsoft avec 25% confiance
   → Correction: Catégorie finale = Réseau
   → Refresh RAG: Nouvelle solution = "Vérifier les identifiants VPN"

3. [Admin] Approuve avec changements
   → Statut: Prise en Charge
   → Commentaire client: "Pouvez-vous vérifier vos identifiants VPN?"
   → Commentaire admin: "VPN corrected from Microsoft to Réseau"
   → TicketHistory enregistre tous les changements

4. [Client] Voit le ticket
   → Timeline: En attente → Prise en Charge ✅
   → Historique: Catégorie changée, solution actualisée
   → Solution: "Vérifier les identifiants VPN"

5. [Client] Résout le problème et signale
   → Statut: Résolu
   → resolved_at: now

6. [Admin] Marque comme résolu dans l'interface
   → Confirmation visible pour le client
```

## Monitoring & Logs

Chaque changement est enregistré dans `TicketHistory`:
- Qui l'a fait (admin ID)
- Quand (timestamp)
- Quel champ a changé
- Ancienne vs nouvelle valeur

Utilisez `/tickets/{id}/history` pour auditer les modifications.
