# notebook.md — Guide des notebooks (audit + étapes)

> Guide de référence des 4 notebooks de `helpdesk-ai/notebooks/`. Pour chacun : **rôle**, **état
> actuel** (audit), **étapes attendues** (à conserver / ajouter / corriger) et **figures à
> produire**. À lire avec le [DIAGNOSTIC_QUALITE_DONNEES.md](../DIAGNOSTIC_QUALITE_DONNEES.md) et le
> [PLAN.md](../PLAN.md). Dernière mise à jour : **2026-06-26**.

## Conventions communes
- **Ordre d'exécution** : `01_eda` → `02_preprocessing` → `03_modeling` → `04_rag`.
- **Données** : `data/raw/HelpDesk1.csv` (encodage `utf-8-sig`), chemins via `params.yaml`.
- **Figures** : enregistrées dans `notebooks/figures/` (PNG). Diagnostic global compilé en PDF par
  `notebooks/data_quality_report.py` → `notebooks/figures/diagnostic_qualite_donnees.pdf`.
- **Hygiène** : à chaque ticket d'une catégorie, même libellé ; **vider les sorties** (`Clear All
  Outputs`) avant de committer pour garder des notebooks propres et reproductibles.
- ❌ **`Untitled.ipynb`** : vide → **à supprimer**.

---

## 1. `01_eda.ipynb` — Analyse exploratoire (EDA)

**Rôle** : comprendre les données, produire le rapport d'audit et les figures de cadrage.

**État actuel (audit) :**
- ✅ Bon contenu : inventaire structurel, distribution de la cible (déséquilibre 5,93×), longueurs
  de texte, doublons, **cohérence des labels (0 incohérence)**, audit de la base RAG, écriture de
  `rapport_audit.txt`.
- ⚠️ **Mélange 3 phases** : le notebook contient aussi le prétraitement (« phase2 ») et la lecture
  des métadonnées (« phase3 »). À recentrer sur l'EDA pure (déplacer la « phase2 » vers `02`).
- ⚠️ **`rapport_audit.txt` périmé** : il indique « Nb colonnes : 23 » alors que le dataset en a
  **18**, et « base RAG 450 » — **ré-exécuter** pour rafraîchir.
- ⚠️ **Cellule TF-IDF dupliquée** (deux fois « TOP 10 MOTS DISCRIMINANTS ») → en supprimer une.
- ⚠️ La cellule « phase3 » (lecture `model_metadata.json`) **plante** (chemin) → la retirer d'ici
  (elle appartient à `03`).

**Étapes attendues (à conserver) :**
1. Chargement + aperçu (`shape`, `head`).
2. Inventaire structurel (types, nuls, % manquants, uniques).
3. Distribution de la cible + ratio de déséquilibre → **figure**.
4. Statistiques de longueur (titre, description, mots) → **figure**.
5. Analyse des doublons + top titres répétés.
6. **Cohérence des labels** par titre répété (résultat : 0 incohérence — à mettre en avant).
7. Audit de la base RAG (tickets documentés par catégorie).
8. Écriture de `rapport_audit.txt`.

**À ajouter :**
- Tableau de **complétude par colonne** trié (figure `dq_02_completude.png`).
- Mention explicite : **58 types de tickets** (titres) → justifie la séparation sans fuite en `03`.
- Corriger l'en-tête du rapport (colonnes réelles = 18).

**Figures :** distribution des classes, longueurs, complétude, redondance (lignes/desc/titres).

---

## 2. `02_preprocessing.ipynb` — Prétraitement

**Rôle** : nettoyer le texte et produire `data/processed/HelpDesk1.csv` (features `text_clean` et
`text_rag`).

**État actuel (audit) :** 🔴 **Non fonctionnel** — seulement 3 cellules ; `df` et `clean_text` ne
sont **pas définis** dans le notebook (ni import, ni chargement). Le vrai prétraitement vit
aujourd'hui dans la « phase2 » de `01`. **À reconstruire** comme notebook autonome.

**Étapes attendues (à mettre en place) :**
1. **Imports** (`pandas`, `re`, `unicodedata`, `nltk`, `yaml`) + chargement `params.yaml`.
2. **Charger** `data/raw/HelpDesk1.csv` (`utf-8-sig`).
3. **Importer** la fonction de nettoyage depuis la source unique : `from src.data.preprocess import
   clean_text, build_text_for_model, build_text_for_rag` (éviter la duplication de code).
4. Construire les features :
   - `text_clean` = description nettoyée (feature du modèle ML) ;
   - `text_rag` = description + résolution + knowledge base (feature du RAG).
5. **Contrôles qualité** : nombre de textes vides, mots moyens, **textes uniques** avant/après.
6. **Sauvegarder** `data/processed/HelpDesk1.csv` (colonnes : ID, STATUT, Catégorie, Titre,
   Description, Résolution/Motif, knowledge Base, text_clean, text_rag).

**À ajouter (recommandation forte — cf. diagnostic §4.3) :**
- **Alléger le nettoyage** : réduire la liste des mots vides du domaine (garder les termes
  techniques), conserver certains codes utiles (`office 365`, `error 80080300`), seuil token `>= 2`.
- Préparer le terrain pour des **bi-grammes** (`ngram_range=(1,2)`) côté vectorisation.
- **Comparer** la diversité lexicale avant/après allègement (nb de textes uniques) → **figure**.

**Figures :** comparaison diversité lexicale (nettoyage actuel vs allégé), distribution des
longueurs après nettoyage.

---

## 3. `03_modeling.ipynb` — Modélisation

**Rôle** : entraîner et évaluer le classifieur, sauvegarder le modèle et ses métadonnées.

**État actuel (audit) :**
- ✅ Riche : fonction `train_and_log` (MLflow), **split sans fuite sur textes uniques**, baseline
  Dummy, GridSearch, analyse structurelle, analyse d'erreurs (Microsoft/Sécurité), analyse des
  probabilités de confiance, sauvegarde du pipeline + `model_metadata.json`.
- ✅ La **séparation sans fuite** est un vrai point fort à valoriser.
- ⚠️ Quelques cellules vides en fin de notebook → nettoyer.
- ⚠️ La note de métadonnées doit rester **neutre et factuelle** (décrire la redondance par types de
  tickets, pas d'étiquette interprétative) — **corrigé** dans `model_metadata.json`.

**Étapes attendues (à conserver / structurer) :**
1. Charger `data/processed/HelpDesk1.csv`.
2. **Split sans fuite** (tous les tickets d'un même texte dans le même split).
3. Vectorisation TF-IDF (`params.yaml`) — **ajouter bi-grammes**.
4. Baseline (DummyClassifier) + modèles (LogReg/RF) avec **SMOTE** + `class_weight`.
5. GridSearchCV + sélection du meilleur modèle.
6. Évaluation : F1-macro, **rappel par classe**, matrice de confusion → **figure**.
7. Analyse de la **confiance** + seuil de routage (human-in-the-loop).
8. Sauvegarde `models/best_pipeline.pkl` + `models/model_metadata.json`.

**À ajouter :**
- **Calibration** de la confiance (Platt/température) + courbe de calibration (ECE) → **figure**.
- Tableau **benchmark** baseline vs modèle (servira de référence pour CamemBERT en Phase 5).
- (Phase 5) cellule comparant LogReg vs **CamemBERT fine-tuné (LoRA)**.

**Figures :** matrice de confusion, distribution des confiances, courbe de calibration, benchmark.

---

## 4. `04_rag.ipynb` — Moteur RAG

**Rôle** : construire la base de connaissance et le moteur de recommandation de résolutions.

**État actuel (audit) :**
- ✅ Classe `RAGEngine` (TF-IDF + cosinus), base = tickets documentés, sauvegarde `rag_engine.pkl`,
  une amorce d'« évaluation quantitative ».
- ⚠️ RAG **lexical** (pas sémantique) et **évaluation incomplète** → à enrichir (Phases 6–7).
- ⚠️ Cellules vides en fin → nettoyer.

**Étapes attendues (à conserver) :**
1. Charger la base RAG (tickets documentés, `text_rag`).
2. Vectoriser + `recommend(query, category_filter, allow_fallback)`.
3. Sauvegarder le moteur.

**À ajouter (Phases 6–7) :**
- **RAG sémantique** : embeddings FR + base vectorielle (remplace TF-IDF/cosinus).
- **Évaluation quantitative** : Precision@k, Recall@k, MRR, nDCG, et (génération) Faithfulness,
  Answer Relevancy, Context Precision/Recall (RAGAS) → **figure**.
- Comparatif **lexical vs sémantique** → **figure/tableau**.

**Figures :** couverture par catégorie, scores de similarité, métriques d'évaluation RAG.

---

## Récapitulatif des actions prioritaires
1. **Supprimer** `Untitled.ipynb`.
2. **Reconstruire** `02_preprocessing.ipynb` (autonome, import depuis `src/`, nettoyage allégé).
3. **Recentrer** `01_eda` sur l'EDA + **ré-exécuter** pour rafraîchir `rapport_audit.txt` (18 col.).
4. **Nettoyer** les cellules vides/dupliquées de `01`, `03`, `04`.
5. **Vider les sorties** avant chaque commit.
6. Lancer `python notebooks/data_quality_report.py` pour (re)générer figures + PDF.
