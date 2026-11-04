"""Le texte envoye au modele en production doit etre celui de l'entrainement.

Le corpus entraine le classifieur sur la colonne `text_clean`, construite par
`build_text_for_model(titre, description)`. L'application a longtemps envoye la
description seule : le titre, qui porte l'essentiel du signal, n'arrivait jamais
au modele. Mesure de l'ecart sur le jeu de test gele : exactitude 31,7 % contre
44,7 %, confiance moyenne 0,41 contre 0,46.

Ces tests verrouillent la correction. Ils n'ont besoin d'aucun modele entraine :
le pipeline est remplace par un espion qui note le texte recu.
"""

import numpy as np
import pytest

from src.data.preprocess import build_text_for_model

TITRE = "Probleme de connexion VPN"
DESCRIPTION = "Le client VPN refuse l'authentification depuis ce matin."


class PipelineEspion:
    """Faux pipeline sklearn : retient le texte recu et renvoie une proba fixe."""

    classes_ = np.array(["Applicatifs", "Reseau"])

    def __init__(self):
        self.recu = None

    def predict_proba(self, textes):
        self.recu = textes[0]
        return np.array([[0.25, 0.75]])


def test_predictor_envoie_titre_et_description():
    from api.predictor import Predictor

    predictor = Predictor()
    espion = PipelineEspion()
    predictor.pipeline = espion
    predictor.threshold = 0.60

    predictor.predict(TITRE, DESCRIPTION)

    assert espion.recu == build_text_for_model(TITRE, DESCRIPTION)


def test_predictor_ne_perd_pas_le_titre():
    """Garde-fou explicite : la description seule ne doit plus suffire."""
    from api.predictor import Predictor

    predictor = Predictor()
    espion = PipelineEspion()
    predictor.pipeline = espion
    predictor.threshold = 0.60

    predictor.predict(TITRE, DESCRIPTION)

    assert "vpn" in espion.recu, "le titre doit apparaitre dans le texte envoye au modele"


def test_ai_service_envoie_titre_et_description(monkeypatch):
    """Meme verification sur le chemin reellement emprunte a la creation d'un ticket."""
    from api.services import ai_service

    espion = PipelineEspion()

    class PredictorFactice:
        pipeline = espion
        threshold = 0.60
        model_version = 1

        def recommend(self, titre, description, categorie, allow_fallback=True):
            return []

    monkeypatch.setattr(ai_service, "get_predictor", lambda: PredictorFactice())
    monkeypatch.setattr(ai_service, "query_similar", lambda *a, **k: [])

    ai_service.predict_and_recommend(TITRE, DESCRIPTION)

    assert espion.recu == build_text_for_model(TITRE, DESCRIPTION)


@pytest.mark.parametrize("titre", ["", "   "])
def test_titre_vide_reste_accepte(titre):
    """Un ticket sans titre ne doit pas casser la prediction."""
    from api.predictor import Predictor

    predictor = Predictor()
    espion = PipelineEspion()
    predictor.pipeline = espion
    predictor.threshold = 0.60

    resultat = predictor.predict(titre, DESCRIPTION)

    assert resultat["categorie"] in PipelineEspion.classes_
