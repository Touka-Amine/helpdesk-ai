# -*- coding: utf-8 -*-
"""Resume extractif d'un ticket, par retrait des formules (EF-11).

Ce que l'exigence demande
-------------------------
EF-11, priorite moyenne : « Resume automatique du ticket — resume affiche a
l'administrateur ». Elle n'avait pas ete traitee.

Pourquoi ce n'est pas un resume au sens ou on l'entend d'habitude
------------------------------------------------------------------
Une description de ce corpus fait 33 mots en mediane. Il n'y a rien a resumer
au sens d'une reformulation : un modele de langage rendrait 15 mots la ou le
lecteur en lit 33, pour un gain nul et un risque d'invention.

En revanche, ces 33 mots sont un courriel. Ils commencent par une civilite et
finissent par une formule de politesse, et ces deux morceaux ne disent rien du
probleme. Les retirer laisse la substance, et c'est ce que ce module fait.

Comment les formules sont reconnues
------------------------------------
Pas par une liste ecrite a la main, qui manquerait les variantes. Par une regle
mesurable : une ligne qui revient sous BEAUCOUP DE TITRES DIFFERENTS n'appartient
a aucun scenario, donc ne decrit aucun probleme. « Cordialement. » apparait sous
les 58 titres du corpus ; « Microsoft Office affiche un message "Produit non
active" » sous un seul.

Le seuil est fixe a la moitie des titres. La liste est construite a partir du
JEU D'ENTRAINEMENT seul, par scripts/construire_formules.py, et rangee dans
`models/formules_civilite.json`. Un ticket de test ne participe pas a sa
construction.

Repli : si la liste n'est pas disponible, le resume rend la description telle
quelle. Un administrateur voit alors ce qu'il voyait avant, jamais rien de faux.
"""
from __future__ import annotations

import io
import json
import os
import re
import unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FORMULES = os.path.join(RACINE, "models", "formules_civilite.json")

_cache: set[str] | None = None


def _clef(ligne: str) -> str:
    """Forme comparable d'une ligne : casse, accents et ponctuation neutralises.

    « Merci d'avance. » et « merci d’avance » doivent se reconnaitre : l'apostrophe
    typographique et l'apostrophe droite coexistent dans le corpus.
    """
    t = unicodedata.normalize("NFKD", ligne.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("’", "'").replace("‘", "'")
    t = re.sub(r"[^a-z0-9' ]+", " ", t)
    return " ".join(t.split())


def formules() -> set[str]:
    global _cache
    if _cache is None:
        try:
            with io.open(FORMULES, encoding="utf-8") as f:
                _cache = {_clef(x) for x in json.load(f).get("formules", [])}
        except (OSError, ValueError):
            _cache = set()
    return _cache


def recharger() -> None:
    """Vide le cache — utile apres avoir reconstruit la liste."""
    global _cache
    _cache = None


def resumer(titre: str, description: str, mots_max: int = 60) -> dict:
    """Le resume d'un ticket, et de quoi juger ce qu'il vaut.

    Returns:
        dict :
            resume            — la description privee de ses formules
            mots_origine      — nombre de mots de la description
            mots_resume       — nombre de mots du resume
            compression       — part des mots retires, entre 0 et 1
            formules_retirees — les lignes ecartees, pour que rien ne disparaisse
                                en silence
            tronque           — vrai si le plafond de mots a joue
    """
    texte = str(description or "")
    connues = formules()
    gardees, retirees = [], []
    for ligne in (l.strip() for l in texte.splitlines()):
        if not ligne:
            continue
        if _clef(ligne) in connues:
            retirees.append(ligne)
        else:
            gardees.append(ligne)

    # Tout retirer voudrait dire que la description n'etait que des formules :
    # mieux vaut alors rendre l'original que rendre le vide.
    if not gardees:
        gardees, retirees = [l.strip() for l in texte.splitlines() if l.strip()], []

    resume = " ".join(gardees)
    mots = resume.split()
    tronque = len(mots) > mots_max
    if tronque:
        resume = " ".join(mots[:mots_max]) + "…"

    origine = len(texte.split())
    return {
        "resume": resume,
        "mots_origine": origine,
        "mots_resume": len(resume.split()),
        "compression": round(1 - (len(resume.split()) / origine), 4) if origine else 0.0,
        "formules_retirees": retirees,
        "tronque": tronque,
    }
