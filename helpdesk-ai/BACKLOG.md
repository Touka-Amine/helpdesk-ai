# BACKLOG.md — Idées et fonctionnalités futures

> Tout ce qui est **hors périmètre « Cœur rehaussé »** mais à valeur ajoutée. Rien ici n'est
> planifié tant que ce n'est pas promu dans [PLAN.md](PLAN.md). Priorités : **S** = Should,
> **C** = Could, **P** = Perspective (hors PFE). Dernière mise à jour : *à la création*.

## RAG & Retrieval
- [ ] **Hybrid Search** (BM25 + dense) — robustesse sur sigles/codes erreurs IT — **S**
- [ ] **Re-ranking** par cross-encoder — précision du top-k — **S**
- [ ] Cache sémantique des requêtes — coût/latence — **C**
- [ ] Chunking avancé (sémantique / parent-child) — **C**

## LLM & Génération
- [ ] **Génération avancée par LLM** avec QLoRA d'un petit LLM sur résolutions historiques — **C**
- [ ] **Guardrails** entrée/sortie + détection d'hallucinations renforcée — **S**
- [ ] **Prompt versioning** outillé (registre, diff, métrique associée) — **S**
- [ ] Détection d'injection de prompt — **S**

## Agents
- [ ] **Agent orchestrateur** (classif → RAG → réponse → escalade) — **C**
- [ ] **Multi-Agent System** — **P**

## NLP / ML
- [ ] **Active learning** : feedback agent → ré-entraînement ciblé — **C**
- [ ] **Continual learning** — **P**
- [ ] Augmentation de données (back-translation, paraphrase) pour classe *Sécurité* — **S**
- [ ] **Knowledge Graph** des entités IT — **P**

## MLOps / LLMOps / Observabilité
- [ ] **Drift detection** (PSI/KL) + alerting + ré-entraînement déclenché — **S**
- [ ] **Monitoring IA** complet (dashboards Grafana) — **S**
- [ ] **Observabilité LLM** (traçage des appels, tokens, coûts) — **S**
- [ ] **Optimisation du coût d'inférence** (quantization, batching) — **C**

## Infrastructure
- [ ] **Kubernetes** (si objectif de scalabilité) — **P**
- [ ] Architecture **microservices** complète — **P**
- [ ] Migration SQLite → **PostgreSQL** (+ pgvector) — **S**

## Produit / UX
- [ ] Notifications temps réel (email / in-app) sur changement de statut — **C**
- [ ] Dashboard analytique (temps de résolution, tendances catégories) — **C**
- [ ] Support **multilingue** — **P**
- [ ] Intégration Power Automate finalisée (`/ingest`) — **S**

---
*Procédure de promotion : un item devient une tâche planifiée uniquement après ajout dans la
phase correspondante de PLAN.md (avec objectif/critères/estimation).*
