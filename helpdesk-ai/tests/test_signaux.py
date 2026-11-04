# -*- coding: utf-8 -*-
"""Tests du releve des signaux de gravite (EF-13).

L'exigence demandait une analyse de tonalite. La mesure a etabli qu'il n'y en a
pas dans ce corpus — zero point d'exclamation sur 1 444 tickets, vingt termes
d'urgence sur vingt-cinq absents. Ce qui est livre releve des faits enonces par
le demandeur. Ces tests verifient qu'il ne releve que ce qui est ecrit.
"""
import os

os.environ.setdefault("DB_URL", "sqlite:///./data/tickets_test.db")

from src.models.signaux import libelles, relever


def codes(titre, description):
    return [s["code"] for s in relever(titre, description)["signaux"]]


def test_une_perte_de_donnees_est_relevee():
    assert "perte_de_donnees" in codes("Incident", "Il y a eu une perte de données sur le partage.")


def test_un_blocage_est_releve():
    assert "blocage" in codes("Incident", "Le poste est bloqué depuis ce matin.")


def test_les_flexions_du_blocage_sont_reconnues():
    for forme in ("bloqué", "bloquée", "bloqués", "bloquant", "arrêté"):
        assert "blocage" in codes("t", "Le service est %s." % forme), forme


def test_une_indisponibilite_est_relevee():
    for forme in ("indisponible", "inaccessible", "hors service", "ne répond plus"):
        assert "indisponibilite" in codes("t", "Le serveur est %s." % forme), forme


def test_un_ticket_calme_ne_declenche_rien():
    r = relever("Demande de licence", "Bonjour, merci de me créer un accès à l'outil. Cordialement.")
    assert r["signaux"] == []
    assert r["n_signaux"] == 0


def test_l_impossibilite_n_est_plus_relevee():
    """Retiree apres mesure : 44 % des tickets, +0,02 point. Elle n'informait pas."""
    assert "impossibilite" not in codes("t", "Il est impossible de se connecter.")


def test_plusieurs_signaux_se_cumulent():
    c = codes("Incident majeur",
              "Le serveur est indisponible, le poste est bloqué et il y a une perte de données.")
    assert set(c) == {"perte_de_donnees", "blocage", "indisponibilite"}


def test_chaque_signal_n_est_compte_qu_une_fois():
    c = codes("t", "bloqué, bloquée, bloquant, paralysé, arrêté")
    assert c.count("blocage") == 1


def test_les_accents_et_la_casse_ne_changent_rien():
    assert codes("t", "PERTE DE DONNÉES") == codes("t", "perte de donnees")


def test_un_texte_vide_ne_fait_pas_tomber_le_releve():
    for vide in ("", None):
        r = relever(vide, vide)
        assert r == {"signaux": [], "n_signaux": 0}


def test_le_module_ne_rend_aucune_note():
    """Il releve, il ne juge pas : aucune cle de score ne doit apparaitre."""
    r = relever("t", "Le serveur est indisponible.")
    assert set(r.keys()) == {"signaux", "n_signaux"}
    for s in r["signaux"]:
        assert set(s.keys()) == {"code", "libelle", "extrait"}


def test_les_libelles_sont_lisibles():
    for lib in libelles("t", "Le serveur est indisponible et les données sont perdues."):
        assert lib == lib.lower() or lib[0].islower()
        assert "_" not in lib
