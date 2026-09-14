# -*- coding: utf-8 -*-
"""Garde sur les secrets de deploiement — risque R-09.

Le fichier .env.example est public. S'il porte des valeurs utilisables et qu'un
deploiement le copie tel quel, le service part avec une cle de signature et un
mot de passe de base connus de quiconque lit le depot. Deux verrous sont testes
ici : le fichier d'exemple ne doit contenir aucun secret exploitable, et le
service doit refuser de demarrer en production tant qu'un secret n'a pas ete
genere.
"""
import os

import pytest

from api.config import Settings

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXEMPLE = os.path.join(RACINE, ".env.example")

CLES_SENSIBLES = ("SECRET_KEY", "POSTGRES_PASSWORD", "INGEST_API_KEY", "DB_URL")


def _valeurs_exemple():
    valeurs = {}
    with open(EXEMPLE, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if "=" in ligne and not ligne.startswith("#"):
                cle, val = ligne.split("=", 1)
                valeurs[cle.strip()] = val.strip()
    return valeurs


@pytest.mark.parametrize("cle", CLES_SENSIBLES)
def test_le_fichier_exemple_ne_porte_aucun_secret_exploitable(cle):
    valeurs = _valeurs_exemple()
    assert cle in valeurs, "%s a disparu de .env.example" % cle
    assert "REMPLACER__" in valeurs[cle], (
        "%s porte une valeur utilisable dans .env.example ; "
        "un deploiement qui copie ce fichier partirait avec un secret public" % cle
    )


def test_production_refuse_de_demarrer_avec_les_valeurs_d_exemple():
    s = Settings(ENVIRONMENT="production",
                 SECRET_KEY="change-this-in-production-min-32-chars")
    with pytest.raises(RuntimeError) as erreur:
        s.verifier_secrets()
    assert "SECRET_KEY" in str(erreur.value)
    # Le message ne doit jamais reproduire la valeur elle-meme.
    assert "change-this-in-production-min-32-chars" not in str(erreur.value)


def test_production_demarre_lorsque_les_secrets_sont_generes():
    s = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="k" * 48,
        INGEST_API_KEY="i" * 48,
        DB_URL="postgresql+psycopg2://helpdesk:" + "p" * 24 + "@postgres:5432/helpdesk",
    )
    assert s.secrets_non_configures() == []
    s.verifier_secrets()


def test_developpement_reste_permissif():
    """Un poste de developpement doit pouvoir demarrer sans ceremonie."""
    s = Settings(ENVIRONMENT="development",
                 SECRET_KEY="change-this-in-production-min-32-chars")
    assert s.secrets_non_configures()
    s.verifier_secrets()
