"""Tests unitaires — src/rag/engine.py (Phase 12).

Utilise une petite base de connaissance en mémoire (pas de données projet).
Les scores TF-IDF attendus ont été vérifiés au préalable (déterministes,
pas de composante aléatoire dans TfidfVectorizer).
"""

import pandas as pd
import pytest

from src.rag.engine import RAGEngine


@pytest.fixture
def kb_df() -> pd.DataFrame:
    return pd.DataFrame({
        "text_rag": [
            "probleme vpn connexion impossible",
            "vpn deconnexion frequente bureau",
            "outlook ouvre plus erreur licence",
            "ransomware detecte poste comptabilite",
        ],
        "Catégorie": ["Réseau", "Réseau", "Microsoft", "Sécurité"],
        "Résolution/Motif": [
            "Redémarrer le client VPN",
            "Vérifier la stabilité réseau",
            "Réactiver la licence Office",
            "Isoler le poste et lancer scan antivirus",
        ],
        "knowledge Base": ["", "", "", ""],
        "Titre": ["Ticket1", "Ticket2", "Ticket3", "Ticket4"],
    })


def test_recommend_before_fit_raises():
    engine = RAGEngine()
    with pytest.raises(RuntimeError):
        engine.recommend("test")


def test_recommend_empty_query_returns_empty_list(kb_df):
    engine = RAGEngine().fit(kb_df)
    assert engine.recommend("") == []
    assert engine.recommend("   ") == []


def test_recommend_exact_match_returns_top_result(kb_df):
    engine = RAGEngine(top_k=3, similarity_threshold=0.50).fit(kb_df)
    results = engine.recommend("probleme vpn connexion impossible")
    assert len(results) == 1
    assert results[0]["score"] == 1.0
    assert results[0]["resolution"] == "Redémarrer le client VPN"


def test_recommend_category_filter_restricts_results(kb_df):
    engine = RAGEngine(top_k=3, similarity_threshold=0.50).fit(kb_df)
    results = engine.recommend(
        "outlook ouvre plus erreur licence", category_filter="Microsoft"
    )
    assert len(results) == 1
    assert results[0]["categorie"] == "Microsoft"


def test_recommend_below_threshold_without_fallback_returns_empty(kb_df):
    engine = RAGEngine(top_k=3, similarity_threshold=0.50).fit(kb_df)
    results = engine.recommend(
        "sauvegarde backup nas indisponible", allow_fallback=False
    )
    assert results == []


def test_recommend_below_threshold_with_fallback_still_empty_if_zero_overlap(kb_df):
    # Le fallback abaisse le seuil à 0.10, mais un score de 0.0 (aucun terme
    # commun) reste sous ce plancher : toujours aucun résultat.
    engine = RAGEngine(top_k=3, similarity_threshold=0.50).fit(kb_df)
    results = engine.recommend(
        "sauvegarde backup nas indisponible", allow_fallback=True
    )
    assert results == []


def test_recommend_fallback_marks_results_when_main_threshold_unreachable(kb_df):
    # Seuil principal volontairement inatteignable (2.0) → le fallback (0.10)
    # doit renvoyer les résultats pertinents avec fallback=True.
    engine = RAGEngine(top_k=3, similarity_threshold=2.0).fit(kb_df)
    results = engine.recommend("vpn connexion", allow_fallback=True)
    assert len(results) == 2
    assert all(r["fallback"] is True for r in results)
    assert results[0]["score"] >= results[1]["score"]


def test_recommend_deduplicates_identical_resolutions():
    df = pd.DataFrame({
        "text_rag": [
            "imprimante bloquee poste bureau",
            "imprimante bloquee poste etage",
        ],
        "Catégorie": ["Applicatifs", "Applicatifs"],
        "Résolution/Motif": [
            "Redémarrer le spouleur imprimante",
            "Redémarrer le spouleur imprimante",
        ],
        "knowledge Base": ["", ""],
        "Titre": ["TicketA", "TicketB"],
    })
    engine = RAGEngine(top_k=5, similarity_threshold=0.0).fit(df)
    results = engine.recommend("imprimante bloquee poste")
    assert len(results) == 1
