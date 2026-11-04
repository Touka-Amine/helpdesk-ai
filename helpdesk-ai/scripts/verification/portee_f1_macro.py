# -*- coding: utf-8 -*-
"""Sur combien de categories le F1-macro du modele servi est-il calcule ?

La remarque
-----------
L'encadrant releve que le memoire annonce 0,5829 « sur les 8 categories » alors
que le jeu de test gele n'en contient que 5. Il a raison de s'en etonner, et la
reponse n'est ni 8 ni 5.

Ce que fait le code aujourd'hui
--------------------------------
`src/pipeline/train.py` appelle :

    f1_score(y_test, y_pred_h, average="macro", zero_division=0)

sans l'argument `labels`. Scikit-learn moyenne alors sur l'UNION des categories
presentes dans les etiquettes vraies et dans les predictions. Le denominateur
n'est donc pas une propriete du referentiel ni du jeu de test : il depend des
categories que le modele a prononcees, donc de ses propres erreurs.

Consequence : un modele qui ne predirait jamais une categorie absente du test
serait divise par un nombre plus petit, et afficherait un meilleur score a
qualite rigoureusement identique. La metrique ne compare pas deux modeles a
armes egales — et c'est elle que `src/registry/model_registry.py` enregistre
sous `primary_metric`.

Ce script recalcule les trois valeurs sans rien modifier, pour que le memoire
cite celle qu'il annonce.

Sortie : metrics/portee_f1_macro.json
"""
from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime, timezone

import joblib

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RACINE)
sys.path.insert(0, os.path.join(RACINE, "src"))

from sklearn.metrics import f1_score  # noqa: E402

from models.heuristics import apply_heuristics  # noqa: E402
from pipeline import jeu_gele  # noqa: E402

TEST = os.path.join(RACINE, "data", "splits", "test.csv")
MODELE = os.path.join(RACINE, "models", "best_pipeline.pkl")
META = os.path.join(RACINE, "models", "model_metadata.json")
SORTIE = os.path.join(RACINE, "metrics", "portee_f1_macro.json")

REFERENTIEL = ["Applicatifs", "Backup", "Communication", "Infrastructure",
               "Microsoft", "Réseau", "Système", "Sécurité"]


def main():
    # Le depot sauvegarde le pipeline depuis un carnet : la classe RAGEngine y
    # etait definie dans __main__, et joblib la recherche au meme endroit.
    import __main__
    from rag.engine import RAGEngine
    __main__.RAGEngine = RAGEngine

    # Lecture de RAPPORT : ce script documente le defaut de portee, il ne
    # choisit rien.
    test = jeu_gele.lire(
        jeu_gele.POUR_RAPPORTER,
        motif="demonstration de l'effet de la portee sur la F1-macro",
        lecteur="scripts/verification/portee_f1_macro.py",
    )
    with io.open(META, encoding="utf-8") as f:
        seuil = json.load(f).get("confidence_threshold", 0.60)
    pipeline = joblib.load(MODELE)

    y = test["Catégorie"].tolist()
    X = test["text_clean"].fillna("").tolist()
    probas = pipeline.predict_proba(X)
    titres = test["Titre"].fillna("").tolist()
    descs = test["Description"].fillna("").tolist()

    y_pred = []
    for proba, titre, desc in zip(probas, titres, descs):
        i = proba.argmax()
        y_pred.append(apply_heuristics(
            text_original="%s %s" % (titre, desc),
            predicted_category=pipeline.classes_[i],
            confidence=float(proba[i]), threshold=seuil)["categorie"])

    presentes = sorted(set(y))
    predites = sorted(set(y_pred))
    union = sorted(set(y) | set(y_pred))

    portees = {
        "referentiel_du_service": {
            "libelle": "les 8 categories du referentiel",
            "categories": REFERENTIEL,
            "n": len(REFERENTIEL),
            "f1_macro": round(float(f1_score(y, y_pred, average="macro",
                                             labels=REFERENTIEL, zero_division=0)), 4),
        },
        "categories_representees_au_test": {
            "libelle": "les categories qui ont au moins un ticket au test",
            "categories": presentes,
            "n": len(presentes),
            "f1_macro": round(float(f1_score(y, y_pred, average="macro",
                                             labels=presentes, zero_division=0)), 4),
        },
        "union_vraies_et_predites": {
            "libelle": "ce que le code calcule aujourd'hui, sans argument labels",
            "categories": union,
            "n": len(union),
            "f1_macro": round(float(f1_score(y, y_pred, average="macro",
                                             zero_division=0)), 4),
        },
    }

    print("jeu de test gele : %d tickets" % len(test))
    print("  categories presentes au test   : %d  %s" % (len(presentes), presentes))
    print("  categories prononcees au test  : %d  %s" % (len(predites), predites))
    print()
    for cle, p in portees.items():
        print("  %-32s n=%d   F1-macro %.4f" % (cle, p["n"], p["f1_macro"]))

    surnumeraires = sorted(set(y_pred) - set(y))
    print()
    print("categories prononcees mais absentes du test : %s" % (surnumeraires or "aucune"))
    print("ce sont elles qui gonflent le denominateur de la valeur publiee.")

    par_classe = {c: round(float(v), 4) for c, v in zip(
        REFERENTIEL, f1_score(y, y_pred, average=None, labels=REFERENTIEL, zero_division=0))}

    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "remarque": ("Le memoire annonce 0,5829 sur 8 categories ; le jeu de test gele "
                         "n'en contient que 5 et le code en moyenne 6."),
            "jeu": "data/splits/test.csv (jeu de test gele du pipeline)",
            "tickets": len(test),
            "seuil_de_confiance": seuil,
            "categories_prononcees_mais_absentes_du_test": surnumeraires,
            "portees": portees,
            "f1_par_categorie_du_referentiel": par_classe,
            "defaut": ("Le denominateur de la valeur publiee depend des categories que le "
                       "modele prononce, donc de ses erreurs : deux modeles de qualite egale "
                       "n'y sont pas compares a armes egales."),
        }, f, ensure_ascii=False, indent=2)
    print("\necrit : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
