# -*- coding: utf-8 -*-
"""Inscrit dans l'index du registre la metrique qui a reellement tranche.

Le defaut
---------
`model_registry.register()` ecrivait sous le nom `primary_metric` la F1-macro
calculee sur le referentiel entier. Or ce n'est pas elle qui decide : la porte
de promotion compare `f1_macro_classes_evaluables`, c'est-a-dire la moyenne sur
les seules categories representees au jeu de test (`promote.py:metrique_effective`).
Un nom affirmait donc une chose que le code ne faisait pas, et `promote --list`
affichait une colonne « metrique » qui n'etait pas celle de la decision.

Pour les versions deja enregistrees, la valeur de decision n'a pas disparu :
elle est dans le `metrics.json` de chaque version. Ce script la recopie dans
l'index. Il ne recalcule rien et ne touche pas au jeu de test gele.

Ce qu'il ne fait pas
--------------------
Il ne complete pas `primary_metric_portee` pour les entrees anterieures au
2026-10-09 : la portee de ces valeurs est inconnue, parce qu'elle suivait les
predictions du modele. Les laisser sans portee est l'information exacte, et
c'est ce que `promote --list` signale desormais par un « ? ».

Usage : python scripts/completer_portee_registre.py [--appliquer]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(RACINE, "models", "registry", "registry.json")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--appliquer", action="store_true",
                    help="ecrit l'index ; sans ce drapeau, se contente de montrer")
    a = ap.parse_args()

    with io.open(INDEX, encoding="utf-8") as f:
        index = json.load(f)

    change = 0
    for entree in index.get("versions", []):
        if entree.get("metrique_de_decision") is not None:
            continue
        chemin = os.path.join(RACINE, entree.get("path", ""), "metrics.json")
        if not os.path.exists(chemin):
            print("v%s : %s introuvable, laissee en l'etat" % (entree["version"], chemin))
            continue
        with io.open(chemin, encoding="utf-8") as f:
            mesures = json.load(f)
        valeur = mesures.get("f1_macro_classes_evaluables")
        portee = (mesures.get("f1_macro_heuristiques_portee") or {}).get("libelle")
        if valeur is None:
            print("v%s : aucune metrique de decision enregistree a l'epoque "
                  "(cle absente du metrics.json), laissee vide" % entree["version"])
            continue
        entree["metrique_de_decision"] = valeur
        if portee:
            entree["primary_metric_portee"] = portee
        change += 1
        print("v%-2s decision=%.4f   ref-8=%s%s"
              % (entree["version"], valeur, entree.get("primary_metric"),
                 "" if portee else "  (portee inconnue, anterieure au 2026-10-09)"))

    if not change:
        print("\nrien a completer.")
        return 0
    if not a.appliquer:
        print("\n%d entree(s) a completer. Relancez avec --appliquer." % change)
        return 0
    with io.open(INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print("\necrit : %s (%d entree(s))" % (INDEX, change))
    return 0


if __name__ == "__main__":
    sys.exit(main())
