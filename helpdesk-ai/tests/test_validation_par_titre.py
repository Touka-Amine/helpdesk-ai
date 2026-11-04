# -*- coding: utf-8 -*-
"""La validation de CamemBERT se preleve par titre, pas ligne a ligne.

La remarque corrigee
--------------------
L'encadrant releve que la validation etait tiree au hasard alors que le test
est separe par groupes de titres. Verifie : le carnet 05 appelait
`ds_train.train_test_split(test_size=0.1, seed=RS)`, un tirage ligne a ligne,
et les 41 titres de la validation etaient tous presents a l'entrainement.

Ce que le defaut coutait n'est pas un chiffre publie — aucun n'en provient —
mais la PROCEDURE : `load_best_model_at_end` avec
`metric_for_best_model='f1_macro'` choisit l'epoque sur la validation. Un signal
fausse commandait donc la selection. Mesure des deux bras :
0,9199 contre 0,4697 de F1 de validation pour une qualite reelle identique
(`metrics/validation_camembert.json`).

Ces tests gardent la correction. Elle vivait jusqu'ici dans cinq lignes au
milieu d'une fonction qui charge torch et transformers, donc hors de portee de
tout test ; elle est desormais dans une fonction du module.
"""
import io
import os

import pandas as pd
import pytest

from src.pipeline.train_camembert import prelever_validation_par_titre

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(RACINE, "src", "pipeline", "train_camembert.py")


def corpus(titres_et_lignes):
    """Un train factice : chaque titre repete le nombre de fois demande."""
    titres, categories = [], []
    for titre, n in titres_et_lignes.items():
        titres += [titre] * n
        categories += ["Réseau"] * n
    return pd.DataFrame({"Titre": titres, "Catégorie": categories,
                         "text_enriched": ["t%d" % i for i in range(len(titres))]})


def test_aucun_titre_ne_passe_des_deux_cotes():
    """Le cas du corpus : des titres repetes des dizaines de fois."""
    df = corpus({"a": 30, "b": 30, "c": 30, "d": 30, "e": 30})
    train, val = prelever_validation_par_titre(df, part=0.2)
    assert not (set(train["Titre"]) & set(val["Titre"]))
    assert len(train) and len(val)
    assert len(train) + len(val) == len(df), "aucune ligne perdue ni dupliquee"


def test_un_tirage_ligne_a_ligne_aurait_fuit():
    """Sans ce test, le precedent pourrait passer pour une evidence.

    Sur le meme corpus, le tirage que le carnet employait place des lignes du
    meme titre des deux cotes. C'est la difference que la correction supprime.
    """
    from sklearn.model_selection import train_test_split

    df = corpus({"a": 30, "b": 30, "c": 30, "d": 30, "e": 30})
    train, val = train_test_split(df, test_size=0.2, random_state=42)
    assert set(train["Titre"]) & set(val["Titre"]), (
        "le tirage ligne a ligne devrait fuir sur un corpus a titres repetes")


def test_la_part_demandee_est_respectee_en_groupes():
    """Le prelevement porte sur les titres, donc la part n'est pas exacte."""
    df = corpus({"a": 10, "b": 10, "c": 10, "d": 10, "e": 10,
                 "f": 10, "g": 10, "h": 10, "i": 10, "j": 10})
    _, val = prelever_validation_par_titre(df, part=0.2)
    assert val["Titre"].nunique() == 2, "deux titres sur dix"


def test_le_prelevement_est_reproductible():
    """Deux appels de meme graine doivent rendre le meme decoupage."""
    df = corpus({chr(97 + i): 12 for i in range(8)})
    a, _ = prelever_validation_par_titre(df, part=0.25, graine=7)
    b, _ = prelever_validation_par_titre(df, part=0.25, graine=7)
    assert list(a.index) == list(b.index)


def test_la_fuite_est_refusee_et_non_signalee_en_silence():
    """Si le decoupage fuyait, la fonction doit s'arreter.

    Un titre vide partout force GroupShuffleSplit a ne constituer qu'un seul
    groupe : il n'y a alors rien a prelever, et l'echec doit etre bruyant.
    """
    df = corpus({"unique": 40})
    with pytest.raises((AssertionError, ValueError)):
        prelever_validation_par_titre(df, part=0.2)


def test_le_tirage_ligne_a_ligne_ne_revient_pas_dans_la_source():
    """Garde : la forme fautive ne doit pas reapparaitre dans ce fichier."""
    source = io.open(SOURCE, encoding="utf-8").read()
    assert "train_test_split" not in source, (
        "train_camembert.py ne doit pas prelever sa validation ligne a ligne")
    assert "groups=train_complet[\"Titre\"]" in source or "groups=" in source, (
        "le prelevement doit se faire par groupe")
