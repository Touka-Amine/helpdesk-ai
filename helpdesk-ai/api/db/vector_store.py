"""
Base de connaissances vectorielle des tickets résolus — ChromaDB.

Architecture à deux piliers :
  - PostgreSQL (SQLAlchemy) : base opérationnelle — intégrité relationnelle et
                              transactionnelle (utilisateurs, tickets en cours, historique)
  - ChromaDB                : base de connaissances vectorielle — recherche sémantique
                              du RAG hybride sur les tickets résolus

Contrairement à l'ancien stockage TinyDB (simple journal JSON, jamais relu par le RAG —
un ticket résolu n'était donc jamais réellement proposé aux tickets suivants avant un
réentraînement complet), cette collection est interrogée en direct par le pipeline de
recommandation (voir query_similar(), appelée depuis api/services/ai_service.py) : une
résolution admin devient exploitable par le RAG immédiatement, sans attendre un nouveau
`dvc repro` ni un redémarrage du serveur.

Mode embarqué (PersistentClient) : pas de serveur ChromaDB séparé, stockage dans
data/chroma/ (monté dans le même volume Docker que les modèles).

CYCLE DE VIE DES CONNAISSANCES (axe 2)
    Toute entrée passe par src/knowledge/quality.py avant indexation. Une entrée
    porte désormais un statut :

        actif       proposée par le RAG
        superseded  remplacée par une connaissance quasi identique plus récente
        obsolete    signalée par le monitoring, jamais supprimée automatiquement

    Le filtrage par statut est appliqué en Python après la requête plutôt que dans
    la clause `where` de Chroma : les entrées écrites avant l'introduction de ce
    champ n'ont pas de `statut`, et un filtre côté base les exclurait silencieusement.
    Une entrée sans statut est traitée comme active.
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_BASE_DIR, "src"))

from knowledge.quality import KB_SCHEMA_VERSION, charger_regles, controler  # noqa: E402

_CHROMA_PATH = os.path.join(_BASE_DIR, "data", "chroma")
_COLLECTION_NAME = "resolved_tickets"
# Même modèle que SemanticRAGEngine (src/rag/semantic_engine.py) — espace vectoriel cohérent.
_EMBED_MODEL = "paraphrase-multilingual-mpnet-base-v2"

STATUT_ACTIF = "actif"
STATUT_REMPLACE = "superseded"
STATUT_OBSOLETE = "obsolete"

# Journal des refus du contrôle qualité. Une connaissance refusée n'entre pas dans
# la base vectorielle, par définition : sans ce journal, le refus ne laissait de
# trace que dans la sortie du serveur. Une ligne JSON par refus, dans le même
# volume Docker que la base (data/), pour survivre aux redémarrages.
_JOURNAL_REFUS = os.path.join(_BASE_DIR, "data", "kb", "refus.jsonl")

_client = None
_embed_fn = None
_regles = None


def _get_embed_fn():
    """Modèle d'embedding — chargement paresseux, mis en cache (coûteux à recharger)."""
    global _embed_fn
    if _embed_fn is None:
        _embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=_EMBED_MODEL)
    return _embed_fn


def _get_regles() -> dict:
    """Règles de qualité lues une fois depuis params.yaml, valeurs par défaut sinon."""
    global _regles
    if _regles is None:
        try:
            import yaml
            with open(os.path.join(_BASE_DIR, "params.yaml"), encoding="utf-8") as f:
                _regles = charger_regles(yaml.safe_load(f))
        except Exception:
            _regles = charger_regles(None)
    return _regles


def _get_collection():
    """
    Ouvre la collection Chroma. Le client persistant est mis en cache (connexion au
    fichier), mais la collection est ré-obtenue à chaque appel plutôt que mise en cache
    globalement : l'API tourne avec plusieurs workers uvicorn (processus séparés,
    Dockerfile.api --workers 2) — une collection mise en cache dans un worker ne voit
    pas les écritures faites par un autre worker tant qu'elle n'est pas ré-ouverte.
    """
    global _client
    if _client is None:
        os.makedirs(_CHROMA_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(path=_CHROMA_PATH)
    return _client.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=_get_embed_fn(),
        metadata={"hnsw:space": "cosine"},
    )


def _est_actif(meta: dict) -> bool:
    """Une entrée sans statut date d'avant le cycle de vie : considérée active."""
    return str(meta.get("statut", STATUT_ACTIF) or STATUT_ACTIF) == STATUT_ACTIF


# ── Contrôle qualité et détection de doublons ──────────────────────────────────

def chercher_voisins(text: str, top_k: int = 3) -> list[dict]:
    """Voisins les plus proches, au format attendu par knowledge.quality.controler()."""
    collection = _get_collection()
    count = collection.count()
    if count == 0 or not text.strip():
        return []
    try:
        res = collection.query(query_texts=[text], n_results=min(top_k, count))
    except Exception:
        return []
    ids = (res.get("ids") or [[]])[0]
    distances = (res.get("distances") or [[]])[0]
    return [
        {"id": str(i), "score": max(0.0, 1.0 - float(d))}
        for i, d in zip(ids, distances)
    ]


def _marquer_remplace(ancien_id: str, nouveau_id: str) -> None:
    """
    Marque une entrée comme remplacée par une plus récente.

    Rien n'est supprimé : le document reste interrogeable pour l'audit et le
    monitoring, il cesse simplement d'être proposé par le RAG.
    """
    collection = _get_collection()
    try:
        existant = collection.get(ids=[ancien_id], include=["metadatas"])
    except Exception:
        return
    metas = existant.get("metadatas") or []
    if not metas:
        return
    meta = dict(metas[0])
    meta["statut"] = STATUT_REMPLACE
    meta["superseded_by"] = nouveau_id
    meta["superseded_at"] = datetime.now(timezone.utc).isoformat()
    try:
        collection.update(ids=[ancien_id], metadatas=[meta])
    except Exception:
        pass


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
    source_solution: str = "inconnu",
) -> dict:
    """
    Contrôle qualité puis indexation d'une résolution dans la base de connaissances.

    Appelé en tâche de fond (BackgroundTasks, api/routers/tickets.py) quand statut →
    'Résolu' — le calcul de l'embedding (sentence-transformers) ne bloque jamais la
    réponse HTTP de l'admin.

    Args:
        source_solution : "admin" si `solution` vient de commentaire_admin (écrite
                          par un humain), "ia" si elle vient de solution_rag
                          (suggestion jamais relue). Le contrôle qualité refuse les
                          secondes : sans cela, le RAG se nourrit de ses propres
                          sorties.

    Returns:
        Le verdict du contrôle, sérialisable. Le ticket reste dans PostgreSQL
        quelle que soit l'issue : seule son entrée dans la base vectorielle
        peut être refusée.
    """
    text = "\n".join(p for p in (titre, description, solution) if p).strip()
    if not text:
        verdict_vide = {"accepte": False, "action": "reject", "motif": "contenu vide", "controles": []}
        _journaliser_refus(ticket_id, titre, categorie, filiale, source_solution, verdict_vide)
        return verdict_vide

    verdict = controler(
        titre=titre,
        description=description,
        solution=solution,
        source_solution=source_solution,
        regles=_get_regles(),
        voisins=chercher_voisins(text, top_k=3),
    )

    if not verdict.accepte:
        print(f"[kb] ticket {ticket_id} refuse — {verdict.motif}")
        _journaliser_refus(ticket_id, titre, categorie, filiale, source_solution, verdict.as_dict())
        return verdict.as_dict()

    collection = _get_collection()
    maintenant = datetime.now(timezone.utc).isoformat()
    collection.upsert(
        ids=[str(ticket_id)],
        documents=[text],
        metadatas=[{
            "ticket_id"         : ticket_id,
            "titre"             : titre,
            "description"       : description,
            "categorie"         : categorie or "",
            "confiance_ml"      : round(confiance, 4) if confiance is not None else 0.0,
            "solution"          : solution or "",
            "knowledge"         : knowledge or "",
            "filiale"           : filiale or "",
            "equipement"        : equipement or "",
            "commentaire_client": commentaire_client or "",
            "approved_by"       : approved_by or "",
            "resolved_at"       : maintenant,
            # Cycle de vie (axe 2)
            "kb_schema"         : KB_SCHEMA_VERSION,
            "statut"            : STATUT_ACTIF,
            "source_solution"   : source_solution,
            "quality_score"     : round(verdict.quality_score, 4),
            "indexed_at"        : maintenant,
            "near_duplicate_of" : verdict.near_duplicate_of or "",
            "superseded_by"     : "",
        }],
    )

    if verdict.near_duplicate_of and verdict.near_duplicate_of != str(ticket_id):
        _marquer_remplace(verdict.near_duplicate_of, str(ticket_id))
        print(f"[kb] ticket {ticket_id} indexe — remplace {verdict.near_duplicate_of}")
    else:
        print(f"[kb] ticket {ticket_id} indexe (qualite {verdict.quality_score:.2f})")

    return verdict.as_dict()


# ── Recherche (utilisée par le RAG) ──────────────────────────────────────────────

def query_similar(text: str, categorie: Optional[str] = None, top_k: int = 3) -> list[dict]:
    """
    Recherche par similarité parmi les tickets résolus archivés. Permet aux résolutions
    récentes — pas encore présentes dans le corpus d'entraînement statique (FAISS/TF-IDF) —
    d'être proposées dès la prochaine requête similaire.

    Les entrées remplacées ou marquées obsolètes sont écartées après la requête. On
    demande donc plus de résultats que nécessaire pour ne pas rendre une liste courte
    une fois le filtre appliqué.

    Retourne une liste au même format que Predictor.recommend() (score/resolution/
    knowledge/fallback) pour pouvoir être fusionnée avec les recommandations statiques.
    """
    collection = _get_collection()
    count = collection.count()
    if count == 0 or not text.strip():
        return []
    where = {"categorie": categorie} if categorie else None
    try:
        res = collection.query(
            query_texts=[text],
            n_results=min(max(top_k * 3, top_k), count),
            where=where,
        )
    except Exception:
        return []

    out: list[dict] = []
    ids = (res.get("ids") or [[]])[0]
    distances = (res.get("distances") or [[]])[0]
    metadatas = (res.get("metadatas") or [[]])[0]
    for _id, dist, meta in zip(ids, distances, metadatas):
        if not _est_actif(meta):
            continue
        similarity = max(0.0, 1.0 - dist)  # distance cosine -> similarite
        out.append({
            "score"     : round(similarity, 4),
            "resolution": meta.get("solution") or meta.get("knowledge") or "",
            "knowledge" : meta.get("knowledge", ""),
            "fallback"  : False,
            "source"    : "chroma_live",
            "ticket_id" : meta.get("ticket_id") or (int(_id) if str(_id).isdigit() else None),
            "categorie" : meta.get("categorie", ""),
            "titre"     : meta.get("titre", ""),
        })
        if len(out) >= top_k:
            break
    return out


# ── Lecture / statistiques (mêmes signatures que l'ancien nosql_store.py) ───────

def get_all_resolved(limit: int = 100) -> list[dict]:
    """Retourne tous les tickets résolus actifs (les plus récents en premier, limité)."""
    collection = _get_collection()
    if collection.count() == 0:
        return []
    docs = collection.get(include=["metadatas"]).get("metadatas", [])
    actifs = [d for d in docs if _est_actif(d)]
    return sorted(actifs, key=lambda d: d.get("resolved_at", ""), reverse=True)[:limit]


def get_all_entries(include_documents: bool = False) -> list[dict]:
    """
    Toutes les entrées, quel que soit leur statut — pour les snapshots et le monitoring.
    Contrairement à get_all_resolved(), n'écarte ni les entrées remplacées ni les obsolètes.
    """
    collection = _get_collection()
    if collection.count() == 0:
        return []
    champs = ["metadatas", "documents"] if include_documents else ["metadatas"]
    res = collection.get(include=champs)
    metas = res.get("metadatas") or []
    ids = res.get("ids") or []
    docs = res.get("documents") or [None] * len(metas)
    sorties = []
    for _id, meta, doc in zip(ids, metas, docs):
        entree = dict(meta or {})
        entree["_id"] = _id
        if include_documents:
            entree["_document"] = doc
        sorties.append(entree)
    return sorties


def marquer_obsolete(ticket_id: int, motif: str = "signale par le monitoring",
                     par: Optional[str] = None) -> bool:
    """
    Marque une connaissance comme obsolète. Elle cesse d'être proposée par le RAG,
    sans être supprimée. Opération réversible en repassant le statut à actif.
    """
    collection = _get_collection()
    try:
        existant = collection.get(ids=[str(ticket_id)], include=["metadatas"])
    except Exception:
        return False
    metas = existant.get("metadatas") or []
    if not metas:
        return False
    meta = dict(metas[0])
    meta["statut"] = STATUT_OBSOLETE
    meta["obsolete_motif"] = motif
    meta["obsolete_at"] = datetime.now(timezone.utc).isoformat()
    meta["obsolete_par"] = par or ""
    try:
        collection.update(ids=[str(ticket_id)], metadatas=[meta])
        return True
    except Exception:
        return False


def reactiver(ticket_id: int, par: Optional[str] = None) -> bool:
    """
    Remet en service une connaissance obsolète : le RAG la propose de nouveau.

    Seule une entrée obsolète peut l'être. Une entrée remplacée a un successeur
    quasi identique : la réactiver ferait proposer deux fois la même solution.
    """
    entree = get_entry(ticket_id)
    if entree is None or entree.get("statut") != STATUT_OBSOLETE:
        return False
    meta = dict(entree)
    meta["statut"] = STATUT_ACTIF
    meta["reactive_at"] = datetime.now(timezone.utc).isoformat()
    meta["reactive_par"] = par or ""
    try:
        _get_collection().update(ids=[str(ticket_id)], metadatas=[meta])
        return True
    except Exception:
        return False


def get_entry(ticket_id: int) -> Optional[dict]:
    """Une entrée de la base, quel que soit son statut ; None si elle n'y est pas."""
    try:
        res = _get_collection().get(ids=[str(ticket_id)], include=["metadatas"])
    except Exception:
        return None
    metas = res.get("metadatas") or []
    if not metas:
        return None
    entree = dict(metas[0])
    entree.setdefault("statut", STATUT_ACTIF)
    return entree


def get_cycle_de_vie() -> dict:
    """
    Toutes les connaissances avec leur statut : actives (proposées par le RAG),
    remplacées par un quasi-doublon plus récent, obsolètes (retirées par un
    administrateur). Rien n'est jamais supprimé : c'est la vue d'audit de la base.
    """
    entrees = []
    for brute in get_all_entries():
        entree = {k: v for k, v in brute.items() if not k.startswith("_")}
        entree.setdefault("statut", STATUT_ACTIF)
        if "ticket_id" not in entree:
            _id = str(brute.get("_id", ""))
            entree["ticket_id"] = int(_id) if _id.isdigit() else _id
        entrees.append(entree)
    entrees.sort(key=lambda e: e.get("resolved_at", ""), reverse=True)
    par_statut = {STATUT_ACTIF: 0, STATUT_REMPLACE: 0, STATUT_OBSOLETE: 0}
    for entree in entrees:
        par_statut[entree["statut"]] = par_statut.get(entree["statut"], 0) + 1
    return {"total": len(entrees), "par_statut": par_statut, "entrees": entrees}


def _journaliser_refus(ticket_id: int, titre: str, categorie: str, filiale: str,
                       source_solution: str, verdict: dict) -> None:
    """
    Ajoute un refus au journal. Un échec d'écriture ne doit jamais empêcher la
    clôture du ticket : il est signalé dans la sortie du serveur, puis ignoré.
    """
    ligne = {
        "ticket_id": ticket_id,
        "titre": titre or "",
        "categorie": categorie or "",
        "filiale": filiale or "",
        "source_solution": source_solution,
        "motif": verdict.get("motif", ""),
        "controles": verdict.get("controles", []),
        "refuse_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        os.makedirs(os.path.dirname(_JOURNAL_REFUS), exist_ok=True)
        with open(_JOURNAL_REFUS, "a", encoding="utf-8") as f:
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"[kb] journal des refus inaccessible : {exc}")


def get_refus(limit: int = 100) -> list[dict]:
    """
    Les refus du contrôle qualité, du plus récent au plus ancien.

    Un ticket peut être refusé puis accepté après correction de sa solution. Seul
    son dernier refus compte, et il n'est montré que s'il est postérieur à la
    dernière indexation du ticket : un refus déjà réparé ne l'est plus.
    """
    if not os.path.exists(_JOURNAL_REFUS):
        return []
    derniers: dict[str, dict] = {}
    with open(_JOURNAL_REFUS, encoding="utf-8") as f:
        for brut in f:
            brut = brut.strip()
            if not brut:
                continue
            try:
                ligne = json.loads(brut)
            except json.JSONDecodeError:
                continue
            derniers[str(ligne.get("ticket_id"))] = ligne
    if not derniers:
        return []
    indexes = {str(e.get("ticket_id", e.get("_id"))): str(e.get("indexed_at", ""))
               for e in get_all_entries()}
    refus = [l for tid, l in derniers.items() if str(l.get("refuse_at", "")) > indexes.get(tid, "")]
    refus.sort(key=lambda l: l.get("refuse_at", ""), reverse=True)
    return refus[:limit]


def get_stats() -> dict:
    """
    Retourne les KPIs agrégés de la base de tickets résolus.
    Utilisé par l'endpoint /tickets/resolved/stats.
    """
    collection = _get_collection()
    if collection.count() == 0:
        return {"total": 0, "par_categorie": {}, "par_filiale": {}}

    docs = collection.get(include=["metadatas"]).get("metadatas", [])
    actifs = [d for d in docs if _est_actif(d)]
    par_categorie: dict[str, int] = {}
    par_filiale: dict[str, int] = {}
    for doc in actifs:
        cat = doc.get("categorie") or "Inconnue"
        fil = doc.get("filiale") or "Inconnue"
        par_categorie[cat] = par_categorie.get(cat, 0) + 1
        par_filiale[fil] = par_filiale.get(fil, 0) + 1

    return {
        "total"        : len(actifs),
        "par_categorie": dict(sorted(par_categorie.items(), key=lambda x: -x[1])),
        "par_filiale"  : dict(sorted(par_filiale.items(), key=lambda x: -x[1])),
    }


def count_resolved() -> int:
    """Nombre total d'entrées archivées, tous statuts confondus."""
    return _get_collection().count()


def delete_resolved(ticket_id: int) -> None:
    """
    Retire un ticket de la base de connaissances vectorielle, s'il y était archivé.

    Appelé lors de la suppression définitive d'un ticket (DELETE /tickets/{id}) : sans
    ce nettoyage, un ticket résolu archivé puis supprimé laisserait une entrée fantôme
    dans ChromaDB — toujours proposée par le RAG et citée par la synthèse IA avec un ID
    qui ne correspond plus à aucun ticket réel (404 si l'admin l'explore). No-op si
    l'id n'était pas archivé (ticket jamais résolu).
    """
    _get_collection().delete(ids=[str(ticket_id)])
