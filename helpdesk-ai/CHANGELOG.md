# CHANGELOG.md — Historique des modifications

> Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/). Types : `Ajouté`,
> `Modifié`, `Corrigé`, `Supprimé`, `Sécurité`, `Déprécié`. Source de vérité : [PLAN.md](PLAN.md).

## [Non publié]

### Ajouté
- Système de pilotage documentaire du PFE : `PLAN.md` (source de vérité) + `PROJECT_STATUS.md`,
  `TASKS.md`, `BACKLOG.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `RISKS.md`, `TESTING.md`,
  `DEPLOYMENT.md`, `PFE_PROGRESS.md`.
- `CAHIER_DES_CHARGES.md` : audit critique + restructuration au niveau ingénieur/industriel.

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
