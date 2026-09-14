# -*- coding: utf-8 -*-
"""Matrice de confusion du modele servi, protocole du pipeline.

Source des valeurs
------------------
helpdesk-ai/metrics/confusion_matrix_candidate.json, produit par la chaine de
traitement elle-meme. Aucune valeur n'est saisie a la main : le script lit le
fichier et trace ce qu'il contient.

Ce protocole est celui de la section 4.7.1 du memoire, distinct du protocole
stratifie des sections comparatives. Le decoupage n'est pas stratifie, de sorte
que trois des huit categories du referentiel n'ont aucun ticket de test :
Applicatifs figure en colonne sans figurer en ligne, Backup et Communication
sont absentes des deux.

Controle arithmetique automatique :
  - total = 356 tickets ;
  - exactitude = 292/356 = 0,8202, valeur publiee au tableau 4.5.

Sortie : report/img/ch04_confusion_production.png
"""
import io
import json
import os
import sys

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
from ch04_confusion_camembert import rendre  # noqa: E402

ARTEFACT = os.path.join(ICI, "..", "..", "helpdesk-ai", "metrics",
                        "confusion_matrix_candidate.json")
SORTIE = os.path.join(ICI, "..", "img", "ch04_confusion_production.png")

TOTAL, EXACTITUDE = 356, 0.8202


def main():
    with io.open(ARTEFACT, encoding="utf-8") as f:
        donnees = json.load(f)

    categories = donnees["labels"]
    M = np.array(donnees["matrix"], dtype=int)

    total = int(M.sum())
    justes = int(np.trace(M))
    exactitude = justes / float(total)
    assert total == TOTAL, "total %d, attendu %d" % (total, TOTAL)
    assert abs(exactitude - EXACTITUDE) < 5e-4, "exactitude %.4f" % exactitude

    titre = "Matrice de confusion du modèle servi en production"
    sous = ("356 tickets de test, protocole du pipeline, règles métier comprises\n"
            "F1-macro 0,5829 sur les 8 catégories, 0,6995 sur les 5 évaluables, "
            "exactitude 82,0 %")

    support, rappel = rendre(M, categories, titre, sous, SORTIE,
                             largeur=9.4, hauteur=6.0)

    print("total %d, corrects %d, exactitude %.4f" % (total, justes, exactitude))
    for c, s, r in zip(categories, support, rappel):
        print("  %-15s support %3d  rappel %s"
              % (c, s, "sans objet" if np.isnan(r) else "%.2f" % r))
    print("categories du referentiel absentes du jeu de test :",
          ", ".join(sorted({"Applicatifs", "Backup", "Communication",
                            "Infrastructure", "Microsoft", "Réseau",
                            "Système", "Sécurité"} - set(categories))))
    print("categorie presente sans aucun ticket reel :",
          ", ".join(donnees["classes_sans_support"]))
    print("ecrit :", os.path.normpath(SORTIE))


if __name__ == "__main__":
    main()
