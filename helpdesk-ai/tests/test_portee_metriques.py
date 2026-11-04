# -*- coding: utf-8 -*-
"""La portee des moyennes par categorie doit etre figee (remarque du 2026-10-09).

Le defaut corrige
-----------------
`f1_score(y, p, average="macro")` sans argument `labels` moyenne sur l'union des
categories vraies et des categories predites. Le denominateur suit alors les
erreurs du modele : sur le jeu de test gele, le modele prononcait
« Applicatifs », absente du test, et la moyenne portait sur six categories
quand le memoire en annoncait huit.

Deux modeles de qualite identique n'y sont pas compares a armes egales : celui
qui ne prononce aucune categorie absente est divise par un nombre plus petit et
affiche un meilleur score. La metrique etait enregistree comme metrique de
reference du registre.

Ces tests verifient que la portee est fixee, et qu'elle le reste.
"""
import glob
import io
import os
import re

import numpy as np
import pandas as pd

from src.pipeline.train import REFERENTIEL, evaluer

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class PipelineFactice:
    """Un classifieur qui rend toujours la meme categorie, avec une confiance haute.

    Il sert a provoquer exactement le cas du defaut : une categorie prononcee
    qui n'existe pas dans le jeu de test.
    """

    def __init__(self, categorie, classes=None):
        self.classes_ = np.array(classes or REFERENTIEL)
        self._i = list(self.classes_).index(categorie)

    def predict(self, X):
        return np.array([self.classes_[self._i]] * len(X))

    def predict_proba(self, X):
        p = np.full((len(X), len(self.classes_)), 0.01)
        p[:, self._i] = 0.93
        return p


def jeu(categories):
    """Un jeu de test minimal, avec des textes qui ne declenchent aucune regle."""
    return pd.DataFrame({
        "text_clean": ["texte neutre numero %d" % i for i in range(len(categories))],
        "Titre": ["titre neutre %d" % i for i in range(len(categories))],
        "Description": ["description neutre sans mot clef %d" % i for i in range(len(categories))],
        "Catégorie": list(categories),
    })


def test_le_denominateur_ne_depend_pas_de_ce_que_le_modele_predit():
    """Le coeur du defaut : deux modeles egaux doivent etre divises pareil."""
    test = jeu(["Microsoft"] * 6 + ["Réseau"] * 4)
    # Les deux se trompent autant : ils rangent tout dans une seule categorie.
    # L'un choisit une categorie presente au test, l'autre une categorie absente.
    m_present, _ = evaluer(PipelineFactice("Microsoft"), test, 0.60)
    m_absent, _ = evaluer(PipelineFactice("Backup"), test, 0.60)
    assert m_present["f1_macro_heuristiques_portee"]["n"] == 8
    assert m_absent["f1_macro_heuristiques_portee"]["n"] == 8


def test_la_portee_est_le_referentiel_entier():
    test = jeu(["Microsoft"] * 5 + ["Système"] * 5)
    m, _ = evaluer(PipelineFactice("Microsoft"), test, 0.60)
    portee = m["f1_macro_heuristiques_portee"]
    assert portee["n"] == 8
    assert sorted(portee["categories"]) == sorted(REFERENTIEL)


def test_la_valeur_sur_le_referentiel_vaut_la_somme_divisee_par_huit():
    """Verification arithmetique : la moyenne doit etre reconstituable a la main."""
    test = jeu(["Microsoft"] * 8 + ["Réseau"] * 2)
    m, _ = evaluer(PipelineFactice("Microsoft"), test, 0.60)
    par_classe = [m["f1_%s" % c.replace(" ", "_")] for c in REFERENTIEL
                  if "f1_%s" % c.replace(" ", "_") in m]
    attendu = sum(par_classe) / 8
    assert abs(m["f1_macro_heuristiques"] - attendu) < 0.001


def test_les_classes_evaluables_portent_leur_propre_portee():
    test = jeu(["Microsoft"] * 5 + ["Système"] * 5)
    m, _ = evaluer(PipelineFactice("Microsoft"), test, 0.60)
    portee = m["f1_macro_classes_evaluables_portee"]
    assert portee["n"] == m["n_classes_evaluables"]
    assert set(portee["categories"]) >= {"Microsoft", "Système"}


def test_les_deux_portees_sont_differentes_quand_le_test_est_partiel():
    """Si elles coincidaient, le lecteur ne saurait pas laquelle il lit."""
    test = jeu(["Microsoft"] * 5 + ["Système"] * 5)
    m, _ = evaluer(PipelineFactice("Microsoft"), test, 0.60)
    assert m["f1_macro_heuristiques"] != m["f1_macro_classes_evaluables"]
    assert m["f1_macro_heuristiques"] < m["f1_macro_classes_evaluables"]


MESURES = {"f1_score", "precision_score", "recall_score"}
# Identifiants qui trahissent une portee calculee sur ce que le modele a
# prononce. Une portee tiree des seules etiquettes vraies reste admise : c'est
# une portee declarable (« les categories presentes au test »), stable d'un
# modele a l'autre sur un meme jeu.
INDICES_DE_PREDICTION = re.compile(r"\bpred|\bavec\b|argmax|\bsortie|\by_hat\b")
# Le script qui documente le defaut l'emploie expres, et la suggestion de
# priorite est binaire : ses deux classes sont toujours presentes.
FICHIERS_DISPENSES = {
    os.path.join("scripts", "verification", "portee_f1_macro.py"),
    os.path.join("src", "pipeline", "train_priorite.py"),
}


def _portees_douteuses(chemin: str) -> list[str]:
    """Les moyennes par categorie dont la portee n'est pas defendable.

    Lecture de l'arbre syntaxique plutot que du texte : la premiere version de
    ce garde cherchait des motifs dans le source et laissait passer la forme
    exacte du defaut, `labels=etiquettes`, ou le nom ne dit rien de ce qu'il
    contient. Il faut remonter a l'affectation.
    """
    import ast

    source = io.open(chemin, encoding="utf-8").read()
    try:
        arbre = ast.parse(source)
    except SyntaxError:
        return []

    # Les constantes du module : une liste ecrite en dur est une portee figee.
    figees = set()
    for noeud in arbre.body:
        if isinstance(noeud, ast.Assign) and isinstance(noeud.value, (ast.List, ast.Tuple)):
            for cible in noeud.targets:
                if isinstance(cible, ast.Name):
                    figees.add(cible.id)
        elif isinstance(noeud, ast.ImportFrom):
            for alias in noeud.names:
                figees.add(alias.asname or alias.name)

    # Les affectations locales, pour remonter d'un nom a son expression.
    affectations: dict[str, str] = {}
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.Assign) and len(noeud.targets) == 1:
            cible = noeud.targets[0]
            if isinstance(cible, ast.Name):
                affectations.setdefault(cible.id, ast.unparse(noeud.value))

    fautifs = []
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.Call):
            continue
        nom = getattr(noeud.func, "id", None) or getattr(noeud.func, "attr", None)
        if nom not in MESURES:
            continue
        mots = {k.arg: k.value for k in noeud.keywords if k.arg}
        moyenne = mots.get("average")
        if not (isinstance(moyenne, ast.Constant) and moyenne.value == "macro"):
            continue
        if "labels" not in mots:
            fautifs.append("%d : aucune portee (labels absent)" % noeud.lineno)
            continue
        portee = mots["labels"]
        # `list(X)` ne change pas la nature de X.
        if isinstance(portee, ast.Call) and getattr(portee.func, "id", "") == "list" \
                and len(portee.args) == 1:
            portee = portee.args[0]
        if isinstance(portee, (ast.List, ast.Tuple)):
            continue
        if isinstance(portee, ast.Name):
            if portee.id in figees:
                continue
            origine = affectations.get(portee.id, "")
            if INDICES_DE_PREDICTION.search(origine):
                fautifs.append("%d : portee « %s » calculee sur les predictions (%s)"
                               % (noeud.lineno, portee.id, origine[:60]))
            continue
        if INDICES_DE_PREDICTION.search(ast.unparse(portee)):
            fautifs.append("%d : portee calculee sur les predictions" % noeud.lineno)
    return fautifs


def test_aucune_moyenne_par_categorie_sans_portee_defendable():
    """Garde : le defaut ne doit pas revenir, ni en clair ni derriere un nom."""
    fautifs = []
    for motif in ("src/**/*.py", "scripts/**/*.py"):
        for chemin in glob.glob(os.path.join(RACINE, *motif.split("/")), recursive=True):
            rel = os.path.relpath(chemin, RACINE)
            if rel in FICHIERS_DISPENSES or "__pycache__" in rel:
                continue
            for faute in _portees_douteuses(chemin):
                fautifs.append("%s:%s" % (rel, faute))
    assert not fautifs, (
        "moyenne par categorie sans argument labels, le denominateur suivrait "
        "les predictions du modele : " + ", ".join(fautifs))
