# -*- coding: utf-8 -*-
"""Tests du resume extractif du ticket (EF-11).

L'exigence n'avait pas ete traitee. Elle l'est par retrait des formules de
civilite, et non par generation : ces tests verifient qu'on ne retire que des
formules, qu'on n'en invente aucune, et qu'un cas limite ne rend jamais le vide.
"""
import os

os.environ.setdefault("DB_URL", "sqlite:///./data/tickets_test.db")

from src.models.resume import resumer

DESCRIPTION = (
    "Bonjour,\n\n"
    "Les fichiers restent en statut 'en attente de synchronisation' sans progression.\n\n"
    "Les documents modifiés ne sont pas accessibles depuis le cloud.\n\n"
    "Merci de vérifier le problème et de me faire un retour.\n\n"
    "Cordialement."
)


def test_les_formules_disparaissent():
    r = resumer("Synchronisation bloquée", DESCRIPTION)
    for formule in ("Bonjour", "Cordialement", "Merci de vérifier"):
        assert formule not in r["resume"], formule


def test_la_substance_reste():
    r = resumer("Synchronisation bloquée", DESCRIPTION)
    assert "attente de synchronisation" in r["resume"]
    assert "documents modifiés" in r["resume"]


def test_rien_n_est_invente():
    """Chaque mot du resume vient de la description : c'est extractif."""
    r = resumer("Synchronisation bloquée", DESCRIPTION)
    origine = set(DESCRIPTION.lower().split())
    for mot in r["resume"].lower().split():
        assert mot in origine, mot


def test_le_gain_est_reel_et_rapporte():
    r = resumer("Synchronisation bloquée", DESCRIPTION)
    assert r["mots_resume"] < r["mots_origine"]
    assert 0 < r["compression"] < 1
    assert len(r["formules_retirees"]) >= 3


def test_une_description_sans_formule_est_rendue_telle_quelle():
    texte = "Le serveur de fichiers ne répond plus depuis 9h."
    r = resumer("Serveur injoignable", texte)
    assert r["resume"] == texte
    assert r["compression"] == 0.0
    assert r["formules_retirees"] == []


def test_une_description_qui_n_est_que_des_formules_n_est_pas_videe():
    """Mieux vaut rendre l'original qu'une chaine vide a l'administrateur."""
    r = resumer("Demande", "Bonjour,\n\nCordialement.")
    assert r["resume"].strip()
    assert "Bonjour" in r["resume"]


def test_une_description_vide_ne_fait_pas_tomber_le_calcul():
    for vide in ("", "   ", None):
        r = resumer("Titre", vide)
        assert r["resume"] == "" or not r["resume"].strip()
        assert r["compression"] == 0.0


def test_le_plafond_de_mots_est_signale():
    long_texte = " ".join("mot%d" % i for i in range(200))
    r = resumer("Titre", long_texte, mots_max=60)
    assert r["tronque"] is True
    assert r["resume"].endswith("…")
    assert len(r["resume"].split()) <= 61


def test_les_variantes_d_apostrophe_sont_reconnues():
    """Le corpus melange l'apostrophe droite et l'apostrophe typographique."""
    droite = resumer("t", "Merci d'avance.\nLe VPN est coupé.")
    typo = resumer("t", "Merci d’avance.\nLe VPN est coupé.")
    assert droite["resume"] == typo["resume"] == "Le VPN est coupé."
