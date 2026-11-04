# -*- coding: utf-8 -*-
"""Prepare une feuille de jugement a l'aveugle, et reporte les jugements.

Pourquoi a l'aveugle
--------------------
Le gabarit `data/knowledge/rag_eval_set.json` presente les candidats dans l'ordre
du moteur, avec leur rang et leur score. Annoter en voyant ces informations
revient a juger le moteur avec ce que le moteur affirme : on confirme son
classement au lieu de l'evaluer. Cette feuille masque rang et score, et melange
les candidats.

Pourquoi par paire distincte
----------------------------
Les quarante requetes ne portent que douze titres, et le vivier ne compte que
quarante et une resolutions. Il n'y a donc que 152 paires (titre, resolution)
reellement differentes : juger deux fois la meme paire ne produirait aucune
information et exposerait a se contredire. Le jugement est porte une fois par
paire, puis reporte sur toutes les requetes concernees.

Usage :
    python scripts/verification/preparer_annotation.py --feuille
    python scripts/verification/preparer_annotation.py --reporter
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import random
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GABARIT = os.path.join(RACINE, "data", "knowledge", "rag_eval_set.json")
FEUILLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feuille_jugement.json")
GRAINE = 42


def charger():
    with io.open(GABARIT, encoding="utf-8") as f:
        return json.load(f)


def paires(donnees):
    """{(titre, cle) -> {titre, description, categorie_requete, resolution, categorie_candidat}}"""
    out = {}
    for q in donnees["requetes"]:
        for c in q["candidats_a_annoter"]:
            cle = (q["titre"], c["cle"])
            if cle not in out:
                out[cle] = {
                    "titre": q["titre"],
                    "description": q["description"],
                    "categorie_requete": q["categorie"],
                    "resolution": c["resolution"],
                    "categorie_candidat": c["categorie"],
                }
    return out


def identifiant(titre, cle):
    return "P" + hashlib.sha1((titre + "||" + cle).encode("utf-8")).hexdigest()[:8]


def construire_feuille():
    donnees = charger()
    p = paires(donnees)
    items = []
    for (titre, cle), v in p.items():
        items.append({
            "id": identifiant(titre, cle),
            "requete_titre": titre,
            "requete_description": v["description"],
            "requete_categorie": v["categorie_requete"],
            "candidat_resolution": v["resolution"],
            "candidat_categorie": v["categorie_candidat"],
            # a remplir : true si la resolution aurait fait gagner du temps
            "utile": None,
        })
    # Melange : l'ordre du moteur ne doit pas transparaitre.
    random.Random(GRAINE).shuffle(items)

    entete = {
        "objet": "Feuille de jugement a l'aveugle pour l'evaluation du moteur de recherche.",
        "critere": ("La resolution proposee aurait-elle fait gagner du temps sur CE ticket ? "
                    "Oui si elle traite le probleme decrit, meme partiellement. Non si elle "
                    "traite autre chose, meme dans le meme domaine."),
        "ce_qui_est_masque": ["rang du candidat", "score du moteur", "ordre d'origine"],
        "n_paires": len(items),
        "note": ("Les paires sont distinctes : chaque couple (titre de requete, resolution) "
                 "n'apparait qu'une fois. Le report vers les quarante requetes est automatique."),
        "paires": items,
    }
    with io.open(FEUILLE, "w", encoding="utf-8") as f:
        json.dump(entete, f, ensure_ascii=False, indent=2)
    print("feuille ecrite : %s (%d paires)" % (FEUILLE, len(items)))
    return 0


def reporter():
    """Reporte les jugements de la feuille vers le gabarit d'evaluation."""
    if not os.path.exists(FEUILLE):
        print("feuille absente — lancer --feuille d'abord")
        return 1
    with io.open(FEUILLE, encoding="utf-8") as f:
        feuille = json.load(f)

    jugement = {}
    manquants = 0
    for item in feuille["paires"]:
        if item["utile"] is None:
            manquants += 1
            continue
        jugement[item["id"]] = bool(item["utile"])
    if manquants:
        print("%d paire(s) non jugee(s) — report refuse." % manquants)
        return 1

    donnees = charger()
    total_pertinents = 0
    for q in donnees["requetes"]:
        pertinents = []
        for c in q["candidats_a_annoter"]:
            if jugement.get(identifiant(q["titre"], c["cle"])):
                pertinents.append(c["cle"])
        q["pertinents"] = pertinents
        # Explicite : la requete a ete jugee, meme si rien n'a ete retenu. Sans ce
        # drapeau, l'evaluation confondrait « zero pertinent » et « non annotee »,
        # et ecarterait les requetes les plus difficiles.
        q["annote"] = True
        total_pertinents += len(pertinents)

    donnees["annotation"] = {
        "annotateur": "auteur du memoire, non consultant du service",
        "protocole": "jugement a l'aveugle, rang et score masques, paires distinctes melangees",
        "portee": ("Cette annotation remplace l'approximation par categorie, mais ne vaut pas "
                   "celle d'un consultant du service : elle juge si la resolution traite le "
                   "probleme decrit, non si elle aurait fait gagner du temps en pratique. "
                   "Elle est a confirmer."),
        "n_paires_jugees": len(jugement),
        "n_pertinents_reportes": total_pertinents,
    }
    with io.open(GABARIT, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=2)
    annotees = sum(1 for q in donnees["requetes"] if q["pertinents"])
    print("report effectue : %d paires jugees, %d pertinents, %d/%d requetes avec au moins un pertinent"
          % (len(jugement), total_pertinents, annotees, len(donnees["requetes"])))
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--feuille", action="store_true", help="construit la feuille de jugement")
    p.add_argument("--reporter", action="store_true", help="reporte les jugements vers le gabarit")
    a = p.parse_args()
    if a.feuille:
        sys.exit(construire_feuille())
    if a.reporter:
        sys.exit(reporter())
    p.print_help()
