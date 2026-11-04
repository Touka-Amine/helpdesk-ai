# -*- coding: utf-8 -*-
"""Tests du journal et du budget de lecture du jeu de test gele.

Remarque de l'encadrant du 2026-10-09 : le jeu de test gele ne doit pas devenir
progressivement un jeu de validation servant a selectionner les modeles.

La reponse n'est pas un verrou — personne ne peut empecher d'ouvrir un fichier —
mais un compteur : rendre chaque lecture visible, distinguer celles qui
tranchent de celles qui rapportent, et arreter la porte de promotion une fois
un budget declare atteint. Ces tests verifient les trois.
"""
import io
import json
import os

import pytest

from src.pipeline import jeu_gele


@pytest.fixture
def journal_isole(tmp_path, monkeypatch):
    """Un journal vide, hors du depot, pour ne pas ecrire dans les donnees."""
    chemin = tmp_path / "journal.json"
    monkeypatch.setattr(jeu_gele, "JOURNAL", str(chemin))
    return chemin


def test_un_journal_absent_part_de_zero(journal_isole):
    assert jeu_gele.lectures_decisionnelles() == 0
    assert jeu_gele.etat()["lectures_totales"] == 0


def test_une_lecture_s_inscrit_avec_sa_date_et_son_motif(journal_isole):
    entree = jeu_gele.inscrire(jeu_gele.POUR_DECIDER, motif="arbitrage v7",
                               lecteur="tests", version_concernee=7)
    assert entree["nature"] == jeu_gele.POUR_DECIDER
    assert entree["motif"] == "arbitrage v7"
    assert entree["version_concernee"] == 7
    assert entree["date"]
    donnees = json.loads(io.open(journal_isole, encoding="utf-8").read())
    assert len(donnees["lectures"]) == 1


def test_seules_les_lectures_qui_tranchent_sont_comptees(journal_isole):
    """Recalculer un chiffre pour un tableau n'influence aucun choix."""
    jeu_gele.inscrire(jeu_gele.POUR_RAPPORTER, motif="tableau du memoire", lecteur="tests")
    jeu_gele.inscrire(jeu_gele.POUR_RAPPORTER, motif="figure du memoire", lecteur="tests")
    assert jeu_gele.lectures_decisionnelles() == 0
    jeu_gele.inscrire(jeu_gele.POUR_DECIDER, motif="arbitrage", lecteur="tests")
    assert jeu_gele.lectures_decisionnelles() == 1
    etat = jeu_gele.etat()
    assert etat["lectures_de_rapport"] == 2
    assert etat["lectures_totales"] == 3


def test_le_budget_laisse_passer_tant_qu_il_reste_de_la_marge(journal_isole):
    for _ in range(4):
        jeu_gele.inscrire(jeu_gele.POUR_DECIDER, motif="arbitrage", lecteur="tests")
    jeu_gele.verifier_budget(5)  # ne doit pas lever


def test_le_budget_arrete_la_porte_une_fois_atteint(journal_isole):
    for _ in range(5):
        jeu_gele.inscrire(jeu_gele.POUR_DECIDER, motif="arbitrage", lecteur="tests")
    with pytest.raises(jeu_gele.BudgetEpuise) as excinfo:
        jeu_gele.verifier_budget(5)
    message = str(excinfo.value)
    # Le message doit dire quoi faire, pas seulement que c'est refuse.
    assert "5" in message
    assert "nouvelle reference" in message
    assert "--force" in message


def test_les_lectures_de_rapport_n_epuisent_pas_le_budget(journal_isole):
    for _ in range(20):
        jeu_gele.inscrire(jeu_gele.POUR_RAPPORTER, motif="tableau", lecteur="tests")
    jeu_gele.verifier_budget(3)  # ne doit pas lever


def test_un_budget_absent_desactive_le_controle(journal_isole):
    for _ in range(50):
        jeu_gele.inscrire(jeu_gele.POUR_DECIDER, motif="arbitrage", lecteur="tests")
    jeu_gele.verifier_budget(None)
    jeu_gele.verifier_budget(0)


def test_le_budget_est_declare_dans_les_parametres():
    """Le reglage doit vivre avec les autres, pas en dur dans le code."""
    import yaml
    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with io.open(os.path.join(racine, "params.yaml"), encoding="utf-8") as f:
        params = yaml.safe_load(f)
    budget = params.get("jeu_gele", {}).get("lectures_de_decision_max")
    assert isinstance(budget, int) and budget > 0


def test_le_journal_du_depot_porte_les_lectures_deja_faites():
    """Un journal qui commencerait a zero laisserait croire que le jeu est neuf."""
    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chemin = os.path.join(racine, "data", "reference", "journal_jeu_gele.json")
    if not os.path.exists(chemin):
        pytest.skip("journal absent")
    donnees = json.loads(io.open(chemin, encoding="utf-8").read())
    decisions = [enr for enr in donnees["lectures"] if enr.get("nature") == jeu_gele.POUR_DECIDER]
    assert len(decisions) >= 3, "les arbitrages v2, v3 et v4 doivent y figurer"
    reconstituees = [enr for enr in decisions if enr.get("reconstitue")]
    assert reconstituees, "les lectures anterieures au journal doivent etre marquees comme telles"


def test_la_porte_de_promotion_verifie_le_budget_avant_de_lire():
    """Garde de lecture : l'ordre compte, et il doit rester celui-la."""
    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    code = io.open(os.path.join(racine, "src", "pipeline", "promote.py"),
                   encoding="utf-8").read()
    i_budget = code.index("verifier_budget")
    i_lecture = code.index("test_df = pd.read_csv(TEST_PATH")
    assert i_budget < i_lecture, (
        "le budget doit etre verifie AVANT d'ouvrir le jeu gele, sinon la lecture "
        "a lieu quand meme")
    assert "jeu_gele.inscrire" in code
