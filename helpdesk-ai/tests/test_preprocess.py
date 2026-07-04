"""Tests unitaires — src/data/preprocess.py (Phase 12)."""

from src.data.preprocess import (
    build_text_enriched,
    build_text_for_model,
    build_text_for_rag,
    clean_text,
    simplify_classification,
    simplify_priorite,
)


# ── clean_text ────────────────────────────────────────────────────────────────

def test_clean_text_lowercase_and_spacing():
    assert clean_text("Connexion   Serveur") == "connexion serveur"


def test_clean_text_removes_accents():
    assert "e" in clean_text("Problème réseau")
    assert "é" not in clean_text("Problème réseau")


def test_clean_text_keeps_it_terms_despite_stopword_lists():
    # "vpn", "outlook", "teams" sont dans _KEEP malgré leur brièveté/généricité
    result = clean_text("Impossible de se connecter au VPN via Outlook Teams")
    assert "vpn" in result
    assert "outlook" in result
    assert "teams" in result


def test_clean_text_removes_domain_stopwords():
    result = clean_text("Bonjour, merci de votre aide, cordialement")
    assert "bonjour" not in result
    assert "merci" not in result
    assert "cordialement" not in result


def test_clean_text_removes_urls_emails_ips():
    result = clean_text("Voir http://exemple.com contact@test.com ou 192.168.1.1")
    assert "http" not in result
    assert "exemple" not in result
    assert "contact" not in result
    assert "192" not in result


def test_clean_text_empty_and_non_string():
    assert clean_text("") == ""
    assert clean_text("   ") == ""
    assert clean_text(None) == ""


def test_clean_text_drops_short_tokens():
    # tokens de longueur < 2 supprimés
    result = clean_text("a b vpn")
    assert result == "vpn"


# ── simplify_priorite ───────────────────────────────────────────────────────

def test_simplify_priorite_known_values():
    assert simplify_priorite("Mineur") == "basse"
    assert simplify_priorite("modere") == "normale"
    assert simplify_priorite("Critique") == "haute"


def test_simplify_priorite_unknown_defaults_to_normale():
    assert simplify_priorite("valeur_inconnue") == "normale"
    assert simplify_priorite(None) == "normale"


# ── simplify_classification ─────────────────────────────────────────────────

def test_simplify_classification_known_values():
    assert simplify_classification("Incident") == "incident"
    assert simplify_classification("Demande") == "demande"
    assert simplify_classification("Problème") == "changement"


def test_simplify_classification_unknown_defaults_to_demande():
    assert simplify_classification("valeur_inconnue") == "demande"
    assert simplify_classification(None) == "demande"


# ── build_text_for_model ─────────────────────────────────────────────────────

def test_build_text_for_model_combines_titre_and_description():
    result = build_text_for_model("Problème VPN", "Impossible de se connecter")
    assert "vpn" in result
    assert "connecter" in result


# ── build_text_for_rag ───────────────────────────────────────────────────────

def test_build_text_for_rag_combines_all_fields():
    result = build_text_for_rag(
        description="Panne serveur",
        resolution="Redémarrage effectué",
        knowledge="Procédure standard",
        titre="Incident serveur",
    )
    assert "serveur" in result
    assert "redemarrage" in result
    assert "procedure" in result


def test_build_text_for_rag_defaults_are_empty():
    result = build_text_for_rag(description="Test panne réseau")
    assert "panne" in result


# ── build_text_enriched ──────────────────────────────────────────────────────

def test_build_text_enriched_includes_type_and_priorite_prefixes():
    result = build_text_enriched(
        titre="Ransomware détecté",
        description="Fichiers chiffrés",
        classification="Incident",
        priorite="Critique",
    )
    assert "type incident" in result
    assert "priorite haute" in result


def test_build_text_enriched_without_classification_or_priorite():
    result = build_text_enriched(titre="Test", description="Description test")
    assert "type" not in result
    assert "priorite" not in result
