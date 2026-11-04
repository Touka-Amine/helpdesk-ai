# -*- coding: utf-8 -*-
"""Entraine et evalue le modele de suggestion de priorite (EF-12).

Ce que l'exigence demande
-------------------------
EF-12, priorite moyenne au dossier de specification : « Suggestion de priorite,
niveau propose a la prise en charge ». Le demandeur saisit deja une priorite a
la creation ; ce que le service attend, c'est une proposition independante de
cette saisie, calculee sur le texte.

Pourquoi la tache n'est pas gagnee d'avance
-------------------------------------------
La priorite n'est pas determinee par le scenario : sur les 58 titres du corpus,
43 portent deux priorites distinctes et 14 en portent trois. Un modele ne peut
donc pas s'en tirer en reconnaissant le titre, il doit lire la description. Rien
ne garantit que la description porte ce signal, et ce script mesure exactement
cela plutot que de le supposer.

Protocole, identique a celui du classifieur de categorie
--------------------------------------------------------
  - decoupage par groupe de titres, aucun titre commun entre entrainement et test ;
  - graine 42, 20 % des titres au test ;
  - reference plancher : la classe majoritaire, et le tirage stratifie ;
  - metrique F1-macro, les trois niveaux comptant autant l'un que l'autre.

Le modele n'est ecrit sur disque que s'il bat les deux references. Un modele qui
ne fait pas mieux que « toujours haute » n'a rien a faire en production.

Sortie : models/priorite_pipeline.pkl, metrics/priorite_eval.json
"""
from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, classification_report,
                             f1_score, precision_score)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV = os.path.join(RACINE, "data", "processed", "HelpDesk1.csv")
MODELE = os.path.join(RACINE, "models", "priorite_pipeline.pkl")
SORTIE = os.path.join(RACINE, "metrics", "priorite_eval.json")

GRAINE = 42
TEST_SIZE = 0.2
NIVEAUX = ["basse", "normale", "haute"]


def decoupage(df):
    """Aucun titre commun entre entrainement et test."""
    gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=GRAINE)
    tr, te = next(gss.split(df, groups=df["Titre"]))
    a, b = df.iloc[tr].reset_index(drop=True), df.iloc[te].reset_index(drop=True)
    assert not (set(a["Titre"]) & set(b["Titre"])), "fuite de titre"
    return a, b


def scores(y, p):
    return {
        "f1_macro": round(float(f1_score(y, p, average="macro", labels=NIVEAUX, zero_division=0)), 4),
        "accuracy": round(float(accuracy_score(y, p)), 4),
        "f1_par_niveau": {n: round(float(v), 4) for n, v in zip(
            NIVEAUX, f1_score(y, p, average=None, labels=NIVEAUX, zero_division=0))},
    }


def main():
    df = pd.read_csv(CSV)
    df = df[df["priorite_simple"].notna()].reset_index(drop=True)
    # Le texte seul : ni la priorite saisie, ni la categorie, qui ne sont pas des
    # entrees legitimes pour une proposition independante.
    df["_texte"] = (df["Titre"].fillna("") + " " + df["Description"].fillna(""))
    train, test = decoupage(df)
    y_tr, y_te = train["priorite_simple"].tolist(), test["priorite_simple"].tolist()
    print("entrainement %d / test %d — %d titres train, %d titres test"
          % (len(train), len(test), train["Titre"].nunique(), test["Titre"].nunique()))

    references = {}
    for nom, strategie in (("majoritaire", "most_frequent"), ("hasard_stratifie", "stratified")):
        d = DummyClassifier(strategy=strategie, random_state=GRAINE).fit(train["_texte"], y_tr)
        references[nom] = scores(y_te, d.predict(test["_texte"]))
        print("  reference %-18s F1-macro %.4f  exactitude %.4f"
              % (nom, references[nom]["f1_macro"], references[nom]["accuracy"]))

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, min_df=2, ngram_range=(1, 2),
                                  sublinear_tf=True)),
        ("clf", CalibratedClassifierCV(
            estimator=LinearSVC(class_weight="balanced", max_iter=2000, random_state=GRAINE),
            cv=3)),
    ])
    pipe.fit(train["_texte"], y_tr)
    pred = pipe.predict(test["_texte"])
    mesure = scores(y_te, pred)
    print("  modele     %-18s F1-macro %.4f  exactitude %.4f"
          % ("tfidf + LinearSVC", mesure["f1_macro"], mesure["accuracy"]))
    print()
    print(classification_report(y_te, pred, labels=NIVEAUX, zero_division=0))

    # ── Critere d'acceptation ────────────────────────────────────────────────
    # Une suggestion montree a un consultant doit remplir deux conditions. Elle
    # doit couvrir les trois niveaux : un modele qui ne propose jamais « basse »
    # ne suggere pas une priorite, il en ignore une. Et elle doit depasser le
    # tirage stratifie d'au moins cinq points de F1-macro, faute de quoi le
    # consultant ferait aussi bien de ne rien lire.
    MARGE_MINIMALE = 0.05
    meilleure_reference = max(r["f1_macro"] for r in references.values())
    couvre_les_trois = all(v > 0 for v in mesure["f1_par_niveau"].values())
    marge = mesure["f1_macro"] - meilleure_reference
    utile = couvre_les_trois and marge >= MARGE_MINIMALE
    print("couvre les trois niveaux : %s" % ("oui" if couvre_les_trois else
                                             "NON (%s a un F1 nul)" % ", ".join(
                                                 n for n, v in mesure["f1_par_niveau"].items() if v == 0)))
    print("marge sur la meilleure reference : %+.4f (minimum exige %.2f)" % (marge, MARGE_MINIMALE))

    # ── Repli : la question que le service se pose vraiment ──────────────────
    # Si les trois niveaux ne sont pas separables, reste a savoir si le texte
    # distingue au moins « haute » du reste. C'est la seule decision que la
    # priorite declenche a la prise en charge.
    y_tr_b = ["haute" if v == "haute" else "autre" for v in y_tr]
    y_te_b = ["haute" if v == "haute" else "autre" for v in y_te]
    pipe_b = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, min_df=2, ngram_range=(1, 2),
                                  sublinear_tf=True)),
        ("clf", CalibratedClassifierCV(
            estimator=LinearSVC(class_weight="balanced", max_iter=2000, random_state=GRAINE),
            cv=3)),
    ]).fit(train["_texte"], y_tr_b)
    pred_b = pipe_b.predict(test["_texte"])
    ref_b = DummyClassifier(strategy="stratified", random_state=GRAINE).fit(
        train["_texte"], y_tr_b).predict(test["_texte"])
    binaire = {
        "f1_macro": round(float(f1_score(y_te_b, pred_b, average="macro", zero_division=0)), 4),
        "accuracy": round(float(accuracy_score(y_te_b, pred_b)), 4),
        "reference_f1_macro": round(float(f1_score(y_te_b, ref_b, average="macro", zero_division=0)), 4),
    }
    binaire["marge"] = round(binaire["f1_macro"] - binaire["reference_f1_macro"], 4)
    # Le F1-macro flatte un classifieur binaire sur classes desequilibrees : la
    # reference de la classe majoritaire y est tres basse, et une marge paraissait
    # confortable alors que le modele ne depassait la classe majoritaire que de
    # 1,4 point d'exactitude. Le critere qui compte pour un affichage est celui-ci :
    # quand le systeme annonce « priorite haute », a-t-il raison assez souvent pour
    # qu'un consultant le croie ?
    PRECISION_MINIMALE = 0.70
    pr = precision_score(y_te_b, pred_b, labels=["haute"], average="macro", zero_division=0)
    taux_de_base = float(np.mean([v == "haute" for v in y_te_b]))
    eq = balanced_accuracy_score(y_te_b, pred_b)
    binaire.update({
        "precision_quand_il_annonce_haute": round(float(pr), 4),
        "taux_de_base_haute": round(taux_de_base, 4),
        "exactitude_equilibree": round(float(eq), 4),
        "exactitude_classe_majoritaire": round(float(max(taux_de_base, 1 - taux_de_base)), 4),
        "precision_minimale_exigee": PRECISION_MINIMALE,
    })
    binaire["retenu"] = bool(pr >= PRECISION_MINIMALE)
    print("\nrepli binaire « haute / autre » :")
    print("  F1-macro %.4f contre %.4f de reference" % (binaire["f1_macro"], binaire["reference_f1_macro"]))
    print("  quand il annonce « haute », il a raison %.1f %% du temps, pour un taux de base de %.1f %%"
          % (100 * pr, 100 * taux_de_base))
    print("  exactitude %.4f contre %.4f pour la classe majoritaire ; exactitude equilibree %.4f"
          % (binaire["accuracy"], binaire["exactitude_classe_majoritaire"], eq))
    print("  -> %s" % ("retenu" if binaire["retenu"] else
                       "ECARTE : une annonce juste une fois sur deux n'aide personne"))

    if utile:
        joblib.dump({"pipeline": pipe, "niveaux": NIVEAUX, "mode": "trois_niveaux"}, MODELE)
        print("ecrit : %s" % MODELE)
    elif binaire["retenu"]:
        joblib.dump({"pipeline": pipe_b, "niveaux": ["autre", "haute"], "mode": "binaire"}, MODELE)
        print("ecrit (mode binaire) : %s" % MODELE)
    else:
        if os.path.exists(MODELE):
            os.remove(MODELE)
        print("aucun modele ecrit : le texte du ticket ne porte pas la priorite sur ce corpus.")

    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "exigence": "EF-12 — suggestion de priorite",
            "protocole": "GroupShuffleSplit sur les titres, graine 42, test_size 0.2",
            "entrainement": len(train), "test": len(test),
            "titres_train": int(train["Titre"].nunique()),
            "titres_test": int(test["Titre"].nunique()),
            "entree": "titre + description, sans la priorite saisie ni la categorie",
            "references": references,
            "modele": mesure,
            "critere_acceptation": {
                "couvre_les_trois_niveaux": bool(couvre_les_trois),
                "marge_sur_la_reference": round(float(marge), 4),
                "marge_minimale_exigee": MARGE_MINIMALE,
            },
            "repli_binaire_haute_ou_autre": binaire,
            "modele_retenu": bool(utile) or bool(binaire["retenu"]),
            "mode_retenu": ("trois_niveaux" if utile else
                            "binaire" if binaire["retenu"] else "aucun"),
            "repartition_test": {k: int(v) for k, v in
                                 pd.Series(y_te).value_counts().items()},
        }, f, ensure_ascii=False, indent=2)
    print("ecrit : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
