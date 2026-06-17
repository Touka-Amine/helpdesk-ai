"""
Règles heuristiques post-prédiction.
Corrigent les erreurs connues du modèle sur les cas ambigus.
Appliquées quand la confiance est faible (< seuil).
"""

# Mots-clés → catégorie forcée
# Format : (liste de mots-clés, catégorie cible, confiance minimale à attribuer)
KEYWORD_RULES = [
    # Réseau — mots très spécifiques jamais dans d'autres catégories
    (["vpn", "dns", "wifi", "wi-fi", "routeur", "switch",
      "bande passante", "ping", "latence", "paquet",
      "dhcp", "passerelle", "ip statique", "vlan"],
     "Réseau", 0.75),

    # Microsoft — produits Microsoft explicites
    (["outlook", "teams", "office 365", "onedrive", "sharepoint",
      "azure", "microsoft 365", "exchange", "onenote"],
     "Microsoft", 0.80),

    # Applicatifs — logiciels métier
    (["sage x3", "sage", "biotime", "erp", "x3"],
     "Applicatifs", 0.80),

    # Backup — mots très spécifiques
    (["sauvegarde", "backup", "restauration", "veeam",
      "snapshot", "rétention"],
     "Backup", 0.80),

    # Sécurité — mots très spécifiques
    (["ransomware", "malware", "virus", "phishing",
      "intrusion", "ids", "firewall", "compromission"],
     "Sécurité", 0.85),
]


def apply_heuristics(text_original: str,
                     predicted_category: str,
                     confidence: float,
                     threshold: float = 0.40) -> dict:
    """
    Applique les règles heuristiques si la confiance est sous le seuil.

    Returns:
        dict avec 'categorie', 'confiance', 'heuristic_applied' (bool)
    """
    # Pas besoin de corriger si confiance suffisante
    if confidence >= threshold:
        return {
            "categorie"          : predicted_category,
            "confiance"          : confidence,
            "heuristic_applied"  : False,
            "heuristic_rule"     : None
        }

    text_lower = text_original.lower()

    for keywords, target_category, min_confidence in KEYWORD_RULES:
        for kw in keywords:
            if kw in text_lower:
                return {
                    "categorie"         : target_category,
                    "confiance"         : min_confidence,
                    "heuristic_applied" : True,
                    "heuristic_rule"    : kw
                }

    # Aucune règle ne s'applique → on garde la prédiction ML
    return {
        "categorie"         : predicted_category,
        "confiance"         : confidence,
        "heuristic_applied" : False,
        "heuristic_rule"    : None
    }