# CADRAGE_SRS.md — Cadrage scientifique & Spécification des besoins

> Document **exécutable** des exigences (Phase 1 du [PLAN.md](PLAN.md)). Version formelle et
> traçable de la narration du [CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md) (Ch. 1–3).
> Dernière mise à jour : **2026-07-05** · Statut : **v0.1** (sections 1–4 à valider) ·
> section 5 (matrice exigences→résultats) mesurée en Phase 12.
>
> 🟠 **À valider par l'étudiant** : les éléments marqués 🟠 dépendent de décisions/contexte
> (entreprise d'accueil, volumétrie réelle, date de soutenance) à confirmer.

---

## 1. Cadrage scientifique

### 1.1 Contexte
Les équipes support IT traitent manuellement un volume important de tickets, avec un temps de
traitement de **30–45 min/ticket** 🟠 (à confirmer avec les chiffres réels de l'entreprise
d'accueil). Le tri par catégorie, la recherche de solutions passées et la rédaction de la réponse
sont chronophages et hétérogènes.

### 1.2 Problématique
> *Comment classer automatiquement et de manière fiable des tickets IT **francophones**, **courts**,
> **déséquilibrés** et **bruités**, et proposer une **assistance à la résolution pertinente et
> vérifiable**, tout en conservant un contrôle humain (human-in-the-loop) ?*

### 1.3 Questions de recherche (QR)
| ID | Question |
|---|---|
| QR1 | Un transformer francophone (CamemBERT) fine-tuné améliore-t-il **significativement** la classification vs la baseline TF-IDF + LogReg, en particulier sur les **classes minoritaires** (ex. *Sécurité*) ? |
| QR2 | Un **RAG sémantique** (embeddings denses + base vectorielle) améliore-t-il la pertinence des suggestions vs le RAG **lexical** actuel (TF-IDF/cosinus), mesuré par les métriques RAGAS ? |
| QR3 | Comment **calibrer la confiance** du modèle pour définir un seuil de **routage automatique fiable** avec mise en revue humaine des cas incertains ? |
| QR4 | *(optionnel)* La **génération de réponse par LLM avec citations** réduit-elle le temps de résolution sans introduire d'hallucinations ? |

### 1.4 Hypothèses (H)
| ID | Hypothèse | Validée si |
|---|---|---|
| H1 | CamemBERT fine-tuné (LoRA) surpasse la baseline | F1-macro ≥ 0.85 **et** rappel *Sécurité* ≥ 0.70 sur test dé-dupliqué |
| H2 | Le RAG sémantique surpasse le RAG lexical | Context Recall et MRR significativement supérieurs |
| H3 | La calibration permet un routage fiable | Sous-ensemble auto-routé à haute précision (≥ 0.95) couvrant ≥ 60 % des tickets |
| H4 | La génération avec citations est fiable | Faithfulness ≥ 0.85, taux d'hallucination faible |

### 1.5 Objectifs SMART
| ID | Objectif | S | M | A | R | T |
|---|---|---|---|---|---|---|
| OBJ1 | Classifieur transformer FR | CamemBERT+LoRA | F1-macro ≥ 0.85 | GPU local | données dispo | Mois 3 |
| OBJ2 | Rappel classe *Sécurité* | rappel dédié | ≥ 0.70 | augmentation/fine-tuning | classe critique | Mois 3 |
| OBJ3 | RAG sémantique évalué | embeddings+vector DB | Context Recall ≥ 0.80, Faithfulness ≥ 0.85 | librairies open-source | KB existante | Mois 4 |
| OBJ4 | Application fonctionnelle bout-en-bout | front↔back | démo création→validation→résolution | scaffold existant | — | Mois 5 |
| OBJ5 | Industrialisation | DVC+MLflow+Docker | pipeline reproductible, `docker-compose up` | périmètre Must | — | Mois 5 |
| OBJ6 | Conformité RGPD | anonymisation+registre | PII anonymisées | obligation légale | — | Mois 2 |
| OBJ7 | Mémoire + soutenance | livrables jury | mémoire complet, démo | — | — | Mois 6 |

### 1.6 Synthèse de l'état de l'art
Détail dans [CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md) (Ch. 2). Points clés :
- **NLP francophone** : CamemBERT / CamemBERTa / FlauBERT (vs baselines TF-IDF). Justifie le choix
  d'un modèle FR plutôt qu'anglophone.
- **Classification déséquilibrée** : pondération, SMOTE, augmentation, focal loss.
- **RAG** : dense retrieval, hybrid search (BM25+dense), re-ranking — vs recherche lexicale.
- **Évaluation RAG** : RAGAS (Faithfulness, Answer Relevancy, Context Precision/Recall) +
  métriques de retrieval (Precision@k, Recall@k, MRR, nDCG) + LLM-as-a-Judge.
- **Positionnement** : le projet combine classification FR fine-tunée + RAG sémantique évalué +
  human-in-the-loop, ce qui le distingue d'un simple classifieur ou moteur de recherche.

---

## 2. Acteurs et personas

| Acteur | Rôle | Besoins principaux |
|---|---|---|
| **Client / Demandeur** | Soumet et suit ses tickets | Créer un ticket simplement, suivre l'état, recevoir la solution |
| **Agent / Technicien IT** | Traite les tickets | Voir catégorie + confiance + suggestions RAG (sources), valider/corriger, répondre |
| **Admin / Responsable** | Supervise | Vue d'ensemble, gestion utilisateurs, statistiques, qualité du modèle |

---

## 3. Exigences fonctionnelles (EF)

> Priorité **MoSCoW** : M = Must, S = Should, C = Could, W = Won't (cette itération).
> Chaque EF a un **critère d'acceptation** vérifiable.

| ID | Exigence | MoSCoW | Critère d'acceptation |
|---|---|---|---|
| EF-01 | Authentification + rôles (client/agent/admin) | M | Login JWT, accès restreint par rôle |
| EF-02 | Création d'un ticket (titre, description, priorité) | M | Ticket persisté, statut initial « En attente » |
| EF-03 | Classification automatique en catégorie | M | Catégorie + score de confiance retournés |
| EF-04 | Suggestion de résolution (RAG) | M | Top-k résolutions avec **sources/citations** |
| EF-05 | Routage par seuil de confiance (HITL) | M | Cas < seuil → file de revue humaine |
| EF-06 | Validation/correction par l'agent | M | Catégorie finale + réponse + transition de statut |
| EF-07 | Journal d'audit (historique) | M | Chaque modification tracée (qui/quoi/quand) |
| EF-08 | Suivi du ticket côté client | M | Statut + solution visibles |
| EF-09 | Résumé automatique du ticket | S | Résumé généré et affiché à l'agent |
| EF-10 | Extraction d'entités (équipement, logiciel, IP, code erreur) | S | Entités extraites et affichées |
| EF-11 | Analyse de priorité / urgence | S | Priorité suggérée |
| EF-12 | Analyse de sentiment | C | Indicateur de ton/urgence |
| EF-13 | Capture de feedback utilisateur (👍/👎 + correction) | S | Feedback persisté pour amélioration |
| EF-14 | Génération de réponse par LLM avec citations | S | Réponse rédigée + sources, avec garde-fous |
| EF-15 | Tableau de bord statistiques (admin) | C | KPIs (volumes, catégories, temps) |
| EF-16 | Intégration Power Automate (`/ingest`) | C | Endpoint fonctionnel et sécurisé |
| EF-17 | Notifications sur changement de statut | W | (backlog) |

---

## 4. Exigences non-fonctionnelles (ENF)

| ID | Catégorie | Exigence / Métrique | Cible | Vérification |
|---|---|---|---|---|
| ENF-01 | Performance | Latence prédiction P95 | ≤ 300 ms | Test de charge (Locust/k6) |
| ENF-02 | Performance | Latence RAG (avec génération) P95 | ≤ 3 s | Test de charge |
| ENF-03 | Qualité IA | F1-macro classification | ≥ 0.85 | Évaluation sur test dé-dupliqué |
| ENF-04 | Qualité IA | Rappel *Sécurité* | ≥ 0.70 | Rapport par classe |
| ENF-05 | Qualité RAG | Context Recall / Faithfulness | ≥ 0.80 / ≥ 0.85 | RAGAS |
| ENF-06 | Fiabilité | Dégradation gracieuse si LLM indisponible | repli sans génération | Test d'injection de panne |
| ENF-07 | Sécurité | JWT + RBAC + secrets non exposés | aucun secret en clair | Revue + scan |
| ENF-08 | Sécurité | Protection injection de prompt | entrées/sorties filtrées | Tests dédiés |
| ENF-09 | RGPD | Anonymisation des PII + registre | PII traitées | Audit RGPD |
| ENF-10 | Maintenabilité | Code testé et structuré en couches | couverture cible ≥ 70 % | `pytest --cov` |
| ENF-11 | Reproductibilité | Pipeline data/modèle reproductible | `dvc repro` OK | Exécution CI |
| ENF-12 | Portabilité | Déploiement conteneurisé | `docker-compose up` | Démo |
| ENF-13 | Observabilité | Logs structurés + métriques IA | dashboards | Inspection |
| ENF-14 | Accessibilité | UI conforme bonnes pratiques | RGAA/WCAG de base | Audit léger |

---

## 5. Matrice exigences → résultats (Phase 12, mesurée le 2026-07-05)

> Remplace l'ancien extrait. Bilan (2026-07-06) : **10/17 EF atteints, 3 partiels, 3 non faits, 1 backlog**
> (EF-13 corrigé — feedback client réellement persisté) ·
> **5/14 ENF atteints, 5 partiels, 4 non atteints**. Sources : `metrics/*.json`, `tests/`,
> exécution `pytest --cov` du 2026-07-05. Risque PLAN.md Phase 12 explicitement anticipé
> (« sur-interprétation liée à la redondance du corpus ») : voir ⚠️ ci-dessous, confirmé.

### Exigences fonctionnelles

| ID | Exigence | Critère d'acceptation | Résultat mesuré | Statut |
|---|---|---|---|---|
| EF-01 | Authentification + rôles | Login JWT, accès restreint par rôle | Implémenté ; RBAC vérifié (`test_get_all_tickets_requires_admin` → 403 si non-admin) ; 18/18 tests d'intégration passent | ✅ Atteint |
| EF-02 | Création de ticket | Ticket persisté, statut initial « En attente » | Testé (`test_create_ticket_avec_auth`/`sans_auth`) | ✅ Atteint |
| EF-03 | Classification automatique | Catégorie + confiance retournées | Testé (`test_predict_vpn`/`microsoft`) ; qualité du résultat → voir ENF-03/04 | ✅ Atteint (fonctionnel) |
| EF-04 | Suggestion résolution (RAG) | Top-k avec sources/citations | RAG hybride actif (sémantique+lexical), citations numérotées, score moyen sémantique 0.69 (`metrics/rag_eval.json`) | ✅ Atteint |
| EF-05 | Routage par seuil (HITL) | Cas < seuil → revue humaine | ⚠️ **Vérifié par test manuel (étude utilisateur, §6)** : `create_ticket()` (`api/routers/tickets.py:46`) fixe `statut="En attente"` **sans condition**, pour tout ticket quel que soit son score de confiance (testé avec 0.78 et 0.91 : même statut que si confiance faible). Le seuil (0.60) et les indicateurs `auto_routed`/`low_confidence` sont bien calculés (`predictor.py`) mais **ne pilotent aucune branche de workflow** — ils ne servent qu'à décider si le RAG élargit sa recherche (`allow_fallback`). Il n'existe donc **aucun routage différencié réel** : tous les tickets suivent la même file de revue humaine, contrairement à ce que EF-05 énonce littéralement. H3 (couverture ≥60 % à ≥95 % de précision) reste une estimation jamais mesurée | 🟡 Partiel — la confiance est calculée et affichée, mais n'entraîne aucune automatisation de workflow |
| EF-06 | Validation/correction agent | Catégorie finale + réponse + transition | `categorie_finale`, `commentaire_admin`, historisation, UI admin (Phase 9) | ✅ Atteint |
| EF-07 | Journal d'audit | Chaque modification tracée | `TicketHistory` (champ, ancienne/nouvelle valeur, qui, quand) | ✅ Atteint |
| EF-08 | Suivi côté client | Statut + solution visibles | Page détail client (Phase 9) | ✅ Atteint |
| EF-09 | Résumé automatique | Résumé généré et affiché | Non implémenté | 🔴 Non fait |
| EF-10 | Extraction d'entités | Entités affichées | Non implémenté (`equipement` = saisie utilisateur libre, aucune extraction NLP) | 🔴 Non fait |
| EF-11 | Analyse priorité/urgence | Priorité suggérée | Non implémenté (`priorite_saisie` = saisie utilisateur uniquement) | 🔴 Non fait |
| EF-12 | Analyse de sentiment | Indicateur de ton/urgence | Non implémenté | 🔴 Non fait |
| EF-13 | Feedback utilisateur | Feedback persisté (👍/👎 + correction) | ✅ **Corrigé (2026-07-06)** : `POST /tickets/{id}/feedback` implémenté (`api/routers/tickets.py`), persiste `feedback_vote`/`feedback_comment` sur le ticket (colonnes ajoutées via migration additive `_migrate_columns`). `ticket-detail.ts` (client) appelle réellement l'endpoint et n'affiche "Merci, votre retour a bien été enregistré" qu'après réponse serveur ; l'état persiste après rechargement complet (vérifié : vote 👍 + commentaire soumis via l'UI, relus à l'identique via un appel API indépendant après reload) | ✅ Atteint |
| EF-14 | Génération LLM + citations | Réponse rédigée + sources, garde-fous | Citations implémentées, mais génération **template-based** (pas d'appel LLM réel) — `metrics/rag_eval.json` : Faithfulness=1.0/hallucination=0% *par construction* (rien n'est généré librement). ⚠️ À ne pas présenter comme « génération LLM » sans cette nuance | 🟡 Partiel — décision de périmètre à assumer explicitement |
| EF-15 | Dashboard admin | KPIs (volumes, catégories, temps) | Service `dashboard/` dédié, conteneurisé (`docker-dashboard-1`), déployé | ✅ Atteint |
| EF-16 | Intégration Power Automate (`/ingest`) | Endpoint fonctionnel et sécurisé | Réparé Phase 8, sécurisé par API key, 4 tests passent (`test_ingest_*`) | ✅ Atteint |
| EF-17 | Notifications changement statut | — | Won't cette itération, assumé | ⚪ Backlog |

### Exigences non-fonctionnelles

| ID | Exigence | Cible | Résultat mesuré | Statut |
|---|---|---|---|---|
| ENF-01 | Latence prédiction P95 | ≤ 300 ms | 330 ms (c=1) → 1068 ms (c=5) → 15022 ms (c=20, 19% timeouts) — `metrics/load_test.json`. Cause identifiée (endpoint sync/CPU-bound, GIL, 2 workers) | 🔴 Non atteint — optimisation Phase 13 |
| ENF-02 | Latence RAG+génération P95 | ≤ 3 s | Non isolée : génération template-based incluse dans `/predict`, pas de LLM externe séparé à mesurer distinctement | 🟡 Non mesuré isolément |
| ENF-03 | F1-macro classification | ≥ 0.85 | **0.685** (heuristiques+ML) / 0.271 (ML seul) — `metrics/ml_eval.json`. ⚠️ **Mesure non représentative** : `data/splits/test.csv` (GroupShuffleSplit par Titre, non stratifié) ne couvre que **5 catégories sur 8** — *Applicatifs*, *Backup* et *Communication* en sont absentes (0/356). Le F1-macro rapporté porte donc sur les classes présentes, pas sur les 8 du domaine, et **n'est pas comparable** au 0.5673 mesuré sur protocole stratifié (notebook 05, 8 classes) | 🔴 Non atteint + fiabilité de la mesure à nuancer dans le mémoire |
| ENF-04 | Rappel *Sécurité* | ≥ 0.70 | **0.364** (36,4 %), recalculé sur `models/best_pipeline.pkl` + `data/splits/test.csv` (33 exemples). Voir aussi la remarque ENF-03 sur la représentativité du test | 🔴 Non atteint |
| ENF-05 | Context Recall / Faithfulness RAG | ≥ 0.80 / ≥ 0.85 | Context Recall = **0.028**, Faithfulness = 1.0 — `metrics/rag_eval.json`. Faithfulness=1.0 s'explique par la génération template-based (pas de génération libre → pas d'hallucination possible par construction), donc non comparable à un vrai score RAGAS sur LLM | 🔴 Non atteint (Context Recall) / 🟡 Faithfulness non représentatif |
| ENF-06 | Dégradation gracieuse si LLM indispo | Repli sans génération | RAG sémantique → repli lexical automatique si FAISS indisponible (`predictor.py`, validé Phase 12 bug pyarrow) ; pas de LLM externe en prod donc le risque ne s'applique pas tel quel | ✅ Atteint (dans l'architecture actuelle) |
| ENF-07 | JWT + RBAC + secrets non exposés | Aucun secret en clair | RBAC testé et fonctionnel ; mais `SECRET_KEY`/`INGEST_API_KEY` restent des placeholders en dur dans `api/config.py` (`change-this-in-production...`), à surcharger via `.env` — cf. [RISKS.md](RISKS.md) R-09 (Ouvert) | 🟡 Partiel |
| ENF-08 | Protection injection de prompt | Entrées/sorties filtrées | Aucun test dédié ; risque limité en pratique tant qu'il n'y a pas d'appel LLM réel en production (génération template-based, EF-14) | 🟡 Non vérifié / risque latent si EF-14 évolue vers un vrai LLM |
| ENF-09 | RGPD anonymisation | PII traitées | Non fait — reliquat Phase 2 toujours ouvert (`TASKS.md`) | 🔴 Non atteint |
| ENF-10 | Couverture de tests | ≥ 70 % | **74 %** en local (59 tests, nécessite `models/best_pipeline.pkl` gitignoré, absent d'un clone frais) mais **22 % seulement en CI** (41 tests unitaires, `test_api_integration.py` exclu faute du `.pkl`) — la cible n'est vérifiée qu'en local, pas par la CI telle qu'actuellement configurée | 🟡 Partiel — atteint en local, non vérifiable en CI |
| ENF-11 | Pipeline reproductible | `dvc repro` OK | Validé Phase 10 (`dvc repro --dry`, 4 stages) | ✅ Atteint |
| ENF-12 | Déploiement conteneurisé | `docker-compose up` | Validé Phase 11-12 bout-en-bout (3 services healthy) | ✅ Atteint |
| ENF-13 | Observabilité (logs + métriques IA) | Dashboards | Healthchecks + logs stdout/stderr (Docker), dashboard admin (EF-15) ; logs non structurés (pas de JSON logging) | 🟡 Partiel |
| ENF-14 | Accessibilité RGAA/WCAG | Audit léger | Non audité | 🔴 Non fait |

> Matrice à jour ; ré-exécuter les mesures ENF-01/03/04/05/10 si le split, le modèle ou le RAG
> changent (Phase 13). Détail méthodologique du test de charge dans [TESTING.md](TESTING.md).

---

## 6. Étude utilisateur légère (Phase 12, 2026-07-05)

### 6.1 Méthodologie et limite assumée
Projet PFE solo, sans accès à de vrais utilisateurs externes à ce stade. Étude réalisée par
l'auteur, endossant tour à tour les 3 personas (§2) sur le parcours cœur de métier (EF-01 à
EF-08), contre l'application réellement déployée (Docker, `docker-api-1`/`docker-frontend-1`).
**Limite technique de cette session** : l'outil de pilotage navigateur (extension Chrome) était
indisponible (non connecté après plusieurs tentatives) — le parcours a donc été rejoué **au niveau
API** (`curl`, chronométré) plutôt qu'en clics réels, complété par une **revue de code** des
templates Angular (`ticket-detail.html`, `new-ticket.html`) pour juger de l'ergonomie réelle
(libellés, états, messages). Cette méthode a un avantage inattendu : elle a permis de vérifier que
le code affiché correspond à ce que l'API renvoie réellement, révélant des écarts invisibles à un
simple clic (§6.3).

### 6.2 Parcours testé (persona Client → Admin → Client)
| Étape | Persona | Résultat | Temps |
|---|---|---|---|
| Login | Client | 200, JWT valide | 48 ms |
| Création ticket (VPN) | Client | 200, catégorie *Réseau* prédite, confiance 0.78, solution RAG pertinente | 2,03 s |
| Liste "mes tickets" | Client | 200, ticket visible avec statut "En attente" | 47 ms |
| Liste globale | Admin | 200, ticket visible | 60 ms |
| Transition "En attente"→"Prise en Charge" | Admin | 200 | — |
| Transition "Prise en Charge"→"Résolu" + réponse | Admin | 200, historique loggé | — |
| Transition invalide "Résolu"→"Prise en Charge" | Admin | **400 correctement rejeté**, message clair | — |
| Consultation finale | Client | 200, statut "Résolu", réponse et date visibles | — |

Golden path EF-01/02/03/04/06/07/08 **fonctionnellement confirmé de bout en bout**. Temps de
création dominé par l'inférence (~2 s), cohérent avec R-13 (latence P95).

### 6.3 Constats positifs
- Formulaire client en langage naturel, non technique (« Quel est votre problème ? »,
  « C'est urgent ? » avec choix 🙂/😟) — bonne adéquation à la persona *Client/Demandeur* (§2),
  seulement 1 champ obligatoire.
- Validation des transitions de statut robuste et lisible : rejet propre (400 + message explicite)
  d'une transition illégale, formulaire admin qui désactive l'action et affiche
  « Statut terminal — aucune transition possible » quand c'est pertinent.
- Suggestions RAG cohérentes avec le contenu du ticket dans les deux essais (VPN → conseils VPN).
- Historique d'audit lisible et correctement horodaté/attribué.

### 6.4 Frictions et anomalies détectées
| # | Constat | Sévérité | Détail |
|---|---|---|---|
| 1 | ~~**Feedback client trompeur**~~ | 🔴 Élevée | `ticket-detail.ts::submitFeedbackComment()` affichait « Merci pour votre retour ! » après un simple `console.log()` — rien n'était envoyé au serveur. **✅ Corrigé le 2026-07-06** : `POST /tickets/{id}/feedback` implémenté et branché (voir EF-13). |
| 2 | **Pas de routage différencié par confiance** | 🟡 Moyenne | Vérifié en pratique (§6.2) : tickets à confiance 0.78 et 0.91 suivent la même file "En attente" qu'un ticket à faible confiance. EF-05 corrigé ci-dessus. |
| 3 | **Incohérence de nommage `priorite` / `priorite_saisie`** | 🟢 Faible | `TicketCreate.priorite` (entrée) vs `TicketOut.priorite_saisie` (sortie) désignent le même concept sous 2 noms différents. Un consommateur externe de l'API devinant le nom depuis la réponse (ex. via `/ingest` ou une future intégration) écrit silencieusement une valeur par défaut, sans erreur de validation. Le frontend Angular n'est pas affecté (utilise le bon nom). |
| 4 | **Seuil de confiance obsolète dans `tickets.py`** | 🟢 Faible | `approve_ticket()`/`refresh_rag()` (`api/routers/tickets.py:123,195`) codent en dur `threshold = 0.40` (ancien seuil v1) pour décider du fallback RAG, alors que le seuil officiel est passé à 0.60 partout ailleurs (`params.yaml`, `predictor.py`, Phase 13). Incohérence, pas un bug bloquant. |

### 6.5 Recommandations (proposées, non implémentées ici)
1. ~~Retirer le faux message de confirmation du feedback client ou implémenter l'endpoint
   `POST /tickets/{id}/feedback` (EF-13)~~ — **fait le 2026-07-06**.
2. Décider explicitement du comportement souhaité pour EF-05 : soit assumer qu'il n'y a pas
   d'auto-routage (reformuler l'exigence dans le mémoire), soit l'implémenter (ex. statut
   "Auto-résolu" si confiance ≥ 0.85 et catégorie stable).
3. Aligner `tickets.py` sur le seuil unique 0.60 (`predictor.threshold`) au lieu de la valeur
   0.40 codée en dur.
4. Renommer `TicketCreate.priorite` en `priorite_saisie` (ou l'inverse) pour un contrat API cohérent.

---

## 6. Points à valider par l'étudiant (🟠)
1. **Entreprise d'accueil** : nom, contexte, volumétrie réelle des tickets, chiffres avant/après.
2. **Données réelles** : possibilité d'obtenir davantage de tickets réels (le corpus actuel présente une forte redondance) ?
3. **Contraintes RGPD** spécifiques de l'organisation.
4. **Date de soutenance** et disponibilité hebdomadaire (pour convertir le planning relatif en daté).
5. **Périmètre EF optionnelles** : confirmer S/C (ex. génération LLM EF-14, dashboard EF-15).
6. **Choix LLM** (EF-14) : modèle local (confidentialité) vs API (qualité/coût) — à trancher Phase 8.
