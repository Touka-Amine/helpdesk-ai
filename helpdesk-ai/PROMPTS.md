# Prompts réutilisables — PFE Plateforme IA Helpdesk

> Deux prompts à coller dans n'importe quel assistant IA (Claude, ChatGPT…) pour lui donner le
> contexte de ton projet. **Prompt 1** = la vision/cible. **Prompt 2** = l'état réel actuel.
> Utilise-les ensemble : l'IA comprend alors *où tu veux aller* ET *d'où tu pars*.
> Remplace toujours `[TA DEMANDE]` à la fin par ce que tu veux obtenir.

---

## PROMPT 1 — Contexte & explication du projet (version CIBLE)

```
Tu es un comité d'experts : architecte IA senior, expert NLP/RAG/LLMOps et encadrant de PFE.
Je réalise un Projet de Fin d'Études (PFE) d'ingénieur en Intelligence Artificielle.
Comprends mon projet en profondeur avant de répondre. Les données sont EN FRANÇAIS.

# TITRE
Plateforme intelligente d'analyse, de classification et d'assistance sur les tickets
informatiques (helpdesk IT) d'une entreprise multi-filiales.

# PROBLÈME
Les tickets IT sont traités manuellement (30 à 45 min/ticket) : catégorisation à la main,
recherche d'une solution dans l'historique, rédaction de la réponse. Objectif : réduire à
5–10 min grâce à l'IA, avec validation humaine (human-in-the-loop).

# OBJECTIFS FONCTIONNELS
1. Classer chaque ticket en 8 catégories : Microsoft, Réseau, Applicatifs, Infrastructure,
   Système, Communication, Sécurité, Backup.
2. NLP enrichi : résumé automatique, extraction d'entités (équipement, logiciel, code erreur,
   IP), analyse de priorité, analyse de sentiment/urgence.
3. Assistance à la résolution par RAG : suggérer les solutions des tickets résolus similaires.
4. Workflow de validation par un agent/admin (statuts contrôlés) + journal d'audit complet.
5. Boucle de feedback utilisateur pour améliorer le modèle.

# ARCHITECTURE CIBLE
- NLP : modèle francophone CamemBERT/CamemBERTa fine-tuné (LoRA) pour la classification ;
  baseline TF-IDF + LogisticRegression conservé comme référence de comparaison (benchmark).
- RAG SÉMANTIQUE : embeddings francophones + base vectorielle (Qdrant/Chroma/pgvector) +
  hybrid search (BM25 + dense) + re-ranking (cross-encoder) + génération par LLM avec citations
  + guardrails anti-hallucination.
- Évaluation RAG : RAGAS (Precision@k, Recall@k, MRR, nDCG, Context Precision/Recall,
  Faithfulness, Answer Relevancy, Hallucination Rate) + LLM-as-a-Judge.
- Backend : API FastAPI (auth JWT + RBAC, CRUD tickets, workflow de statut, historique d'audit).
- Frontend : Angular (parcours client/agent/admin, restitution de la confiance et des sources
  RAG, collecte de feedback).
- MLOps/LLMOps : DVC (versionnage données), MLflow (registre de modèles), CI/CD, monitoring
  (drift, coût d'inférence), prompt versioning.
- Déploiement : Docker multi-services + docker-compose, observabilité (Prometheus/Grafana).
- Gouvernance : conformité RGPD (les tickets contiennent des données personnelles),
  anonymisation/pseudonymisation.

# NIVEAU VISÉ
Niveau ingénieur / industriel + académique : démarche scientifique complète (problématique,
état de l'art, benchmark chiffré, évaluation rigoureuse, analyse critique des limites).

À partir de ce contexte : [TA DEMANDE]
```

---

## PROMPT 2 — Niveau de réalisation ATTEINT (état réel honnête)

```
Tu es un ML Engineer senior et un architecte logiciel. Voici l'ÉTAT RÉEL ACTUEL de mon PFE
(ce qui est DÉJÀ codé), à bien distinguer de la version cible. Sois lucide et critique, et
aide-moi à combler l'écart. Données EN FRANÇAIS.

# CE QUI EST FAIT ET FONCTIONNE
- Données : HelpDesk1.csv — 1800 tickets, 8 catégories, en français.
  ⚠️ Corpus à forte redondance : ~58 types de tickets récurrents (≈125 textes uniques sur 1800,
  beaucoup de doublons) ; chaque Titre est lié à une seule Catégorie ; classe Sécurité
  sous-représentée.
- Classification ML : pipeline scikit-learn = TF-IDF (unigrammes, max_features=3000) + SMOTE
  + LinearSVC calibré. Avec un **split anti-fuite GroupShuffleSplit par Titre** (le modèle ne voit
  aucun Titre de test en entraînement), F1-macro honnête = **0.38 ML seul / 0.57 avec heuristiques**
  (les anciens F1≈0.77 / 1.0 venaient d'une fuite : mêmes Titres en train et test). Seuil de
  confiance = 0.40 (≈91% auto-routés à ~70% de précision ; le reste en revue humaine). Heuristiques
  mots-clés (FORCE_RULES) pour corriger les prédictions peu confiantes.
- Classification avancée : **CamemBERT-base + LoRA** (features enrichies `text_enriched`) —
  F1-macro = **0.5685**, à parité avec TF-IDF+heuristiques (0.5673 ; écart +0.0012 dans le bruit
  statistique), mais obtenu par compréhension sémantique sans règles codées à la main.
- RAG : src/rag/engine.py = TF-IDF + similarité cosinus → RECHERCHE LEXICALE, PAS sémantique.
  Top-3, seuil 0.30, fallback 0.10. AUCUN embedding, AUCUNE base vectorielle, AUCUN LLM, AUCUN
  re-ranking, AUCUNE métrique RAG.
- Backend FastAPI (~85%) : auth JWT + bcrypt + rôles (admin/client) ; CRUD tickets ; workflow
  de statut (En attente → Prise en Charge → Résolu/Rejeté/Problème) avec transitions contrôlées ;
  historique d'audit (table TicketHistory) ; SQLite + SQLAlchemy ; intégration ML+RAG via
  ai_service.py.
- Frontend Angular 21 (~60-70%) : layouts client/admin ; pages new-ticket, my-tickets,
  approval-queue, dashboard.
- Documentation : TICKET_WORKFLOW.md et RAPPORT_TEMPLATE.md (complets).

# CE QUI EST CASSÉ OU MANQUANT
- Endpoint /ingest cassé (import datetime manquant + mauvais appel de fonction) et non enregistré.
- Couches services/, db/repositories/, middleware/ = squelettes VIDES (toute la logique est dans
  les routers).
- Frontend : environment.ts VIDE → URL d'API undefined (le front ne communique PAS encore avec
  le back) ; enum de statuts désaligné avec le backend ; modèle Ticket sans les champs IA
  (confiance, categorie_finale, solution_rag) ; page de détail ticket MANQUANTE ; aucun guard
  d'authentification sur /admin.
- MLOps : DVC installé mais dvc.yaml VIDE (pipeline non configuré) ; MLflow en local seulement.
- Sécurité : SECRET_KEY=change-me en clair dans .env.
- Absents : gouvernance RGPD, monitoring, Docker/CI-CD fonctionnel, tests automatisés.

# STACK ACTUELLE
Python 3.13, scikit-learn, imbalanced-learn, NLTK, FastAPI, SQLAlchemy, SQLite, Angular 21,
DVC, MLflow.

# ÉCART VS CIBLE
Modèle = baseline ancien (à élever vers CamemBERT fine-tuné) ; RAG = lexical (à élever vers
sémantique + évaluation RAGAS) ; pas de LLM ni de fine-tuning ; pas de MLOps réel ; intégration
front/back incomplète ; pas de gouvernance ni de déploiement.

Aide-moi à : [TA DEMANDE]
```
