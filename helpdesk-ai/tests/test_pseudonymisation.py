# -*- coding: utf-8 -*-
"""Tests de la pseudonymisation des personnes nommees (ENF-04 b).

Le memoire declarait l'exigence non tenue : le corpus portait les noms en clair.
Ces tests verifient les quatre proprietes sur lesquelles repose la correction.
"""
import os

import pandas as pd
import pytest

from src.data.pseudonymisation import (CleManquante, cle, pseudonyme,
                                   pseudonymiser_tableau, retrouver)

SECRET = b"cle-de-test-uniquement"


def test_la_meme_personne_porte_toujours_le_meme_pseudonyme():
    """Sans cette propriete, les statistiques par demandeur seraient fausses."""
    a = pseudonyme("Ismail SBAA", "DEM", SECRET)
    b = pseudonyme("Ismail SBAA", "DEM", SECRET)
    assert a == b


def test_les_variantes_de_saisie_donnent_le_meme_pseudonyme():
    """« ISMAIL SBAA », « ismail  sbaa » et « Ismaïl SBAA » sont la meme personne."""
    attendu = pseudonyme("Ismail SBAA", "DEM", SECRET)
    for variante in ("ISMAIL SBAA", "ismail  sbaa", " Ismail SBAA ", "Ismaïl SBAA"):
        assert pseudonyme(variante, "DEM", SECRET) == attendu, variante


def test_deux_personnes_differentes_ne_se_confondent_pas():
    assert pseudonyme("Ismail SBAA", "DEM", SECRET) != pseudonyme("Naoufel Shaiek", "DEM", SECRET)


def test_une_cle_differente_donne_un_pseudonyme_different():
    """C'est ce qui empeche de remonter au nom en essayant un annuaire."""
    assert (pseudonyme("Ismail SBAA", "DEM", b"cle-a")
            != pseudonyme("Ismail SBAA", "DEM", b"cle-b"))


def test_le_pseudonyme_ne_laisse_rien_passer_du_nom():
    p = pseudonyme("Ismail SBAA", "DEM", SECRET)
    assert "ismail" not in p.lower()
    assert "sbaa" not in p.lower()
    assert p.startswith("DEM-") and len(p) == len("DEM-") + 10


def test_une_valeur_vide_reste_vide():
    for vide in ("", "   ", None, "nan"):
        assert pseudonyme(vide, "DEM", SECRET) == ""


def test_le_service_retrouve_les_tickets_d_une_personne_avec_la_cle():
    """La reidentification legitime, sans table de correspondance conservee."""
    df = pd.DataFrame({"Demandeur": ["Ismail SBAA", "Naoufel Shaiek", "Ismail SBAA"],
                       "Titre": ["a", "b", "c"]})
    df, _ = pseudonymiser_tableau(df, ("Demandeur",), SECRET)
    recherche = retrouver("Ismail SBAA", "Demandeur", SECRET)
    assert (df["Demandeur"] == recherche).sum() == 2


def test_la_pseudonymisation_conserve_le_nombre_de_personnes():
    noms = ["Ismail SBAA", "Naoufel Shaiek", "Ismail SBAA", "Hafedh Chebly"]
    df = pd.DataFrame({"Demandeur": noms})
    df, rapport = pseudonymiser_tableau(df, ("Demandeur",), SECRET)
    assert rapport["Demandeur"]["personnes_distinctes"] == 3
    assert rapport["Demandeur"]["pseudonymes_distincts"] == 3


def test_une_colonne_absente_est_ignoree_sans_erreur():
    df = pd.DataFrame({"Titre": ["a"]})
    df, rapport = pseudonymiser_tableau(df, ("Demandeur", "Assigné à"), SECRET)
    assert rapport == {}


def test_sans_cle_le_module_refuse_plutot_que_d_inventer():
    """Une cle tiree au hasard donnerait des pseudonymes differents a chaque
    execution, et les tableaux cesseraient d'etre comparables."""
    ancienne = os.environ.pop("PSEUDO_KEY", None)
    try:
        with pytest.raises(CleManquante):
            cle()
    finally:
        if ancienne is not None:
            os.environ["PSEUDO_KEY"] = ancienne


def test_le_corpus_livre_ne_porte_plus_de_nom():
    """Verification de bout en bout sur le tableau que le pipeline utilise."""
    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chemin = os.path.join(racine, "data", "processed", "HelpDesk1.csv")
    if not os.path.exists(chemin):
        pytest.skip("corpus absent")
    df = pd.read_csv(chemin, usecols=lambda c: c in ("Demandeur", "Assigné à"))
    for col, prefixe in (("Demandeur", "DEM"), ("Assigné à", "AGT")):
        if col not in df.columns:
            continue
        valeurs = df[col].dropna().astype(str)
        valeurs = valeurs[valeurs.str.strip() != ""]
        if valeurs.empty:
            continue
        assert valeurs.str.match(r"^%s-[0-9a-f]{10}$" % prefixe).all(), (
            "%s porte encore des valeurs en clair : %s"
            % (col, valeurs[~valeurs.str.match(r"^%s-[0-9a-f]{10}$" % prefixe)].head(3).tolist()))
