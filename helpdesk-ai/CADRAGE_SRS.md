# CADRAGE_SRS.md — Cadrage scientifique & Spécification des besoins

> Document **exécutable** des exigences (Phase 1 du [PLAN.md](PLAN.md)). Version formelle et
> traçable de la narration du [CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md) (Ch. 1–3).
> Dernière mise à jour : **2026-06-26** · Statut : **v0.1 — première version à valider**.
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

## 5. Matrice de traçabilité (extrait)

| Exigence | Phase PLAN.md | Vérification (TESTING.md) |
|---|---|---|
| EF-03 / ENF-03, 04 | Phase 4–5 | Tests IA / non-régression métriques |
| EF-04 / ENF-05 | Phase 6–7 | Évaluation RAGAS |
| EF-05 / H3 | Phase 4 | Test de calibration + seuil |
| EF-01,06,07,08 | Phase 8–9 | Tests d'intégration end-to-end |
| EF-14 / ENF-06,08 | Phase 7–8 | Tests guardrails + panne LLM |
| ENF-09 | Phase 2 | Audit RGPD |
| ENF-11,12 | Phase 10–11 | CI : `dvc repro`, `docker-compose` |
| ENF-01,02 | Phase 12 | Test de charge |

> Matrice complète à maintenir au fil des phases (objectif : chaque EF/ENF couverte par ≥ 1 test).

---

## 6. Points à valider par l'étudiant (🟠)
1. **Entreprise d'accueil** : nom, contexte, volumétrie réelle des tickets, chiffres avant/après.
2. **Données réelles** : possibilité d'obtenir davantage de tickets réels (le corpus actuel présente une forte redondance) ?
3. **Contraintes RGPD** spécifiques de l'organisation.
4. **Date de soutenance** et disponibilité hebdomadaire (pour convertir le planning relatif en daté).
5. **Périmètre EF optionnelles** : confirmer S/C (ex. génération LLM EF-14, dashboard EF-15).
6. **Choix LLM** (EF-14) : modèle local (confidentialité) vs API (qualité/coût) — à trancher Phase 8.
