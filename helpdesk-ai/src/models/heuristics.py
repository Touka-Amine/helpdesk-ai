"""
Règles heuristiques hybrides post-prédiction.

Deux niveaux de règles :
  - FORCE_RULES  : mots-clés tellement discriminants qu'ils écrasent la prédiction ML
                   MÊME si la confiance est haute (produits nommés, menaces précises).
  - SOFT_RULES   : appliquées uniquement quand la confiance ML est < seuil.
                   Corrigent les ambiguïtés sur les cas à faible confiance.

Appelé par ai_service.predict_and_recommend() sur le texte brut (non nettoyé).
"""

import unicodedata
import re


def _normalize(text: str) -> str:
    """Minuscules + suppression accents pour matching insensible à la casse/accentuation."""
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text


# ── FORCE_RULES ────────────────────────────────────────────────────────────────
# Ces mots-clés correspondent à des produits/concepts qui ne peuvent appartenir
# qu'à une seule catégorie. Ils écrasent toute prédiction ML, quelle que soit
# la confiance.
FORCE_RULES: list[tuple[list[str], str]] = [
    # Microsoft — noms de produits exclusifs Microsoft
    (
        ["outlook", "teams", "office 365", "office365", "onedrive",
         "sharepoint", "azure ad", "azure active directory", "exchange server",
         "microsoft 365", "m365", "onenote", "microsoft defender"],
        "Microsoft",
    ),
    # Sécurité — menaces explicites / incidents de sécurité avérés
    (
        ["ransomware", "malware", "cryptolocker", "wannacry",
         "virus informatique", "attaque ddos", "intrusion detectee",
         "cyberattaque"],
        "Sécurité",
    ),
    # Applicatifs — logiciels métier nommés
    (
        ["sage x3", "sage erp", "biotime"],
        "Applicatifs",
    ),
    # Backup — outils de sauvegarde nommés
    (
        ["veeam", "acronis backup", "commvault"],
        "Backup",
    ),
]

# ── SOFT_RULES ─────────────────────────────────────────────────────────────────
# Appliquées uniquement si confiance ML < seuil.
# Format : (liste mots-clés, catégorie cible, confiance à attribuer)
SOFT_RULES: list[tuple[list[str], str, float]] = [
    # Réseau — terminologie réseau précise
    (
        ["vpn", "dns", "wi-fi", "wifi", "routeur", "switch reseau",
         "bande passante", "ping", "latence reseau", "perte de paquets",
         "dhcp", "passerelle", "ip statique", "vlan", "proxy",
         "internet lent", "connexion internet", "acces internet",
         "debit internet", "coupure reseau", "reseau instable"],
        "Réseau", 0.75,
    ),
    # Sécurité — vocabulaire sécurité IT large
    (
        ["phishing", "hameconnage", "intrusion", "ids", "firewall",
         "dossier securise", "acces securise", "connexion suspecte",
         "tentatives connexion", "alerte securite", "droits acces refuses",
         "acces refuse dossier", "compromis", "credential",
         "mot de passe compromis", "fuite donnees", "chiffrement",
         "antivirus", "malveillant", "piratage", "brute force"],
        "Sécurité", 0.85,
    ),
    # Microsoft — produits Microsoft à confiance modérée
    (
        ["outlook", "teams", "office", "onedrive", "sharepoint",
         "azure", "exchange", "onenote", "boite mail", "messagerie outlook",
         "calendrier teams", "reunion teams"],
        "Microsoft", 0.80,
    ),
    # Applicatifs — logiciels métier génériques
    (
        ["sage", "erp", "application metier", "logiciel rh",
         "logiciel comptable", "devis", "stock", "pointage",
         "facturation", "crm"],
        "Applicatifs", 0.78,
    ),
    # Backup — mots liés aux sauvegardes
    (
        ["sauvegarde", "backup", "restauration", "snapshot",
         "retention", "plan de reprise", "pra", "pca"],
        "Backup", 0.80,
    ),
    # Infrastructure — serveurs, hyperviseurs
    (
        ["hyperviseur", "vmware", "hyper-v", "esxi", "vcenter",
         "serveur physique", "baie de stockage", "san", "nas",
         "alimentation serveur", "salle serveur"],
        "Infrastructure", 0.78,
    ),
    # Système — OS et configurations locales
    (
        ["windows update", "mise a jour windows", "pilote",
         "driver", "registre windows", "bsod", "ecran bleu",
         "redemarrage intempestif poste", "profil utilisateur corrompu"],
        "Système", 0.78,
    ),
    # Communication — téléphonie / messagerie unifiée
    (
        ["voip", "telephone ip", "standard telephonique", "ipbx",
         "pbx", "messagerie vocale", "reunion video", "webex",
         "zoom", "cisco"],
        "Communication", 0.78,
    ),
]


def apply_heuristics(
    text_original: str,
    predicted_category: str,
    confidence: float,
    threshold: float = 0.40,
) -> dict:
    """
    Pipeline d'heuristiques en deux passes :

    1. FORCE_RULES  → écrase la prédiction ML quel que soit le score
    2. SOFT_RULES   → corrige uniquement si confiance < seuil

    Args:
        text_original     : texte brut (titre + description, non nettoyé)
        predicted_category: catégorie retournée par le modèle ML
        confidence        : score de confiance du modèle ML
        threshold         : seuil en dessous duquel les SOFT_RULES s'appliquent

    Returns:
        dict :
            categorie         — catégorie finale
            confiance         — confiance finale
            heuristic_applied — True si une règle a modifié la prédiction
            heuristic_rule    — mot-clé déclencheur (ou None)
            heuristic_type    — "force" | "soft" | None
    """
    text_norm = _normalize(text_original)

    # ── Passe 1 : FORCE_RULES ─────────────────────────────────────────────────
    for keywords, target_category in FORCE_RULES:
        for kw in keywords:
            kw_norm = _normalize(kw)
            # Correspondance sur mot entier pour éviter les faux positifs
            pattern = r"\b" + re.escape(kw_norm) + r"\b"
            if re.search(pattern, text_norm):
                changed = target_category != predicted_category
                return {
                    "categorie"        : target_category,
                    "confiance"        : max(confidence, 0.80),
                    "heuristic_applied": changed,
                    "heuristic_rule"   : kw,
                    "heuristic_type"   : "force" if changed else None,
                }

    # ── Passe 2 : SOFT_RULES (uniquement si confiance < seuil) ───────────────
    if confidence < threshold:
        for keywords, target_category, min_confidence in SOFT_RULES:
            for kw in keywords:
                kw_norm = _normalize(kw)
                if kw_norm in text_norm:
                    return {
                        "categorie"        : target_category,
                        "confiance"        : min_confidence,
                        "heuristic_applied": True,
                        "heuristic_rule"   : kw,
                        "heuristic_type"   : "soft",
                    }

    # ── Aucune règle déclenchée → on garde la prédiction ML ──────────────────
    return {
        "categorie"        : predicted_category,
        "confiance"        : confidence,
        "heuristic_applied": False,
        "heuristic_rule"   : None,
        "heuristic_type"   : None,
    }
