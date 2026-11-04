# -*- coding: utf-8 -*-
"""Ecart entre le texte d'entrainement et le texte reellement soumis au modele.

Pourquoi ce script existe
-------------------------
Le classifieur est entraine sur la colonne `text_clean`, construite par
`build_text_for_model(titre, description)`. L'application, elle, n'envoyait que
la description : le titre, qui porte l'essentiel du signal dans un corpus
organise par scenarios, n'atteignait jamais le modele. Le memoire mesurait donc
un systeme que le service n'executait pas.

Le defaut est corrige dans api/predictor.py et api/services/ai_service.py, et
verrouille par tests/test_coherence_entrainement.py. Ce script chiffre l'ecart
qui existait, pour que les valeurs citees au chapitre 6 soient tracables et non
rapportees de memoire.

Protocole
---------
  - jeu de test GELE du pipeline, data/splits/test.csv, 356 tickets ;
  - modele servi, models/best_pipeline.pkl, inchange entre les deux variantes :
    seul le texte d'entree change ;
  - regles metier telles qu'elles figurent dans src/models/heuristics.py ;
  - seuil de confiance lu dans models/model_metadata.json.

Sortie : metrics/coherence_entree_modele.json

Usage :
    python scripts/coherence_entree_modele.py
"""
import io
import json
import os
import sys
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.path.insert(0, os.path.join(RACINE, "src"))

from sklearn.metrics import accuracy_score, f1_score

from data.preprocess import clean_text, build_text_for_model
from models.heuristics import apply_heuristics

TEST = os.path.join(RACINE, "data", "splits", "test.csv")
MODELE = os.path.join(RACINE, "models", "best_pipeline.pkl")
META = os.path.join(RACINE, "models", "model_metadata.json")
SORTIE = os.path.join(RACINE, "metrics", "coherence_entree_modele.json")

# Seuil au-dela duquel le filtre de categorie de la recherche de cas comparables
# s'active. C'est sur lui que l'ecart de confiance se repercute.
SEUIL_FILTRE_RAG = 0.70

# Une seule definition du referentiel pour tout le depot : celle du pipeline.
from pipeline.train import REFERENTIEL  # noqa: E402
from pipeline import jeu_gele  # noqa: E402


def mesurer(pipeline, textes, bruts, verite, classes, seuil_confiance):
    proba = pipeline.predict_proba(textes)
    pred = classes[proba.argmax(axis=1)]
    conf = proba.max(axis=1)

    avec = [apply_heuristics(b, p, float(c), threshold=seuil_confiance)["categorie"]
            for b, p, c in zip(bruts, pred, conf)]

    # Denominateur fige sur le referentiel du service (revue du 2026-10-09).
    #
    # Ce script passait `labels=sorted(set(verite) | set(pred) | set(avec))`,
    # c'est-a-dire un argument explicite mais calcule sur les PREDICTIONS. Le
    # denominateur variait donc d'une variante a l'autre, et c'est precisement
    # ce que l'on cherche a comparer ici : deux entrees du meme modele. Une
    # variante qui prononce une categorie de plus etait divisee par un nombre
    # plus grand, a qualite egale.
    #
    # L'ecart publie entre les deux variantes etait mesure avec ce biais.
    etiquettes = list(REFERENTIEL)
    return {
        "modele_seul": {
            "exactitude": round(float(accuracy_score(verite, pred)), 4),
            "f1_macro": round(float(f1_score(verite, pred, average="macro",
                                             labels=etiquettes, zero_division=0)), 4),
        },
        "avec_regles": {
            "exactitude": round(float(accuracy_score(verite, avec)), 4),
            "f1_macro": round(float(f1_score(verite, avec, average="macro",
                                             labels=etiquettes, zero_division=0)), 4),
        },
        "confiance": {
            "moyenne": round(float(conf.mean()), 4),
            "mediane": round(float(np.median(conf)), 4),
            "part_sous_seuil_confiance": round(float((conf < seuil_confiance).mean()), 4),
            "part_sous_seuil_filtre_rag": round(float((conf < SEUIL_FILTRE_RAG).mean()), 4),
        },
    }


def main():
    # Lecture de RAPPORT : mesure de l'ecart entre deux entrees, aucun choix.
    test = jeu_gele.lire(
        jeu_gele.POUR_RAPPORTER,
        motif="ecart entre l'entree d'entrainement et l'entree de production",
        lecteur="scripts/coherence_entree_modele.py",
    )
    with io.open(META, encoding="utf-8") as f:
        seuil_confiance = json.load(f).get("confidence_threshold", 0.60)

    pipeline = joblib.load(MODELE)
    classes = np.asarray(pipeline.classes_)
    verite = test["Catégorie"].tolist()

    titres = test["Titre"].fillna("").tolist()
    descriptions = test["Description"].fillna("").tolist()
    # Texte brut soumis aux regles : inchange d'une variante a l'autre, les
    # regles ont toujours vu le titre.
    bruts = [("%s %s" % (t, d)).strip() for t, d in zip(titres, descriptions)]

    variantes = {
        "description_seule": {
            "libelle": "Ancien comportement : l'API ne transmettait que la description",
            "textes": [clean_text(d) for d in descriptions],
        },
        "titre_et_description": {
            "libelle": "Comportement corrige : titre puis description, comme a l'entrainement",
            "textes": [build_text_for_model(t, d) for t, d in zip(titres, descriptions)],
        },
    }

    resultats = {}
    for cle, v in variantes.items():
        resultats[cle] = {"libelle": v["libelle"]}
        resultats[cle].update(
            mesurer(pipeline, v["textes"], bruts, verite, classes, seuil_confiance))

    avant, apres = resultats["description_seule"], resultats["titre_et_description"]
    rapport = {
        "date": datetime.now(timezone.utc).isoformat(),
        "objet": ("Ecart mesure entre le texte d'entrainement et le texte que "
                  "l'application soumettait au modele. Corrige depuis."),
        "protocole": {
            "jeu": "data/splits/test.csv (jeu de test gele du pipeline)",
            "n_tickets": int(len(test)),
            "modele": "models/best_pipeline.pkl, identique pour les deux variantes",
            "seuil_confiance": seuil_confiance,
            "seuil_filtre_rag": SEUIL_FILTRE_RAG,
        },
        "variantes": resultats,
        "ecarts": {
            "exactitude_modele_seul": round(
                apres["modele_seul"]["exactitude"] - avant["modele_seul"]["exactitude"], 4),
            "f1_avec_regles": round(
                apres["avec_regles"]["f1_macro"] - avant["avec_regles"]["f1_macro"], 4),
            "confiance_moyenne": round(
                apres["confiance"]["moyenne"] - avant["confiance"]["moyenne"], 4),
        },
        "lecture": ("Les regles metier recoivent le texte brut, titre compris, dans "
                    "les deux variantes : elles rattrapent l'essentiel de l'ecart "
                    "d'exactitude. L'effet qui subsiste porte sur la confiance, donc "
                    "sur le filtre de categorie de la recherche de cas comparables."),
    }

    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)

    for cle, r in resultats.items():
        print("%-22s modele seul %.1f%% (F1 %.4f) | avec regles %.1f%% (F1 %.4f) "
              "| confiance %.4f | sous %.2f : %.0f%%"
              % (cle, 100 * r["modele_seul"]["exactitude"], r["modele_seul"]["f1_macro"],
                 100 * r["avec_regles"]["exactitude"], r["avec_regles"]["f1_macro"],
                 r["confiance"]["moyenne"], SEUIL_FILTRE_RAG,
                 100 * r["confiance"]["part_sous_seuil_filtre_rag"]))
    print("ecrit %s" % os.path.relpath(SORTIE, RACINE))


if __name__ == "__main__":
    main()
