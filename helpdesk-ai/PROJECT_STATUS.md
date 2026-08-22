# PROJECT_STATUS.md — Avancement global

> Résumé concis. **Source de vérité : [PLAN.md](PLAN.md)** (section 10 — Tableau de bord).
> Dernière mise à jour : **2026-08-22** (industrialisation MLOps : boucle d'amélioration du
> modèle et cycle de vie des connaissances RAG — voir [MLOPS.md](MLOPS.md) et
> [CHANGELOG.md](CHANGELOG.md) pour le détail daté).

## Bandeau

| | |
|---|---|
| **Phase active** | Phase 13 — Optimisation (Phases 0–12 terminées) + travaux d'ingénierie hors-phases (RAG live, workflow tickets, infra) |
| **Progression globale** | ~86 % |
| **Périmètre** | Cœur rehaussé (Must) |
| **Durée** | Stage 6 mois · GPU local |
| **Prochaine étape** | Décider : activer `split.strategy: stratified_group` (R-14) ou conserver la référence publiée, puis Phase 14 (mémoire PFE) |

## ✅ Terminé
- EDA + preprocessing (notebooks 01–02) + features enrichies (`text_enriched`)
- Baseline ML TF-IDF + heuristiques — F1-macro **0.685** sur le protocole DVC ⚠️ *(test ne
  couvrant que 5 catégories sur 8 — voir R-14 ; chiffre non comparable au 0.5673 ci-dessous)*
- **CamemBERT-base + LoRA — F1-macro 0.5685** (protocole stratifié 8 classes, notebook 05 :
  à parité avec la baseline mesurée **sur le même split**, 0.5673, sans règles codées)
- RAG lexical (conservé comme fallback) + **RAG sémantique FAISS** (score cosinus 0.93 vs 0.76, +0.17)
- **RAG hybride** (0.5×sémantique + 0.5×lexical, Phase 13 Semaine 2)
- **Évaluation RAG (RAGAS, Phase 7)** — P@3=0.30 sém/0.42 lex, MRR=0.56/0.65, AR=0.58, Faithfulness=1.0
- **Backend API v1.1 (Phase 8)** — `/api/v1` versionné, CORS+rate limiting, SemanticRAG intégré, `/ingest` réparé, couches services remplies
- **Frontend connecté (Phase 9)** — auth JWT, guards, intercepteur, pages détail, feedback persisté
- **Refonte des 15 écrans (design Stitch) + module gestion des comptes** (2026-07-06/07) : CRUD
  utilisateurs admin-only, mot de passe temporaire auto-généré, `first_login` forcé, 3 bugs
  préexistants corrigés (ticket 404 admin, statut d'approbation invalide, badge invisible),
  bugfix redirection logout client
- **MLOps léger (Phase 10)** — pipeline DVC (4 stages) + suivi MLflow
- **Déploiement Docker (Phase 11)** — 3 services, CI/CD (lint, tests, build), healthchecks
- **Tests & validation (Phase 12)** — 41 tests unitaires, 18/18 tests d'intégration, test de
  charge, matrice exigences→résultats, étude utilisateur légère (5 bugs de déploiement/auth trouvés et corrigés)
  ; suite portée à **125 tests** le 2026-08-22
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
- **Interface client épurée + assistant de triage IA (2026-07-30)** — vue client : retrait
  des métadonnées IA (catégorie prédite, confiance), colonne latérale remplacée par suivi
  simplifié + cas similaires + contact rapide, message de résolution auto différencié ;
  écran admin : clôture pilotée par le choix du statut final (modale ouverte par
  « Enregistrer », plus de menu déroulant pré-rempli), édition inline du tableau, création/
  suppression sécurisée de tickets ; nouveau service **Ollama** (LLM local `llama3.2:3b`,
  100% on-premise) reformulant les tickets similaires archivés en français professionnel
  au lieu d'afficher leur résolution brute — vérifié en direct avec repli automatique testé ;
  synthèse affichée par défaut (au lieu d'un bouton à découvrir) avec latence réduite
  (`keep_alive`, ~19s à chaud vs ~95s à froid) ; garde-fou anti-hallucination (résolution
  contaminée assainie en entrée, ID inventés rejetés en sortie) après reproduction en
  direct d'un cas réel ; chat conversationnel avec l'assistant IA pour les questions de
  suivi libres, mêmes garde-fous, vérifié en direct

- **Industrialisation MLOps — deux boucles (2026-08-22)** — voir [MLOPS.md](MLOPS.md).
  *Boucle classification* : jeu de test **gelé** (empreinte SHA-256, condition sans laquelle
  comparer deux modèles ne mesure rien), collecte des tickets validés depuis PostgreSQL avec
  qualification de la **force de l'étiquette** (corrigée / confirmée / faible, les faibles
  exclues pour que le modèle ne se réentraîne pas sur ses propres sorties), dataset versionné
  avec garde-fous anti-fuite, entraînement produisant un **candidat**, **porte de promotion**
  à trois conditions réévaluant les deux modèles dans la même exécution, registre de versions
  avec rollback, rechargement du modèle sans redémarrage. Vérifié : un candidat identique au
  modèle en service est rejeté et la production restaurée intacte.
  *Boucle connaissances* : contrôle qualité avant indexation qui **ferme le chemin
  d'auto-contamination** du RAG (une suggestion IA jamais relue ne peut plus devenir une
  connaissance de référence — cause structurelle de R-04), statuts de cycle de vie
  (actif / remplacé / obsolète, sans suppression automatique), versionnement par instantanés,
  évaluation rejouable en stage DVC. Le **moteur hybride réellement servi** est mesuré pour la
  première fois : P@3 = 0.354 contre 0.292 (sémantique) et 0.154 (lexical).
  *Au passage* : le stage `rag_semantic_build` entre dans DVC (l'index FAISS de production
  était construit hors pipeline, ni reproductible ni versionné), `metrics/rag_eval.json` ne
  publie plus un rappel non interprétable, et `api/config.py` ne bloque plus la collecte des
  tests d'intégration en local.
  *Limite* : aucun trafic de production à traiter, les seuils restent à calibrer (R-20).

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
| 4 ML baseline | ✅ 100 % (multi-modèles + heuristiques ; F1=0.685 protocole DVC ⚠️ 5/8 classes, ou 0.5673 protocole stratifié 8 classes) |
| 5 Fine-Tuning | ✅ 100 % (CamemBERT LoRA, F1=0.5685 sur protocole stratifié 8 classes) |
| 6 RAG sémantique | ✅ 100 % (FAISS + paraphrase-multilingual, score 0.93) |
| 7 Éval RAG | ✅ 100 % (P@3=0.30 sém, MRR=0.56, AR=0.58, Faith=1.0) |
| 8 Backend | ✅ 100 % (API v1.1 : /api/v1, sécurité, SemanticRAG, /ingest, services, tests) |
| 9 Frontend | ✅ 100 % (connexion + 15 écrans Stitch + gestion des comptes, 2026-07-06) |
| 10 MLOps | ✅ 100 % (DVC **8 stages**, registre de modèles avec promotion/rollback, monitoring ML et RAG, suivi MLflow — [MLOPS.md](MLOPS.md)) |
| 11 Déploiement | ✅ 100 % (Docker 3 services + CI/CD) |
| 12 Tests | ✅ 100 % (125 tests : unitaires, intégration, cycle de vie ChromaDB, charge, matrice exigences, étude utilisateur) |
| 13 Optimisation | 🟡 ~65 % (Semaines 1–2 faites, Semaine 3 conditionnelle) |
| 14 Doc/mémoire | 🟡 ~15 % |
| 15 Soutenance | 🔴 0 % |
