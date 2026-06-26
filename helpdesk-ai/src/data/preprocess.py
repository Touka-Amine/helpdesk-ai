"""
Module de prétraitement textuel — HelpDesk AI.

Deux fonctions principales :
  - clean_text(text)             : nettoyage de base (lowercase, accents, stop-words)
  - build_text_for_model(t, d)   : feature ML = titre + description nettoyés
  - build_text_for_rag(...)      : feature enrichie pour le moteur RAG
"""

import re
import unicodedata
import nltk

nltk.download("stopwords", quiet=True)
from nltk.corpus import stopwords

# ── Stop-words ─────────────────────────────────────────────────────────────────
# On conserve UNIQUEMENT les mots vraiment non-discriminants.
# ATTENTION : ne pas supprimer les termes IT clés (outlook, vpn, dns, sage…).
_STOP_FR = set(stopwords.words("french"))
_STOP_EN = set(stopwords.words("english"))

# Mots de politesse et termes génériques de communication ticket —
# PAS les termes métier IT (ils restent).
_STOP_DOMAIN = {
    "bonjour", "support", "merci", "cordialement", "cher",
    "bonne", "journee", "svp", "lors", "suite",
    "hello", "hi", "dear", "team", "please", "regards",
    "otbs", "tech", "business", "solutions",
    "ticket",  # trop générique dans ce contexte
}

# Termes IT discriminants à NE PAS supprimer même s'ils sont dans STOP_FR/EN :
_KEEP = {
    "reseau", "systeme", "application", "serveur", "poste", "acces",
    "connexion", "microsoft", "outlook", "teams", "vpn", "dns", "wifi",
    "sage", "erp", "backup", "sauvegarde", "securite", "virus",
    "firewall", "internet", "email", "mail", "bureau", "windows",
    "erreur", "probleme", "impossible", "fonctionne", "lent",
}

STOP_WORDS = (_STOP_FR | _STOP_EN | _STOP_DOMAIN) - _KEEP


def clean_text(text: str) -> str:
    """
    Nettoyage standard :
      1. Minuscules
      2. Normalisation Unicode (suppression accents)
      3. Suppression URLs, emails, IPs
      4. Suppression ponctuation (sauf chiffres — certains codes utiles)
      5. Suppression stop-words (liste allégée)
      6. Tokens de longueur ≥ 2

    Conserver les chiffres (codes erreur, numéros de version) à ce stade ;
    seules les IP sont supprimées (trop spécifiques et non discriminantes).
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    # Lowercase
    text = text.lower()

    # Normalisation unicode (retire les accents)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # Supprimer URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    # Supprimer emails
    text = re.sub(r"\S+@\S+", " ", text)
    # Supprimer adresses IP
    text = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", " ", text)
    # Supprimer caractères spéciaux (garder lettres, chiffres, espaces)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Normaliser espaces
    text = re.sub(r"\s+", " ", text).strip()

    # Tokenisation + filtrage
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOP_WORDS and len(t) >= 2]

    return " ".join(tokens)


def build_text_for_model(titre: str, description: str) -> str:
    """
    Feature pour la classification ML.

    Utilise titre + description (dans cet ordre) pour que les mots-clés
    du titre (souvent très discriminants : 'Problème VPN', 'Ransomware détecté')
    soient bien représentés dans le vecteur TF-IDF.
    """
    combined = f"{titre} {description}"
    return clean_text(combined)


def build_text_for_rag(
    description: str,
    resolution: str = "",
    knowledge: str = "",
    titre: str = "",
) -> str:
    """
    Feature enrichie pour le moteur RAG.
    Combine tout le contexte disponible pour maximiser la similarité cosinus.
    """
    combined = f"{titre} {description} {resolution} {knowledge}"
    return clean_text(combined)
