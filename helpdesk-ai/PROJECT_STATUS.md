# PROJECT_STATUS.md — Avancement global

> Résumé concis. **Source de vérité : [PLAN.md](PLAN.md)** (section 10 — Tableau de bord).
> Suivi de la rédaction du mémoire : [PFE_PROGRESS.md](PFE_PROGRESS.md).
> Dernière mise à jour : **2026-09-08** (rédaction du mémoire : introduction et chapitres 1 à 4
> rédigés, chapitre 6 ajouté, 115 pages compilées — voir [PFE_PROGRESS.md](PFE_PROGRESS.md) et
> [CHANGELOG.md](CHANGELOG.md) pour le détail daté).

## Bandeau

| | |
|---|---|
| **Phase active** | Phase 14 — Rédaction du mémoire (Phases 0–12 terminées, Phase 13 partielle) |
| **Progression globale** | ~90 % |
| **Périmètre** | Cœur rehaussé (Must) |
| **Durée** | Stage 6 mois · GPU local |
| **Mémoire** | 6 chapitres sur 7 rédigés · 115 pages compilées, dans la cible de 110–135 |
| **Prochaine étape** | Rédiger le chapitre 7 (industrialisation, tests et validation) |

## ✅ Terminé
- EDA + preprocessing (notebooks 01–02) + features enrichies (`text_enriched`)
- Baseline ML TF-IDF + heuristiques — F1-macro **0.5829** sur le protocole DVC ⚠️ *(test ne
  couvrant que 5 catégories sur 8 — voir R-14 ; chiffre non comparable au 0.5827 du protocole
  stratifié). Valeur postérieure à l'audit des règles du 2026-08-22, qui a retiré quatre
  mots-clés introduits en consultant le jeu de test*
- **CamemBERT-base + LoRA — F1-macro 0.5685** (protocole stratifié 8 classes, notebook 05 :
  la baseline sans règles atteignant 0.3753 sur le même split)
- **Meilleure combinaison : CamemBERT + LoRA + règles métier — F1-macro 0.8343** (protocole
  stratifié 8 classes, à 0.016 de l'objectif ENF-03). Comparaison à configuration égale menée
  le 2026-08-22 : CamemBERT devance TF-IDF de +0.252 avec les règles, ce qui **vérifie H1**
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
  ; suite portée à **133 tests** (mesurés le 2026-09-08)
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

- **Audit des règles métier et campagne d'évaluation (2026-08-22)** — quatre mots-clés ajoutés en
  consultant le jeu de test ont été retirés (R-23, clos). Les sept approches ont été réévaluées
  sur un protocole unique, ce qui a permis la première comparaison à configuration égale entre
  TF-IDF et CamemBERT : **H1 est vérifiée**. Comparaison avant/après conservée dans
  [../reports/analyse-notebooks/COMPARAISON_AVANT_APRES.md](../reports/analyse-notebooks/COMPARAISON_AVANT_APRES.md)
- **Cartographie des notebooks (2026-08-22)** — rôle architectural de chacun, carte des
  dépendances, écarts à l'architecture cible :
  [../reports/analyse-notebooks/ANALYSE_NOTEBOOKS.md](../reports/analyse-notebooks/ANALYSE_NOTEBOOKS.md)
- **Mémoire PFE — introduction et chapitres 1 à 6 (2026-08 → 2026-09)** — 115 pages compilées,
  17 figures, 40 tableaux, chaque valeur citée renvoyant à un fichier du dépôt. Le chapitre 5 a
  mis au jour un défaut de calibrage : le moteur hybride servi n'atteint jamais le seuil de
  pertinence de 0,50, calibré sur l'échelle du moteur sémantique, ce qui conduit l'application à
  traiter tout ticket comme un cas nouveau

## 🟡 En cours
- **Phase 14 (mémoire PFE) — ~80 %.** Introduction et chapitres 1 à 6 rédigés, 115 pages
  compilées sans erreur. Prochain : chapitre 7 (industrialisation, tests et validation). Les
  captures d'écran du chapitre 6 restent bloquées sur la question d'anonymisation. Détail et
  blocages dans [PFE_PROGRESS.md](PFE_PROGRESS.md)
- Phase 13 (Optimisation) — Semaines 1–2 terminées (heuristiques + RAG hybride), Semaine 3
  (données réelles) conditionnelle

## 🔴 À faire (prioritaire)
- Mémoire : chapitre 7, conclusion générale, annexes, résumés FR et EN, captures d'écran
- Réponses au questionnaire OTBS ([../report/QUESTIONS_ENTREPRISE.md](../report/QUESTIONS_ENTREPRISE.md)) — le chapitre 1 reste sous sa cible sans elles
- Phase 2 (reliquat) : RGPD / anonymisation
- Phase 13 : optimiser la latence P95 (R-13, non conforme sous charge)
- Phase 15 : préparation de la soutenance

## Avancement par phase
| Phase | Avancement |
|---|---|
| 0 Initialisation | ✅ 100 % |
| 1 Cadrage & SRS | ✅ 100 % (SRS v0.1) |
| 2 Data & RGPD | 🟡 ~45 % (diagnostic qualité + features enrichies faits, RGPD à faire) |
| 3 EDA | ✅ ~90 % (consolidé + benchmark externe) |
| 4 ML baseline | ✅ 100 % (multi-modèles + heuristiques ; F1=0.5829 protocole DVC ⚠️ 5/8 classes, ou 0.5827 protocole stratifié 8 classes ; **meilleure combinaison CamemBERT+règles = 0.8343**) |
| 5 Fine-Tuning | ✅ 100 % (CamemBERT LoRA, F1=0.5685 sur protocole stratifié 8 classes) |
| 6 RAG sémantique | ✅ 100 % (FAISS + paraphrase-multilingual, score 0.93) |
| 7 Éval RAG | ✅ 100 % (P@3=0.30 sém, MRR=0.56, AR=0.58, Faith=1.0) |
| 8 Backend | ✅ 100 % (API v1.1 : /api/v1, sécurité, SemanticRAG, /ingest, services, tests) |
| 9 Frontend | ✅ 100 % (connexion + 15 écrans Stitch + gestion des comptes, 2026-07-06) |
| 10 MLOps | ✅ 100 % (DVC **8 stages**, registre de modèles avec promotion/rollback, monitoring ML et RAG, suivi MLflow — [MLOPS.md](MLOPS.md)) |
| 11 Déploiement | ✅ 100 % (Docker 3 services + CI/CD) |
| 12 Tests | ✅ 100 % (**133 tests** : unitaires, intégration, cycle de vie ChromaDB, charge, matrice exigences, étude utilisateur) |
| 13 Optimisation | 🟡 ~65 % (Semaines 1–2 faites, Semaine 3 conditionnelle) |
| 14 Doc/mémoire | 🟡 ~80 % (introduction + chapitres 1–6 rédigés, 115 p. compilées ; restent le chapitre 7, la conclusion, les annexes, les résumés et les captures d'écran) |
| 15 Soutenance | 🔴 0 % |
