"""
AXE 2 — Controle qualite d'une connaissance avant son entree dans la base RAG.

Ce module est le point de passage oblige entre "un ticket a ete resolu" et "cette
resolution devient une reference proposee aux tickets suivants". Il ne parle ni a
ChromaDB ni a PostgreSQL : il recoit des chaines et rend un verdict. Cela le rend
testable sans base et reutilisable par l'API comme par les scripts hors ligne.

LE PROBLEME QU'IL RESOUT
    Avant, api/routers/tickets.py archivait :

        solution = ticket.commentaire_admin or ticket.solution_rag or ""

    Quand un administrateur cloturait un ticket sans ecrire de commentaire, et que
    le score RAG depassait le seuil de nouveaute, c'est la SUGGESTION DE L'IA,
    jamais relue par un humain, qui entrait dans la base de connaissances. Elle
    devenait ensuite une source pour les tickets suivants, dont les resolutions
    etaient a leur tour archivees. Le RAG se nourrissait de ses propres sorties.

LES CONTROLES
    solution_presente        une connaissance sans solution n'apprend rien
    longueur_minimale        "ok", "fait", "resolu" ne sont pas des connaissances
    origine_humaine          la solution doit venir d'un humain, pas du RAG
    non_recopie              une solution qui recopie la description ne resout rien
    doublon_proche           gere par le cycle de vie, pas par un rejet

Un rejet n'efface rien : le ticket reste dans PostgreSQL, qui est la verite metier.
Seule son entree dans la base de connaissances vectorielle est refusee.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

# Version du schema de metadonnees ecrit dans ChromaDB. Incrementer si la forme
# des metadonnees change, pour pouvoir distinguer les entrees anciennes.
KB_SCHEMA_VERSION = 1

REGLES_PAR_DEFAUT = {
    "min_solution_words": 4,
    "require_human_solution": True,
    "max_overlap_with_description": 0.90,
    "near_duplicate_threshold": 0.95,
}


@dataclass
class Verdict:
    """Resultat du controle. `action` dit quoi faire, `controles` dit pourquoi."""

    accepte: bool
    action: str                      # "index" | "update" | "reject"
    motif: str
    controles: list[dict] = field(default_factory=list)
    quality_score: float = 0.0
    near_duplicate_of: Optional[str] = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepte": self.accepte,
            "action": self.action,
            "motif": self.motif,
            "controles": self.controles,
            "quality_score": round(self.quality_score, 4),
            "near_duplicate_of": self.near_duplicate_of,
        }


def charger_regles(params: Optional[dict] = None) -> dict:
    """Fusionne params.yaml → knowledge.quality avec les valeurs par defaut."""
    regles = dict(REGLES_PAR_DEFAUT)
    if params:
        regles.update(params.get("knowledge", {}).get("quality", {}) or {})
    return regles


# ── utilitaires texte ────────────────────────────────────────────────────────

def normaliser(texte: str) -> str:
    t = unicodedata.normalize("NFKD", str(texte or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip()


def mots(texte: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{3,}", normaliser(texte)))


def recouvrement(source: str, cible: str) -> float:
    """Part du vocabulaire de `cible` deja presente dans `source`. 0.0 si vide."""
    ms, mc = mots(source), mots(cible)
    if not mc:
        return 0.0
    return len(ms & mc) / len(mc)


# ── controle ─────────────────────────────────────────────────────────────────

def controler(
    titre: str,
    description: str,
    solution: str,
    *,
    source_solution: str,
    regles: Optional[dict] = None,
    voisins: Optional[Iterable[dict]] = None,
) -> Verdict:
    """
    Verdict sur une connaissance candidate.

    Args:
        source_solution : "admin" si la solution a ete ecrite par un humain,
                          "ia" si elle provient d'une suggestion RAG non relue,
                          "inconnu" sinon.
        voisins         : resultats d'une recherche de similarite dans la base
                          existante, au format {"score": float, "id": str}. Sert
                          uniquement a detecter les quasi-doublons.
    """
    regles = regles or dict(REGLES_PAR_DEFAUT)
    controles: list[dict] = []

    def noter(nom: str, passe: bool, detail: str) -> None:
        controles.append({"controle": nom, "passe": bool(passe), "detail": detail})

    solution = str(solution or "").strip()
    description = str(description or "")

    presente = bool(solution) and normaliser(solution) not in ("", "nan", "none")
    noter("solution_presente", presente, "solution non vide")
    if not presente:
        return Verdict(False, "reject", "solution absente", controles)

    n_mots = len(solution.split())
    mini = int(regles.get("min_solution_words", 4))
    assez_longue = n_mots >= mini
    noter("longueur_minimale", assez_longue, f"{n_mots} mots (minimum {mini})")
    if not assez_longue:
        return Verdict(False, "reject", f"solution trop courte ({n_mots} mots)", controles)

    humaine = source_solution == "admin"
    exige_humain = bool(regles.get("require_human_solution", True))
    noter("origine_humaine", humaine or not exige_humain, f"source = {source_solution}")
    if exige_humain and not humaine:
        return Verdict(
            False, "reject",
            "solution non redigee par un humain — une suggestion IA non validee "
            "ne peut pas devenir une connaissance de reference",
            controles,
        )

    part = recouvrement(description, solution)
    plafond = float(regles.get("max_overlap_with_description", 0.90))
    original = part <= plafond
    noter("non_recopie", original, f"recouvrement avec la description {part:.2f} (plafond {plafond})")
    if not original:
        return Verdict(
            False, "reject",
            f"la solution recopie la description ({part:.0%} de vocabulaire commun)",
            controles,
        )

    seuil_doublon = float(regles.get("near_duplicate_threshold", 0.95))
    doublon_de = None
    for voisin in (voisins or []):
        if float(voisin.get("score", 0.0)) >= seuil_doublon:
            doublon_de = str(voisin.get("id") or voisin.get("ticket_id") or "")
            break
    noter(
        "doublon_proche",
        True,
        f"quasi-doublon de {doublon_de} (seuil {seuil_doublon})" if doublon_de
        else f"aucun voisin au-dessus de {seuil_doublon}",
    )

    # Note de qualite indicative, utilisee par le monitoring pour suivre le niveau
    # des connaissances entrantes. Ce n'est pas un seuil d'acceptation.
    score = min(1.0, n_mots / 40.0) * 0.6 + (1.0 - part) * 0.4

    if doublon_de:
        return Verdict(
            True, "update",
            f"connaissance retenue, quasi-doublon de {doublon_de} qui sera marque comme remplace",
            controles, quality_score=score, near_duplicate_of=doublon_de,
        )
    return Verdict(True, "index", "connaissance retenue", controles, quality_score=score)
