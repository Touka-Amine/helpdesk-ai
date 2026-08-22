"""
Tests de la collecte des tickets valides (axe 1, etape 1).

Deux choses comptent ici : qu'un ticket non traite par un humain n'entre pas dans
le dataset, et que la force de l'etiquette soit correctement deduite de
l'historique. La seconde est ce qui separe un reentrainement utile d'une boucle
ou le modele se confirme lui-meme.
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pipeline.collect import force_etiquette, qualifier, vers_format_corpus  # noqa: E402

PARAMS = {
    "collect": {
        "eligible_statuts": ["Résolu"],
        "require_approved_by": True,
        "min_description_words": 5,
        "include_weak_labels": False,
        "label_weights": {"corrected": 1.0, "confirmed": 0.7, "weak": 0.3},
    }
}

DESCRIPTION = "Impossible de me connecter au VPN depuis ce matin avec une erreur"


def ticket(**surcharges):
    base = {
        "id": 1, "titre": "VPN inaccessible", "description": DESCRIPTION,
        "statut": "Résolu", "categorie_predite": "Réseau", "categorie_finale": "Réseau",
        "approved_by": "7", "commentaire_admin": "Certificat renouvele.",
        "filiale": "OTBS", "priorite_saisie": "Urgent", "priorite_finale": "Urgent",
        "classification_finale": "Incident", "assigne_a": "Amine", "equipement": "PC",
        "created_at": "2026-08-01", "resolved_at": "2026-08-02",
        "knowledge_rag": "", "model_version": "v1",
    }
    base.update(surcharges)
    return base


def historique(*evenements):
    return pd.DataFrame(list(evenements)) if evenements else pd.DataFrame(
        columns=["ticket_id", "changed_by", "champ_modifie"]
    )


# ── force de l'etiquette ─────────────────────────────────────────────────────

def test_etiquette_corrigee_quand_un_admin_change_la_categorie():
    histo = historique(
        {"ticket_id": 1, "changed_by": None, "champ_modifie": "categorie_finale"},
        {"ticket_id": 1, "changed_by": 7, "champ_modifie": "categorie_finale"},
    )
    assert force_etiquette(1, histo) == "corrected"


def test_etiquette_confirmee_quand_l_admin_agit_sans_toucher_la_categorie():
    histo = historique(
        {"ticket_id": 1, "changed_by": None, "champ_modifie": "categorie_finale"},
        {"ticket_id": 1, "changed_by": 7, "champ_modifie": "statut"},
    )
    assert force_etiquette(1, histo) == "confirmed"


def test_etiquette_faible_sans_intervention_humaine():
    """Le journal de creation a changed_by a NULL : ce n'est pas une validation."""
    histo = historique(
        {"ticket_id": 1, "changed_by": None, "champ_modifie": "categorie_finale"},
        {"ticket_id": 1, "changed_by": None, "champ_modifie": "statut"},
    )
    assert force_etiquette(1, histo) == "weak"


def test_etiquette_faible_sans_historique():
    assert force_etiquette(1, historique()) == "weak"
    assert force_etiquette(99, historique({"ticket_id": 1, "changed_by": 7,
                                           "champ_modifie": "statut"})) == "weak"


# ── eligibilite ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("surcharges,motif", [
    ({"statut": "En attente"}, "statut non terminal"),
    ({"statut": "Prise en Charge"}, "statut non terminal"),
    ({"categorie_finale": ""}, "categorie_finale vide"),
    ({"approved_by": None}, "aucun approbateur"),
    ({"description": "trop court"}, "description trop courte"),
])
def test_tickets_non_eligibles(surcharges, motif):
    df = qualifier(pd.DataFrame([ticket(**surcharges)]), historique(), PARAMS)
    assert not df.iloc[0]["eligible"]
    assert motif in df.iloc[0]["motif_rejet"]


def test_ticket_eligible():
    histo = historique({"ticket_id": 1, "changed_by": 7, "champ_modifie": "categorie_finale"})
    df = qualifier(pd.DataFrame([ticket()]), histo, PARAMS)
    assert df.iloc[0]["eligible"]
    assert df.iloc[0]["motif_rejet"] is None
    assert df.iloc[0]["label_strength"] == "corrected"


def test_base_vide_ne_casse_pas():
    df = qualifier(pd.DataFrame(), historique(), PARAMS)
    assert df.empty
    assert {"eligible", "motif_rejet", "label_strength"} <= set(df.columns)


# ── mise au format corpus ────────────────────────────────────────────────────

def test_format_corpus_recalcule_le_texte_nettoye():
    """
    text_clean doit etre recalcule et non repris tel quel : un ecart de
    pretraitement entre corpus historique et production serait lu par le modele
    comme un signal.
    """
    histo = historique({"ticket_id": 1, "changed_by": 7, "champ_modifie": "categorie_finale"})
    qualifie = qualifier(pd.DataFrame([ticket()]), histo, PARAMS)
    corpus = vers_format_corpus(qualifie[qualifie["eligible"]], PARAMS)

    ligne = corpus.iloc[0]
    assert ligne["ID"] == "PROD-1"
    assert ligne["Catégorie"] == "Réseau"
    assert ligne["text_clean"]
    assert ligne["text_clean"] != DESCRIPTION      # nettoye, pas recopie
    assert ligne["source"] == "production"
    assert ligne["sample_weight"] == 1.0           # corrected
    assert ligne["Résolution/Motif"] == "Certificat renouvele."


def test_poids_selon_la_force_de_l_etiquette():
    histo = historique({"ticket_id": 1, "changed_by": 7, "champ_modifie": "statut"})
    qualifie = qualifier(pd.DataFrame([ticket()]), histo, PARAMS)
    corpus = vers_format_corpus(qualifie[qualifie["eligible"]], PARAMS)
    assert corpus.iloc[0]["sample_weight"] == 0.7   # confirmed


def test_le_demandeur_n_est_pas_exporte():
    """Donnee nominative : elle reste dans PostgreSQL, elle ne part pas au dataset."""
    histo = historique({"ticket_id": 1, "changed_by": 7, "champ_modifie": "categorie_finale"})
    qualifie = qualifier(pd.DataFrame([ticket()]), histo, PARAMS)
    corpus = vers_format_corpus(qualifie[qualifie["eligible"]], PARAMS)
    assert corpus.iloc[0]["Demandeur"] == ""
