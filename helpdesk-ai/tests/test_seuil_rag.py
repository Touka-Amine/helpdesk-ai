"""Le seuil de pertinence servi doit etre celui que le pipeline declare, et rester
dans la plage que le score hybride peut atteindre.

Le seuil valait 0.50, repris de l'echelle du cosinus. Le score hybride est la
moyenne d'un score semantique (plafond mesure 0.7024) et d'un score lexical
(plafond 0.3099) : sur les 40 requetes annotees, son maximum est 0.4886. Le seuil
ne filtrait donc rien et marquait « repli » la totalite des recommandations.
Recalibre a 0.35, point ou la precision de ce qui est affiche est la plus haute.

Ce que ces tests ne verifient PAS, et qui doit etre rappele la ou le chiffre est
cite : 0.35 a ete choisi sur les memes 40 requetes qui le jugent. Hors
echantillon, la precision tombe de 0.5652 a 0.4886, soit +0.0766 d'optimisme
(`scripts/seuil_rag_hors_echantillon.py`). Un test ne peut pas garder une
reserve de lecture ; il garde la plage atteignable et la source du seuil.

Deux regressions sont verrouillees ici :
  - reintroduire un seuil hors de portee du score hybride ;
  - recopier le seuil en dur dans l'API au lieu de le lire dans params.yaml.
"""

import os

# Importer api.routers.tickets ouvre une connexion a la base des l'import.
# Meme convention que tests/test_api_integration.py : une base SQLite de test.
os.environ.setdefault("DB_URL", "sqlite:///./data/tickets_test.db")

import pytest
import yaml

from src.rag.hybrid_engine import HybridRAGEngine

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARAMS = os.path.join(RACINE, "params.yaml")

# Maximum observe du score hybride sur le protocole annote (40 requetes), mesure
# apres la correction de l'elargissement semantique du 2026-10-09 :
# metrics/rag_seuil_balayage.json, moteurs.hybride.distribution.max.
# Un seuil au-dessus est inatteignable : le repli devient systematique.
MAX_SCORE_HYBRIDE_MESURE = 0.4886


@pytest.fixture(scope="module")
def params_rag():
    with open(PARAMS, encoding="utf-8") as f:
        return yaml.safe_load(f)["rag"]


def test_le_seuil_est_dans_la_plage_atteignable(params_rag):
    seuil = params_rag["similarity_threshold"]
    assert seuil <= MAX_SCORE_HYBRIDE_MESURE, (
        f"Seuil {seuil} au-dessus du maximum mesure {MAX_SCORE_HYBRIDE_MESURE} : "
        "aucune recommandation ne peut l'atteindre, le repli redeviendrait total."
    )
    assert seuil > params_rag["fallback_threshold"], (
        "Le seuil de pertinence doit rester au-dessus du plancher de repli, "
        "sinon le repli ne peut jamais se declencher."
    )


def test_api_lit_le_seuil_du_fichier_de_parametres(params_rag):
    """Le service ne doit pas porter sa propre copie du seuil."""
    from api.predictor import _params_rag

    servi = _params_rag()
    assert servi["similarity_threshold"] == params_rag["similarity_threshold"]
    assert servi["hybrid_alpha"] == params_rag["hybrid_alpha"]
    assert servi["top_k"] == params_rag["top_k"]


def test_la_regle_metier_ne_suit_pas_le_seuil_de_pertinence(params_rag):
    """
    NOVELTY_THRESHOLD commande l'obligation de saisir la solution avant de clore.
    Elle est volontairement decouplee du seuil d'affichage : les avoir confondus
    faisait dependre une regle metier d'un reglage de pertinence sans rapport.
    """
    from api.routers.tickets import NOVELTY_THRESHOLD

    assert NOVELTY_THRESHOLD != params_rag["similarity_threshold"], (
        "Les deux seuils ont ete refusionnes : une recalibration de la pertinence "
        "modifierait silencieusement la regle de cloture."
    )
    assert NOVELTY_THRESHOLD > MAX_SCORE_HYBRIDE_MESURE, (
        "La regle doit rester declenchee sur tous les tickets : c'est la solution "
        "redigee par l'admin qui alimente la base de connaissances."
    )


class MoteurDoublure:
    """Sous-moteur minimal : renvoie une liste fixe, quelle que soit la requete."""

    def __init__(self, resultats):
        self.top_k = 3
        self.similarity_threshold = 0.0
        self.model_name = "doublure"
        self.knowledge_base = None
        self._resultats = resultats

    def recommend(self, query_text, category_filter=None, allow_fallback=True):
        return self._resultats


def _moteur(score_sem, seuil, plancher):
    hybride = HybridRAGEngine(
        alpha=1.0, top_k=3, similarity_threshold=seuil, fallback_threshold=plancher
    )
    hybride._sem = MoteurDoublure(
        [{"resolution": "r1", "score": score_sem, "categorie": "Réseau"}]
    )
    hybride._lex = MoteurDoublure([])
    hybride._fitted = True
    return hybride


def test_le_plancher_de_repli_est_configurable():
    """Il etait code en dur dans recommend() ; il doit venir du constructeur."""
    # alpha=1.0 : le score hybride vaut exactement le score semantique.
    hybride = _moteur(score_sem=0.25, seuil=0.35, plancher=0.20)
    resultats = hybride.recommend("requete")
    assert len(resultats) == 1
    assert resultats[0]["fallback"] is True, "0.25 est sous le seuil : c'est un repli"

    # Avec un plancher au-dessus du score, plus rien ne doit sortir.
    hybride = _moteur(score_sem=0.25, seuil=0.35, plancher=0.30)
    assert hybride.recommend("requete") == []


def test_un_score_au_dessus_du_seuil_n_est_pas_un_repli():
    hybride = _moteur(score_sem=0.42, seuil=0.35, plancher=0.20)
    resultats = hybride.recommend("requete")
    assert len(resultats) == 1
    assert resultats[0].get("fallback", False) is False
