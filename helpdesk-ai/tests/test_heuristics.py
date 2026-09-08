"""Tests unitaires — src/models/heuristics.py (Phase 12).

Couvre les deux passes du système : FORCE_RULES (écrase toujours la prédiction
ML) et SOFT_RULES (uniquement si confiance < seuil).
"""

from src.models.heuristics import apply_heuristics


# ── FORCE_RULES ──────────────────────────────────────────────────────────────

def test_force_rule_overrides_high_confidence_prediction():
    result = apply_heuristics(
        text_original="Ransomware détecté sur le poste comptabilité",
        predicted_category="Microsoft",
        confidence=0.95,
        threshold=0.60,
    )
    assert result["categorie"] == "Sécurité"
    assert result["heuristic_applied"] is True
    assert result["heuristic_type"] == "force"


def test_force_rule_matching_but_no_change_reports_not_applied():
    # Le mot-clé matche mais la catégorie ML était déjà correcte
    result = apply_heuristics(
        text_original="Ransomware détecté sur le poste comptabilité",
        predicted_category="Sécurité",
        confidence=0.30,
        threshold=0.60,
    )
    assert result["categorie"] == "Sécurité"
    assert result["heuristic_applied"] is False
    assert result["heuristic_type"] is None


def test_force_rule_word_boundary_matches_standalone_keyword():
    # « esxi » en tant que mot isolé → Infrastructure, quelle que soit la confiance
    result = apply_heuristics(
        text_original="L'hôte ESXi du cluster ne répond plus depuis ce matin",
        predicted_category="Réseau",
        confidence=0.90,
        threshold=0.60,
    )
    assert result["categorie"] == "Infrastructure"
    assert result["heuristic_applied"] is True
    assert result["heuristic_type"] == "force"


def test_force_rule_word_boundary_avoids_substring_false_positive():
    # « sage erp » ne doit PAS matcher à l'intérieur de « usage erp » : la frontière
    # de mot exige un séparateur avant le « s ».
    result = apply_heuristics(
        text_original="Nous étudions l'usage erp dans les filiales",
        predicted_category="Communication",
        confidence=0.90,
        threshold=0.60,
    )
    assert result["heuristic_applied"] is False


def test_mots_cles_retires_de_l_audit_ne_declenchent_plus():
    """
    Audit du 2026-08-22 : quatre mots-clés ont été retirés des règles fermes parce
    qu'ils n'étaient attestés dans aucun ticket d'entraînement et ne se
    déclenchaient que sur des tickets de test. Les réintroduire sans validation
    écrite du service support gonflerait artificiellement les résultats publiés.
    """
    cas = [
        ("Le SAN ne répond plus", "Infrastructure"),
        ("OneDrive ne synchronise pas les fichiers", "Microsoft"),
        ("Accès non autorisé détecté par l'IDS", "Sécurité"),
    ]
    for texte, categorie_autrefois_forcee in cas:
        r = apply_heuristics(
            text_original=texte,
            predicted_category="Réseau",
            confidence=0.90,
            threshold=0.60,
        )
        assert r["categorie"] != categorie_autrefois_forcee, (
            f"« {texte} » force encore {categorie_autrefois_forcee} : "
            f"un mot-clé retiré à l'audit a été réintroduit."
        )


# ── SOFT_RULES ───────────────────────────────────────────────────────────────

def test_soft_rule_applies_below_threshold():
    result = apply_heuristics(
        text_original="Problème de connexion VPN au bureau",
        predicted_category="Applicatifs",
        confidence=0.30,
        threshold=0.60,
    )
    assert result["categorie"] == "Réseau"
    assert result["heuristic_applied"] is True
    assert result["heuristic_type"] == "soft"
    assert result["confiance"] == 0.75


def test_soft_rule_does_not_apply_above_threshold():
    result = apply_heuristics(
        text_original="Problème de connexion VPN au bureau",
        predicted_category="Applicatifs",
        confidence=0.80,
        threshold=0.60,
    )
    assert result["categorie"] == "Applicatifs"
    assert result["heuristic_applied"] is False


# ── Aucune règle ─────────────────────────────────────────────────────────────

def test_no_rule_matches_keeps_ml_prediction():
    result = apply_heuristics(
        text_original="Texte générique sans mot-clé métier particulier",
        predicted_category="Applicatifs",
        confidence=0.55,
        threshold=0.60,
    )
    assert result["categorie"] == "Applicatifs"
    assert result["confiance"] == 0.55
    assert result["heuristic_applied"] is False
    assert result["heuristic_rule"] is None
    assert result["heuristic_type"] is None


def test_force_rule_confidence_floor_is_at_least_0_80():
    # Le score de confiance est remonté au minimum à 0.80 quand une FORCE_RULE s'applique
    result = apply_heuristics(
        text_original="Attaque DDOS en cours sur le pare-feu",
        predicted_category="Réseau",
        confidence=0.20,
        threshold=0.60,
    )
    assert result["categorie"] == "Sécurité"
    assert result["confiance"] >= 0.80
