# -*- coding: utf-8 -*-
"""Fait relire une partie de l'annotation RAG par un consultant du service.

La remarque
-----------
L'encadrant demande, « si possible », de faire valider au moins une partie de
l'annotation RAG par un consultant du service. Les 152 paires de
`feuille_jugement.json` ont ete jugees par l'auteur du memoire : le chapitre 6
le dit, et en tire la portee du resultat. Ce script fournit l'instrument qui
manquait pour lever la reserve au lieu de la declarer.

Ce qu'il fait
-------------
  --tirer N     ecrit un extrait de N paires, A L'AVEUGLE, que le consultant
                remplit. Ni rang, ni score, ni le jugement de l'auteur.
  --comparer    relit l'extrait rempli, donne l'accord brut, le kappa de Cohen,
                la liste des desaccords, et ce que le jugement du consultant
                changerait au compte de paires utiles.

Ce qu'un extrait de quarante paires peut etablir, et ce qu'il ne peut pas
------------------------------------------------------------------------
Il peut montrer que les deux jugements se rejoignent, ou qu'ils divergent, et
sur quel genre de paire. Il ne peut pas donner un kappa a la deuxieme decimale :
avec une quarantaine de paires dont six positives en tirage uniforme,
l'intervalle reste large. C'est une verification d'ordre de grandeur, et le
memoire doit la presenter comme telle.

Le tirage est uniforme par defaut. `--equilibrer` tire autant de paires jugees
utiles que de paires jugees inutiles : l'accord sur les positives se mesure
alors mieux, mais les marges du tableau ne sont plus celles du jeu complet et le
kappa s'en trouve fausse. Le script le rappelle a l'ecran et dans le fichier.

Usage :
    python scripts/verification/revue_consultant.py --tirer 40
    python scripts/verification/revue_consultant.py --comparer
"""
from __future__ import annotations

import argparse
import io
import json
import os
import random
import sys
from datetime import datetime, timezone

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
FEUILLE = os.path.join(ICI, "feuille_jugement.json")
EXTRAIT = os.path.join(ICI, "revue_consultant.json")
GRAINE = 42


def charger_feuille() -> dict:
    with io.open(FEUILLE, encoding="utf-8") as f:
        return json.load(f)


def tirer(n: int, equilibrer: bool) -> int:
    feuille = charger_feuille()
    paires = feuille["paires"]
    alea = random.Random(GRAINE)

    if equilibrer:
        utiles = [p for p in paires if p.get("utile") is True]
        autres = [p for p in paires if p.get("utile") is not True]
        moitie = min(n // 2, len(utiles))
        choix = alea.sample(utiles, moitie) + alea.sample(autres, min(n - moitie, len(autres)))
        note_tirage = ("tirage equilibre : autant de paires jugees utiles par l'auteur que "
                       "d'inutiles. L'accord sur les positives se mesure mieux, mais les "
                       "marges ne sont plus celles du jeu complet : le kappa est fausse et "
                       "ne doit pas etre lu comme celui des 152 paires.")
    else:
        choix = alea.sample(paires, min(n, len(paires)))
        note_tirage = ("tirage uniforme sur les 152 paires, graine %d. Les marges sont celles "
                       "du jeu complet ; en contrepartie l'extrait ne contient qu'une poignee "
                       "de paires jugees utiles." % GRAINE)

    alea.shuffle(choix)
    sortie = {
        "objet": "Revue par un consultant du service d'un extrait de l'annotation RAG.",
        "critere": feuille["critere"],
        "consigne": [
            "Pour chaque paire, repondre a la question du critere par true ou false "
            "dans le champ « utile_consultant ».",
            "Ne pas modifier le champ « id ».",
            "Le jugement de l'auteur n'est pas montre : c'est voulu, les deux doivent "
            "etre portes independamment.",
            "Une paire sur laquelle vous hesitez doit etre laissee a null et signalee "
            "dans « commentaire » : une hesitation est une information, pas un echec.",
        ],
        "ce_qui_est_masque": ["le rang du candidat", "son score", "le jugement de l'auteur"],
        "tirage": note_tirage,
        "n_paires_extraites": len(choix),
        "n_paires_totales": feuille["n_paires"],
        "annotateur_de_reference": feuille["annotateur"],
        "consultant": "<nom, et date de la relecture>",
        "paires": [{
            "id": p["id"],
            "requete_titre": p["requete_titre"],
            "requete_description": p["requete_description"],
            "requete_categorie": p["requete_categorie"],
            "candidat_resolution": p["candidat_resolution"],
            "candidat_categorie": p["candidat_categorie"],
            "utile_consultant": None,
            "commentaire": "",
        } for p in choix],
    }
    with io.open(EXTRAIT, "w", encoding="utf-8") as f:
        json.dump(sortie, f, ensure_ascii=False, indent=2)
    print("ecrit : %s" % EXTRAIT)
    print("%d paires sur %d, %s" % (len(choix), feuille["n_paires"],
                                    "tirage equilibre" if equilibrer else "tirage uniforme"))
    print("\nA remettre au consultant. Le champ a remplir est « utile_consultant ».")
    return 0


def kappa_de_cohen(a: list, b: list) -> float | None:
    """Accord corrige du hasard. None si une des deux colonnes est constante."""
    n = len(a)
    if not n:
        return None
    accord = sum(1 for x, y in zip(a, b) if x == y) / n
    pa1 = sum(1 for x in a if x) / n
    pb1 = sum(1 for x in b if x) / n
    hasard = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    if abs(1 - hasard) < 1e-12:
        return None
    return (accord - hasard) / (1 - hasard)


def comparer() -> int:
    if not os.path.exists(EXTRAIT):
        print("extrait introuvable : %s\nLancez d'abord --tirer." % EXTRAIT)
        return 1
    with io.open(EXTRAIT, encoding="utf-8") as f:
        extrait = json.load(f)
    reference = {p["id"]: bool(p.get("utile")) for p in charger_feuille()["paires"]}

    juges, auteur, consultant, desaccords, hesitations = [], [], [], [], []
    for p in extrait["paires"]:
        v = p.get("utile_consultant")
        if v is None:
            hesitations.append(p)
            continue
        if p["id"] not in reference:
            print("paire %s absente de la feuille de reference, ignoree" % p["id"])
            continue
        juges.append(p["id"])
        a, c = reference[p["id"]], bool(v)
        auteur.append(a)
        consultant.append(c)
        if a != c:
            desaccords.append({"id": p["id"], "requete": p["requete_titre"],
                               "candidat": p["candidat_resolution"][:90],
                               "auteur": a, "consultant": c,
                               "commentaire": p.get("commentaire", "")})

    if not juges:
        print("aucune paire remplie : le champ « utile_consultant » est partout a null.")
        return 1

    n = len(juges)
    accord = sum(1 for a, c in zip(auteur, consultant) if a == c) / n
    k = kappa_de_cohen(auteur, consultant)
    print("paires relues et remplies : %d (%d laissees en hesitation)" % (n, len(hesitations)))
    print("accord brut                : %.4f  (%d/%d)" % (accord, round(accord * n), n))
    print("kappa de Cohen             : %s" % ("indefini (un jugement est constant)"
                                               if k is None else "%.4f" % k))
    print("paires jugees utiles       : auteur %d, consultant %d"
          % (sum(auteur), sum(consultant)))
    if desaccords:
        print("\ndesaccords (%d) :" % len(desaccords))
        for d in desaccords:
            print("  %s  auteur=%-5s consultant=%-5s  %s | %s"
                  % (d["id"], d["auteur"], d["consultant"], d["requete"][:38], d["candidat"][:48]))

    rapport = {
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "remarque": "Faire valider une partie de l'annotation RAG par un consultant du service.",
        "consultant": extrait.get("consultant"),
        "tirage": extrait.get("tirage"),
        "n_paires_relues": n,
        "n_hesitations": len(hesitations),
        "accord_brut": round(accord, 4),
        "kappa_de_cohen": None if k is None else round(k, 4),
        "paires_utiles_auteur": int(sum(auteur)),
        "paires_utiles_consultant": int(sum(consultant)),
        "desaccords": desaccords,
        "lecture": ("Un extrait de cette taille donne un ordre de grandeur de l'accord, "
                    "pas un kappa a la deuxieme decimale. Les desaccords sont plus "
                    "instructifs que le taux : ils disent sur quel genre de paire les deux "
                    "jugements divergent."),
    }
    chemin = os.path.join(RACINE, "metrics", "revue_consultant.json")
    with io.open(chemin, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)
    print("\necrit : %s" % chemin)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tirer", type=int, metavar="N",
                    help="ecrit un extrait de N paires a l'aveugle")
    ap.add_argument("--equilibrer", action="store_true",
                    help="avec --tirer : autant de paires jugees utiles que d'inutiles")
    ap.add_argument("--comparer", action="store_true",
                    help="relit l'extrait rempli et donne l'accord")
    a = ap.parse_args()
    if a.tirer:
        return tirer(a.tirer, a.equilibrer)
    if a.comparer:
        return comparer()
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
