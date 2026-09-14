# -*- coding: utf-8 -*-
"""Calibration de l'index de confiance : precision et couverture par seuil.

Pourquoi ce script existe
-------------------------
Le memoire annonce, pour le seuil de routage releve a 0,60, « environ 70 % de
routage automatique et 85 % de precision », en precisant qu'il s'agit d'une
estimation issue des metadonnees du modele et non d'une mesure sur le jeu de
test. Ce script la mesure.

Il verifie au passage le tableau des tranches de confiance publie au chapitre 4
(42 / 121 / 110 / 82 tickets, precisions 0 %, 33,9 %, 89,1 %, 81,7 %) et
identifie a quelle chaine il correspond.

Protocole : celui des experiences, identique a scripts/campagne_comparative.py.

Sortie : metrics/calibration_confiance.json
"""
import io
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from models.heuristics import apply_heuristics
from campagne_comparative import decoupage, GRAINE, SEUIL

CSV = os.path.join(RACINE, "data", "processed", "HelpDesk1.csv")
SORTIE = os.path.join(RACINE, "metrics", "calibration_confiance.json")

TRANCHES = [(0.0, 0.40), (0.40, 0.60), (0.60, 0.80), (0.80, 1.01)]


def tranches(conf, juste):
    out = []
    for bas, haut in TRANCHES:
        m = (conf >= bas) & (conf < haut)
        n = int(m.sum())
        out.append({
            "borne_basse": bas,
            "borne_haute": min(haut, 1.0),
            "tickets": n,
            "part": round(100.0 * n / len(conf), 1),
            "precision": round(100.0 * float(juste[m].mean()), 1) if n else None,
        })
    return out


def courbe(conf, juste):
    """Couverture et precision du lot automatique, pour chaque seuil."""
    pts = []
    for s in np.arange(0.0, 1.001, 0.02):
        m = conf >= s
        n = int(m.sum())
        pts.append({
            "seuil": round(float(s), 2),
            "couverture": round(100.0 * n / len(conf), 2),
            "precision": round(100.0 * float(juste[m].mean()), 2) if n else None,
        })
    return pts


def main():
    df = pd.read_csv(CSV)
    train, test, _, _ = decoupage(df)
    y = test["Catégorie"].to_numpy()
    brut = (test["Titre"].fillna("") + " " + test["Description"].fillna("")).tolist()

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, min_df=2,
                                  ngram_range=(1, 2), sublinear_tf=True)),
        ("clf", CalibratedClassifierCV(
            estimator=LinearSVC(class_weight="balanced", max_iter=2000,
                                random_state=GRAINE), cv=3)),
    ])
    pipe.fit(train["text_clean"].fillna(""), train["Catégorie"])
    proba = pipe.predict_proba(test["text_clean"].fillna(""))
    pred_ml = pipe.classes_[proba.argmax(axis=1)]
    conf_ml = proba.max(axis=1)

    # Chaine servie : le classifieur puis les regles metier, qui peuvent relever
    # la confiance a 0,80 lorsqu'une regle ferme se declenche.
    pred_f, conf_f = [], []
    for txt, p, c in zip(brut, pred_ml, conf_ml):
        r = apply_heuristics(txt, p, float(c), threshold=SEUIL)
        pred_f.append(r["categorie"])
        conf_f.append(r["confiance"])
    pred_f = np.array(pred_f)
    conf_f = np.array(conf_f)

    resultats = {}
    for nom, pred, conf in (("ml_seul", pred_ml, conf_ml),
                            ("chaine_servie", pred_f, conf_f)):
        juste = (pred == y)
        resultats[nom] = {
            "tranches": tranches(conf, juste),
            "courbe": courbe(conf, juste),
            "au_seuil_0_40": None,
            "au_seuil_0_60": None,
        }
        for s in (0.40, 0.60):
            m = conf >= s
            resultats[nom]["au_seuil_0_%d" % int(s * 100)] = {
                "couverture": round(100.0 * int(m.sum()) / len(conf), 1),
                "precision": round(100.0 * float(juste[m].mean()), 1) if m.sum() else None,
            }

    sortie = {
        "date": datetime.now(timezone.utc).isoformat(),
        "protocole": "experiences, 355 tickets, graine 42",
        "resultats": resultats,
    }
    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump(sortie, f, ensure_ascii=False, indent=2)

    for nom in resultats:
        print("==", nom)
        for t in resultats[nom]["tranches"]:
            print("   [%.2f, %.2f)  %3d tickets  %5.1f %%  precision %s"
                  % (t["borne_basse"], t["borne_haute"], t["tickets"], t["part"],
                     "n/a" if t["precision"] is None else "%.1f %%" % t["precision"]))
        for s in ("au_seuil_0_40", "au_seuil_0_60"):
            v = resultats[nom][s]
            print("   %s : couverture %.1f %%, precision %.1f %%"
                  % (s, v["couverture"], v["precision"]))
        print()
    print("ecrit :", os.path.normpath(SORTIE))


if __name__ == "__main__":
    main()
