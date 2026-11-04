# -*- coding: utf-8 -*-
"""Journal et budget de lecture du jeu de test gele.

Le probleme
-----------
Un jeu de test ne se degrade pas d'un coup : il se degrade par usage. Chaque
fois qu'on le lit pour DECIDER — promouvoir ou non un candidat, retenir un
reglage, choisir une variante — une part de son information passe dans le
modele retenu, et le chiffre qu'il rendra la fois suivante est un peu moins une
mesure de generalisation. Au bout d'un certain nombre de lectures, il ne mesure
plus rien : il est devenu un jeu de validation, sans que personne ne l'ait
decide.

`src/pipeline/promote.py` lisait ce jeu a chaque arbitrage, sans que rien ne
compte les lectures ni ne les rende visibles. Rien n'etait faux ; simplement,
la derive ne se voyait pas.

Ce que ce module apporte
------------------------
Il ne protege pas le jeu, il le rend AUDITABLE, ce qui est la seule chose qu'un
programme puisse faire ici. Trois mecanismes :

  1. un journal, `data/reference/journal_jeu_gele.json`, ou chaque lecture
     s'inscrit avec sa date, son motif et ce qu'elle a servi a decider ;
  2. une distinction entre les lectures qui DECIDENT et celles qui RAPPORTENT.
     Seules les premieres erodent le jeu. Recalculer une metrique pour un
     tableau du memoire n'influence aucun choix ;
  3. un budget, declare dans `params.yaml`. Une fois atteint, la porte de
     promotion refuse d'arbitrer et renvoie a une decision humaine : constituer
     une nouvelle reference a partir de tickets de production recents, ou
     assumer par ecrit la lecture supplementaire.

Ce que le module ne fait pas
-----------------------------
Il n'empeche personne de lire le fichier directement. Un budget est une
convention outillee, pas un verrou ; sa valeur est de rendre une transgression
visible dans un fichier versionne plutot que silencieuse.
"""
from __future__ import annotations

import io
import json
import os
from datetime import datetime, timezone

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Le chemin du journal se laisse deplacer par l'environnement, et il le faut.
# `tests/test_promote_idempotence.py` lance promote.py dans un SOUS-PROCESSUS :
# un monkeypatch d'attribut n'y parvient pas, et jusqu'au 2026-10-10 ces essais
# ecrivaient leurs lectures dans le journal du depot. Le compte des lectures
# decisionnelles n'en a pas souffert — les essais n'empruntent pas ce chemin —
# mais celui des lectures de rapport melait des executions d'essai a de vraies.
JOURNAL = os.environ.get("JOURNAL_JEU_GELE") or os.path.join(
    RACINE, "data", "reference", "journal_jeu_gele.json")

# Les deux natures de lecture. Seule la premiere consomme le budget.
POUR_DECIDER = "decision"
POUR_RAPPORTER = "rapport"


class BudgetEpuise(RuntimeError):
    """Levee quand une lecture decisionnelle depasserait le budget declare."""


def _charger() -> dict:
    if not os.path.exists(JOURNAL):
        return {
            "objet": ("Chaque lecture du jeu de test gele, avec son motif. Les lectures "
                      "« decision » erodent le jeu ; les lectures « rapport » ne font que "
                      "le citer."),
            "jeu": "data/reference/test_reference.csv",
            "lectures": [],
        }
    with io.open(JOURNAL, encoding="utf-8") as f:
        return json.load(f)


def _ecrire(journal: dict) -> None:
    os.makedirs(os.path.dirname(JOURNAL), exist_ok=True)
    with io.open(JOURNAL, "w", encoding="utf-8") as f:
        json.dump(journal, f, ensure_ascii=False, indent=2)


def lectures_decisionnelles() -> int:
    """Combien de fois le jeu a servi a trancher."""
    return sum(1 for enr in _charger()["lectures"] if enr.get("nature") == POUR_DECIDER)


def etat() -> dict:
    journal = _charger()
    decisions = [enr for enr in journal["lectures"] if enr.get("nature") == POUR_DECIDER]
    rapports = [enr for enr in journal["lectures"] if enr.get("nature") != POUR_DECIDER]
    return {
        "lectures_totales": len(journal["lectures"]),
        "lectures_de_decision": len(decisions),
        "lectures_de_rapport": len(rapports),
        "derniere_lecture": journal["lectures"][-1]["date"] if journal["lectures"] else None,
    }


def verifier_budget(budget: int | None) -> None:
    """Leve si une lecture decisionnelle de plus depasserait le budget.

    Un budget absent ou nul desactive le controle : le journal continue de
    tenir le compte, mais rien n'est refuse.
    """
    if not budget:
        return
    deja = lectures_decisionnelles()
    if deja >= int(budget):
        raise BudgetEpuise(
            "Le jeu de test gele a deja servi a trancher %d fois, pour un budget de %d. "
            "Une lecture de plus en ferait un jeu de validation : le chiffre qu'il rend "
            "cesserait de mesurer la generalisation.\n"
            "Deux issues, toutes deux humaines : constituer une nouvelle reference a "
            "partir de tickets de production recents (supprimer %s et relancer le "
            "decoupage), ou assumer la lecture par ecrit avec --force, qui l'inscrit au "
            "journal comme telle."
            % (deja, int(budget), "data/reference/test_reference.csv"))


def inscrire(nature: str, motif: str, lecteur: str, **details) -> dict:
    """Inscrit une lecture au journal et retourne l'entree ecrite."""
    journal = _charger()
    entree = {
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "nature": nature,
        "lecteur": lecteur,
        "motif": motif,
    }
    entree.update({k: v for k, v in details.items() if v is not None})
    journal["lectures"].append(entree)
    journal["resume"] = {
        "lectures_de_decision": sum(1 for enr in journal["lectures"]
                                    if enr.get("nature") == POUR_DECIDER),
        "lectures_de_rapport": sum(1 for enr in journal["lectures"]
                                   if enr.get("nature") != POUR_DECIDER),
    }
    _ecrire(journal)
    return entree


# Le jeu de test gele, tel que le pipeline l'expose. `split.py` l'ecrit depuis
# data/reference/test_reference.csv, dont il est la copie de travail. Deplacable
# par l'environnement pour la meme raison que le journal.
CHEMIN_JEU = os.environ.get("CHEMIN_JEU_GELE") or os.path.join(
    RACINE, "data", "splits", "test.csv")


def lire(nature: str, motif: str, lecteur: str, budget: int | None = None, **details):
    """Ouvre le jeu de test gele EN S'INSCRIVANT au journal, et rend le DataFrame.

    Pourquoi passer par ici plutot que par `pd.read_csv`
    ----------------------------------------------------
    Jusqu'au 2026-10-10, seule `promote.py` s'inscrivait. Neuf autres points
    d'entree du depot ouvraient le meme fichier sans rien declarer, dont deux qui
    TRANCHENT : `scripts/arbitrage_modele_servi.py`, qui choisit la configuration
    servie, et le balayage de seuil de `rag_eval.py`, qui a retenu 0,35. Le
    journal decrivait donc une porte, pas l'usage du fichier.

    Le budget n'est pas applique ici. Il arrete la porte de promotion, parce que
    c'est la qu'une lecture change le modele servi ; ailleurs, un refus
    interromprait une mesure sans rien proteger. Une lecture decisionnelle qui
    depasse le budget est donc inscrite, et marquee `hors_budget`.
    """
    import pandas as pd

    hors = None
    if nature == POUR_DECIDER and budget and lectures_decisionnelles() >= int(budget):
        hors = True
        print("[jeu_gele] AVERTISSEMENT : %d lecture(s) decisionnelle(s) deja inscrites "
              "pour un budget de %s. Celle-ci est inscrite hors budget."
              % (lectures_decisionnelles(), budget))
    inscrire(nature, motif=motif, lecteur=lecteur, hors_budget=hors, **details)
    return pd.read_csv(CHEMIN_JEU, encoding="utf-8")
