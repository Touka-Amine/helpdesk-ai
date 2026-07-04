"""
Stage DVC 3/4 — Entraînement ML + évaluation + MLflow.

Pipeline : TF-IDF (1-2grammes) + CalibratedClassifierCV(LinearSVC).
Post-traitement : heuristiques FORCE/SOFT_RULES.
Logging MLflow : paramètres, métriques F1 par classe, artefacts (modèle + metadata).

Usage :
    python src/pipeline/train.py
"""

import os
import sys
import json
import yaml
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    classification_report,
    f1_score,
    accuracy_score,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models.heuristics import apply_heuristics

TRAIN_PATH  = "data/splits/train.csv"
TEST_PATH   = "data/splits/test.csv"
PARAMS_PATH = "params.yaml"
MODEL_OUT   = "models/best_pipeline.pkl"
META_OUT    = "models/model_metadata.json"
METRICS_OUT = "metrics/ml_eval.json"


def run() -> None:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        params = yaml.safe_load(f)
    nlp_p = params["nlp"]
    ml_p  = params["ml"]

    print("[train] Lecture des données...")
    train_df = pd.read_csv(TRAIN_PATH, encoding="utf-8")
    test_df  = pd.read_csv(TEST_PATH,  encoding="utf-8")

    X_train = train_df["text_clean"].fillna("").tolist()
    y_train = train_df["Catégorie"].tolist()
    X_test  = test_df["text_clean"].fillna("").tolist()
    y_test  = test_df["Catégorie"].tolist()

    print(f"[train] train={len(X_train)} | test={len(X_test)}")

    # ── Pipeline ML ──────────────────────────────────────────────────────────
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
    print("[train] Entraînement...")
    pipeline.fit(X_train, y_train)

    # ── Évaluation ML seul ───────────────────────────────────────────────────
    y_pred_ml   = pipeline.predict(X_test)
    f1_ml       = f1_score(y_test, y_pred_ml, average="macro", zero_division=0)
    acc_ml      = accuracy_score(y_test, y_pred_ml)
    print(f"[train] F1-macro ML seul : {f1_ml:.4f} | Accuracy : {acc_ml:.4f}")

    # ── Évaluation avec heuristiques ─────────────────────────────────────────
    threshold = ml_p["confidence_threshold"]
    y_pred_h  = []
    titres     = test_df["Titre"].fillna("").tolist()
    descs      = test_df["Description"].fillna("").tolist()
    probas     = pipeline.predict_proba(X_test)

    for i, (proba, titre, desc) in enumerate(zip(probas, titres, descs)):
        pred_idx  = proba.argmax()
        cat       = pipeline.classes_[pred_idx]
        conf      = float(proba[pred_idx])
        h = apply_heuristics(
            text_original      = f"{titre} {desc}",
            predicted_category = cat,
            confidence         = conf,
            threshold          = threshold,
        )
        y_pred_h.append(h["categorie"])

    f1_h  = f1_score(y_test, y_pred_h, average="macro", zero_division=0)
    acc_h = accuracy_score(y_test, y_pred_h)
    print(f"[train] F1-macro avec heuristiques : {f1_h:.4f} | Accuracy : {acc_h:.4f}")

    report = classification_report(
        y_test, y_pred_h, output_dict=True, zero_division=0
    )

    # ── Sauvegarde du modèle ─────────────────────────────────────────────────
    os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
    joblib.dump(pipeline, MODEL_OUT)
    print(f"[train] Modèle sauvegardé : {MODEL_OUT}")

    # ── Métadonnées ──────────────────────────────────────────────────────────
    existing_meta = {}
    if os.path.exists(META_OUT):
        with open(META_OUT, encoding="utf-8") as f:
            existing_meta = json.load(f)

    meta = {
        **existing_meta,
        "model_name"                : "LinearSVC_calibré",
        "sklearn_version"           : __import__("sklearn").__version__,
        "f1_macro_ml_seul"          : round(f1_ml, 4),
        "f1_macro_avec_heuristiques": round(f1_h, 4),
        "accuracy_test"             : round(acc_h, 4),
        "confidence_threshold"      : threshold,
        "confidence_threshold_v1"   : ml_p.get("confidence_threshold_v1", 0.40),
        "classes"                   : list(pipeline.classes_),
        "train_size"                : len(X_train),
        "test_size"                 : len(X_test),
        "unique_train"              : int(train_df["Titre"].nunique()),
        "unique_test"               : int(test_df["Titre"].nunique()),
    }
    with open(META_OUT, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"[train] Métadonnées : {META_OUT}")

    # ── Métriques DVC ────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(METRICS_OUT), exist_ok=True)
    dvc_metrics = {
        "f1_macro_ml"          : round(f1_ml, 4),
        "f1_macro_heuristiques": round(f1_h, 4),
        "accuracy"             : round(acc_h, 4),
    }
    for cls in pipeline.classes_:
        if cls in report:
            dvc_metrics[f"f1_{cls.replace(' ', '_')}"] = round(report[cls]["f1-score"], 4)
    with open(METRICS_OUT, "w", encoding="utf-8") as f:
        json.dump(dvc_metrics, f, ensure_ascii=False, indent=2)
    print(f"[train] Métriques DVC : {METRICS_OUT}")

    # ── MLflow ───────────────────────────────────────────────────────────────
    try:
        import mlflow
        import mlflow.sklearn

        mlflow_uri = os.environ.get("MLFLOW_TRACKING_URI", "file:./mlruns")
        mlflow.set_tracking_uri(mlflow_uri)
        mlflow.set_experiment("helpdesk-ai-classification")

        with mlflow.start_run(run_name="LinearSVC_heuristics"):
            # Params
            mlflow.log_params({
                "model"              : "LinearSVC_calibré",
                "max_features"       : nlp_p["max_features"],
                "ngram_range"        : str(nlp_p["ngram_range"]),
                "min_df"             : nlp_p["min_df"],
                "confidence_threshold": threshold,
                "train_size"         : len(X_train),
                "test_size"          : len(X_test),
            })
            # Métriques globales
            mlflow.log_metrics({
                "f1_macro_ml"          : round(f1_ml, 4),
                "f1_macro_heuristiques": round(f1_h, 4),
                "accuracy"             : round(acc_h, 4),
            })
            # Métriques par classe
            for cls in pipeline.classes_:
                if cls in report:
                    safe = cls.replace(" ", "_").replace("/", "_")
                    mlflow.log_metric(f"f1_{safe}", round(report[cls]["f1-score"], 4))
            # Artefacts
            mlflow.sklearn.log_model(pipeline, "model")
            mlflow.log_artifact(META_OUT,    artifact_path="metadata")
            mlflow.log_artifact(METRICS_OUT, artifact_path="metrics")
            print(f"[train] MLflow run enregistré dans {mlflow_uri}")
    except ImportError:
        print("[train] mlflow non installé — logging skippé.")
    except Exception as e:
        print(f"[train] MLflow erreur (non bloquant) : {e}")


if __name__ == "__main__":
    run()
