# -*- coding: utf-8 -*-
"""Reconstitue le journal de lecture du jeu gele a partir du registre.

Le journal (`src/pipeline/jeu_gele.py`) est pose le 2026-10-09, apres la
remarque de l'encadrant. Les lectures anterieures ne s'y trouvent donc pas, et
un journal qui commence a zero laisserait croire que le jeu est neuf.

Le registre, lui, garde la trace de chaque arbitrage : un `promote` ou un
`reject` signifie que le jeu a ete lu pour trancher. Ce script relit cet
historique et inscrit les lectures correspondantes, marquees comme
reconstituees — on sait qu'elles ont eu lieu, on ne connait pas la valeur lue.

Le `bootstrap` n'est pas compte : adopter un modele preexistant ne compare rien.

Usage :
    python scripts/reconstituer_journal_jeu_gele.py --essai
    python scripts/reconstituer_journal_jeu_gele.py
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.path.insert(0, os.path.join(RACINE, "src"))

from pipeline import jeu_gele  # noqa: E402

REGISTRE = os.path.join(RACINE, "models", "registry", "registry.json")
ACTIONS_QUI_TRANCHENT = {"promote", "reject", "rollback"}


# Lectures decisionnelles du jeu gele par le volet RECHERCHE, trouvees le
# 2026-10-10 en verifiant la regle annoncee au chapitre 7 plutot qu'en la
# recitant. Elles ne lisent pas test.csv en direct : le gabarit d'annotation en
# descend, et tout ce qui est choisi sur ces requetes l'est donc sur le jeu gele.
# Les dates sont celles des fichiers produits, seule trace conservee.
LECTURES_RECHERCHE = [
    {
        "motif": "constitution du gabarit d'annotation du moteur de recherche : "
                 "tirage stratifie de 40 requetes dans le jeu gele",
        "lecteur": "src/pipeline/rag_eval.py --build-template",
        "date_reelle": "2026-10-03T20:13:00+00:00",
        "reference": "data/knowledge/rag_eval_set.json",
    },
    {
        "motif": "balayage du seuil de pertinence ayant retenu 0,35",
        "lecteur": "src/pipeline/rag_eval.py --balayage-seuil",
        "date_reelle": "2026-10-03T20:20:00+00:00",
        "reference": "metrics/rag_seuil_balayage.json (premiere version)",
    },
    {
        "motif": "balayage du seuil rejoue apres la correction de l'elargissement "
                 "semantique ; 0,35 confirme",
        "lecteur": "src/pipeline/rag_eval.py --balayage-seuil",
        "date_reelle": "2026-10-09T22:13:02+00:00",
        "reference": "metrics/rag_seuil_balayage.json",
    },
]


def reconstituer_la_recherche(essai: bool) -> int:
    """Inscrit les lectures du volet recherche, une fois et pas deux."""
    journal = jeu_gele._charger()
    deja_vues = {(l.get("lecteur"), l.get("date_reelle"))
                 for l in journal.get("lectures", [])}
    a_inscrire = [l for l in LECTURES_RECHERCHE
                  if (l["lecteur"], l["date_reelle"]) not in deja_vues]
    print("volet recherche : %d lecture(s) decisionnelle(s) connue(s), %d a inscrire"
          % (len(LECTURES_RECHERCHE), len(a_inscrire)))
    for l in a_inscrire:
        print("  %s  %s" % (l["date_reelle"][:19], l["motif"][:62]))
    if essai or not a_inscrire:
        return 0
    for l in a_inscrire:
        jeu_gele.inscrire(
            jeu_gele.POUR_DECIDER,
            motif=l["motif"],
            lecteur=l["lecteur"],
            date_reelle=l["date_reelle"],
            reference=l["reference"],
            provenance="indirecte : requetes tirees du jeu gele via le gabarit annote",
            reconstitue=True,
            note="inscrit apres coup : ces lectures precedent l'instrumentation "
                 "de rag_eval.py, posee le 2026-10-10",
        )
    return len(a_inscrire)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--essai", action="store_true", help="affiche sans rien inscrire")
    a = ap.parse_args()

    with io.open(REGISTRE, encoding="utf-8") as f:
        registre = json.load(f)
    arbitrages = [e for e in registre.get("history", [])
                  if e.get("action") in ACTIONS_QUI_TRANCHENT]

    deja = jeu_gele.lectures_decisionnelles()
    print("historique du registre : %d entrees, dont %d arbitrages"
          % (len(registre.get("history", [])), len(arbitrages)))
    print("journal actuel : %d lecture(s) de decision\n" % deja)
    for e in arbitrages:
        print("  %s  %-8s v%-3s %s" % (e.get("at", "")[:19], e.get("action"),
                                       e.get("version"), (e.get("reason") or "")[:52]))

    if a.essai:
        reconstituer_la_recherche(essai=True)
        print("\nessai : rien n'a ete inscrit.")
        return 0
    if deja:
        n_recherche = reconstituer_la_recherche(essai=False)
        if n_recherche:
            print("journal complete : %d lecture(s) de decision"
                  % jeu_gele.etat()["lectures_de_decision"])
        print("\nle journal porte deja des lectures de decision — rien n'est reinscrit, "
              "pour ne pas compter deux fois.")
        return 0

    for e in arbitrages:
        jeu_gele.inscrire(
            jeu_gele.POUR_DECIDER,
            motif="arbitrage de promotion : %s" % (e.get("reason") or e.get("action")),
            lecteur="src/pipeline/promote.py",
            version_concernee=e.get("version"),
            decision=e.get("action"),
            date_reelle=e.get("at"),
            reconstitue=True,
            note="inscrit apres coup depuis models/registry/registry.json ; "
                 "la valeur lue a l'epoque n'est pas connue",
        )
    etat = jeu_gele.etat()
    print("\njournal reconstitue : %d lecture(s) de decision" % etat["lectures_de_decision"])
    print("ecrit : %s" % os.path.relpath(jeu_gele.JOURNAL, RACINE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
