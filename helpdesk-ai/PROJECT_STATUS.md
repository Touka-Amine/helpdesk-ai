# PROJECT_STATUS.md — Avancement global

> Résumé concis. **Source de vérité : [PLAN.md](PLAN.md)** (section 10 — Tableau de bord).
> Dernière mise à jour : **2026-07-29** (boucle RAG, refonte workflow tickets, migration
> PostgreSQL/ChromaDB — voir [CHANGELOG.md](CHANGELOG.md) pour le détail daté).

## Bandeau

| | |
|---|---|
| **Phase active** | Phase 13 — Optimisation (Phases 0–12 terminées) + travaux d'ingénierie hors-phases (RAG live, workflow tickets, infra) |
| **Progression globale** | ~86 % |
| **Périmètre** | Cœur rehaussé (Must) |
| **Durée** | Stage 6 mois · GPU local |
| **Prochaine étape** | Décider : Phase 13 Semaine 3 (données réelles) ou Phase 14 (mémoire PFE) |

## ✅ Terminé
- EDA + preprocessing (notebooks 01–02) + features enrichies (`text_enriched`)
- Baseline ML TF-IDF + heuristiques (F1-macro **0.685**, référence de comparaison)
- **CamemBERT-base + LoRA — F1-macro 0.5685** (à parité avec la baseline, sans règles codées)
- RAG lexical (conservé comme fallback) + **RAG sémantique FAISS** (score cosinus 0.93 vs 0.76, +0.17)
- **RAG hybride** (0.5×sémantique + 0.5×lexical, Phase 13 Semaine 2)
- **Évaluation RAG (RAGAS, Phase 7)** — P@3=0.30 sém/0.42 lex, MRR=0.56/0.65, AR=0.58, Faithfulness=1.0
- **Backend API v1.1 (Phase 8)** — `/api/v1` versionné, CORS+rate limiting, SemanticRAG intégré, `/ingest` réparé, couches services remplies
- **Frontend connecté (Phase 9)** — auth JWT, guards, intercepteur, pages détail, feedback persisté
- **Refonte des 15 écrans (design Stitch) + module gestion des comptes** (2026-07-06/07) : CRUD
  utilisateurs admin-only, mot de passe temporaire auto-généré, `first_login` forcé, 3 bugs
  préexistants corrigés (ticket 404 admin, statut d'approbation invalide, badge invisible),
  bugfix redirection logout client
- **MLOps léger (Phase 10)** — pipeline DVC (4 stages) + MLflow registry
- **Déploiement Docker (Phase 11)** — 3 services, CI/CD (lint, tests, build), healthchecks
- **Tests & validation (Phase 12)** — 41 tests unitaires, 18/18 tests d'intégration, test de
  charge, matrice exigences→résultats, étude utilisateur légère (5 bugs de déploiement/auth trouvés et corrigés)
- Documentation (cahier des charges, workflow, système de pilotage 11 fichiers)
- **UX complémentaire (2026-07-16)** — sidebar noire + mode sombre (admin/client), formulaire
  Nouveau ticket reconstruit (exemples guidés), fix routing racine→login, expiration de session
  par inactivité
- **Boucle de feedback RAG (2026-07-16)** — détection de « cas nouveau » (`rag_score`, seuil
  0.50), solution appliquée par l'admin rendue obligatoire sur les cas nouveaux avant résolution,
  archive alimentée en priorité par la solution réelle (pas la suggestion IA non validée), panneau
  RAG technique masqué côté client (remplacé par un suivi en langage simple)
- **Login redessiné (2026-07-16)** — logo OneTech B.S. recréé en CSS/SVG, mise en page deux
  colonnes, teaser IA décoratif retiré
- **Refonte du workflow de traitement des tickets (2026-07-29)** — file d'approbation : popup de
  décision retiré, remplacé par un clic simple (prise en charge automatique + redirection directe) ;
  écran de détail admin restructuré en 2 étapes (revue puis clôture), statut regroupé avec
  catégorie/priorité/classification finales à la clôture plutôt que demandé en amont ; ticket
  résolu/rejeté reste éditable après coup (bug de blocage trouvé et corrigé en vérification)
- **Migration infrastructure PostgreSQL + ChromaDB (2026-07-29, ADR-004 / ADR-006)** — base
  opérationnelle SQLite→PostgreSQL (2 bugs de course entre workers uvicorn trouvés et corrigés
  en vérification, sur `CREATE TABLE` et sur la fraîcheur inter-processus de la collection
  vectorielle) ; TinyDB→ChromaDB avec une différence de fond : la base de connaissances est
  désormais **interrogée en direct** par le RAG à chaque recommandation (`query_similar()`),
  alors que TinyDB n'était qu'un journal jamais relu — vérifié en direct : une solution admin
  devient la suggestion proposée dès le ticket similaire suivant

## 🟡 En cours
- Phase 13 (Optimisation) — Semaines 1–2 terminées (heuristiques + RAG hybride), Semaine 3
  (données réelles) conditionnelle
- Phase 14 (mémoire PFE) — ~15 %, à intensifier

## 🔴 À faire (prioritaire)
- Phase 2 (reliquat) : RGPD / anonymisation
- Phase 13 : optimiser la latence P95 (R-13, non conforme sous charge)
- Phases 14–15 : mémoire PFE, préparation soutenance

## Avancement par phase
| Phase | Avancement |
|---|---|
| 0 Initialisation | ✅ 100 % |
| 1 Cadrage & SRS | ✅ 100 % (SRS v0.1) |
| 2 Data & RGPD | 🟡 ~45 % (diagnostic qualité + features enrichies faits, RGPD à faire) |
| 3 EDA | ✅ ~90 % (consolidé + benchmark externe) |
| 4 ML baseline | ✅ 100 % (multi-modèles + heuristiques, F1=0.685) |
| 5 Fine-Tuning | ✅ 100 % (CamemBERT LoRA, F1=0.5685) |
| 6 RAG sémantique | ✅ 100 % (FAISS + paraphrase-multilingual, score 0.93) |
| 7 Éval RAG | ✅ 100 % (P@3=0.30 sém, MRR=0.56, AR=0.58, Faith=1.0) |
| 8 Backend | ✅ 100 % (API v1.1 : /api/v1, sécurité, SemanticRAG, /ingest, services, tests) |
| 9 Frontend | ✅ 100 % (connexion + 15 écrans Stitch + gestion des comptes, 2026-07-06) |
| 10 MLOps | ✅ 100 % (DVC 4 stages + MLflow) |
| 11 Déploiement | ✅ 100 % (Docker 3 services + CI/CD) |
| 12 Tests | ✅ 100 % (unitaires, intégration, charge, matrice exigences, étude utilisateur) |
| 13 Optimisation | 🟡 ~65 % (Semaines 1–2 faites, Semaine 3 conditionnelle) |
| 14 Doc/mémoire | 🟡 ~15 % |
| 15 Soutenance | 🔴 0 % |
