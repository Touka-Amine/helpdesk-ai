# -*- coding: utf-8 -*-
"""Construit la liste des formules de civilite, sur le seul jeu d'entrainement (EF-11).

La regle
--------
Une ligne de description qui revient sous beaucoup de titres differents
n'appartient a aucun scenario, donc ne decrit aucun probleme : c'est une
formule. « Cordialement. » apparait sous tous les titres du corpus ; « Microsoft
Office affiche un message "Produit non active" » sous un seul.

Le seuil est fixe a la moitie des titres d'entrainement. Un ticket du jeu de
test ne participe pas a la construction : la liste ne doit rien devoir aux
donnees qui servent a juger le systeme.

Le script affiche aussi ce que le retrait fait gagner, mesure sur le jeu
d'entrainement : c'est ce chiffre qui dit si l'exigence EF-11 apporte quelque
chose ou non.

Sorties : models/formules_civilite.json, metrics/resume_eval.json
"""
from __future__ import annotations

import collections
import io
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "src"))

from models.resume import _clef, recharger, resumer  # noqa: E402
from pipeline import jeu_gele  # noqa: E402

TRAIN = os.path.join(RACINE, "data", "splits", "train.csv")
TEST = os.path.join(RACINE, "data", "splits", "test.csv")
SORTIE = os.path.join(RACINE, "models", "formules_civilite.json")
METRIQUES = os.path.join(RACINE, "metrics", "resume_eval.json")

PART_DES_TITRES = 0.5


def main():
    train = pd.read_csv(TRAIN)
    n_titres = train["Titre"].nunique()
    seuil = max(2, int(PART_DES_TITRES * n_titres))

    titres_par_ligne = collections.defaultdict(set)
    forme_lisible = {}
    for titre, desc in zip(train["Titre"], train["Description"].fillna("")):
        for ligne in (l.strip() for l in desc.splitlines()):
            if not ligne:
                continue
            k = _clef(ligne)
            titres_par_ligne[k].add(titre)
            forme_lisible.setdefault(k, ligne)

    formules = sorted((forme_lisible[k] for k, t in titres_par_ligne.items()
                       if len(t) >= seuil), key=str.lower)
    print("%d titres d'entrainement, seuil a %d titres" % (n_titres, seuil))
    print("%d formules retenues :" % len(formules))
    for f in formules:
        print("   %-70s %d titres" % (f[:70], len(titres_par_ligne[_clef(f)])))

    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({
            "regle": "ligne presente sous au moins %d des %d titres du jeu d'entrainement"
                     % (seuil, n_titres),
            "jeu": "data/splits/train.csv — le jeu de test ne participe pas",
            "formules": formules,
        }, f, ensure_ascii=False, indent=2)
    recharger()

    # Ce que le retrait fait gagner, sur l'entrainement ET sur le test. Le test
    # ne sert ici qu'a verifier que la liste tient sur des scenarios inedits ;
    # elle n'a pas ete construite dessus.
    mesures = {}
    # Lecture de RAPPORT : le gain du resume est mesure sur le jeu gele, mais
    # les formules sont minees sur l'entrainement seul.
    test_gele = jeu_gele.lire(
        jeu_gele.POUR_RAPPORTER,
        motif="mesure du gain du resume extractif sur scenarios inedits",
        lecteur="scripts/construire_formules.py",
    )
    for nom, df in (("entrainement", train), ("test_gele", test_gele)):
        resumes = [resumer(t, d) for t, d in zip(df["Titre"], df["Description"].fillna(""))]
        compressions = [r["compression"] for r in resumes]
        mesures[nom] = {
            "tickets": len(df),
            "mots_origine_median": int(np.median([r["mots_origine"] for r in resumes])),
            "mots_resume_median": int(np.median([r["mots_resume"] for r in resumes])),
            "compression_mediane": round(float(np.median(compressions)), 4),
            "compression_moyenne": round(float(np.mean(compressions)), 4),
            "tickets_sans_gain": int(sum(1 for c in compressions if c <= 0.001)),
        }
        m = mesures[nom]
        print("\n%-14s %d mots -> %d mots, soit %.1f %% retires (mediane) ; "
              "%d ticket(s) sans gain"
              % (nom, m["mots_origine_median"], m["mots_resume_median"],
                 100 * m["compression_mediane"], m["tickets_sans_gain"]))

    with io.open(METRIQUES, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "exigence": "EF-11 — resume automatique du ticket",
            "methode": "retrait extractif des formules de civilite, aucune generation",
            "n_formules": len(formules),
            "seuil_titres": seuil,
            "mesures": mesures,
        }, f, ensure_ascii=False, indent=2)
    print("\necrit : %s" % SORTIE)
    print("ecrit : %s" % METRIQUES)
    return 0


if __name__ == "__main__":
    sys.exit(main())
