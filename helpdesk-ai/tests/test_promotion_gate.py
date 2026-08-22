"""
Tests de la porte de promotion (axe 1, etape 4).

Ces tests portent sur la fonction de decision seule, sans entrainement ni disque.
Ils verifient la promesse faite au systeme : un modele en production n'est jamais
remplace par un candidat qui n'a pas demontre qu'il est meilleur.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from pipeline.promote import comparer, metrique_effective  # noqa: E402

PARAMS = {
    "promotion": {
        "primary_metric": "f1_macro_heuristiques",
        "min_improvement": 0.005,
        "max_class_regression": 0.05,
        "allow_accuracy_regression": False,
        "ignore_zero_support_classes": True,
    }
}

CONFUSION = {
    "labels": ["Applicatifs", "Infrastructure", "Microsoft", "Réseau", "Système", "Sécurité"],
    "support": {"Applicatifs": 0, "Infrastructure": 91, "Microsoft": 135,
                "Réseau": 45, "Système": 52, "Sécurité": 33},
    "classes_sans_support": ["Applicatifs"],
}


def metriques(macro, accuracy=0.85, **par_classe):
    base = {
        "f1_macro_classes_evaluables": macro,
        "f1_macro_heuristiques": macro,
        "accuracy": accuracy,
        "f1_Applicatifs": 0.0,
        "f1_Infrastructure": 0.79,
        "f1_Microsoft": 0.97,
        "f1_Réseau": 0.81,
        "f1_Système": 1.0,
        "f1_Sécurité": 0.53,
    }
    base.update(par_classe)
    return base


def test_metrique_effective_exclut_les_classes_sans_support():
    """
    Une classe absente du jeu de test a une F1 de 0.0 par construction, dans les
    deux modeles. L'inclure ferait dependre la decision de la composition du jeu.
    """
    assert metrique_effective(PARAMS) == "f1_macro_classes_evaluables"

    params_stricts = {"promotion": dict(PARAMS["promotion"],
                                        ignore_zero_support_classes=False)}
    assert metrique_effective(params_stricts) == "f1_macro_heuristiques"


def test_gain_suffisant_accepte():
    decision = comparer(metriques(0.83), metriques(0.82), CONFUSION, PARAMS)
    assert decision["accepte"]
    assert decision["delta"] == 0.01


def test_gain_insuffisant_rejete():
    """Un candidat marginalement meilleur ne justifie pas de changer la production."""
    decision = comparer(metriques(0.8220), metriques(0.8210), CONFUSION, PARAMS)
    assert not decision["accepte"]
    assert "metrique_principale" in decision["portes_en_echec"]


def test_modele_identique_rejete():
    decision = comparer(metriques(0.822), metriques(0.822), CONFUSION, PARAMS)
    assert not decision["accepte"]
    assert decision["delta"] == 0.0


def test_regression_rejetee():
    decision = comparer(metriques(0.75), metriques(0.82), CONFUSION, PARAMS)
    assert not decision["accepte"]


def test_effondrement_d_une_classe_rejete_malgre_un_gain_global():
    """
    Le cas que la deuxieme porte existe pour attraper : la moyenne progresse
    pendant qu'une classe minoritaire s'effondre.
    """
    candidat = metriques(0.84, f1_Sécurité=0.20)      # -0.33 sur Sécurité
    decision = comparer(candidat, metriques(0.82), CONFUSION, PARAMS)

    assert decision["delta"] > 0.005                  # la premiere porte passe
    assert not decision["accepte"]
    assert "aucune_regression_par_classe" in decision["portes_en_echec"]
    assert decision["regressions_par_classe"][0]["classe"] == "Sécurité"


def test_petite_baisse_de_classe_toleree():
    candidat = metriques(0.84, f1_Sécurité=0.50)      # -0.03, sous le seuil de 0.05
    decision = comparer(candidat, metriques(0.82), CONFUSION, PARAMS)
    assert decision["accepte"]


def test_classe_sans_support_ignoree():
    """Applicatifs n'a aucun ticket de test : sa F1 ne doit bloquer aucune porte."""
    candidat = metriques(0.84, f1_Applicatifs=0.0)
    reference = metriques(0.82, f1_Applicatifs=0.9)   # valeur absurde, sans support
    decision = comparer(candidat, reference, CONFUSION, PARAMS)

    assert "Applicatifs" not in decision["classes_evaluees"]
    assert decision["accepte"]


def test_regression_d_accuracy_rejetee():
    decision = comparer(metriques(0.84, accuracy=0.80),
                        metriques(0.82, accuracy=0.85), CONFUSION, PARAMS)
    assert not decision["accepte"]
    assert "accuracy_non_regressive" in decision["portes_en_echec"]


def test_regression_d_accuracy_toleree_si_autorisee():
    params = {"promotion": dict(PARAMS["promotion"], allow_accuracy_regression=True)}
    decision = comparer(metriques(0.84, accuracy=0.80),
                        metriques(0.82, accuracy=0.85), CONFUSION, params)
    assert decision["accepte"]


def test_decision_tracable():
    """Chaque porte doit expliquer son verdict : une decision opaque est inutilisable."""
    decision = comparer(metriques(0.83), metriques(0.82), CONFUSION, PARAMS)
    noms = {p["porte"] for p in decision["portes"]}
    assert noms == {"metrique_principale", "aucune_regression_par_classe",
                    "accuracy_non_regressive"}
    assert all(p["detail"] for p in decision["portes"])
