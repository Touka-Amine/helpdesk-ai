# -*- coding: utf-8 -*-
"""Signaux de gravite enonces par le demandeur (EF-13, version mesuree).

Ce que l'exigence demandait, et ce qu'on peut en tenir
-------------------------------------------------------
EF-13 : « Analyse de tonalite du message — indicateur d'urgence affiche ».

La mesure prealable (scripts/mesurer_tonalite.py, metrics/tonalite_eval.json)
etablit qu'il n'y a pas de tonalite a analyser dans ce corpus :

  - sur 25 termes d'urgence du francais courant, 20 sont ABSENTS : « urgent »,
    « critique », « immediat », « au plus vite », « prioritaire » n'apparaissent
    pas une seule fois dans 1 444 tickets ;
  - il n'y a AUCUN point d'exclamation dans tout le jeu d'entrainement ;
  - sur 97 mots qui separent la priorite, 95 n'apparaissent que sous un ou deux
    titres : ils reconnaissent un scenario, ils ne mesurent pas une humeur.

Les descriptions sont des courriels polis et gabarites. Un analyseur de tonalite
n'y trouverait rien, et en afficher un reviendrait a montrer du bruit.

Ce qui reste, et qui est vrai
------------------------------
Cinq termes de GRAVITE sont bien la, et ils ne decrivent pas une emotion mais un
fait : le demandeur dit que quelque chose est impossible, bloque, ou que des
donnees sont perdues. Ces enonces sont associes a la priorite haute au-dela du
taux de base, mesure sur le jeu d'entrainement :

    perte de donnees   77 % de priorite haute   contre 49 % de taux de base
    blocage            64 %
    impossibilite      61 %

Ce module les releve et les rend tels quels. Il n'attribue pas de note, ne
predit pas de priorite — scripts/../train_priorite.py a montre qu'une telle
prediction se trompe une fois sur deux — et n'interprete rien. Il surligne ce
que le demandeur a ecrit, pour qu'un administrateur qui parcourt une file le
voie sans lire chaque description.
"""
from __future__ import annotations

import re
import unicodedata

# Familles de signaux. Chaque motif est atteste dans le jeu d'entrainement ;
# ceux du lexique d'urgence qui n'y figuraient pas ont ete retires plutot que
# gardes « au cas ou ».
SIGNAUX: list[tuple[str, str, list[str]]] = [
    ("perte_de_donnees", "perte de données annoncée",
     [r"perte de donnees", r"donnees perdues", r"fichiers perdus"]),
    ("blocage", "blocage décrit",
     [r"bloqu(?:e|ee|es|ees|ant|ante)\b", r"paralys", r"arret(?:e|ee)?\b"]),
    # « impossibilite » a ete retiree apres mesure : elle se declenchait sur 629
    # tickets d'entrainement, soit 44 % du jeu, pour un ecart de +0,02 point sur
    # le taux de priorite haute. Un signal qui s'allume presque toujours et qui
    # ne distingue rien n'informe pas, il encombre — et il aurait dilue les trois
    # autres, qui eux portent de 0,13 a 0,28 point.
    ("indisponibilite", "service déclaré indisponible",
     [r"indisponible", r"inaccessible", r"hors service", r"ne repond plus"]),
]


def _normaliser(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def relever(titre: str, description: str) -> dict:
    """Les signaux de gravite que le texte enonce.

    Returns:
        dict :
            signaux   — liste de {code, libelle, extrait} dans l'ordre du texte
            n_signaux — combien de familles different se sont declenchees
            note      — AUCUNE. Ce module ne note pas : voir l'en-tete du fichier.
    """
    texte = "%s %s" % (titre or "", description or "")
    norme = _normaliser(texte)
    trouves = []
    for code, libelle, motifs in SIGNAUX:
        for motif in motifs:
            m = re.search(motif, norme)
            if m:
                debut = max(0, m.start() - 30)
                fin = min(len(norme), m.end() + 30)
                trouves.append({
                    "code": code,
                    "libelle": libelle,
                    "extrait": norme[debut:fin].strip(),
                })
                break
    return {"signaux": trouves, "n_signaux": len(trouves)}


def libelles(titre: str, description: str) -> list[str]:
    """Juste les libelles, pour un affichage en pastilles."""
    return [s["libelle"] for s in relever(titre, description)["signaux"]]
