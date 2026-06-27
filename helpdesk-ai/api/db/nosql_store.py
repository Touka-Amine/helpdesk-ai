"""
Stockage NoSQL des tickets résolus — TinyDB.

Architecture :
  - SQLite (SQLAlchemy) : base opérationnelle (utilisateurs, tickets en cours, historique)
  - TinyDB              : archive des tickets résolus après approbation agent

Avantages TinyDB pour ce projet :
  - Sans serveur (fichier JSON local)
  - Schéma flexible (document store)
  - Requêtes simples par catégorie, filiale, date
  - Peut alimenter le moteur RAG avec les nouvelles résolutions accumulées

Fichier JSON : data/resolved_tickets.json
"""

import os
from datetime import datetime
from typing import Optional

from tinydb import TinyDB, Query
from tinydb.table import Document

# Chemin absolu du fichier JSON (relatif à ce fichier → data/)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DB_PATH = os.path.join(_BASE_DIR, "data", "resolved_tickets.json")


def _open_db() -> TinyDB:
    """Ouvre une instance TinyDB (crée le dossier si nécessaire)."""
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    return TinyDB(_DB_PATH, indent=2, ensure_ascii=False)


# ── Écriture ───────────────────────────────────────────────────────────────────

def archive_resolved_ticket(
    ticket_id: int,
    titre: str,
    description: str,
    categorie: str,
    confiance: Optional[float],
    solution: str,
    knowledge: str,
    filiale: str = "",
    equipement: str = "",
    commentaire_client: str = "",
    approved_by: Optional[str] = None,
) -> int:
    """
    Archive un ticket résolu dans TinyDB.

    Appelé automatiquement depuis approve_ticket() quand statut → 'Résolu'.
    Retourne le doc_id TinyDB du document inséré.
    """
    with _open_db() as db:
        doc_id = db.insert({
            "ticket_id"         : ticket_id,
            "titre"             : titre,
            "description"       : description,
            "categorie"         : categorie,
            "confiance_ml"      : round(confiance, 4) if confiance is not None else None,
            "solution"          : solution,
            "knowledge"         : knowledge,
            "filiale"           : filiale,
            "equipement"        : equipement,
            "commentaire_client": commentaire_client,
            "approved_by"       : approved_by,
            "resolved_at"       : datetime.utcnow().isoformat(),
        })
    return doc_id


# ── Lecture ────────────────────────────────────────────────────────────────────

def get_all_resolved(limit: int = 100) -> list[Document]:
    """Retourne tous les tickets résolus (les plus récents en premier, limité)."""
    with _open_db() as db:
        docs = db.all()
    return sorted(docs, key=lambda d: d.get("resolved_at", ""), reverse=True)[:limit]


def get_resolved_by_categorie(categorie: str) -> list[Document]:
    """Retourne les tickets résolus d'une catégorie donnée."""
    with _open_db() as db:
        Q = Query()
        return db.search(Q.categorie == categorie)


def get_resolved_by_filiale(filiale: str) -> list[Document]:
    """Retourne les tickets résolus d'une filiale donnée."""
    with _open_db() as db:
        Q = Query()
        return db.search(Q.filiale == filiale)


# ── Statistiques ───────────────────────────────────────────────────────────────

def get_stats() -> dict:
    """
    Retourne les KPIs agrégés de la base de tickets résolus.
    Utilisé par l'endpoint /tickets/resolved/stats.
    """
    with _open_db() as db:
        docs = db.all()

    total = len(docs)
    if total == 0:
        return {"total": 0, "par_categorie": {}, "par_filiale": {}}

    par_categorie: dict[str, int] = {}
    par_filiale: dict[str, int] = {}

    for doc in docs:
        cat = doc.get("categorie", "Inconnue")
        fil = doc.get("filiale", "Inconnue") or "Inconnue"
        par_categorie[cat] = par_categorie.get(cat, 0) + 1
        par_filiale[fil] = par_filiale.get(fil, 0) + 1

    return {
        "total"         : total,
        "par_categorie" : dict(sorted(par_categorie.items(), key=lambda x: -x[1])),
        "par_filiale"   : dict(sorted(par_filiale.items(), key=lambda x: -x[1])),
    }


def count_resolved() -> int:
    """Nombre total de tickets résolus archivés."""
    with _open_db() as db:
        return len(db)
