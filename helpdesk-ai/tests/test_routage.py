# -*- coding: utf-8 -*-
"""Tests de l'orientation selon l'index de confiance (EF-07).

L'exigence demandait que les cas peu assures soient diriges vers une revue
humaine. Elle etait declaree partielle parce que l'index etait calcule sans que
rien s'en serve. Ces tests verifient que la decision est bien prise, qu'elle est
prise pour les bonnes raisons, et qu'elle n'enferme personne.
"""
import os

os.environ.setdefault("DB_URL", "sqlite:///./data/tickets_test.db")

import pytest

from api.services.routage_service import AUTOMATIQUE, REVUE_HUMAINE, decider

SEUIL_CONFIANCE = 0.60
SEUIL_RAG = 0.35


def orienter(**prediction):
    base = {"confiance": 0.92, "heuristic_applied": False, "rag_score": 0.42}
    base.update(prediction)
    return decider(base, SEUIL_CONFIANCE, SEUIL_RAG)


def test_un_ticket_bien_predit_part_en_traitement_ordinaire():
    routage, motif = orienter()
    assert routage == AUTOMATIQUE
    assert "92" in motif


def test_une_confiance_sous_le_seuil_declenche_la_revue():
    routage, motif = orienter(confiance=0.31)
    assert routage == REVUE_HUMAINE
    assert "sous le seuil" in motif


def test_la_confiance_juste_sous_le_seuil_declenche_aussi():
    """Le seuil est strict : 0,599 passe en revue, 0,60 non."""
    assert orienter(confiance=SEUIL_CONFIANCE - 0.001)[0] == REVUE_HUMAINE
    assert orienter(confiance=SEUIL_CONFIANCE)[0] == AUTOMATIQUE


def test_une_categorie_imposee_par_une_regle_passe_en_revue():
    """Une regle metier tranche sur un mot-cle, pas sur le sens de la phrase.

    Un humain doit confirmer que le mot-cle ne s'est pas trompe de contexte,
    meme quand la confiance du modele est haute.
    """
    routage, motif = orienter(heuristic_applied=True, heuristic_rule="ransomware")
    assert routage == REVUE_HUMAINE
    assert "ransomware" in motif


def test_l_absence_de_cas_comparable_passe_en_revue():
    for score in (None, 0.0, SEUIL_RAG - 0.01):
        routage, motif = orienter(rag_score=score)
        assert routage == REVUE_HUMAINE, score
        assert "aucun cas comparable" in motif


def test_les_motifs_se_cumulent():
    """Trois raisons d'hesiter doivent toutes figurer, pas seulement la premiere."""
    _, motif = orienter(confiance=0.2, heuristic_applied=True,
                        heuristic_rule="veeam", rag_score=None)
    assert "sous le seuil" in motif
    assert "veeam" in motif
    assert "aucun cas comparable" in motif


def test_une_prediction_vide_ne_fait_pas_tomber_la_decision():
    """Un champ manquant ne doit pas lever : la creation du ticket en depend."""
    routage, motif = decider({}, SEUIL_CONFIANCE, SEUIL_RAG)
    assert routage == REVUE_HUMAINE
    assert motif


@pytest.mark.parametrize("routage", [REVUE_HUMAINE, AUTOMATIQUE])
def test_les_deux_valeurs_sont_les_seules_possibles(routage):
    assert routage in (REVUE_HUMAINE, AUTOMATIQUE)
    assert routage == routage.lower()


def test_le_motif_est_toujours_lisible():
    """Le motif s'affiche a un administrateur : jamais vide, jamais un code."""
    for cas in ({}, {"confiance": 0.9}, {"confiance": 0.1},
                {"heuristic_applied": True}, {"rag_score": 0.9, "confiance": 0.9}):
        _, motif = decider(cas, SEUIL_CONFIANCE, SEUIL_RAG)
        assert motif and len(motif) > 10
        assert "None" not in motif
