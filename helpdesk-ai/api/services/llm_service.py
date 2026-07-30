# api/services/llm_service.py
"""
Synthèse IA "human-in-the-loop" des tickets similaires (RAG admin) — LLM local Ollama.

Le RAG seul (ChromaDB) ne fait que retrouver le texte brut d'une résolution passée,
qui peut contenir des fautes ou des formulations informelles ("c est bon resolous").
Ce module ajoute une étape de triage : un LLM local reformule les cas trouvés en
français professionnel, sans jamais recracher le texte brut, pour que l'admin
choisisse rapidement le cas le plus pertinent avant d'explorer sa procédure complète.

100% on-premise : le LLM tourne dans le service Docker "ollama" (aucun appel externe,
aucune donnée de ticket ne sort de l'infrastructure). Dégradation gracieuse : si Ollama
est indisponible ou trop lent, on retombe sur un récapitulatif formaté sans reformulation
IA plutôt que de faire échouer la requête (cf. ARCHITECTURE.md).
"""

import requests

from api.config import settings

SYSTEM_PROMPT = """Tu es un assistant expert en support IT interne pour l'entreprise OneTech.
Un administrateur va te fournir un nouveau ticket ainsi que des tickets historiques
similaires trouvés par un moteur de recherche par similarité.

Ta réponse doit contenir EXACTEMENT 3 parties, dans cet ordre, rien d'autre :
1. Une phrase d'intro : "Bonjour. J'ai analysé cette demande et j'ai identifié [N]
   ticket(s) historique(s) similaire(s) :"
2. Une ligne à puce PAR ticket reçu (autant de lignes que de tickets reçus, ni plus ni
   moins), au format exact : "- **Ticket #<id> (Score : <score>% - <catégorie>) :**
   <une seule phrase professionnelle, sans faute, qui résume la cause et l'action de
   résolution — ne recopie jamais le texte brut fourni, qui peut être mal écrit>".
   Utilise l'ID, le score et la catégorie EXACTS des données reçues, jamais inventés.
3. Une question finale : "Quel ticket correspond le mieux à l'incident actuel ?
   Indiquez son ID pour afficher la procédure complète."

N'ajoute RIEN d'autre : aucune phrase d'analyse, aucun commentaire, aucun paragraphe
entre la liste et la question finale. Réponds uniquement en français."""

# Exemple concret (few-shot) injecté dans l'historique de conversation : un modèle
# local de petite taille (3B) suit un format strict beaucoup plus fidèlement quand on
# lui montre un exemple complet plutôt que de ne lui donner que des règles abstraites.
_EXAMPLE_USER = """Nouveau ticket : "Impossible de synchroniser mes emails" — Depuis ce matin la synchronisation échoue sur mon poste.

Tickets historiques similaires (à reformuler, ne pas recopier tel quel) :
- Ticket #1042 | Score 80% | Catégorie Microsoft | Résolution brute : jai vidé le cache et relancé ca a remarché nickel
- Ticket #985 | Score 72% | Catégorie Réseau | Résolution brute : pb de license expiree, jai reattribue les droits a l utilisateur"""

_EXAMPLE_ASSISTANT = """Bonjour. J'ai analysé cette demande et j'ai identifié deux tickets historiques très similaires :
- **Ticket #1042 (Score : 80% - Microsoft) :** Ce ticket traitait d'un problème de synchronisation. L'incident a été résolu en réinitialisant le cache.
- **Ticket #985 (Score : 72% - Réseau) :** Ce ticket concernait une erreur de licence. La solution a été de réattribuer les droits.
Lequel de ces deux cas correspond le mieux à l'incident actuel ? Fournissez-moi l'ID du ticket pour afficher la procédure complète."""


def _build_user_prompt(titre: str, description: str, candidates: list[dict]) -> str:
    lines = [
        f'Nouveau ticket : "{titre}" — {description}',
        "",
        "Tickets historiques similaires (à reformuler, ne pas recopier tel quel) :",
    ]
    for c in candidates:
        score_pct = round((c.get("score") or 0) * 100)
        lines.append(
            f"- Ticket #{c.get('ticket_id')} | Score {score_pct}% | "
            f"Catégorie {c.get('categorie') or 'Inconnue'} | "
            f"Résolution brute : {c.get('resolution', '')}"
        )
    return "\n".join(lines)


def _fallback_synthesis(candidates: list[dict]) -> str:
    """Repli sans LLM : récapitulatif formaté, texte brut non reformulé."""
    lines = [
        "Voici les tickets historiques les plus proches (synthèse IA indisponible, "
        "résultats bruts non reformulés) :",
    ]
    for c in candidates:
        score_pct = round((c.get("score") or 0) * 100)
        lines.append(
            f"- Ticket #{c.get('ticket_id')} (Score : {score_pct}% - "
            f"{c.get('categorie') or 'Inconnue'}) : {c.get('resolution', '')}"
        )
    lines.append("Indiquez l'ID du ticket à explorer pour afficher la procédure complète.")
    return "\n".join(lines)


def synthesize_recommendations(titre: str, description: str, candidates: list[dict]) -> dict:
    """
    Retourne {"text": str, "source": "ollama" | "fallback" | "none"}.

    "none"     : aucun ticket similaire trouvé, rien à synthétiser.
    "ollama"   : reformulation générée par le LLM local.
    "fallback" : Ollama indisponible/en erreur — récapitulatif brut formaté.
    """
    if not candidates:
        return {"text": "Aucun cas historique similaire n'a été trouvé pour ce ticket.", "source": "none"}

    try:
        resp = requests.post(
            f"{settings.OLLAMA_HOST}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _EXAMPLE_USER},
                    {"role": "assistant", "content": _EXAMPLE_ASSISTANT},
                    {"role": "user", "content": _build_user_prompt(titre, description, candidates)},
                ],
                "stream": False,
            },
            timeout=settings.OLLAMA_TIMEOUT,
        )
        resp.raise_for_status()
        content = (resp.json().get("message", {}) or {}).get("content", "").strip()
        if content:
            return {"text": content, "source": "ollama"}
    except Exception:
        pass

    return {"text": _fallback_synthesis(candidates), "source": "fallback"}
