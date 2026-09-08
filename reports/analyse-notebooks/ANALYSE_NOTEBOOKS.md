# Cartographie des notebooks — HelpDesk AI

> Analyse d'architecture, 2026-08-22. Établie par lecture du code et des sorties réellement
> enregistrées dans `helpdesk-ai/notebooks/`, confrontées aux artefacts présents dans le dépôt.
> **Aucun fichier n'a été modifié.**
>
> Convention : une affirmation non démontrée par le dépôt est marquée **« Relation à vérifier »**.

## Liste des notebooks

| Fichier | Cellules (code) | Lignes |
|---|---|---|
| `01_eda.ipynb` | 31 (27) | 627 |
| `02_preprocessing.ipynb` | 21 (12) | 216 |
| `03_modeling.ipynb` | 28 (17) | 463 |
| `04_benchmark_externe.ipynb` | 17 (9) | 174 |
| `04_rag.ipynb` | 10 (9) | 274 |
| `05_camembert_finetuning.ipynb` | 24 (12) | 393 |
| `06_rag_semantique.ipynb` | 18 (9) | 221 |
| `07_rag_evaluation.ipynb` | 16 (10) | 255 |

Deux notebooks portent le numéro **04**. Il n'existe pas de notebook 08 ni de notebook consacré
au MLOps, à ChromaDB ou au monitoring.

---

# Notebook : 01_eda.ipynb

## 1. Rôle
Première exploration du corpus brut : volumétrie, distribution de la variable cible, longueur des
textes, mots discriminants par catégorie. Il contient en outre une seconde partie sans rapport avec
l'EDA, consacrée au jeu de données public externe, et il écrit une version allégée du fichier
prétraité.

## 2. Objectif
Établir ce que contient le corpus avant toute modélisation et fournir les premières figures de
diagnostic.

## 3. Pourquoi ce notebook est nécessaire
Il répond à la question posée en ouverture du chapitre 3 du mémoire : que vaut ce corpus. Sans lui,
la redondance des 58 scénarios et le déséquilibre de facteur 5,93 resteraient invisibles.

## 4. Entrées
- `data/raw/HelpDesk1.csv` (via `params.yaml`)
- `data/external/similar_helpdesk_dataset.csv` — 11 923 lignes, 15 colonnes, 100 % anglophone
- `models/model_metadata.json` — lu et affiché, jamais écrit
- `params.yaml`

## 5. Traitements principaux
Chargement et description du corpus, distribution des huit catégories, statistiques de longueur,
tests de `clean_text` sur cinq exemples, extraction des dix termes TF-IDF les plus discriminants par
catégorie, puis comparaison structurelle avec le jeu public.

## 6. Sorties
- `data/processed/HelpDesk1.csv` — **9 colonnes seulement** : `ID`, `STATUT`, `Catégorie`, `Titre`,
  `Description`, `Résolution/Motif`, `knowledge Base`, `text_clean`, `text_rag`
- `notebooks/figures/01_distribution_cible.png`, `02_longueurs_textes.png`,
  `bench_01_distribution_classes.png`, `bench_02_comparaison.png`

## 7. Connexions avec les autres composants
Reçoit des données de : `data/raw/`, `data/external/`.
Produit des données utilisées par : aucun composant ne consomme sa version du fichier prétraité, qui
est systématiquement écrasée par `02_preprocessing` ou par `src/pipeline/preprocess.py`. Ses figures
alimentent le chapitre 3 du mémoire.

## 8. Position dans l'architecture
EDA, avec une intrusion en Data Preparation et une seconde en benchmark externe.

## 9. Cycle de vie
Exécution unique, au démarrage du projet. Il n'a pas vocation à être rejoué.

## 10. État actuel
🟡 **À améliorer.** Le contenu analytique est juste, mais le notebook écrit un artefact partagé avec
un schéma incompatible.

## 11. Ce qui doit être corrigé
- **L'écriture de `data/processed/HelpDesk1.csv` doit disparaître.** Ce notebook produit 9 colonnes
  quand les deux autres producteurs en produisent 23. L'exécuter après `dvc repro` détruit
  `text_enriched`, `priorite_simple` et `classification_simple`, ce qui casse les notebooks 03 et 05.
- La partie « benchmark externe » gagnerait à rejoindre `04_benchmark_externe.ipynb`, qui traite le
  même jeu de données.
- La cellule 23 affiche un `model_metadata.json` figé décrivant un modèle `LR_SMOTE_GridSearch` avec
  `f1_macro_cv = 1.0`, signature d'une fuite de données, et un découpage par textes uniques
  (100 / 25) et non par titres. Cette sortie est un vestige d'un protocole abandonné et induit en
  erreur quiconque relit le notebook.

## 12. Ce qui manque pour l'architecture future
Rien. Un notebook d'EDA n'a pas sa place dans une boucle automatisée. Il documente un état initial.

## 13. Captures recommandées
Voir captures **C1** et **C2**.

---

# Notebook : 02_preprocessing.ipynb

## 1. Rôle
Transforme le corpus brut en corpus exploitable : nettoyage textuel, construction des cinq variables
dérivées, analyse de la redondance, écriture du fichier prétraité.

## 2. Objectif
Produire `data/processed/HelpDesk1.csv` à 23 colonnes, l'entrée unique de toute la modélisation.

## 3. Pourquoi ce notebook est nécessaire
Il matérialise les règles de nettoyage adaptées au vocabulaire informatique, décrites au chapitre 3
§3.5.1, et fabrique `text_enriched`, dont le chapitre 4 montre qu'il apporte +0,036 de F1-macro à
CamemBERT.

## 4. Entrées
- `data/raw/HelpDesk1.csv`
- `params.yaml`
- `src/data/preprocess.py` (fonctions `clean_text`, `build_text_for_rag`)

## 5. Traitements principaux
Nettoyage, construction de `text_clean`, `text_rag`, `text_enriched`, simplification de `Priorité`
(4 → 3 niveaux) et de `Classification` (5 → 3 types), puis mesure de la redondance par catégorie.

## 6. Sorties
- `data/processed/HelpDesk1.csv` — 23 colonnes, encodage **`utf-8-sig`** (avec BOM)
- `notebooks/figures/prep_01_distribution_classes.png`, `prep_02_longueurs_avant_apres.png`,
  `prep_03_redondance_par_categorie.png`

## 7. Connexions avec les autres composants
Reçoit des données de : `data/raw/`.
Produit des données utilisées par : notebooks 03 et 05, et **en principe** tout le pipeline. En
pratique, c'est `src/pipeline/preprocess.py` qui produit le fichier réellement utilisé — le fichier
actuel a 23 colonnes et **aucun BOM**, ce qui prouve qu'il vient du script, pas du notebook.

## 8. Position dans l'architecture
Data Preparation.

## 9. Cycle de vie
À rejouer à chaque nouvelle version du dataset. **C'est précisément pourquoi il a déjà été
transformé en script** (`src/pipeline/preprocess.py`, stage DVC `preprocess`).

## 10. État actuel
🟡 **À améliorer.** Sa logique est correcte mais dupliquée dans le pipeline, ce qui crée deux
sources de vérité pour le même fichier.

## 11. Ce qui doit être corrigé
- **Divergence d'encodage** : le notebook écrit en `utf-8-sig`, le script en `utf-8`. Un fichier
  produit par le notebook porte un BOM qui se retrouve dans le nom de la première colonne à la
  relecture, avec des effets silencieux.
- **Duplication de la logique** avec `src/pipeline/preprocess.py`. Toute règle de nettoyage modifiée
  à un seul endroit crée une divergence invisible.

## 12. Ce qui manque pour l'architecture future
Rien à ajouter au notebook. Il doit devenir une **documentation exécutable** du prétraitement, le
script restant l'unique producteur. Idéalement, il importerait les fonctions du script au lieu de
les réimplémenter.

## 13. Captures recommandées
Voir captures **C3** et **C4**.

---

# Notebook : 03_modeling.ipynb

## 1. Rôle
Cœur expérimental du volet classification. Il établit le découpage anti-fuite, entraîne cinq modèles
sur vecteurs TF-IDF, mesure l'apport des heuristiques métier, analyse la calibration de la confiance
et sauvegarde le modèle retenu.

## 2. Objectif
Répondre à la question : quelle approche classique donne le meilleur F1-macro sur ce corpus, et
combien vaut l'injection de connaissance métier.

## 3. Pourquoi ce notebook est nécessaire
Il produit le modèle servi en production et fournit tous les chiffres comparatifs du chapitre 4.

## 4. Entrées
- `data/processed/HelpDesk1.csv`
- `params.yaml` (`test_size`, `random_state`, bloc `nlp`)
- `src/models/heuristics.py`

## 5. Traitements principaux
Découpage **`StratifiedShuffleSplit` appliqué aux 58 titres uniques**, stratifié par catégorie, ce
qui donne 46 titres à l'entraînement et 12 au test, soit 1 445 / 355 tickets, sans aucun titre
commun, et **8 catégories sur 8 représentées au test**. Puis entraînement de `DummyClassifier`,
`LogisticRegression + SMOTE`, `LightGBM`, `LinearSVC` calibré et d'un vote souple, évaluation du
meilleur avec les heuristiques, analyse de confiance par tranche, sauvegarde, log MLflow.

**Note importante :** le titre de la section 2 annonce « GroupShuffleSplit par Titre », mais le code
utilise `StratifiedShuffleSplit`. Le libellé est faux, le code est correct.

## 6. Sorties
- `models/best_pipeline.pkl`, `models/model_metadata.json`
- `notebooks/figures/mod_01_benchmark.png`, `mod_02_confusion_ml.png`,
  `mod_03_confusion_heuristiques.png`, `mod_04_hitl_analyse.png`
- Runs MLflow dans l'expérience `helpdesk-classification`
- Métriques : Dummy 0,0519 · LightGBM 0,3746 · LR+SMOTE 0,3746 · LinearSVC 0,3753 · vote 0,3753 ·
  LinearSVC + heuristiques **0,5673** (exactitude 0,8141)

## 7. Connexions avec les autres composants
Reçoit des données de : `02_preprocessing` ou `src/pipeline/preprocess.py`.
Produit des données utilisées par : `05_camembert_finetuning` (tableau comparatif), `api/predictor.py`
(qui charge `best_pipeline.pkl` et `model_metadata.json`), et le chapitre 4 du mémoire.

## 8. Position dans l'architecture
ML Training + ML Evaluation, avec un débordement en déploiement puisqu'il écrit directement
l'artefact servi.

## 9. Cycle de vie
Expérimental à l'origine, mais **déjà transformé en script** (`src/pipeline/train.py`). Le notebook
subsiste comme trace de la comparaison multi-modèles, que le script ne refait pas.

## 10. État actuel
🟡 **À améliorer.** Contenu scientifique solide, mais il écrit l'artefact de production.

## 11. Ce qui doit être corrigé
- **Il écrit `models/best_pipeline.pkl` et `models/model_metadata.json`**, exactement comme
  `src/pipeline/train.py`, mais sous un découpage différent (stratifié contre non stratifié). Selon
  qui a été exécuté en dernier, l'API sert un modèle dont les métadonnées décrivent l'autre
  protocole. C'est le défaut le plus grave de l'ensemble des notebooks.
- Le libellé « GroupShuffleSplit » de la section 2 doit être corrigé en « StratifiedShuffleSplit sur
  les titres ».
- La cellule 14 affiche « Objectif jury : F1-macro ≥ 0.87 », alors que l'exigence ENF-03 du cahier
  des charges est **0,85**.

## 12. Ce qui manque pour l'architecture future
Le notebook doit cesser d'écrire dans `models/`. Dans la boucle cible, l'écriture de l'artefact servi
appartient au seul `src/pipeline/promote.py`, après passage de la porte de promotion. Le notebook
resterait un banc de comparaison écrivant dans un répertoire d'expérimentation.

## 13. Captures recommandées
Voir captures **C5**, **C6**, **C7**, **C8**.

---

# Notebook : 04_benchmark_externe.ipynb

## 1. Rôle
Applique le pipeline du projet à un corpus public réel et indépendant, sur deux tâches de
granularité différente.

## 2. Objectif
Vérifier si le plafond de performance observé sur le corpus OTBS vient de la méthode ou des données.

## 3. Pourquoi ce notebook est nécessaire
C'est l'**expérience témoin** du projet. Sans elle, affirmer que la limite tient au corpus reste une
hypothèse invérifiable. C'est le notebook le plus sous-exploité du dépôt.

## 4. Entrées
- `data/external/similar_helpdesk_dataset.csv` — 11 923 lignes, 15 colonnes, 11 918 retenues,
  **99,9 % de textes uniques**
- `src/data/preprocess.py` (`clean_text`), même vectorisation TF-IDF que le notebook 03

## 5. Traitements principaux
Mise en correspondance des schémas (`subject`+`body` → texte, `queue` → cible fine analogue à
`Catégorie`, `type` → cible large analogue à `Classification`), puis entraînement des mêmes modèles
sur les deux cibles. Train 9 534 / test 2 384.

## 6. Sorties
- `notebooks/figures/bench_mdl_01_distribution.png`, `bench_mdl_02_benchmark_queue.png`,
  `bench_mdl_03_confusion_queue.png`, `bench_mdl_04_confusion_type.png`
- Métriques : `queue` 10 classes → LinearSVC 0,4071 · LR+SMOTE 0,4127 · **LightGBM 0,4780**
  (exactitude 0,5214) ; `type` 4 classes ITIL → **0,8328** (exactitude 0,8372)
- Aucun modèle sauvegardé

## 7. Connexions avec les autres composants
Reçoit des données de : `data/external/`.
Produit des données utilisées par : le chapitre 3 §3.2.3 du mémoire pour la seule partie
structurelle. **Ses résultats de modélisation ne sont exploités nulle part.**

## 8. Position dans l'architecture
ML Evaluation, en validation externe.

## 9. Cycle de vie
Exécution unique. À rejouer seulement si le pipeline de nettoyage change substantiellement.

## 10. État actuel
🟢 **Correct et exploitable**, et nettement sous-utilisé.

## 11. Ce qui doit être corrigé
- Le notebook signale `overlap train/test : 2`. Deux textes communs sur 11 918 sont négligeables mais
  doivent être mentionnés si les chiffres entrent au mémoire.
- Le numéro 04 est partagé avec `04_rag.ipynb`. À renuméroter.

## 12. Ce qui manque pour l'architecture future
Rien. C'est une référence externe figée, dont la valeur tient précisément à ce qu'elle ne bouge pas.

## 13. Captures recommandées
Voir capture **C9**, la plus importante du dépôt après la matrice de confusion CamemBERT.

---

# Notebook : 04_rag.ipynb

## 1. Rôle
Construit la première version du moteur de recherche : similarité cosinus sur vecteurs TF-IDF, avec
filtrage par catégorie et repli.

## 2. Objectif
Retrouver dans l'historique les tickets dont la résolution peut servir à un ticket entrant.

## 3. Pourquoi ce notebook est nécessaire
Il fonde le second volet de la solution. Il exploite la redondance du corpus, que le volet
classification subit.

## 4. Entrées
- Base de connaissances issue des tickets résolus
- `params.yaml` (`rag.top_k`, `rag.similarity_threshold`)
- `src/rag/engine.py`

## 5. Traitements principaux
Ajustement du `RAGEngine` lexical sur la base de connaissances, puis tests qualitatifs sur des
tickets types (Office 365, Sage X3, sauvegarde, internet lent) avec affichage des scores et des
résolutions proposées.

## 6. Sorties
- `models/rag_engine.pkl`
- Aucune figure, aucune métrique agrégée

## 7. Connexions avec les autres composants
Reçoit des données de : le fichier prétraité, filtré sur les tickets résolus.
Produit des données utilisées par : `api/predictor.py` en repli lexical, et `HybridRAGEngine` comme
composante lexicale du score hybride.

## 8. Position dans l'architecture
RAG, version 1.

## 9. Cycle de vie
**Déjà transformé en script** (`src/pipeline/rag_build.py`, stage DVC `rag_build`).

## 10. État actuel
🟡 **À améliorer.** Il produit un artefact servi en production sans aucune métrique.

## 11. Ce qui doit être corrigé
- **Aucune évaluation quantitative.** Le notebook montre quatre exemples choisis et s'arrête. Rien ne
  permet de dire si le moteur est bon.
- Il n'a qu'un seul titre de section pour 274 lignes de code, ce qui le rend difficile à relire.
- L'artefact `models/rag_engine.pkl` actuel contient **1 357 tickets**, produit par le script à
  partir de `data/splits/rag.csv`. La base utilisée par le notebook n'est pas explicitée dans ses
  sorties. **Relation à vérifier.**

## 12. Ce qui manque pour l'architecture future
Il est déjà remplacé par le stage DVC. Dans la boucle RAG cible, la construction de l'index lexical
reste une étape hors ligne, mais l'évaluation associée doit exister, ce que couvre désormais
`src/pipeline/rag_eval.py`.

## 13. Captures recommandées
Voir capture **C10**.

---

# Notebook : 05_camembert_finetuning.ipynb

## 1. Rôle
Adapte un modèle de langue français à la tâche de classification, sous forte contrainte matérielle.

## 2. Objectif
Déterminer si une représentation contextuelle dépasse la combinaison TF-IDF et règles métier.

## 3. Pourquoi ce notebook est nécessaire
Il teste l'hypothèse H1 du cahier des charges, qui postule que CamemBERT fine-tuné surpasse la
baseline. Le résultat infirme cette hypothèse, ce qui est le résultat scientifique central du
chapitre 4.

## 4. Entrées
- `data/processed/HelpDesk1.csv`, colonne `text_enriched`
- `params.yaml`
- `camembert-base` téléchargé depuis Hugging Face
- Découpage identique à celui du notebook 03

## 5. Traitements principaux
Découpage stratifié par titre, second découpage pour la validation (1 300 / 145 / 355), tokenisation
à 128 jetons, insertion d'adaptateurs LoRA de rang 8 et de facteur 16 sur les modules requête et
valeur, entraînement sur 10 époques avec arrêt anticipé, précision réduite et point de contrôle de
gradient, évaluation, analyse de confiance, comparaison à la baseline.

## 6. Sorties
- `models/camembert_lora_adapter/`, `models/camembert_metadata.json`
- `notebooks/figures/cam_01_confusion.png`, `cam_02_confiance.png`, `cam_03_benchmark.png`
- Runs MLflow
- Métriques : F1-macro **0,5685**, exactitude 0,6873 ; sans `text_enriched` 0,5325 / 0,6451 ;
  891 656 paramètres entraînables sur 111 519 760, soit **0,80 %** ; 447 Mo de VRAM sur 2 147 ;
  1 630 pas ; routage à 0,40 → 323 tickets (91,0 %) à 69,97 % de précision

## 7. Connexions avec les autres composants
Reçoit des données de : le fichier prétraité, et les résultats du notebook 03 pour la comparaison.
Produit des données utilisées par : le chapitre 4 du mémoire. **L'adaptateur n'est chargé par aucun
composant de l'application** — vérifié par recherche sur `api/`.

## 8. Position dans l'architecture
ML Training + ML Evaluation, en expérimentation.

## 9. Cycle de vie
Expérimental, exécuté deux fois (avec et sans enrichissement du texte). Aucune vocation à
l'automatisation tant que le corpus ne gagne pas en diversité.

## 10. État actuel
🟢 **Correct et exploitable.** C'est le notebook le mieux structuré du dépôt.

## 11. Ce qui doit être corrigé
- `camembert_metadata.json` porte `"split_strategy": "GroupShuffleSplit par Titre"`, ce qui est
  **faux** : le code applique `StratifiedShuffleSplit` sur les titres. Cette étiquette a induit en
  erreur toute la documentation du projet et se retrouve sur l'axe de `cam_03_benchmark.png`.
- La même figure affiche « Cible ≥ 0.80 » quand l'exigence ENF-03 vaut 0,85.

## 12. Ce qui manque pour l'architecture future
Si CamemBERT devait un jour entrer en production, il faudrait qu'il traverse la même porte de
promotion que la chaîne TF-IDF, donc que `promote.py` sache évaluer un artefact non scikit-learn.
Ce n'est pas le cas aujourd'hui, et ce n'est pas urgent.

## 13. Captures recommandées
Voir captures **C11**, **C12**, **C13**.

---

# Notebook : 06_rag_semantique.ipynb

## 1. Rôle
Construit la deuxième version du moteur de recherche : embeddings de phrases et index FAISS, avec un
index par catégorie.

## 2. Objectif
Dépasser la recherche lexicale, incapable de rapprocher deux formulations qui ne partagent aucun mot.

## 3. Pourquoi ce notebook est nécessaire
La recherche par mots-clés échoue sur un corpus où le même incident se décrit de vingt manières.

## 4. Entrées
- `data/splits/rag.csv`
- `params.yaml`
- `paraphrase-multilingual-mpnet-base-v2` (768 dimensions)
- `src/rag/semantic_engine.py`

## 5. Traitements principaux
Encodage de la base de connaissances, construction d'un index FAISS global et de huit index par
catégorie, tests qualitatifs, évaluation en held-out, comparaison au moteur lexical.

## 6. Sorties
- `models/semantic_rag/` : `index.faiss`, huit `index_cat_*.faiss`, `knowledge_base.parquet`,
  `metadata.json`
- `models/semantic_rag_metadata.json` (à la racine de `models/`)
- `notebooks/figures/rag6_01_comparaison.png`
- Métriques annoncées : score moyen top-1 sémantique **0,9321** contre lexical **0,7646**, gain 0,1675

## 7. Connexions avec les autres composants
Reçoit des données de : `data/splits/rag.csv`, produit par le stage `split`.
Produit des données utilisées par : `api/predictor.py`, qui charge `models/semantic_rag/` et
construit le moteur hybride servi en production.

## 8. Position dans l'architecture
RAG, version 2. C'est le composant de recherche réellement servi.

## 9. Cycle de vie
Transformé en script (`src/pipeline/rag_semantic_build.py`), lequel n'était **pas déclaré dans
`dvc.yaml`** jusqu'aux travaux d'industrialisation d'août 2026.

## 10. État actuel
🔴 **Problématique**, pour des raisons de traçabilité et non de contenu.

## 11. Ce qui doit être corrigé
- **Les cellules 10 à 17 n'ont aucune sortie enregistrée.** Toute la section d'évaluation et de
  comparaison est vide dans l'état sauvegardé. Les chiffres 0,9321 et 0,7646 n'existent que dans un
  fichier de métadonnées ; rien dans le notebook ne montre comment ils ont été obtenus.
- **`models/semantic_rag_metadata.json` est périmé.** Il annonce `n_tickets_indexed: 476` et
  `similarity_threshold: 0.3`, alors que l'index réellement servi contient **1 357 tickets** et que
  la production applique un seuil de **0,50**. Le fichier faisant autorité est
  `models/semantic_rag/metadata.json`, produit par le script. Deux fichiers de métadonnées décrivent
  le même artefact et se contredisent.
- **Conséquence pour le mémoire** : la comparaison « 0,93 contre 0,76 » prévue au chapitre 5 porte
  sur un index de 476 tickets qui n'est plus celui servi. Elle doit être recalculée ou explicitement
  datée.

## 12. Ce qui manque pour l'architecture future
Dans la boucle RAG cible, cet index statique reste la couche historique. Ce qui manque autour de lui,
la validation des connaissances, le versionnement et l'indexation en direct, est traité par
`src/knowledge/` et `api/db/vector_store.py`, hors notebooks.

## 13. Captures recommandées
Voir capture **C14**.

---

# Notebook : 07_rag_evaluation.ipynb

## 1. Rôle
Évalue le système de recherche : métriques de retrieval, comparaison lexical contre sémantique,
génération de réponse avec citations, métriques RAGAS simplifiées.

## 2. Objectif
Chiffrer la qualité du RAG plutôt que de la constater sur des exemples choisis.

## 3. Pourquoi ce notebook est nécessaire
Les notebooks 04_rag et 06 ne produisent que des démonstrations qualitatives. Celui-ci est le seul à
produire des métriques.

## 4. Entrées
- `models/semantic_rag/`, `models/semantic_rag/knowledge_base.parquet`
- Le moteur lexical, pour la comparaison

## 5. Traitements principaux
Construction d'un jeu d'évaluation de 80 requêtes stratifiées, calcul de précision@3, rappel@3,
MRR@3 et nDCG@3, comparaison des deux moteurs, génération de réponses avec citations numérotées,
puis métriques RAGAS.

## 6. Sorties
- `metrics/rag_eval.json`
- `notebooks/figures/07_rag_evaluation_metrics.png`, `07_answer_relevancy_dist.png`,
  `07_ragas_summary.png`
- Métriques : précision@3 0,3042 sémantique contre 0,4208 lexical ; MRR@3 0,5646 contre 0,6521 ;
  nDCG@3 0,3505 contre 0,4520 ; fidélité 1,0 ; taux d'hallucination 0,0

## 7. Connexions avec les autres composants
Reçoit des données de : les deux moteurs construits en amont.
Produit des données utilisées par : le chapitre 5 du mémoire.

## 8. Position dans l'architecture
RAG Evaluation.

## 9. Cycle de vie
Devrait être rejoué à chaque évolution de la base de connaissances. **Transformé en script en août
2026** (`src/pipeline/rag_eval.py`, stage DVC `rag_eval`).

## 10. État actuel
🔴 **Problématique.**

## 11. Ce qui doit être corrigé
- **Aucune cellule du notebook ne possède de sortie.** Il est intégralement non exécuté dans son état
  sauvegardé, alors que `metrics/rag_eval.json` et trois figures existent. Les résultats du chapitre 5
  ne sont donc pas reproductibles depuis le notebook.
- Le protocole retient « même catégorie = pertinent », ce qui rend le **rappel@3 ininterprétable** :
  avec des centaines de documents pertinents par requête, il vaut mécaniquement 3 sur plusieurs
  centaines. La valeur 0,0277 publiée n'est pas une mesure de qualité.
- L'évaluation interroge les moteurs avec `allow_fallback=False`, une configuration que la production
  n'utilise pas.
- **La fidélité de 1,0 est vraie par construction** : la génération est fondée sur un gabarit, pas sur
  un modèle de langue libre. Le plan du mémoire le signale déjà, et c'est correct.
- Le moteur **hybride**, seul réellement servi en production, n'est pas évalué.

## 12. Ce qui manque pour l'architecture future
Un **jeu de requêtes annoté par un administrateur**. Tant qu'il n'existe pas, aucune métrique de
pertinence du RAG n'est défendable. `src/pipeline/rag_eval.py --build-template` génère les 80
requêtes à annoter ; c'est environ une demi-journée de travail.

## 13. Captures recommandées
Aucune capture de ce notebook n'est recommandée en l'état, puisqu'il ne contient aucune sortie. Les
figures `07_*.png` existent et peuvent être utilisées, mais les métriques qu'elles portent doivent
être recalculées avec le protocole corrigé avant publication.

---

# Carte des dépendances

## Pipeline ML

```
data/raw/HelpDesk1.csv
      ↓
01_eda.ipynb ──────────► figures de diagnostic          (branche morte pour les données :
      │                                                   son écriture est écrasée)
      ↓
02_preprocessing.ipynb ═══► data/processed/HelpDesk1.csv (23 colonnes)
      ║                          ▲
      ║                          ║  MÊME FICHIER, trois producteurs
      ╚══ src/pipeline/preprocess.py (stage DVC, producteur réel)
                                 ↓
                    StratifiedShuffleSplit sur les 58 titres
                          46 titres / 12 titres
                          1 445 / 355 tickets, 8 classes
                                 ↓
              ┌──────────────────┴──────────────────┐
              ↓                                     ↓
      03_modeling.ipynb                   05_camembert_finetuning.ipynb
      Dummy 0,0519                        CamemBERT + LoRA 0,5685
      LinearSVC 0,3753                    (adaptateur jamais chargé par l'application)
      + heuristiques 0,5673
              ↓                                     ↓
      models/best_pipeline.pkl ◄══ CONFLIT ══ src/pipeline/train.py
      models/model_metadata.json               (découpage NON stratifié, 5/8 classes)
              ↓
      api/predictor.py  →  PRODUCTION

      04_benchmark_externe.ipynb ──► validation externe de la méthode
      (jeu public, 99,9 % de textes uniques : type 0,8328 · queue 0,4780)
      → aucun consommateur dans le dépôt
```

## Pipeline RAG

```
data/splits/rag.csv  (1 357 tickets, produit par le stage split)
      ↓
      ├─► 04_rag.ipynb ──────► models/rag_engine.pkl        (lexical TF-IDF)
      │        ║                        ▲
      │        ╚══ src/pipeline/rag_build.py (stage DVC)
      │
      └─► 06_rag_semantique.ipynb ─► models/semantic_rag/    (FAISS + mpnet, 1 357)
               ║                     models/semantic_rag_metadata.json (PÉRIMÉ : 476)
               ╚══ src/pipeline/rag_semantic_build.py
                                 ↓
                    api/predictor.py → HybridRAGEngine (0,5 lex + 0,5 sém)
                                 ↓
                          07_rag_evaluation.ipynb → metrics/rag_eval.json
                          (non exécuté ; n'évalue pas le moteur hybride)
```

## Pipeline MLOps cible — couverture par les notebooks

```
PostgreSQL
   ↓ tickets validés            🔴 aucun notebook ne lit PostgreSQL
   ↓ dataset candidat           🔴 aucun notebook
   ↓ contrôle qualité           🔴 aucun notebook
   ↓ versionnement              🔴 aucun notebook n'appelle DVC
   ↓ entraînement               🟢 notebooks 03 et 05
   ↓ tracking                   🟡 MLflow présent, deux expériences distinctes
   ↓ évaluation                 🟢 notebooks 03 et 05
   ↓ promotion / rejet          🔴 aucun notebook
   ↓ production                 🔴 écriture directe, sans porte
```

Les étapes en rouge sont couvertes par `src/` depuis les travaux d'industrialisation. **Aucune
n'appartient à un notebook, et aucune ne devrait y appartenir.**

---

# Tableau global

| Notebook | Entrées | Sorties | Utilisé par | Domaine | Statut |
|---|---|---|---|---|---|
| `01_eda` | raw, external, `model_metadata.json` | processed (9 col.), 4 figures | mémoire ch.3 | EDA | 🟡 |
| `02_preprocessing` | raw, params | processed (23 col., BOM), 3 figures | nb 03, 05 | Data Preparation | 🟡 |
| `03_modeling` | processed, heuristics | `best_pipeline.pkl`, `model_metadata.json`, 4 figures, MLflow | API, nb 05, ch.4 | ML Training + Eval | 🟡 |
| `04_benchmark_externe` | external | 4 figures | rien | ML Evaluation | 🟢 |
| `04_rag` | tickets résolus, params | `rag_engine.pkl` | API (repli lexical) | RAG v1 | 🟡 |
| `05_camembert` | processed, `camembert-base` | adaptateur LoRA, metadata, 3 figures, MLflow | ch.4 | ML Training + Eval | 🟢 |
| `06_rag_semantique` | `rag.csv`, mpnet | `semantic_rag/`, metadata, 1 figure | API (moteur servi) | RAG v2 | 🔴 |
| `07_rag_evaluation` | moteurs RAG | `rag_eval.json`, 3 figures | ch.5 | RAG Evaluation | 🔴 |

---

# Problèmes d'architecture détectés

### P1 — Trois producteurs pour `data/processed/HelpDesk1.csv`
**Impact.** `01_eda` écrit 9 colonnes, `02_preprocessing` 23 colonnes avec BOM,
`src/pipeline/preprocess.py` 23 colonnes sans BOM. Exécuter `01_eda` après le pipeline détruit
`text_enriched` et casse les notebooks 03 et 05 sans message clair.
**Gravité. 🔴 Élevée.**
**Solution.** Retirer l'écriture du notebook 01. Faire de `02_preprocessing` une documentation qui
importe les fonctions du script au lieu de les réimplémenter. Un seul producteur : le stage DVC.

### P2 — Deux producteurs pour le modèle servi
**Impact.** `03_modeling` et `src/pipeline/train.py` écrivent tous deux `models/best_pipeline.pkl` et
`models/model_metadata.json`, sous **deux découpages différents**. Selon l'ordre d'exécution, l'API
sert un modèle dont les métadonnées décrivent l'autre protocole, avec un seuil de confiance et une
liste de classes possiblement incohérents.
**Gravité. 🔴 Élevée.**
**Solution.** Le notebook écrit dans `models/experiments/`. L'écriture de l'artefact servi appartient
au seul `src/pipeline/promote.py`.

### P3 — Notebooks d'évaluation RAG sans sorties enregistrées
**Impact.** `07_rag_evaluation` est intégralement vide de sorties, `06_rag_semantique` l'est de la
cellule 10 à la fin. Les chiffres du chapitre 5 ne sont donc reproductibles depuis aucun notebook.
Un jury qui demanderait à voir l'exécution ne trouverait rien.
**Gravité. 🔴 Élevée** pour un mémoire.
**Solution.** Réexécuter les deux notebooks et committer les sorties, ou renvoyer explicitement le
chapitre 5 vers le stage DVC `rag_eval` comme source des chiffres.

### P4 — Deux fichiers de métadonnées contradictoires pour l'index sémantique
**Impact.** `models/semantic_rag_metadata.json` annonce 476 tickets et un seuil de 0,3 ;
`models/semantic_rag/metadata.json` annonce 1 357 tickets, et c'est lui qui décrit l'index servi. Le
chiffre « 0,93 contre 0,76 » prévu au chapitre 5 vient du premier, donc d'un index périmé.
**Gravité. 🟠 Moyenne**, élevée si le chiffre est publié tel quel.
**Solution.** Supprimer le fichier racine, ou le dater explicitement. Recalculer la comparaison sur
l'index à 1 357 tickets avant publication.

### P5 — MLflow mélange deux protocoles incompatibles
**Impact.** L'expérience `helpdesk-classification` contient 53 runs. Certains proviennent d'un
protocole abandonné, reconnaissable à `f1_macro_cv = 1.0` et à une exactitude de 0,7702, où le
découpage se faisait sur les textes uniques et non sur les titres, donc **avec fuite**. Rien ne les
distingue des runs valides sans connaître l'historique du projet.
**Gravité. 🟠 Moyenne.**
**Solution.** Marquer les runs par une étiquette de protocole, ou archiver l'expérience ancienne.
`src/pipeline/train.py` écrit déjà dans une expérience distincte, `helpdesk-ai-classification`.

### P6 — Étiquette de découpage fausse, propagée dans toute la documentation
**Impact.** Le notebook 03 intitule sa section « GroupShuffleSplit par Titre » et
`camembert_metadata.json` porte la même mention, alors que le code applique un
`StratifiedShuffleSplit` sur les titres. Cette erreur d'étiquette s'est propagée jusque dans les
figures et a fait croire pendant des mois que les notebooks utilisaient le découpage du pipeline.
**Gravité. 🟠 Moyenne.**
**Solution.** Corriger les libellés. Le code est juste, seule l'étiquette ment.

### P7 — Deux notebooks numérotés 04
**Impact.** `04_benchmark_externe` et `04_rag` traitent des sujets sans rapport. L'ordre d'exécution
est ambigu pour un lecteur extérieur.
**Gravité. 🟡 Faible.**
**Solution.** Renuméroter le benchmark externe en 08, ou le placer dans un sous-dossier `benchmarks/`.

### P8 — Le notebook 04_rag ne produit aucune métrique
**Impact.** Il construit un artefact servi en production à partir de quatre exemples qualitatifs.
Aucun élément ne permet de juger sa qualité.
**Gravité. 🟡 Faible**, puisque le notebook 07 comble partiellement le manque.
**Solution.** S'appuyer sur le stage `rag_eval`, qui évalue désormais les trois moteurs.

### P9 — Objectif chiffré incohérent dans le notebook 03
**Impact.** La cellule 14 imprime « Objectif jury : F1-macro ≥ 0.87 » quand ENF-03 vaut 0,85. La
figure `cam_03_benchmark.png` affiche pour sa part 0,80. Trois valeurs pour un même objectif.
**Gravité. 🟡 Faible**, mais visible en soutenance.
**Solution.** Aligner sur 0,85, valeur du cahier des charges.

### P10 — Chevauchement résiduel dans le benchmark externe
**Impact.** `overlap train/test : 2` sur 11 918 tickets. Effet négligeable sur les métriques.
**Gravité. 🟡 Faible.**
**Solution.** Mentionner le chiffre si les résultats entrent au mémoire.

---

# Cohérence avec l'architecture cible

## Boucle ML

| Étape | Notebooks | Couverture globale du dépôt |
|---|---|---|
| PostgreSQL → tickets validés | 🔴 absent | 🟢 `src/pipeline/collect.py` |
| Sélection et contrôle qualité | 🔴 absent | 🟢 `collect.py` (force de l'étiquette) |
| Dataset ML | 🟡 nb 02 produit un fichier, sans version | 🟢 `build_dataset.py` |
| DVC | 🔴 aucun notebook | 🟢 `dvc.yaml` |
| Entraînement | 🟢 nb 03, nb 05 | 🟢 `train.py` |
| MLflow | 🟡 deux expériences, runs mêlés | 🟡 même réserve |
| Évaluation | 🟢 nb 03, nb 05 | 🟢 `train.py` |
| Comparaison ancien / nouveau | 🟡 nb 05 §8, manuelle | 🟢 `promote.py` |
| Model Registry | 🔴 absent | 🟢 `src/registry/` |
| Promotion / rejet | 🔴 absent | 🟢 `promote.py` |
| Modèle en production | 🔴 écriture directe, sans porte | 🟢 `promote.py` |

## Boucle RAG

| Étape | Notebooks | Couverture globale du dépôt |
|---|---|---|
| PostgreSQL → tickets résolus | 🔴 absent | 🟢 `api/routers/tickets.py` |
| Contrôle qualité | 🔴 absent | 🟢 `src/knowledge/quality.py` |
| Knowledge dataset versionné | 🔴 absent | 🟢 `src/knowledge/snapshot.py` |
| Embeddings | 🟢 nb 06 | 🟢 `rag_semantic_build.py` |
| ChromaDB | 🔴 aucun notebook | 🟢 `api/db/vector_store.py` |
| Évaluation RAG | 🟡 nb 07 non exécuté | 🟢 `rag_eval.py` |
| Monitoring | 🔴 absent | 🟢 `src/monitoring/rag_monitor.py` |

**Conclusion.** Les notebooks couvrent l'expérimentation ML et la construction des index. Ils ne
couvrent aucune étape des deux boucles d'amélioration continue, et il n'y a pas lieu de les y faire
entrer : une boucle automatisée n'a pas sa place dans un notebook.

---

# Classification par nature

| Notebook | Type | Justification |
|---|---|---|
| `01_eda` | **A** — Exploration | Décrit, ne décide rien. Son écriture de données est un accident. |
| `02_preprocessing` | **E + H** — Préparation, à transformer | Déjà transformé en `preprocess.py`. Le notebook doit devenir documentation. |
| `03_modeling` | **B + C + D + H** | Expérimentation, entraînement, évaluation. Sa partie production est déjà dans `train.py`. |
| `04_benchmark_externe` | **B** — Expérimentation | Référence externe figée. Ne doit pas être automatisée. |
| `04_rag` | **F + H** | Déjà transformé en `rag_build.py`. |
| `05_camembert` | **B + C + D** | Expérimentation pure. L'adaptateur n'est pas servi. |
| `06_rag_semantique` | **F + H** | Déjà transformé en `rag_semantic_build.py`. |
| `07_rag_evaluation` | **D + F + H** | Déjà transformé en `rag_eval.py`. |

Cinq notebooks sur huit ont déjà un équivalent en script. Le risque « toute la logique de production
enfermée dans des notebooks » est donc **largement écarté**. Le risque restant est inverse et bien
réel : **les notebooks et les scripts coexistent en écrivant les mêmes fichiers** (P1 et P2).

---

# Captures recommandées pour le rapport

## Chapitre 3 — Données et gouvernance

### C1 — Distribution des catégories ⭐⭐⭐
- **Notebook** : `01_eda` (ou figure `dq_01_distribution_classes.png`, déjà utilisée)
- **À capturer** : le diagramme en barres des huit catégories
- **On voit** : Microsoft 409, Réseau 369, jusqu'à Sécurité 73 et Backup 69
- **Cela prouve** : le déséquilibre de facteur 5,93 qui justifie le choix du F1-macro
- **Titre** : Répartition des tickets par catégorie
- **Statut** : déjà insérée au mémoire (figure 3.1)

### C2 — Comparaison avec le jeu public ⭐⭐⭐
- **Notebook** : `01_eda`, section « Benchmark externe »
- **À capturer** : `bench_02_comparaison.png`, ou le chiffre 91 % contre 3 % de titres uniques
- **On voit** : deux corpus de support, l'un à 10 891 titres pour 11 923 tickets, l'autre à 58 pour 1 800
- **Cela prouve** : la redondance du corpus OTBS est anormale, et non une propriété du domaine
- **Pourquoi c'est important** : c'est le seul élément extérieur qui valide le diagnostic de redondance
- **Titre** : Diversité lexicale comparée au corpus public
- **Chapitre** : 3, §3.2.3

### C3 — Redondance du corpus ⭐⭐⭐
- **Notebook** : `02_preprocessing`, section 5
- **À capturer** : `prep_03_redondance_par_categorie.png` ou `dq_04_redondance.png`
- **On voit** : 1 800 lignes, 1 535 descriptions distinctes, 58 titres distincts
- **Cela prouve** : le corpus s'organise en scénarios répétés, ce qui commande tout le protocole
- **Titre** : Diversité du corpus : lignes, descriptions et titres distincts
- **Statut** : déjà insérée (figure 3.2)

### C4 — Effet du nettoyage sur la longueur des textes ⭐⭐
- **Notebook** : `02_preprocessing`, section 7
- **À capturer** : `prep_02_longueurs_avant_apres.png`
- **On voit** : la distribution avant et après nettoyage
- **Cela prouve** : le prétraitement ne détruit pas le signal, contrairement à la première version
  décrite au §3.5.1
- **Titre** : Longueur des descriptions avant et après nettoyage
- **Chapitre** : 3, §3.5.1

## Chapitre 4 — Modélisation

### C5 — Benchmark des approches ⭐⭐⭐
- **Notebook** : `03_modeling` section 5, ou la figure corrigée `ch04_benchmark.png`
- **À capturer** : le graphique en barres des sept approches
- **On voit** : Dummy 0,0519, les modèles lexicaux groupés à 0,375, les heuristiques et CamemBERT à
  0,568, la cible à 0,85 hors d'atteinte
- **Cela prouve** : quatre familles de modèles butent sur le même plafond
- **Titre** : Comparaison des approches de classification
- **Statut** : déjà insérée (figure 4.2). **Ne pas utiliser `cam_03_benchmark.png`**, dont l'axe et
  la cible sont faux.

### C6 — Matrice de confusion sans heuristiques ⭐⭐
- **Notebook** : `03_modeling` section 6, `mod_02_confusion_ml.png`
- **On voit** : quatre catégories entièrement ignorées par le modèle
- **Cela prouve** : le modèle lexical n'échoue pas à la marge, il abandonne la moitié du référentiel
- **Titre** : Matrice de confusion du modèle lexical seul
- **Chapitre** : 4, §4.3.3

### C7 — Gain des heuristiques ⭐⭐⭐
- **Notebook** : `03_modeling` section 6, `mod_03_confusion_heuristiques.png`
- **On voit** : Infrastructure et Microsoft passent d'un F1 nul à 1,00 et 0,86
- **Cela prouve** : la connaissance métier rend des catégories que l'apprentissage abandonnait
- **Pourquoi c'est important** : c'est le gain le plus important du chapitre, +0,192
- **Titre** : Matrice de confusion après application des règles métier
- **Chapitre** : 4, §4.4.3

### C8 — Calibration de la confiance ⭐⭐
- **Notebook** : `03_modeling` section 7, `mod_04_hitl_analyse.png`
- **On voit** : la précision par tranche, dont l'anomalie 89,1 % puis 81,7 %
- **Cela prouve** : le score de confiance sépare les extrêmes mais n'est pas monotone
- **Titre** : Précision observée par tranche de confiance
- **Chapitre** : 4, §4.6.4

### C9 — Validation externe de la méthode ⭐⭐⭐
- **Notebook** : `04_benchmark_externe`, sections 5 à 7
- **À capturer** : le tableau de synthèse, ou `bench_mdl_02_benchmark_queue.png`
- **On voit** : le même pipeline atteint 0,833 sur `type` (4 classes) et 0,478 sur `queue`
  (10 classes chevauchantes), sur 11 918 tickets à 99,9 % uniques
- **Cela prouve deux choses** : la méthode n'est pas en cause, puisqu'elle atteint 0,83 sur des
  données diverses ; et le routage fin sur classes chevauchantes est intrinsèquement difficile, ce
  qui relativise l'objectif de 0,85
- **Pourquoi c'est important** : c'est l'argument le plus difficile à contester du mémoire, et il
  n'y figure pas encore
- **Titre** : Validation du pipeline sur un corpus public indépendant
- **Chapitre** : 4, section à créer avant le bilan

### C11 — Matrice de confusion CamemBERT ⭐⭐⭐
- **Notebook** : `05_camembert_finetuning` section 6, `cam_01_confusion.png`
- **On voit** : Réseau absorbe 21 Infrastructure, 19 Sécurité et 45 Microsoft ; Microsoft se scinde
  exactement en 48 corrects et 45 erreurs, soit les deux scénarios du jeu de test
- **Cela prouve** : la décision se joue au niveau du scénario et non du ticket
- **Titre** : Matrice de confusion de CamemBERT adapté par LoRA
- **Statut** : déjà insérée (figure 4.1)

### C12 — Empreinte mémoire de l'adaptation LoRA ⭐⭐
- **Notebook** : `05_camembert_finetuning` cellule 8
- **À capturer** : la sortie `trainable params: 891,656 || all params: 111,519,760 || trainable%:
  0.7995` suivie de `GPU mémoire utilisée : 447 MB / 2147 MB`
- **Cela prouve** : l'adaptation d'un modèle de 110 millions de paramètres sur un GPU de 2 Go
- **Pourquoi c'est important** : c'est la justification chiffrée du choix de LoRA, contrainte
  matérielle réelle du stage
- **Titre** : Paramètres entraînables et occupation mémoire de l'adaptation LoRA
- **Chapitre** : 4, §4.5.2

### C13 — Distribution des scores de confiance ⭐
- **Notebook** : `05_camembert_finetuning` section 7, `cam_02_confiance.png`
- **Titre** : Distribution des scores de confiance et seuil de routage
- **Statut** : déjà insérée (figure 4.3)

## Chapitre 5 — Système RAG

### C10 — Recherche lexicale, exemples ⭐⭐
- **Notebook** : `04_rag` cellule 4
- **À capturer** : les quatre tickets de test avec leurs scores et résolutions proposées
- **On voit** : Office 365 à 0,4827, Sage X3 à 0,1847, sauvegarde à 0,4435
- **Cela prouve** : la recherche lexicale fonctionne quand le vocabulaire coïncide et s'effondre
  sinon, ce qui motive le passage au sémantique
- **Titre** : Recommandations du moteur lexical sur quatre cas types
- **Chapitre** : 5, §5.3.2

### C14 — Comparaison lexical contre sémantique ⭐⭐⭐
- **Notebook** : `06_rag_semantique` sections 4 et 6
- **À capturer** : les mêmes quatre tickets qu'en C10, avec leurs scores sémantiques
- **On voit** : Office 365 passe de 0,4827 à 0,7845, Sage X3 de 0,1847 à 0,6429
- **Cela prouve** : le moteur sémantique rapproche des formulations que le lexical manque
- **Pourquoi c'est important** : c'est une comparaison à cas identiques, donc directement lisible
- **Titre** : Scores de similarité, moteur lexical et moteur sémantique
- **Chapitre** : 5, §5.4.3
- **Réserve** : ne pas reprendre le chiffre agrégé « 0,93 contre 0,76 » de
  `semantic_rag_metadata.json`, calculé sur un index périmé de 476 tickets. Les exemples
  ticket par ticket, eux, restent valides.

## Chapitre 7 — Industrialisation

### C15 — Graphe du pipeline DVC ⭐⭐⭐
- **Source** : `dvc dag`
- **On voit** : les huit stages, et les deux chaînes qui partent de `split` sans se rejoindre
- **Cela prouve** : la séparation stricte entre la boucle classification et la boucle connaissances
- **Titre** : Graphe d'exécution du pipeline de données
- **Chapitre** : 7

### C16 — Registre de modèles et décision de promotion ⭐⭐⭐
- **Source** : `python src/pipeline/promote.py --list`
- **On voit** : les versions, leur métrique, leur dataset et l'alias de production
- **Cela prouve** : un candidat identique au modèle servi est rejeté, la porte fonctionne
- **Titre** : Registre des versions et arbitrage de promotion
- **Chapitre** : 7

### C17 — Suivi MLflow ⭐⭐
- **Source** : interface MLflow sur l'expérience `helpdesk-ai-classification`
- **On voit** : les runs successifs avec leurs paramètres et métriques
- **Réserve** : montrer l'expérience `helpdesk-ai-classification`, **pas**
  `helpdesk-classification`, qui contient des runs d'un protocole avec fuite
- **Titre** : Traçabilité des expériences d'entraînement
- **Chapitre** : 7

---

# Les dix captures à retenir si le nombre doit être réduit

| # | Capture | Ce qu'elle démontre | Chapitre |
|---|---|---|---|
| 1 | **C1** Distribution des catégories | Le déséquilibre qui commande le choix de la métrique | 3 |
| 2 | **C3** Redondance du corpus | 58 scénarios pour 1 800 tickets : la limite structurelle | 3 |
| 3 | **C2** Comparaison au corpus public | Cette redondance est anormale, preuve extérieure | 3 |
| 4 | **C5** Benchmark des approches | Quatre familles de modèles, un seul plafond | 4 |
| 5 | **C7** Confusion après heuristiques | Le gain de +0,192, et d'où il vient | 4 |
| 6 | **C11** Confusion CamemBERT | La décision se joue au scénario, pas au ticket | 4 |
| 7 | **C9** Validation externe | La méthode atteint 0,83 quand les données sont diverses | 4 |
| 8 | **C14** Lexical contre sémantique | Le gain du RAG sémantique sur cas identiques | 5 |
| 9 | **C15** Graphe DVC | Les deux boucles, séparées et reproductibles | 7 |
| 10 | **C16** Registre et promotion | Le modèle de production est protégé par une porte | 7 |

Les captures 1, 2, 4, 5, 6 et 8 sont déjà produites. La 3 existe en figure mais mérite d'être
refaite pour le mémoire. Les 7, 9 et 10 sont à produire.

---

# Synthèse des actions

## Notebooks à modifier
1. `01_eda` — retirer l'écriture de `data/processed/`, retirer la cellule 23 périmée
2. `02_preprocessing` — aligner l'encodage sur `utf-8`, importer les fonctions du script
3. `03_modeling` — écrire dans `models/experiments/`, corriger le libellé du découpage et l'objectif
4. `05_camembert` — corriger `split_strategy` dans les métadonnées
5. `06_rag_semantique` — réexécuter, supprimer `models/semantic_rag_metadata.json` périmé
6. `07_rag_evaluation` — réexécuter, ou renvoyer explicitement vers le stage `rag_eval`

## Notebooks à fusionner
La section « benchmark externe » de `01_eda` rejoint `04_benchmark_externe`, qui traite le même jeu.

## Notebooks déjà transformés en scripts
`02` → `preprocess.py` · `03` → `train.py` · `04_rag` → `rag_build.py` ·
`06` → `rag_semantic_build.py` · `07` → `rag_eval.py`

## Notebooks à créer
**Aucun.** Les étapes manquantes des deux boucles appartiennent à `src/`, pas à des notebooks. Un
notebook de démonstration du cycle complet serait utile pour la soutenance, mais
`scripts/mlops_e2e_demo.py` remplit déjà cet office.
