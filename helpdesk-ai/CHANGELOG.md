# CHANGELOG.md — Historique des modifications

> Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/). Types : `Ajouté`,
> `Modifié`, `Corrigé`, `Supprimé`, `Sécurité`, `Déprécié`. Source de vérité : [PLAN.md](PLAN.md).

## [Non publié] — branche `chore/gouvernance-pfe`

### Phase 3–4 — Modélisation multi-modèles + Backend NoSQL (2026-06-26)

#### Notebooks restructurés
- `Modifié` : `notebooks/02_preprocessing.ipynb` — notebook complet (imports → nettoyage → features titre+desc → analyse redondance → sauvegarde → 3 figures PNG).
- `Modifié` : `notebooks/03_modeling.ipynb` — multi-modèles (LR+SMOTE, LinearSVC calibré, LightGBM, Ensemble) + évaluation pipeline complet ML+heuristiques + benchmark PNG + matrices de confusion PNG + analyse HITL PNG + sauvegarde modèle.
- `Ajouté` : `notebooks/figures/mod_01_benchmark.png`, `mod_02_confusion_ml.png`, `mod_03_confusion_heuristiques.png`, `mod_04_hitl_analyse.png`, `prep_01_*.png`, `prep_02_*.png`, `prep_03_*.png`.

#### ML & Heuristiques
- `Modifié` : `src/data/preprocess.py` — `build_text_for_model` utilise désormais **titre + description** (signal discriminant du titre capturé). Stop-words allégés (termes IT conservés).
- `Modifié` : `src/models/heuristics.py` — ajout `FORCE_RULES` (outlook → Microsoft toujours, ransomware → Sécurité toujours) + enrichissement `SOFT_RULES` Sécurité (dossier sécurisé, connexion suspecte, accès refusé) et Réseau (internet lent, connexion internet).
- `Ajouté` : `requirements.txt` — `lightgbm>=4.0.0`, `tinydb>=4.8.0`, `scikit-learn>=1.6.0`.

#### Backend NoSQL
- `Ajouté` : `api/db/nosql_store.py` — TinyDB (`data/resolved_tickets.json`) : archive des tickets résolus après approbation agent.
- `Modifié` : `api/routers/tickets.py` — intégration TinyDB dans `approve_ticket` (statut → Résolu déclenche l'archivage NoSQL). Nouveaux endpoints : `GET /tickets/resolved/stats` et `GET /tickets/resolved/archive`.

### Ajouté
- Système de pilotage documentaire du PFE : `PLAN.md` (source de vérité) + `PROJECT_STATUS.md`,
  `TASKS.md`, `BACKLOG.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `RISKS.md`, `TESTING.md`,
  `DEPLOYMENT.md`, `PFE_PROGRESS.md`.
- `CAHIER_DES_CHARGES.md` : audit critique + restructuration au niveau ingénieur/industriel.
- `.gitignore` racine du dépôt (exclut `venv/`, `node_modules/`, `*.pkl`, `*.db`, `.env`).

### Modifié
- `helpdesk-ai/.gitignore` : ajout `node_modules/`, `data/*.db`, artefacts build frontend.

### Qualité des données & notebooks (2026-06-26)
- `Ajouté` : `DIAGNOSTIC_QUALITE_DONNEES.md` (diagnostic chiffré et neutre de la qualité des données).
- `Ajouté` : `notebooks/data_quality_report.py` (profilage + figures + PDF
  `notebooks/figures/diagnostic_qualite_donnees.pdf`).
- `Ajouté` : `notebooks/notebook.md` (audit + étapes des 4 notebooks).
- `Modifié` : reformulation neutre du vocabulaire décrivant les données (notebooks, métadonnées,
  cahier des charges, rapport template, fichiers de suivi).
- `Corrigé` : `notebooks/rapport_audit.txt` (nombre de colonnes 23 → 18).
- `Supprimé` : `notebooks/Untitled.ipynb` (vide).

### Phase 1 — Cadrage & SRS (2026-06-26)
- `Ajouté` : `CADRAGE_SRS.md` v0.1 — problématique, questions de recherche, hypothèses, objectifs
  SMART, exigences fonctionnelles (MoSCoW), non-fonctionnelles (métriques) et matrice de
  traçabilité. **En attente de validation** des points 🟠.

### Phase 0 — commits (2026-06-26)
- `07cd6a9` docs(pilotage) : système de gestion de projet PFE + cahier des charges.
- `8dae2fd` feat(frontend) : application Angular 21 (scaffold client/admin).
- `2532828` chore(ml) : maj notebooks, preprocessing, moteur RAG, config + metadata.

---

## Historique antérieur (d'après git)

### [0.4.0] — Phase RAG
- `Ajouté` : moteur RAG par similarité cosinus (`src/rag/engine.py`).
- `Corrigé` : suppression des `nan` dans les résolutions — repli sur la knowledge base.

### [0.3.0] — Phase Modélisation
- `Ajouté` : pipeline baseline TF-IDF + SMOTE + LogisticRegression (F1-macro 0.77).
- `Modifié` : seuil de confiance ajusté à 0.40 (68.7 % d'auto-routage à 100 % de précision).

### [0.2.0] — Phase API
- `Ajouté` : structure API (routers, services, schemas, db, middleware).

### [0.1.0] — Phases EDA & Preprocessing
- `Ajouté` : notebooks EDA, preprocessing, modélisation, RAG ; rapport d'audit.
