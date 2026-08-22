"""
Tests du controle qualite des connaissances (axe 2).

Le test central est test_suggestion_ia_refusee : c'est la regle qui empeche le RAG
de se nourrir de ses propres sorties.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from knowledge.quality import (  # noqa: E402
    KB_SCHEMA_VERSION,
    charger_regles,
    controler,
    recouvrement,
)

DESCRIPTION = (
    "Impossible de me connecter au VPN depuis ce matin, le client affiche "
    "une erreur d'authentification apres la saisie du mot de passe."
)
SOLUTION_VALIDE = (
    "Le certificat machine avait expire. Renouvellement via la console PKI "
    "puis redemarrage du service client, connexion retablie."
)


def regles(**surcharges):
    base = dict(charger_regles(None))
    base.update(surcharges)
    return base


def test_connaissance_valide_acceptee():
    verdict = controler(
        titre="VPN inaccessible",
        description=DESCRIPTION,
        solution=SOLUTION_VALIDE,
        source_solution="admin",
        regles=regles(),
    )
    assert verdict.accepte
    assert verdict.action == "index"
    assert verdict.quality_score > 0


def test_suggestion_ia_refusee():
    """
    Regle centrale de l'axe 2. Une solution non relue par un humain ne peut pas
    devenir une connaissance de reference, sinon le RAG apprend de lui-meme.
    """
    verdict = controler(
        titre="VPN inaccessible",
        description=DESCRIPTION,
        solution=SOLUTION_VALIDE,
        source_solution="ia",
        regles=regles(),
    )
    assert not verdict.accepte
    assert verdict.action == "reject"
    assert "humain" in verdict.motif


def test_suggestion_ia_acceptee_si_la_regle_est_desactivee():
    verdict = controler(
        titre="VPN inaccessible",
        description=DESCRIPTION,
        solution=SOLUTION_VALIDE,
        source_solution="ia",
        regles=regles(require_human_solution=False),
    )
    assert verdict.accepte


def test_solution_vide_refusee():
    verdict = controler("t", DESCRIPTION, "", source_solution="admin", regles=regles())
    assert not verdict.accepte
    assert "absente" in verdict.motif


@pytest.mark.parametrize("solution", ["ok", "fait", "resolu", "RAS merci"])
def test_solution_trop_courte_refusee(solution):
    verdict = controler("t", DESCRIPTION, solution, source_solution="admin", regles=regles())
    assert not verdict.accepte
    assert "courte" in verdict.motif


def test_solution_qui_recopie_la_description_refusee():
    """Recopier l'enonce du probleme n'apprend rien a la base."""
    verdict = controler("t", DESCRIPTION, DESCRIPTION, source_solution="admin", regles=regles())
    assert not verdict.accepte
    assert "recopie" in verdict.motif


def test_quasi_doublon_declenche_une_mise_a_jour():
    verdict = controler(
        "VPN inaccessible", DESCRIPTION, SOLUTION_VALIDE,
        source_solution="admin",
        regles=regles(),
        voisins=[{"id": "42", "score": 0.97}],
    )
    assert verdict.accepte
    assert verdict.action == "update"
    assert verdict.near_duplicate_of == "42"


def test_voisin_sous_le_seuil_reste_une_indexation():
    verdict = controler(
        "VPN inaccessible", DESCRIPTION, SOLUTION_VALIDE,
        source_solution="admin",
        regles=regles(),
        voisins=[{"id": "42", "score": 0.80}],
    )
    assert verdict.accepte
    assert verdict.action == "index"
    assert verdict.near_duplicate_of is None


def test_recouvrement_insensible_aux_accents_et_a_la_casse():
    assert recouvrement("Le certificat a expire", "LE CERTIFICAT A EXPIRÉ") == 1.0
    assert recouvrement("connexion vpn", "impression imprimante") == 0.0


def test_verdict_serialisable():
    verdict = controler("t", DESCRIPTION, SOLUTION_VALIDE,
                        source_solution="admin", regles=regles())
    donnees = verdict.as_dict()
    assert set(donnees) >= {"accepte", "action", "motif", "controles", "quality_score"}
    assert all("controle" in c and "passe" in c for c in donnees["controles"])


def test_schema_version_exposee():
    assert isinstance(KB_SCHEMA_VERSION, int)
    assert KB_SCHEMA_VERSION >= 1
