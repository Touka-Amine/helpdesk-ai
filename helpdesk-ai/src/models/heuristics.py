"""
Règles heuristiques hybrides post-prédiction.

Deux niveaux de règles :
  - FORCE_RULES  : mots-clés tellement discriminants qu'ils écrasent la prédiction ML
                   MÊME si la confiance est haute (produits nommés, menaces précises).
  - SOFT_RULES   : appliquées uniquement quand la confiance ML est < seuil.
                   Corrigent les ambiguïtés sur les cas à faible confiance.

Appelé par ai_service.predict_and_recommend() sur le texte brut (non nettoyé).

RÈGLE MÉTHODOLOGIQUE — audit du 2026-08-22
------------------------------------------
Un mot-clé n'est admis ici que s'il est **attesté dans le jeu d'entraînement**, ou
s'il est inerte sur le jeu de test. Aucun mot-clé ne doit être ajouté après avoir
observé une erreur sur le jeu de test : cela revient à ajuster le système sur les
données qui servent à le juger, et le score cesse alors de mesurer la
généralisation.

Quatre mots-clés ont été retirés à ce titre. Ils ne figuraient dans aucun ticket
d'entraînement, se déclenchaient uniquement sur des tickets de test, et un
commentaire de ce fichier attestait que l'un d'eux avait été ajouté en lisant un
titre de test :

    onedrive             (Microsoft)      45 tickets de test corrigés
    ids                  (Sécurité)       12 tickets de test corrigés
    acces non autorise   (Sécurité)       redondant avec « ids »
    san                  (Infrastructure) 21 tickets de test corrigés

Effet mesuré du retrait, CamemBERT + règles, protocole stratifié 8 catégories :
F1-macro 0,9499 -> 0,8343. L'écart de 0,116 était la part non généralisable.

Ces quatre termes désignent des produits ou technologies dont la catégorie est
exacte (OneDrive est un produit Microsoft, un IDS relève de la sécurité, un SAN du
stockage). Ils pourront être réintroduits si le service support les valide par
écrit comme référentiel métier, indépendamment de tout résultat de test. Cette
validation doit être documentée en annexe du mémoire avant réintroduction.
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
    # "teams" retiré : les 64 tickets d'entraînement contenant « teams » sont TOUS
    # classés Communication par le service. Traité en SOFT_RULES Communication.
    # "onedrive" retiré (2026-08-22, audit des règles) : voir la note en tête de fichier.
    (
        ["outlook", "office 365", "office365",
         "sharepoint", "azure ad", "azure active directory", "exchange server",
         "microsoft 365", "m365", "onenote", "microsoft defender"],
        "Microsoft",
    ),
    # Sécurité — menaces explicites et incidents avérés
    # "ids", "acces non autorise" et "acces non-autorise" retirés (2026-08-22, audit
    # des règles) : voir la note en tête de fichier.
    (
        ["ransomware", "malware", "cryptolocker", "wannacry",
         "virus informatique", "attaque ddos", "intrusion detectee",
         "cyberattaque"],
        "Sécurité",
    ),
    # Infrastructure — équipements physiques critiques
    # "san" et "perte communication san" retirés (2026-08-22, audit des règles) :
    # voir la note en tête de fichier.
    (
        ["baie de stockage", "hyperviseur", "esxi", "vcenter"],
        "Infrastructure",
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
    # "ids" retiré : déjà couvert par FORCE_RULES Sécurité (code mort en SOFT_RULES)
    (
        ["phishing", "hameconnage", "intrusion", "firewall",
         "dossier securise", "acces securise", "connexion suspecte",
         "tentatives connexion", "alerte securite", "droits acces refuses",
         "acces refuse dossier", "compromis", "credential",
         "mot de passe compromis", "fuite donnees", "chiffrement",
         "antivirus", "malveillant", "piratage", "brute force",
         "compte bloque", "compte utilisateur bloque", "acces bloque",
         "utilisateur bloque", "session bloquee", "tentative connexion"],
        "Sécurité", 0.85,
    ),
    # Microsoft — produits Microsoft à confiance modérée
    # "teams"/"reunion teams"/"calendrier teams" retirés : SOFT_RULES Communication
    # "outlook"/"onedrive"/"sharepoint"/"onenote" retirés : déjà en FORCE_RULES Microsoft
    (
        ["office", "azure", "exchange", "boite mail", "messagerie outlook"],
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
    # "san"/"hyperviseur"/"esxi"/"vcenter"/"baie de stockage" retirés : déjà en FORCE_RULES
    (
        ["vmware", "hyper-v", "nas",
         "serveur physique", "alimentation serveur", "salle serveur"],
        "Infrastructure", 0.78,
    ),
    # Système — OS et configurations locales
    (
        ["windows update", "mise a jour windows", "pilote",
         "driver", "registre windows", "bsod", "ecran bleu",
         "redemarrage intempestif poste", "profil utilisateur corrompu"],
        "Système", 0.78,
    ),
    # Communication — téléphonie / messagerie unifiée + Teams en contexte communication
    # "teams" ici car "Problème Microsoft Teams" = outil de communication, pas incident Microsoft
    (
        ["voip", "telephone ip", "standard telephonique", "ipbx",
         "pbx", "messagerie vocale", "reunion video", "webex",
         "zoom", "cisco", "teams", "probleme teams", "appel teams",
         "reunion teams", "visioconference"],
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
