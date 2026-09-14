# -*- coding: utf-8 -*-
"""Campagne comparative des approches de classification, regles nettoyees.

Pourquoi ce script existe
-------------------------
La campagne du 2026-09-07 (metrics/campagne_avant_nettoyage.json) a mesure sept
configurations, dont deux reposant sur des regles contaminees par le jeu de test.
L'audit du 2026-08-22 a retire quatre mots-cles de heuristics.py. Les scores
publies dans le memoire apres cet audit (0.8343 pour CamemBERT + regles, 0.5827
pour TF-IDF + regles) n'existaient jusqu'ici que dans CHANGELOG.md et RISKS.md,
sans artefact machine. Ce script les recalcule pour qu'ils soient tracables.

Protocole, identique a celui du notebook 05 et de la campagne precedente
-----------------------------------------------------------------------
  - corpus data/processed/HelpDesk1.csv, 1800 tickets, 58 titres uniques ;
  - StratifiedShuffleSplit sur les 58 titres, test_size 0.2, graine 42 ;
  - aucun titre de test n'apparait a l'entrainement ;
  - TF-IDF sur text_clean, CamemBERT sur text_enriched ;
  - regles metier telles qu'elles figurent aujourd'hui dans src/models/heuristics.py ;
  - seuil de confiance 0.6 pour les SOFT_RULES.

Sortie : metrics/campagne_apres_nettoyage.json

Le script mesure aussi le cout de service de chaque chaine (latence par ticket,
empreinte memoire), chiffres necessaires pour arbitrer le modele a servir.
"""
import io
import json
import os
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "src"))

from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from models.heuristics import FORCE_RULES, SOFT_RULES, apply_heuristics

CSV = os.path.join(RACINE, "data", "processed", "HelpDesk1.csv")
SORTIE = os.path.join(RACINE, "metrics", "campagne_apres_nettoyage.json")
ADAPTATEUR = os.path.join(RACINE, "models", "camembert_lora_adapter")

GRAINE = 42
TEST_SIZE = 0.2
SEUIL = 0.6
MAX_LEN = 128


def decoupage(df):
    """Reproduit le decoupage anti-fuite du notebook 05."""
    titres = df.groupby("Titre")["Catégorie"].first().reset_index()
    sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE,
                                 random_state=GRAINE)
    tr, te = next(sss.split(titres["Titre"], titres["Catégorie"]))
    t_train = set(titres.iloc[tr]["Titre"])
    t_test = set(titres.iloc[te]["Titre"])
    assert not (t_train & t_test), "fuite de titre entre train et test"
    return (df[df["Titre"].isin(t_train)].reset_index(drop=True),
            df[df["Titre"].isin(t_test)].reset_index(drop=True),
            len(t_train), len(t_test))


def scores(y_vrai, y_pred, classes):
    """Metriques d'une configuration, arrondies au dix-millieme."""
    return {
        "f1_macro": round(float(f1_score(y_vrai, y_pred, average="macro",
                                         labels=classes, zero_division=0)), 4),
        "precision_macro": round(float(precision_score(y_vrai, y_pred, average="macro",
                                                       labels=classes, zero_division=0)), 4),
        "recall_macro": round(float(recall_score(y_vrai, y_pred, average="macro",
                                                 labels=classes, zero_division=0)), 4),
        "accuracy": round(float(accuracy_score(y_vrai, y_pred)), 4),
        "corrects": int((np.array(y_vrai) == np.array(y_pred)).sum()),
        "f1_par_classe": {c: round(float(v), 4) for c, v in zip(
            classes, f1_score(y_vrai, y_pred, average=None, labels=classes,
                              zero_division=0))},
    }


def avec_regles(textes, predictions, confiances):
    """Applique les regles metier courantes a une sortie de modele."""
    out = []
    for txt, pred, conf in zip(textes, predictions, confiances):
        r = apply_heuristics(txt, pred, float(conf), threshold=SEUIL)
        out.append(r["categorie"])
    return out


def chrono(fonction, n=3):
    """Retourne la mediane du temps d'execution, en secondes."""
    mesures = []
    for _ in range(n):
        t0 = time.perf_counter()
        fonction()
        mesures.append(time.perf_counter() - t0)
    return float(np.median(mesures))


def main():
    df = pd.read_csv(CSV)
    classes = sorted(df["Catégorie"].unique())
    train, test, n_tr, n_te = decoupage(df)
    y_test = test["Catégorie"].tolist()
    # Texte brut soumis aux regles : titre et description non nettoyes.
    brut = (test["Titre"].fillna("") + " " + test["Description"].fillna("")).tolist()

    resultats = {}

    # ── 01 Reference plancher ────────────────────────────────────────────────
    dummy = DummyClassifier(strategy="stratified", random_state=GRAINE)
    dummy.fit(train["text_clean"].fillna(""), train["Catégorie"])
    resultats["01_hasard"] = dict(
        libelle="Reference plancher (hasard stratifie)",
        **scores(y_test, dummy.predict(test["text_clean"].fillna("")), classes))

    # ── 02 TF-IDF seul ───────────────────────────────────────────────────────
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, min_df=2,
                                  ngram_range=(1, 2), sublinear_tf=True)),
        ("clf", CalibratedClassifierCV(
            estimator=LinearSVC(class_weight="balanced", max_iter=2000,
                                random_state=GRAINE), cv=3)),
    ])
    pipe.fit(train["text_clean"].fillna(""), train["Catégorie"])
    proba_tfidf = pipe.predict_proba(test["text_clean"].fillna(""))
    pred_tfidf = pipe.classes_[proba_tfidf.argmax(axis=1)]
    conf_tfidf = proba_tfidf.max(axis=1)
    resultats["02_tfidf_seul"] = dict(
        libelle="TF-IDF + LinearSVC calibre, seul",
        **scores(y_test, pred_tfidf, classes))

    # ── 03 TF-IDF + regles nettoyees ─────────────────────────────────────────
    pred_tfidf_r = avec_regles(brut, pred_tfidf, conf_tfidf)
    resultats["03_tfidf_regles"] = dict(
        libelle="TF-IDF + regles metier nettoyees",
        **scores(y_test, pred_tfidf_r, classes))

    # ── 04 et 05 CamemBERT ───────────────────────────────────────────────────
    import torch
    from peft import PeftModel
    from transformers import (AutoModelForSequenceClassification,
                              AutoTokenizer)

    tok = AutoTokenizer.from_pretrained(ADAPTATEUR)
    base = AutoModelForSequenceClassification.from_pretrained(
        "camembert-base", num_labels=len(classes))
    modele = PeftModel.from_pretrained(base, ADAPTATEUR).eval()

    def inferer(device, textes):
        m = modele.to(device)
        sorties = []
        with torch.no_grad():
            for i in range(0, len(textes), 32):
                lot = tok(textes[i:i + 32], padding="max_length", truncation=True,
                          max_length=MAX_LEN, return_tensors="pt").to(device)
                logits = m(**lot).logits
                sorties.append(torch.softmax(logits, dim=-1).cpu().numpy())
        return np.vstack(sorties)

    textes_cam = test["text_enriched"].fillna("").tolist()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    proba_cam = inferer(device, textes_cam)
    pred_cam = np.array(classes)[proba_cam.argmax(axis=1)]
    conf_cam = proba_cam.max(axis=1)

    resultats["04_camembert_seul"] = dict(
        libelle="CamemBERT-base + LoRA, seul",
        **scores(y_test, pred_cam, classes))

    pred_cam_r = avec_regles(brut, pred_cam, conf_cam)
    resultats["05_camembert_regles"] = dict(
        libelle="CamemBERT + LoRA + regles metier nettoyees",
        **scores(y_test, pred_cam_r, classes))

    # ── Cout de service ──────────────────────────────────────────────────────
    un = [textes_cam[0]]
    cout = {}
    t_tfidf = chrono(lambda: pipe.predict_proba([test["text_clean"].iloc[0]]), n=20)
    cout["tfidf_un_ticket_ms"] = round(t_tfidf * 1000, 1)
    for dev in (["cpu", "cuda"] if torch.cuda.is_available() else ["cpu"]):
        t = chrono(lambda: inferer(dev, un), n=10)
        cout["camembert_%s_un_ticket_ms" % dev] = round(t * 1000, 1)
    taille = sum(os.path.getsize(os.path.join(ADAPTATEUR, f))
                 for f in os.listdir(ADAPTATEUR))
    cout["adaptateur_lora_Mo"] = round(taille / 1048576.0, 1)
    cout["parametres_camembert_M"] = round(
        sum(p.numel() for p in base.parameters()) / 1e6, 1)
    cout["taille_pipeline_tfidf_Mo"] = round(
        os.path.getsize(os.path.join(RACINE, "models", "best_pipeline.pkl"))
        / 1048576.0, 2)

    sortie = {
        "date": datetime.now(timezone.utc).isoformat(),
        "objet": ("Campagne comparative posterieure a l'audit des regles du "
                  "2026-08-22, destinee a rendre tracables les scores publies."),
        "protocole": {
            "decoupage": "StratifiedShuffleSplit sur les 58 titres uniques, graine 42",
            "train": int(len(train)),
            "test": int(len(test)),
            "titres_train": n_tr,
            "titres_test": n_te,
            "categories_au_test": int(test["Catégorie"].nunique()),
            "seuil_confiance": SEUIL,
            "regles_fermes": len(FORCE_RULES),
            "regles_souples": len(SOFT_RULES),
            "motifs_fermes": sum(len(k) for k, _ in FORCE_RULES),
        },
        "resultats": resultats,
        "cout_de_service": cout,
    }

    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump(sortie, f, ensure_ascii=False, indent=2)

    print("Protocole : train %d / test %d, %d titres train / %d test, %d categories au test"
          % (len(train), len(test), n_tr, n_te, test["Catégorie"].nunique()))
    print()
    for cle in sorted(resultats):
        r = resultats[cle]
        print("  %-22s F1-macro %.4f  exactitude %.4f  (%d/%d)"
              % (cle, r["f1_macro"], r["accuracy"], r["corrects"], len(test)))
    print()
    for cle, val in cout.items():
        print("  %-32s %s" % (cle, val))
    print()
    print("ecrit :", os.path.normpath(SORTIE))


if __name__ == "__main__":
    main()
