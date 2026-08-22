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

import re

import requests

from api.config import settings

# Detecte un texte de "resolution" qui est en fait une synthese IA deja generee
# (ex: solution appliquee collee par erreur par un admin depuis ce meme panneau) —
# la reinjecter telle quelle dans le prompt fait "continuer le motif" au LLM, qui
# se met a inventer des tickets supplementaires (observe en usage reel : il reprend
# les ID de l'exemple few-shot, #1042/#985).
_SYNTHESIS_PATTERN_RE = re.compile(r"ticket\s*#\s*\d+\s*\(score\s*:", re.IGNORECASE)

# Un ticket cite par le LLM dans sa reponse ("Ticket #<id>") doit obligatoirement
# correspondre a l'un des candidats reellement fournis dans le prompt — le "#" est
# attendu ici car le system prompt impose ce format exact pour toute citation reelle.
_TICKET_ID_RE = re.compile(r"ticket\s*#\s*(\d+)", re.IGNORECASE)

# Variante tolerante ("#" optionnel) utilisee uniquement pour detecter les ID de ticket
# qu'un ADMIN mentionne dans ses propres questions au chat (langage naturel : "le ticket
# 9999" sans "#") — ces ID sont ensuite autorises en echo dans la reponse du LLM sans
# etre consideres comme une hallucination.
_LENIENT_TICKET_ID_RE = re.compile(r"ticket\s*#?\s*(\d+)", re.IGNORECASE)

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

# Prompt du mode "chat" (Tache 3 bis) : l'admin peut poser des questions de suivi libres
# sur le ticket et ses cas similaires, au lieu de se limiter au format fige en 3 parties
# de la synthese initiale. Les memes regles anti-hallucination s'appliquent.
CHAT_SYSTEM_PROMPT = """Tu es un assistant expert en support IT interne pour l'entreprise OneTech,
en discussion avec un administrateur qui traite un ticket. Le message suivant te donne le ticket
en cours et les tickets historiques similaires réellement trouvés (ID, score, catégorie et
résolution réels) — c'est ta seule source d'information.

Règles strictes :
- Réponds UNIQUEMENT à partir des informations fournies. N'invente JAMAIS un ticket, un ID, un
  score ou une catégorie qui n'y figure pas.
- Si l'admin demande une information absente des données fournies, dis-le clairement plutôt que
  d'inventer une réponse.
- Quand tu references un ticket, utilise toujours le format exact "Ticket #<id>" avec l'ID exact
  fourni.
- Réponds de façon concise et professionnelle, uniquement en français."""


def _build_user_prompt(titre: str, description: str, candidates: list[dict]) -> str:
    lines = [
        f'Nouveau ticket : "{titre}" — {description}',
        "",
        "Tickets historiques similaires (à reformuler, ne pas recopier tel quel) :",
    ]
    for c in candidates:
        score_pct = round((c.get("score") or 0) * 100)
        resolution = c.get("resolution", "") or ""
        if _SYNTHESIS_PATTERN_RE.search(resolution):
            # Resolution brute deja formatee comme une reponse IA (cf. commentaire plus
            # haut) : on ne la transmet pas telle quelle pour ne pas induire le LLM en erreur.
            resolution = "(résolution non disponible en texte clair)"
        lines.append(
            f"- Ticket #{c.get('ticket_id')} | Score {score_pct}% | "
            f"Catégorie {c.get('categorie') or 'Inconnue'} | "
            f"Résolution brute : {resolution}"
        )
    return "\n".join(lines)


def _cited_ticket_ids(text: str) -> set[int]:
    return {int(m) for m in _TICKET_ID_RE.findall(text)}


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
                # Garde le modele charge en memoire entre deux requetes (defaut Ollama : 5 min)
                # pour eviter de repayer le cold-start (~10s) a chaque nouveau ticket ouvert,
                # maintenant que la synthese se declenche automatiquement (plus seulement a la
                # demande) — cf. RISKS.md R-19.
                "keep_alive": "30m",
                "options": {
                    # Temperature basse : reponse factuelle, fidele aux donnees recues,
                    # plutot que creative — reduit aussi le risque d'inventer des tickets
                    # qui n'ont jamais ete fournis en contexte.
                    "temperature": 0.2,
                    # Plafond de tokens generes : borne le pire cas de latence si le
                    # modele derape et continue a generer (ex: tickets inventes en boucle)
                    # sans affecter une reponse normale (3 puces + intro + question tient
                    # largement dans cette limite).
                    "num_predict": 400,
                },
            },
            timeout=settings.OLLAMA_TIMEOUT,
        )
        resp.raise_for_status()
        content = (resp.json().get("message", {}) or {}).get("content", "").strip()
        if content:
            valid_ids = {c.get("ticket_id") for c in candidates if c.get("ticket_id") is not None}
            cited_ids = _cited_ticket_ids(content)
            if cited_ids and cited_ids.issubset(valid_ids):
                return {"text": content, "source": "ollama"}
            # Le LLM cite un ticket jamais fourni en contexte (hallucination) ou n'a cite
            # aucun ticket du tout — reponse non fiable, on ne l'affiche pas a l'admin.
    except Exception:
        pass

    return {"text": _fallback_synthesis(candidates), "source": "fallback"}


# Nombre de tours de conversation (question+reponse) conserves dans le prompt envoye au
# LLM — borne la croissance du prompt (donc la latence) sur une longue discussion, sans
# empecher l'admin de continuer a poser des questions (l'historique le plus recent prime).
_CHAT_HISTORY_LIMIT = 10


def chat_reply(titre: str, description: str, candidates: list[dict], history: list[dict]) -> dict:
    """
    Reponse conversationnelle a une question de l'admin sur ce ticket et ses cas
    similaires (Tache 3 bis, chat human-in-the-loop). Le contexte (ticket + candidats
    reels) est reconstruit ici a chaque appel a partir de l'etat actuel de la base —
    jamais fourni par le client — pour beneficier de l'assainissement anti-contamination
    (cf. _build_user_prompt) et rester fidele aux vraies donnees a tout moment.

    `history` : liste de {"role": "user"|"assistant", "content": str}, dans l'ordre
    chronologique (dernier message = derniere question de l'admin).

    Retourne {"reply": str, "source": "ollama" | "fallback"}.
    """
    grounding = (
        _build_user_prompt(titre, description, candidates)
        if candidates
        else f'Nouveau ticket : "{titre}" — {description}\n\nAucun ticket historique similaire connu pour ce ticket.'
    )

    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "user", "content": grounding},
        *history[-_CHAT_HISTORY_LIMIT:],
    ]

    try:
        resp = requests.post(
            f"{settings.OLLAMA_HOST}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "keep_alive": "30m",
                "options": {"temperature": 0.2, "num_predict": 400},
            },
            timeout=settings.OLLAMA_TIMEOUT,
        )
        resp.raise_for_status()
        content = (resp.json().get("message", {}) or {}).get("content", "").strip()
        if content:
            valid_ids = {c.get("ticket_id") for c in candidates if c.get("ticket_id") is not None}
            # Un ID mentionne par l'admin dans sa propre question n'est pas une
            # hallucination du LLM meme s'il ne correspond a aucun candidat reel (ex :
            # admin demande "et le ticket #9999 ?", le LLM repond honnetement qu'il n'a
            # pas cette information — c'est une reponse valide, pas une invention).
            # Seul un ID que le LLM introduit lui-meme, jamais vu ni dans les candidats
            # ni dans les questions de l'admin, compte comme une hallucination.
            admin_mentioned_ids: set[int] = set()
            for m in history:
                if m.get("role") == "user":
                    admin_mentioned_ids |= {
                        int(x) for x in _LENIENT_TICKET_ID_RE.findall(m.get("content", ""))
                    }
            allowed_ids = valid_ids | admin_mentioned_ids
            cited_ids = _cited_ticket_ids(content)
            # Contrairement a la synthese initiale, une reponse de chat valide peut ne
            # citer aucun ticket (ex: question generale sur la priorite a donner) — seule
            # une citation d'ID hors de allowed_ids invalide la reponse.
            if cited_ids.issubset(allowed_ids):
                return {"reply": content, "source": "ollama"}
    except Exception:
        pass

    return {
        "reply": (
            "Je ne peux pas répondre de façon fiable à cette question pour le moment "
            "— consultez directement les tickets similaires listés ci-dessus."
        ),
        "source": "fallback",
    }
