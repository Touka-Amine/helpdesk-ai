# -*- coding: utf-8 -*-
"""Remesure le modele EN SERVICE avec la portee de metrique corrigee.

Pourquoi ce script plutot qu'un `dvc repro`
--------------------------------------------
La revue du 2026-10-09 a corrige la facon dont `src/pipeline/train.py` calcule
les moyennes par categorie : le denominateur est desormais fige sur les huit
categories du referentiel au lieu de suivre les categories que le modele
prononce. Les valeurs publiees dans `metrics/ml_eval.json` datent d'avant cette
correction.

Reentrainer pour les rafraichir changerait le modele servi, ce qui n'est pas le
but : on veut la MEME chaine, mesuree correctement. Ce script recharge donc
l'artefact de production et rejoue la seule evaluation.

Il ne touche ni au registre, ni au modele, ni a la porte de promotion. Il
reecrit `metrics/ml_eval.json` en conservant les cles que l'evaluation ne
produit pas, pour ne rien perdre de ce que d'autres outils y lisent.

Usage :
    python scripts/reevaluer_modele_servi.py --essai
    python scripts/reevaluer_modele_servi.py
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from datetime import datetime, timezone

import joblib

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.path.insert(0, os.path.join(RACINE, "src"))

from pipeline.train import evaluer  # noqa: E402
from pipeline import jeu_gele  # noqa: E402

TEST = os.path.join(RACINE, "data", "splits", "test.csv")
MODELE = os.path.join(RACINE, "models", "best_pipeline.pkl")
META = os.path.join(RACINE, "models", "model_metadata.json")
METRIQUES = os.path.join(RACINE, "metrics", "ml_eval.json")
CONFUSION = os.path.join(RACINE, "metrics", "confusion_matrix.json")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--essai", action="store_true", help="affiche sans rien reecrire")
    a = ap.parse_args()

    # Le pipeline a ete sauvegarde depuis un carnet ou RAGEngine vivait dans
    # __main__ : joblib le cherche au meme endroit.
    import __main__
    from rag.engine import RAGEngine
    __main__.RAGEngine = RAGEngine

    # Lecture de RAPPORT : on rafraichit des chiffres publies, aucun choix
    # n'en depend. Elle est inscrite, elle n'erode pas le jeu.
    test = jeu_gele.lire(
        jeu_gele.POUR_RAPPORTER,
        motif="reevaluation du modele en service, portee des metriques corrigee",
        lecteur="scripts/reevaluer_modele_servi.py",
    )
    with io.open(META, encoding="utf-8") as f:
        seuil = json.load(f).get("confidence_threshold", 0.60)
    pipeline = joblib.load(MODELE)

    neuf, confusion = evaluer(pipeline, test, seuil)

    ancien = {}
    if os.path.exists(METRIQUES):
        with io.open(METRIQUES, encoding="utf-8") as f:
            ancien = json.load(f)

    print("modele en service, jeu de test gele (%d tickets), seuil %.2f\n" % (len(test), seuil))
    print("%-34s %10s %10s" % ("indicateur", "avant", "apres"))
    print("-" * 56)
    for cle in ("f1_macro_ml", "f1_macro_heuristiques", "f1_macro_classes_evaluables",
                "precision_macro", "recall_macro", "accuracy"):
        av = ancien.get(cle)
        ap_ = neuf.get(cle)
        marque = "" if av == ap_ else "  <-- change"
        print("%-34s %10s %10s%s" % (cle, "n/a" if av is None else "%.4f" % av,
                                     "n/a" if ap_ is None else "%.4f" % ap_, marque))
    print("\nportee de f1_macro_heuristiques        : %d categories — %s"
          % (neuf["f1_macro_heuristiques_portee"]["n"],
             neuf["f1_macro_heuristiques_portee"]["libelle"]))
    print("portee de f1_macro_classes_evaluables  : %d categories — %s"
          % (neuf["f1_macro_classes_evaluables_portee"]["n"],
             neuf["f1_macro_classes_evaluables_portee"]["libelle"]))

    if a.essai:
        print("\nessai : rien n'a ete reecrit.")
        return 0

    fusion = dict(ancien)
    fusion.update(neuf)
    fusion["remesure_le"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    fusion["remesure_motif"] = (
        "portee des moyennes par categorie figee sur le referentiel ; "
        "meme modele, meme jeu de test, calcul corrige")
    with io.open(METRIQUES, "w", encoding="utf-8") as f:
        json.dump(fusion, f, ensure_ascii=False, indent=2)
    with io.open(CONFUSION, "w", encoding="utf-8") as f:
        json.dump(confusion, f, ensure_ascii=False, indent=2)
    print("\necrit : %s" % METRIQUES)
    print("ecrit : %s" % CONFUSION)
    return 0


if __name__ == "__main__":
    sys.exit(main())
