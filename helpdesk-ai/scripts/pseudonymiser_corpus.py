# -*- coding: utf-8 -*-
"""Remplace les personnes nommees par des pseudonymes, dans tout ce qui derive du corpus.

Ce que le script touche
-----------------------
Les tableaux produits par le projet : `data/processed`, `data/splits`,
`data/reference`, `data/curated`. Deux colonnes y sont remplacees, `Demandeur`
et `Assigne a` ; le reste des champs n'est pas modifie, parce que le releve
prealable a etabli qu'aucun nom ne figure dans le texte libre.

Ce que le script NE touche PAS, et pourquoi
--------------------------------------------
`data/raw/HelpDesk1.csv` reste en clair. C'est l'export que l'entreprise a
fourni, la seule piece qui atteste de l'origine des donnees, et l'ecraser serait
irreversible. Le passer en pseudonymes se demande explicitement, avec
`--inclure-export-origine`, et le script ecrit d'abord une copie de sauvegarde.

La table des comptes de l'application garde elle aussi les noms : un compte sans
nom ni adresse ne sert a rien. Ces donnees relevent de la duree de conservation
et du controle d'acces, traites ailleurs.

La cle
------
Lue dans la variable d'environnement PSEUDO_KEY. Sans elle le script refuse de
tourner : une cle tiree au hasard a chaque execution donnerait des pseudonymes
differents a chaque fois, et les tableaux cesseraient d'etre comparables.

Usage :
    PSEUDO_KEY="..." python scripts/pseudonymiser_corpus.py
    PSEUDO_KEY="..." python scripts/pseudonymiser_corpus.py --essai
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import shutil
import sys
from datetime import datetime, timezone

import pandas as pd

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "src"))

from data.pseudonymisation import (COLONNES_IDENTIFIANTES, CleManquante,  # noqa: E402
                                   cle, pseudonymiser_tableau)

DOSSIERS = ["data/processed", "data/splits", "data/reference", "data/curated"]
EXPORT_ORIGINE = os.path.join(RACINE, "data", "raw", "HelpDesk1.csv")
JOURNAL = os.path.join(RACINE, "metrics", "pseudonymisation.json")


def tableaux(inclure_origine: bool) -> list[str]:
    out = []
    for d in DOSSIERS:
        out.extend(sorted(glob.glob(os.path.join(RACINE, *d.split("/"), "*.csv"))))
    if inclure_origine and os.path.exists(EXPORT_ORIGINE):
        out.append(EXPORT_ORIGINE)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--essai", action="store_true",
                    help="montre ce qui serait fait, n'ecrit rien")
    ap.add_argument("--inclure-export-origine", action="store_true",
                    help="pseudonymise aussi data/raw/HelpDesk1.csv, apres sauvegarde")
    a = ap.parse_args()

    try:
        secret = cle()
    except CleManquante as e:
        print(str(e))
        return 1

    fichiers = tableaux(a.inclure_export_origine)
    print("%d tableau(x) a traiter%s" % (len(fichiers), " (essai)" if a.essai else ""))
    journal = {}
    for chemin in fichiers:
        rel = os.path.relpath(chemin, RACINE).replace("\\", "/")
        df = pd.read_csv(chemin)
        presentes = [c for c in COLONNES_IDENTIFIANTES if c in df.columns]
        if not presentes:
            print("  %-46s aucune colonne identifiante" % rel)
            continue
        if len(df) == 0:
            print("  %-46s tableau vide" % rel)
            journal[rel] = {"etat": "vide"}
            continue
        # `.all()` sur une colonne vide repond vrai : d'ou le test de longueur
        # ci-dessus, sans lequel un tableau vide passait pour deja traite.
        deja = all(df[c].astype(str).str.match(r"^(DEM|AGT)-[0-9a-f]{10}$").all()
                   for c in presentes)
        if deja:
            print("  %-46s deja pseudonymise" % rel)
            journal[rel] = {"etat": "deja_pseudonymise"}
            continue
        df, rapport = pseudonymiser_tableau(df, presentes, secret)
        journal[rel] = {"etat": "pseudonymise", "colonnes": rapport}
        print("  %-46s %s" % (rel, ", ".join(
            "%s : %d personnes" % (c, r["personnes_distinctes"]) for c, r in rapport.items())))
        if not a.essai:
            if chemin == EXPORT_ORIGINE:
                sauvegarde = chemin + ".avant_pseudonymisation"
                if not os.path.exists(sauvegarde):
                    shutil.copy2(chemin, sauvegarde)
                    print("      sauvegarde : %s" % os.path.basename(sauvegarde))
            df.to_csv(chemin, index=False)

    if a.essai:
        print("\nessai : rien n'a ete ecrit.")
        return 0

    with io.open(JOURNAL, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "exigence": "ENF-04 (b)",
            "methode": "HMAC-SHA256 tronque a 10 caracteres, cle hors du depot",
            "colonnes": list(COLONNES_IDENTIFIANTES),
            "export_origine_inclus": bool(a.inclure_export_origine),
            "tableaux": journal,
        }, f, ensure_ascii=False, indent=2)
    print("\necrit : %s" % JOURNAL)
    print("verifier avec : python scripts/verification/audit_donnees_personnelles.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
