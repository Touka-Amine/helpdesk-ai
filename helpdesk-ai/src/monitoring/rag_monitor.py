"""
Monitoring de la base de connaissances et de la pertinence du RAG.

Deux sources, deux questions differentes :
  PostgreSQL  ce que le RAG a produit en situation reelle (scores servis, avis des
              utilisateurs, taux de rejet implicite par les administrateurs)
  ChromaDB    ce que la base contient (volume, statuts, doublons, anciennete)

CE QUI EST MESURABLE
    distribution des rag_score      colonne stockee sur chaque ticket
    taux de nouveaute               part des tickets sous le seuil de nouveaute :
                                    aucun cas comparable trouve dans la base
    avis utilisateurs               feedback_vote, renseigne par l'endpoint feedback
    rejet implicite                 part des tickets resolus ou la solution ecrite
                                    par l'admin differe de la suggestion du RAG.
                                    Signal fort : l'admin a vu la suggestion et a
                                    ecrit autre chose.
    volume et composition           entrees actives, remplacees, obsoletes
    doublons                        entrees marquees near_duplicate_of
    anciennete                      entrees non re-confirmees depuis longtemps
    qualite entrante                quality_score attribue a l'indexation

CE QUI N'EST PAS MESURABLE, ET NE DOIT PAS ETRE INVENTE
    - Quelle recommandation parmi les trois l'administrateur a reellement utilisee.
      Aucun evenement de clic ou de selection n'est journalise.
    - La pertinence objective d'une recommandation sans jeu annote. Les indicateurs
      precision@k demandent le jeu construit par src/pipeline/rag_eval.py.
    - Les contradictions entre connaissances. Detecter que deux solutions se
      contredisent demande une comparaison semantique dirigee que le systeme ne
      fait pas. Seuls les quasi-doublons sont detectes, ce qui est different.

Usage :
    python src/monitoring/rag_monitor.py
    python src/monitoring/rag_monitor.py --db-url sqlite:///data/tickets.db
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone

import pandas as pd
import yaml

_RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _RACINE)
sys.path.insert(0, os.path.join(_RACINE, "src"))

PARAMS_PATH = "params.yaml"
OUT = "metrics/rag_monitor.json"
NOVELTY_THRESHOLD = 0.50   # meme valeur que api/routers/tickets.py

NON_MESURABLE = [
    "Recommandation effectivement utilisee par l'administrateur : aucun evenement "
    "de selection n'est journalise.",
    "Pertinence objective sans jeu annote : voir src/pipeline/rag_eval.py.",
    "Contradictions entre connaissances : seuls les quasi-doublons sont detectes.",
]


def normaliser(texte: str) -> str:
    t = unicodedata.normalize("NFKD", str(texte or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip()


def indicateurs_production(tickets: pd.DataFrame, params: dict) -> dict:
    if tickets.empty:
        return {"n_tickets": 0, "note": "aucune donnee de production"}

    out: dict = {"n_tickets": int(len(tickets))}

    # DataFrame.get renvoie None quand la colonne manque, et pd.to_numeric(None)
    # produit un scalaire, pas une Serie. Les bases anterieures a la migration
    # n'ont pas toutes ces colonnes : on verifie leur presence explicitement.
    scores = (
        pd.to_numeric(tickets["rag_score"], errors="coerce").dropna()
        if "rag_score" in tickets.columns else pd.Series(dtype=float)
    )
    if not scores.empty:
        seuil = params.get("rag", {}).get("similarity_threshold", 0.50)
        out["rag_score"] = {
            "n": int(len(scores)),
            "moyenne": round(float(scores.mean()), 4),
            "mediane": round(float(scores.median()), 4),
            "p10": round(float(scores.quantile(0.10)), 4),
            "p90": round(float(scores.quantile(0.90)), 4),
            "part_sous_seuil_pertinence": round(float((scores < seuil).mean()), 4),
            "taux_nouveaute": round(float((scores < NOVELTY_THRESHOLD).mean()), 4),
            "lecture_nouveaute": (
                "Part des tickets sans cas comparable dans la base. Une hausse "
                "durable signale soit un elargissement du perimetre, soit une base "
                "de connaissances qui ne suit plus."
            ),
        }

    if "feedback_vote" in tickets.columns:
        votes = tickets["feedback_vote"].dropna()
        out["feedback_utilisateurs"] = {
            "n_votes": int(len(votes)),
            "repartition": {str(k): int(v) for k, v in votes.value_counts().items()},
            "taux_participation": round(float(len(votes) / len(tickets)), 4),
        }

    if "statut" not in tickets.columns:
        return out
    resolus = tickets[tickets["statut"].astype(str).eq("Résolu")]
    if not resolus.empty and {"commentaire_admin", "solution_rag"} <= set(resolus.columns):
        avec_solution = resolus[
            resolus["commentaire_admin"].astype(str).str.strip().ne("")
        ]
        if not avec_solution.empty:
            differe = (
                avec_solution["commentaire_admin"].map(normaliser)
                != avec_solution["solution_rag"].map(normaliser)
            )
            out["rejet_implicite_suggestion"] = {
                "n_tickets_avec_solution_admin": int(len(avec_solution)),
                "taux_solution_differente": round(float(differe.mean()), 4),
                "lecture": (
                    "L'administrateur a vu la suggestion du RAG et a ecrit autre "
                    "chose. Proxy direct du taux de suggestions non retenues."
                ),
            }
        out["taux_cloture_sans_solution_ecrite"] = round(
            float((resolus["commentaire_admin"].astype(str).str.strip() == "").mean()), 4
        )

    return out


def indicateurs_base(params: dict) -> dict:
    """Etat de ChromaDB. Retourne une explication plutot qu'une erreur si absente."""
    try:
        from api.db.vector_store import get_all_entries, STATUT_ACTIF
    except Exception as exc:
        return {"disponible": False,
                "motif": f"module inaccessible ({type(exc).__name__}: {exc})"}

    try:
        entrees = get_all_entries()
    except Exception as exc:
        return {"disponible": False,
                "motif": f"ChromaDB injoignable ({type(exc).__name__}: {exc})"}

    if not entrees:
        return {"disponible": True, "total": 0,
                "note": "base de connaissances vide — aucun ticket resolu archive"}

    statuts: dict[str, int] = {}
    categories: dict[str, int] = {}
    sources: dict[str, int] = {}
    qualites: list[float] = []
    doublons = 0
    obsoletes_potentiels = 0

    jours = int(params.get("knowledge", {}).get("lifecycle", {}).get("stale_after_days", 365))
    limite = datetime.now(timezone.utc) - timedelta(days=jours)

    for e in entrees:
        statut = str(e.get("statut", STATUT_ACTIF) or STATUT_ACTIF)
        statuts[statut] = statuts.get(statut, 0) + 1
        if statut != STATUT_ACTIF:
            continue
        categories[str(e.get("categorie") or "Inconnue")] = (
            categories.get(str(e.get("categorie") or "Inconnue"), 0) + 1
        )
        sources[str(e.get("source_solution") or "inconnu")] = (
            sources.get(str(e.get("source_solution") or "inconnu"), 0) + 1
        )
        if e.get("quality_score") is not None:
            try:
                qualites.append(float(e["quality_score"]))
            except (TypeError, ValueError):
                pass
        if str(e.get("near_duplicate_of") or ""):
            doublons += 1
        horodatage = str(e.get("indexed_at") or e.get("resolved_at") or "")
        try:
            quand = datetime.fromisoformat(horodatage)
            if quand.tzinfo is None:
                quand = quand.replace(tzinfo=timezone.utc)
            if quand < limite:
                obsoletes_potentiels += 1
        except ValueError:
            pass

    actives = statuts.get(STATUT_ACTIF, 0)
    rapport = {
        "disponible": True,
        "total": len(entrees),
        "par_statut": statuts,
        "actives": actives,
        "par_categorie": dict(sorted(categories.items(), key=lambda x: -x[1])),
        "par_origine_solution": sources,
        "quasi_doublons_signales": doublons,
        "taux_doublons": round(doublons / actives, 4) if actives else 0.0,
        "obsoletes_potentiels": obsoletes_potentiels,
        "seuil_anciennete_jours": jours,
        "note_obsolescence": (
            "Signalement seul. Aucune connaissance n'est supprimee automatiquement : "
            "une procedure ancienne peut rester la bonne."
        ),
    }
    if qualites:
        serie = pd.Series(qualites)
        rapport["qualite_entrante"] = {
            "n": len(qualites),
            "moyenne": round(float(serie.mean()), 4),
            "mediane": round(float(serie.median()), 4),
            "min": round(float(serie.min()), 4),
        }
    if sources.get("ia"):
        rapport["alerte"] = (
            f"{sources['ia']} entrees d'origine IA presentes. Elles datent d'avant le "
            f"controle qualite : les entrees actuelles sont refusees si la solution "
            f"n'a pas ete ecrite par un humain."
        )
    return rapport


def run(args: argparse.Namespace) -> int:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        params = yaml.safe_load(f)

    db_url = args.db_url or os.environ.get("DB_URL")
    if not db_url:
        try:
            from api.config import settings
            db_url = settings.DB_URL
        except Exception:
            db_url = "sqlite:///data/tickets.db"

    tickets = pd.DataFrame()
    erreur_db = None
    try:
        from sqlalchemy import create_engine
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        engine = create_engine(db_url, connect_args=connect_args)
        with engine.connect() as conn:
            tickets = pd.read_sql("SELECT * FROM tickets", conn)
    except Exception as exc:
        erreur_db = f"{type(exc).__name__}: {exc}"
        print(f"[rag_monitor] Base injoignable : {erreur_db}")
        if not args.allow_offline:
            return 1

    rapport = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "production": indicateurs_production(tickets, params),
        "base_connaissances": indicateurs_base(params),
        "evaluation_hors_ligne": _lire_eval(),
        "non_mesurable": NON_MESURABLE,
    }
    if erreur_db:
        rapport["production"]["erreur"] = erreur_db

    os.makedirs("metrics", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)

    base = rapport["base_connaissances"]
    print(f"[rag_monitor] connaissances : {base.get('total', 0)} "
          f"({base.get('actives', 0)} actives) | tickets : {len(tickets)}")
    print(f"[rag_monitor] ecrit {OUT}")
    return 0


def _lire_eval() -> dict:
    """Derniere evaluation hors ligne du RAG, si elle existe."""
    try:
        with open("metrics/rag_eval.json", encoding="utf-8") as f:
            donnees = json.load(f)
        return {"disponible": True, "date": donnees.get("date"),
                "protocole": donnees.get("eval_protocol") or donnees.get("protocole"),
                "resume": {k: v for k, v in donnees.items()
                           if isinstance(v, (int, float, str))}}
    except (OSError, json.JSONDecodeError):
        return {"disponible": False,
                "note": "lancez python src/pipeline/rag_eval.py"}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db-url", help="surcharge de l'URL de base")
    p.add_argument("--allow-offline", action="store_true",
                   help="continue si la base est injoignable")
    sys.exit(run(p.parse_args()))
