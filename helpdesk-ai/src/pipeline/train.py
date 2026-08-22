"""
Stage DVC — AXE 1, etape 3 : entrainement d'un modele CANDIDAT.

Pipeline : TF-IDF (1-2grammes) + CalibratedClassifierCV(LinearSVC).
Post-traitement : heuristiques FORCE/SOFT_RULES.

CE QUI A CHANGE, ET POURQUOI
    Ce stage n'ecrit plus models/best_pipeline.pkl. Il produit un CANDIDAT
    (models/candidate_pipeline.pkl) et l'enregistre dans le registre avec le tag
    "candidate". C'est src/pipeline/promote.py qui decide, apres comparaison avec
    le modele en production sur le jeu de test gele, si ce candidat devient le
    modele servi.

    Sans cette separation, tout `dvc repro` remplacerait la production par le
    dernier entrainement, quelle que soit sa qualite. C'est exactement ce que la
    consigne "un nouveau modele ne doit jamais remplacer automatiquement un
    modele performant" interdit.

DONNEES
    Entree : data/splits/train_current.csv (produit par build_dataset.py), qui
    contient le corpus historique plus les tickets de production valides.
    Evaluation : data/splits/test.csv, copie de travail du jeu de test GELE.

PONDERATION
    Les lignes issues de production portent un sample_weight fonction de la force
    de leur etiquette (corrected 1.0 / confirmed 0.7 / weak 0.3). Une etiquette
    simplement non contestee par un admin pese moins qu'une correction explicite.

Usage :
    python src/pipeline/train.py
"""

import json
import os
import sys
from datetime import datetime, timezone

import joblib
import pandas as pd
import yaml
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models.heuristics import apply_heuristics
from registry.model_registry import ModelRegistry

TRAIN_CURRENT = "data/splits/train_current.csv"
TRAIN_FALLBACK = "data/splits/train.csv"
TRAIN_MANIFEST = "data/splits/train_current.manifest.json"
TEST_PATH = "data/splits/test.csv"
PARAMS_PATH = "params.yaml"
MODEL_OUT = "models/candidate_pipeline.pkl"
META_OUT = "models/candidate_metadata.json"
METRICS_OUT = "metrics/ml_eval_candidate.json"
CONFUSION_OUT = "metrics/confusion_matrix_candidate.json"


def _lire_json(path, defaut=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return defaut


def evaluer(pipeline, test_df, threshold):
    """
    Evalue le pipeline seul puis le pipeline suivi des heuristiques.

    Retourne un dict de metriques adaptees au desequilibre des classes : F1-macro,
    precision et rappel macro et ponderes, F1 par classe, matrice de confusion.
    """
    X_test = test_df["text_clean"].fillna("").tolist()
    y_test = test_df["Catégorie"].tolist()

    y_pred_ml = pipeline.predict(X_test)
    f1_ml = f1_score(y_test, y_pred_ml, average="macro", zero_division=0)

    titres = test_df["Titre"].fillna("").tolist()
    descs = test_df["Description"].fillna("").tolist()
    probas = pipeline.predict_proba(X_test)

    y_pred_h, n_heuristiques = [], 0
    for proba, titre, desc in zip(probas, titres, descs):
        idx = proba.argmax()
        h = apply_heuristics(
            text_original=f"{titre} {desc}",
            predicted_category=pipeline.classes_[idx],
            confidence=float(proba[idx]),
            threshold=threshold,
        )
        y_pred_h.append(h["categorie"])
        n_heuristiques += int(bool(h["heuristic_applied"]))

    labels = sorted(set(y_test) | set(y_pred_h))
    rapport = classification_report(y_test, y_pred_h, output_dict=True, zero_division=0)
    matrice = confusion_matrix(y_test, y_pred_h, labels=labels)

    support = {c: int(rapport.get(c, {}).get("support", 0)) for c in labels}
    classes_evaluables = [c for c in labels if support.get(c, 0) > 0]
    f1_macro_support = (
        sum(rapport[c]["f1-score"] for c in classes_evaluables) / len(classes_evaluables)
        if classes_evaluables else 0.0
    )

    metriques = {
        "f1_macro_ml": round(float(f1_ml), 4),
        "f1_macro_heuristiques": round(
            float(f1_score(y_test, y_pred_h, average="macro", zero_division=0)), 4
        ),
        # Meme moyenne, calculee sur les seules classes ayant du support au test.
        # Une classe absente du test a une F1 de 0.0 par construction : la compter
        # mesure la composition du jeu de test, pas le modele.
        "f1_macro_classes_evaluables": round(float(f1_macro_support), 4),
        "n_classes_evaluables": len(classes_evaluables),
        "accuracy": round(float(accuracy_score(y_test, y_pred_h)), 4),
        "precision_macro": round(
            float(precision_score(y_test, y_pred_h, average="macro", zero_division=0)), 4
        ),
        "recall_macro": round(
            float(recall_score(y_test, y_pred_h, average="macro", zero_division=0)), 4
        ),
        "precision_weighted": round(
            float(precision_score(y_test, y_pred_h, average="weighted", zero_division=0)), 4
        ),
        "recall_weighted": round(
            float(recall_score(y_test, y_pred_h, average="weighted", zero_division=0)), 4
        ),
        "taux_heuristiques": round(n_heuristiques / max(len(y_test), 1), 4),
    }
    for classe in labels:
        cle = classe.replace(" ", "_")
        infos = rapport.get(classe, {})
        metriques[f"f1_{cle}"] = round(float(infos.get("f1-score", 0.0)), 4)
        metriques[f"precision_{cle}"] = round(float(infos.get("precision", 0.0)), 4)
        metriques[f"recall_{cle}"] = round(float(infos.get("recall", 0.0)), 4)
        metriques[f"support_{cle}"] = support.get(classe, 0)

    confusion = {
        "labels": labels,
        "matrix": matrice.tolist(),
        "support": support,
        "classes_sans_support": [c for c in labels if support.get(c, 0) == 0],
    }
    return metriques, confusion


def _ecrire_png_confusion(confusion: dict, chemin: str) -> None:
    """Rendu graphique de la matrice. Non bloquant si matplotlib est absent."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        labels = confusion["labels"]
        matrice = np.array(confusion["matrix"])
        fig, ax = plt.subplots(figsize=(1.1 * len(labels) + 2, 1.0 * len(labels) + 2))
        ax.imshow(matrice, cmap="Blues")
        ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(labels)), labels, fontsize=8)
        for i in range(len(labels)):
            for j in range(len(labels)):
                if matrice[i, j]:
                    ax.text(j, i, int(matrice[i, j]), ha="center", va="center", fontsize=8)
        ax.set_xlabel("Predit")
        ax.set_ylabel("Reel")
        ax.set_title("Matrice de confusion — candidat")
        fig.tight_layout()
        fig.savefig(chemin, dpi=130)
        plt.close(fig)
        print(f"[train] Matrice de confusion : {chemin}")
    except Exception as exc:
        print(f"[train] Rendu de la matrice ignore ({type(exc).__name__}: {exc})")


def _logger_mlflow(params_nlp, threshold, metriques, confusion, meta, lineage):
    """
    Suivi d'experience MLflow.

    Le bloc est non bloquant, mais l'erreur est desormais AFFICHEE : la version
    precedente avalait silencieusement toute exception, ce qui permettait a un
    entrainement de reussir sans laisser aucune trace sans que personne le voie.
    Retourne l'identifiant du run, ou None.
    """
    try:
        import mlflow
        import mlflow.sklearn
    except ImportError:
        print("[train] mlflow non installe — suivi d'experience desactive.")
        return None

    try:
        uri = os.environ.get("MLFLOW_TRACKING_URI", "file:./mlruns")
        mlflow.set_tracking_uri(uri)
        mlflow.set_experiment("helpdesk-ai-classification")
        with mlflow.start_run(run_name=f"candidate_{lineage['dataset_version']}") as run:
            mlflow.log_params({
                "model": "LinearSVC_calibré",
                "max_features": params_nlp["max_features"],
                "ngram_range": str(params_nlp["ngram_range"]),
                "min_df": params_nlp["min_df"],
                "confidence_threshold": threshold,
                "train_size": meta["train_size"],
                "test_size": meta["test_size"],
                "dataset_version": lineage["dataset_version"],
                "n_production_rows": lineage["n_production_rows"],
                "sample_weight_applique": lineage["sample_weight_applique"],
            })
            mlflow.log_metrics({k: v for k, v in metriques.items() if isinstance(v, (int, float))})
            mlflow.sklearn.log_model(joblib.load(MODEL_OUT), name="model")
            mlflow.log_artifact(META_OUT, artifact_path="metadata")
            mlflow.log_artifact(METRICS_OUT, artifact_path="metrics")
            mlflow.log_artifact(CONFUSION_OUT, artifact_path="metrics")
            print(f"[train] MLflow run {run.info.run_id} ({uri})")
            return run.info.run_id
    except Exception as exc:
        print(f"[train] MLflow indisponible — {type(exc).__name__}: {exc}")
        print("[train]   L'entrainement continue, mais ce run n'est PAS trace.")
        return None


def run() -> None:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        params = yaml.safe_load(f)
    nlp_p = params["nlp"]
    threshold = params["ml"]["confidence_threshold"]

    chemin_train = TRAIN_CURRENT if os.path.exists(TRAIN_CURRENT) else TRAIN_FALLBACK
    if chemin_train == TRAIN_FALLBACK:
        print(f"[train] {TRAIN_CURRENT} absent — repli sur {TRAIN_FALLBACK}. "
              f"Lancez build_dataset.py pour inclure les donnees de production.")

    train_df = pd.read_csv(chemin_train, encoding="utf-8")
    test_df = pd.read_csv(TEST_PATH, encoding="utf-8")

    X_train = train_df["text_clean"].fillna("").tolist()
    y_train = train_df["Catégorie"].tolist()
    n_production = int((train_df.get("source", pd.Series(dtype=str)) == "production").sum())

    print(f"[train] source : {chemin_train}")
    print(f"[train] train={len(X_train)} ({n_production} de production) | test={len(test_df)}")

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=nlp_p["max_features"],
            ngram_range=tuple(nlp_p["ngram_range"]),
            min_df=nlp_p["min_df"],
            sublinear_tf=True,
        )),
        ("clf", CalibratedClassifierCV(
            LinearSVC(
                class_weight="balanced",
                max_iter=2000,
                random_state=params["data"]["random_state"],
            ),
            cv=3,
        )),
    ])

    poids_appliques = False
    if "sample_weight" in train_df.columns and train_df["sample_weight"].nunique() > 1:
        poids = pd.to_numeric(train_df["sample_weight"], errors="coerce").fillna(1.0).tolist()
        try:
            pipeline.fit(X_train, y_train, clf__sample_weight=poids)
            poids_appliques = True
            print("[train] Ponderation par force d'etiquette appliquee.")
        except (TypeError, ValueError) as exc:
            print(f"[train] Ponderation refusee par l'estimateur ({exc}) — "
                  f"entrainement non pondere.")
            pipeline.fit(X_train, y_train)
    else:
        print("[train] Aucune ponderation (corpus homogene).")
        pipeline.fit(X_train, y_train)

    metriques, confusion = evaluer(pipeline, test_df, threshold)
    print(f"[train] F1-macro ML seul          : {metriques['f1_macro_ml']:.4f}")
    print(f"[train] F1-macro + heuristiques   : {metriques['f1_macro_heuristiques']:.4f}")
    print(f"[train] F1-macro classes evaluees : {metriques['f1_macro_classes_evaluables']:.4f} "
          f"({metriques['n_classes_evaluables']} classes)")
    print(f"[train] Accuracy                  : {metriques['accuracy']:.4f}")
    if confusion["classes_sans_support"]:
        print(f"[train] Classes sans support au test : {confusion['classes_sans_support']}")

    os.makedirs("models", exist_ok=True)
    os.makedirs("metrics", exist_ok=True)
    joblib.dump(pipeline, MODEL_OUT)

    manifeste = _lire_json(TRAIN_MANIFEST, defaut={}) or {}
    meta = {
        "model_name": "LinearSVC_calibré",
        "sklearn_version": __import__("sklearn").__version__,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "f1_macro_ml_seul": metriques["f1_macro_ml"],
        "f1_macro_avec_heuristiques": metriques["f1_macro_heuristiques"],
        "f1_macro_classes_evaluables": metriques["f1_macro_classes_evaluables"],
        "accuracy_test": metriques["accuracy"],
        "precision_macro": metriques["precision_macro"],
        "recall_macro": metriques["recall_macro"],
        "confidence_threshold": threshold,
        "classes": list(pipeline.classes_),
        "train_size": len(X_train),
        "test_size": len(test_df),
        "train_production_rows": n_production,
        "unique_train": int(train_df["Titre"].nunique()),
        "unique_test": int(test_df["Titre"].nunique()),
        "dataset_version": manifeste.get("dataset_version", "inconnu"),
        "sample_weight_applique": poids_appliques,
        "split_strategy": params.get("split", {}).get("strategy", "group"),
        "test_reference_frozen": params.get("split", {}).get("freeze_test", True),
        "classes_sans_support_test": confusion["classes_sans_support"],
        "dataset_note": (
            "Corpus historique a 58 types de tickets recurrents, decoupe par Titre, "
            "enrichi des tickets de production valides par un administrateur."
        ),
    }
    with open(META_OUT, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    with open(METRICS_OUT, "w", encoding="utf-8") as f:
        json.dump(metriques, f, ensure_ascii=False, indent=2)
    with open(CONFUSION_OUT, "w", encoding="utf-8") as f:
        json.dump(confusion, f, ensure_ascii=False, indent=2)
    _ecrire_png_confusion(confusion, "metrics/confusion_matrix_candidate.png")

    lineage = {
        "dataset_version": manifeste.get("dataset_version", "inconnu"),
        "dataset_sha256": manifeste.get("sha256"),
        "dataset_file": chemin_train,
        "dataset_manifest": manifeste,
        "test_reference": TEST_PATH,
        "test_manifest": _lire_json(
            params.get("split", {}).get(
                "reference_manifest", "data/reference/test_reference_manifest.json"
            ),
            defaut={},
        ),
        "n_production_rows": n_production,
        "sample_weight_applique": poids_appliques,
        "params_nlp": nlp_p,
        "confidence_threshold": threshold,
        "trained_at": meta["trained_at"],
    }
    lineage["mlflow_run_id"] = _logger_mlflow(nlp_p, threshold, metriques, confusion, meta, lineage)

    registre = ModelRegistry(
        root=params.get("registry", {}).get("dir", "models/registry")
    )
    registre.bootstrap_from_existing()
    version = registre.register(
        pipeline_path=MODEL_OUT,
        metadata=meta,
        metrics=metriques,
        lineage=lineage,
        tag="candidate",
    )
    print(f"[train] Candidat enregistre : v{version} (non promu)")
    print(f"[train] Decision de promotion : python src/pipeline/promote.py")


if __name__ == "__main__":
    run()
