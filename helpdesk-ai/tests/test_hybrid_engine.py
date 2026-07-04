"""Tests unitaires — src/rag/hybrid_engine.py (Phase 12).

Les sous-moteurs (_sem, _lex) sont remplacés par des doublures (FakeEngine)
pour tester la logique de fusion sans dépendre du téléchargement du modèle
sentence-transformers ni de FAISS.
"""

import pytest

from src.rag.hybrid_engine import HybridRAGEngine


class FakeEngine:
    """Doublure de test imitant l'interface RAGEngine / SemanticRAGEngine."""

    def __init__(self, results, top_k=3, threshold=0.5, model_name="fake"):
        self.top_k = top_k
        self.similarity_threshold = threshold
        self.model_name = model_name
        self.knowledge_base = None
        self._results = results
        self.received_calls = []

    def recommend(self, query_text, category_filter=None, allow_fallback=True):
        self.received_calls.append({
            "query_text": query_text,
            "category_filter": category_filter,
            "allow_fallback": allow_fallback,
            "top_k_at_call": self.top_k,
            "threshold_at_call": self.similarity_threshold,
        })
        return self._results


def make_hybrid(sem_results, lex_results, alpha=0.5, top_k=2, similarity_threshold=0.3):
    hybrid = HybridRAGEngine(alpha=alpha, top_k=top_k, similarity_threshold=similarity_threshold)
    hybrid._sem = FakeEngine(sem_results)
    hybrid._lex = FakeEngine(lex_results)
    hybrid._fitted = True
    return hybrid


# ── Validation ────────────────────────────────────────────────────────────────

def test_alpha_out_of_range_raises():
    with pytest.raises(ValueError):
        HybridRAGEngine(alpha=1.5)
    with pytest.raises(ValueError):
        HybridRAGEngine(alpha=-0.1)


def test_recommend_before_fit_raises():
    hybrid = HybridRAGEngine()
    with pytest.raises(RuntimeError):
        hybrid.recommend("test")


def test_recommend_empty_query_returns_empty_without_calling_sub_engines():
    hybrid = make_hybrid(sem_results=[], lex_results=[])
    assert hybrid.recommend("") == []
    assert hybrid._sem.received_calls == []
    assert hybrid._lex.received_calls == []


# ── Fusion des scores ─────────────────────────────────────────────────────────

def test_score_fusion_formula_and_ordering():
    sem_results = [
        {"score": 0.8, "resolution": "R1", "categorie": "Réseau", "titre": "T1", "knowledge": ""},
        {"score": 0.6, "resolution": "R2", "categorie": "Réseau", "titre": "T2", "knowledge": ""},
    ]
    lex_results = [
        {"score": 0.9, "resolution": "R1", "categorie": "Réseau", "titre": "T1", "knowledge": ""},
        {"score": 0.2, "resolution": "R3", "categorie": "Microsoft", "titre": "T3", "knowledge": ""},
    ]
    hybrid = make_hybrid(sem_results, lex_results, alpha=0.5, top_k=2, similarity_threshold=0.3)

    results = hybrid.recommend("test query", category_filter="Réseau")

    # R1 : 0.5*0.8 + 0.5*0.9 = 0.85 | R2 : 0.5*0.6 = 0.30 | R3 (0.10) exclu (< seuil 0.3)
    assert [r["resolution"] for r in results] == ["R1", "R2"]
    assert results[0]["score"] == 0.85
    assert results[0]["score_sem"] == 0.8
    assert results[0]["score_sem"] == 0.8
    assert results[0]["score_lex"] == 0.9
    assert results[1]["score"] == 0.3


def test_top_k_limits_results():
    sem_results = [
        {"score": 0.9, "resolution": "R1", "categorie": "X", "titre": "T1", "knowledge": ""},
        {"score": 0.8, "resolution": "R2", "categorie": "X", "titre": "T2", "knowledge": ""},
        {"score": 0.7, "resolution": "R3", "categorie": "X", "titre": "T3", "knowledge": ""},
    ]
    hybrid = make_hybrid(sem_results, lex_results=[], alpha=1.0, top_k=1, similarity_threshold=0.0)
    results = hybrid.recommend("test")
    assert len(results) == 1
    assert results[0]["resolution"] == "R1"


# ── Sauvegarde/restauration de l'état des sous-moteurs (régression Bug 1) ─────

def test_sub_engines_top_k_and_threshold_are_multiplied_during_call_then_restored():
    hybrid = make_hybrid(sem_results=[], lex_results=[], top_k=2)
    original_sem_top_k, original_sem_threshold = hybrid._sem.top_k, hybrid._sem.similarity_threshold
    original_lex_top_k, original_lex_threshold = hybrid._lex.top_k, hybrid._lex.similarity_threshold

    hybrid.recommend("test query")

    # Pendant l'appel, les sous-moteurs devaient recevoir top_k×5 et threshold=0.0
    sem_call = hybrid._sem.received_calls[0]
    lex_call = hybrid._lex.received_calls[0]
    assert sem_call["top_k_at_call"] == hybrid.top_k * 5
    assert sem_call["threshold_at_call"] == 0.0
    assert lex_call["top_k_at_call"] == hybrid.top_k * 5
    assert lex_call["threshold_at_call"] == 0.0

    # Après l'appel, l'état d'origine des sous-moteurs partagés doit être restauré
    assert hybrid._sem.top_k == original_sem_top_k
    assert hybrid._sem.similarity_threshold == original_sem_threshold
    assert hybrid._lex.top_k == original_lex_top_k
    assert hybrid._lex.similarity_threshold == original_lex_threshold


def test_category_filter_and_allow_fallback_false_passed_to_sub_engines():
    hybrid = make_hybrid(sem_results=[], lex_results=[])
    hybrid.recommend("test query", category_filter="Sécurité", allow_fallback=True)

    sem_call = hybrid._sem.received_calls[0]
    assert sem_call["category_filter"] == "Sécurité"
    # allow_fallback est toujours forcé à False sur les sous-moteurs :
    # c'est HybridRAGEngine qui gère son propre fallback après fusion.
    assert sem_call["allow_fallback"] is False


# ── Fallback hybride ─────────────────────────────────────────────────────────

def test_fallback_marks_results_below_main_threshold_but_above_fallback_floor():
    lex_results = [
        {"score": 0.5, "resolution": "R4", "categorie": "X", "titre": "T4", "knowledge": ""},
    ]
    hybrid = make_hybrid(sem_results=[], lex_results=lex_results, alpha=0.5, similarity_threshold=0.3)
    # score hybride = 0.5*0 + 0.5*0.5 = 0.25 < seuil principal 0.3, mais >= seuil fallback 0.20
    results = hybrid.recommend("test", allow_fallback=True)
    assert len(results) == 1
    assert results[0]["fallback"] is True


def test_no_fallback_returns_empty_when_below_main_threshold():
    lex_results = [
        {"score": 0.5, "resolution": "R4", "categorie": "X", "titre": "T4", "knowledge": ""},
    ]
    hybrid = make_hybrid(sem_results=[], lex_results=lex_results, alpha=0.5, similarity_threshold=0.3)
    results = hybrid.recommend("test", allow_fallback=False)
    assert results == []
