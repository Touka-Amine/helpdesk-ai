# CHANGELOG.md — Historique des modifications

> Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/). Types : `Ajouté`,
> `Modifié`, `Corrigé`, `Supprimé`, `Sécurité`, `Déprécié`. Source de vérité : [PLAN.md](PLAN.md).

## [Non publié] — branche `chore/gouvernance-pfe`

### Phase 5 — Fine-tuning CamemBERT (LoRA) + features enrichies (2026-06-27)

#### Fine-tuning CamemBERT-base + LoRA
- `Ajouté` : `notebooks/05_camembert_finetuning.ipynb` — pipeline complet (dataset HuggingFace → tokenisation CamemBERT → split anti-fuite GroupShuffleSplit par Titre → LoRA r=8/alpha=16 sur `query,value` → entraînement GPU local (10 epochs, FP32) → évaluation F1-macro + matrice de confusion + analyse HITL → benchmark vs TF-IDF). **F1-macro = 0.5685 / Accuracy = 0.6873** — à parité avec TF-IDF+heuristiques (0.5673 ; écart +0.0012 dans le bruit statistique sur 355 tickets), mais atteint par compréhension sémantique **sans règles codées à la main**.
- `Ajouté` : adaptateur LoRA `models/camembert_lora_adapter/` (adapter_config + safetensors + tokenizer) et `models/camembert_metadata.json`.
- `Ajouté` : figures `notebooks/figures/cam_01_confusion.png`, `cam_02_confiance.png`, `cam_03_benchmark.png`.

#### Features enrichies (réduction du bruit catégoriel)
- `Ajouté` : `src/data/preprocess.py` — `simplify_priorite` (4→3 : Majeur+Critique→haute), `simplify_classification` (5→3 : Incident+Alerte→incident, Problème+Changement→changement), `build_text_enriched` (préfixe `type <clf> priorite <prio>` + titre + description). La cible métier `Catégorie` (8 classes) reste inchangée.
- `Modifié` : `notebooks/02_preprocessing.ipynb` — section 4b ajoutée ; génère `priorite_simple`, `classification_simple`, `text_enriched` (1638 valeurs uniques vs 1133 pour `text_clean`). CSV `data/processed/HelpDesk1.csv` régénéré (23 colonnes).
- `Modifié` : `notebooks/05_camembert_finetuning.ipynb` — entraînement sur `text_enriched`. **Gain enrichissement : F1 0.5325 → 0.5685 (+0.036)** ; Backup et Système passent à F1=1.00, Microsoft 0.45→0.58. Infrastructure et Sécurité restent à 0.00 (Titres de test sans équivalent sémantique en entraînement — effet du split anti-fuite).
- `Corrigé` : `models/camembert_metadata.json` et cellule métadonnées du notebook — `torch_dtype` réel **float32** (LoRA incompatible avec le scaler FP16), traçage de la feature `text_enriched` et du F1 sans enrichissement.

### Phase 3–4 — Correctifs qualité ML + Benchmark externe (2026-06-27)

#### Correction fuite de données — 03_modeling.ipynb
- `Corrigé` : split **GroupShuffleSplit par Titre** (46 train / 12 test) dans `notebooks/03_modeling.ipynb` — le modèle ne voit plus aucun Titre de test en entraînement. F1 honnête : **0.38 ML seul / 0.57 avec heuristiques** (était 1.0 artificiel).
- `Corrigé` : sélection `best_ml_name` dans la cellule d'évaluation heuristiques — filtre sur `pipelines` pour éviter un `KeyError` si `Dummy` avait le meilleur F1.
- `Modifié` : `models/model_metadata.json` — métriques, `split_strategy`, `known_weaknesses` et `dataset_note` mis à jour avec les valeurs honnêtes.
- `Ajouté` : cellule d'interprétation (`aa110028`) dans `03_modeling.ipynb` — narrative jury : GroupShuffleSplit / heuristiques / CamemBERT.

#### Benchmark externe sur données réelles publiques
- `Ajouté` : `notebooks/04_benchmark_externe.ipynb` — 17 cellules, pipeline identique à `03_modeling.ipynb` appliqué au dataset public `Tobi-Bueck/customer-support-tickets` (11 918 tickets, aucune redondance artificielle). **Résultats : TYPE (analogue Classification) F1=0.83 / QUEUE (analogue Catégorie, 10 classes) F1=0.48**.
- `Ajouté` : `data/external/similar_helpdesk_dataset.csv` — sous-ensemble anglais (11 923 lignes, 15 colonnes), ignoré par git (`data/external/` dans `.gitignore`).
- `Ajouté` : 6 figures dans `notebooks/figures/` : `bench_01_distribution_classes.png`, `bench_02_comparaison.png`, `bench_mdl_01_distribution.png`, `bench_mdl_02_benchmark_queue.png`, `bench_mdl_03_confusion_queue.png`, `bench_mdl_04_confusion_type.png`.

#### Correctifs code (audit qualité)
- `Corrigé` : `api/db/nosql_store.py` — fuite de handles fichiers TinyDB : toutes les fonctions encapsulées dans `with _open_db() as db:`.
- `Corrigé` : `src/models/heuristics.py` — règle `FORCE_RULES` Sécurité dédoublonnée (`"intrusion détectée"` redondant avec `"intrusion detectee"` après normalisation).
- `Corrigé` : `notebooks/03_modeling.ipynb` — cellules code mortes supprimées (`tfidf_shared`, `clf_lr`, `clf_svc` inutilisés).

#### EDA (01_eda.ipynb)
- `Ajouté` : section « Benchmark externe » dans `notebooks/01_eda.ipynb` — 5 cellules : introduction (table de correspondance colonnes), aperçu dataset, distribution classes, longueur textes, tableau de comparaison.

---

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
