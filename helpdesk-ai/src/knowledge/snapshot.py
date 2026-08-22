"""
AXE 2 — Versionnement de la base de connaissances.

ChromaDB n'a pas de notion de version : la collection reflete son dernier etat et
rien ne permet de dire ce qu'elle contenait le mois dernier. Ce script en exporte
un instantane horodate, versionnable par DVC, qui rend possible :

  - de savoir quelles connaissances etaient disponibles a une date donnee, et donc
    d'interpreter une evaluation RAG passee ;
  - de comparer deux etats et de voir ce qui a ete ajoute, remplace ou marque
    obsolete ;
  - de reconstruire la collection si le volume Docker est perdu.

Le format est du JSON Lines : une connaissance par ligne, lisible, diffable, et
lisible en flux sans charger tout le fichier.

Usage :
    python src/knowledge/snapshot.py
    python src/knowledge/snapshot.py --diff data/knowledge/kb_20260801.jsonl
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

import yaml

_RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _RACINE)
sys.path.insert(0, os.path.join(_RACINE, "src"))

PARAMS_PATH = "params.yaml"


def charger_entrees() -> list[dict]:
    from api.db.vector_store import get_all_entries
    return get_all_entries(include_documents=True)


def ecrire_snapshot(entrees: list[dict], dossier: str) -> tuple[str, dict]:
    os.makedirs(dossier, exist_ok=True)
    horodatage = datetime.now(timezone.utc)
    chemin = os.path.join(dossier, f"kb_{horodatage.strftime('%Y%m%d_%H%M%S')}.jsonl")

    empreinte = hashlib.sha256()
    with open(chemin, "w", encoding="utf-8") as f:
        for entree in sorted(entrees, key=lambda e: str(e.get("_id", ""))):
            ligne = json.dumps(entree, ensure_ascii=False, sort_keys=True)
            f.write(ligne + "\n")
            empreinte.update(ligne.encode("utf-8"))

    statuts: dict[str, int] = {}
    for e in entrees:
        s = str(e.get("statut", "actif") or "actif")
        statuts[s] = statuts.get(s, 0) + 1

    manifeste = {
        "created_at": horodatage.isoformat(),
        "kb_version": empreinte.hexdigest()[:12],
        "sha256": empreinte.hexdigest(),
        "n_entrees": len(entrees),
        "par_statut": statuts,
        "fichier": chemin.replace("\\", "/"),
    }
    with open(chemin.replace(".jsonl", ".manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifeste, f, ensure_ascii=False, indent=2)
    return chemin, manifeste


def comparer(chemin_avant: str, entrees_apres: list[dict]) -> dict:
    """Difference entre un instantane anterieur et l'etat courant."""
    avant: dict[str, dict] = {}
    with open(chemin_avant, encoding="utf-8") as f:
        for ligne in f:
            if ligne.strip():
                entree = json.loads(ligne)
                avant[str(entree.get("_id"))] = entree
    apres = {str(e.get("_id")): e for e in entrees_apres}

    ajoutees = sorted(set(apres) - set(avant))
    retirees = sorted(set(avant) - set(apres))
    statut_change = [
        {"id": i,
         "avant": avant[i].get("statut", "actif"),
         "apres": apres[i].get("statut", "actif")}
        for i in sorted(set(avant) & set(apres))
        if avant[i].get("statut", "actif") != apres[i].get("statut", "actif")
    ]
    contenu_change = [
        i for i in sorted(set(avant) & set(apres))
        if avant[i].get("solution") != apres[i].get("solution")
    ]
    return {
        "reference": chemin_avant,
        "ajoutees": ajoutees,
        "retirees": retirees,
        "statut_modifie": statut_change,
        "solution_modifiee": contenu_change,
        "resume": (f"{len(ajoutees)} ajoutee(s), {len(retirees)} retiree(s), "
                   f"{len(statut_change)} changement(s) de statut, "
                   f"{len(contenu_change)} solution(s) modifiee(s)"),
    }


def run(args: argparse.Namespace) -> int:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        params = yaml.safe_load(f)
    dossier = params.get("knowledge", {}).get("snapshot_dir", "data/knowledge")

    try:
        entrees = charger_entrees()
    except Exception as exc:
        print(f"[snapshot] Base de connaissances inaccessible : {type(exc).__name__}: {exc}")
        if not args.allow_offline:
            return 1
        entrees = []

    if args.diff:
        reference = args.diff
        if reference == "last":
            candidats = sorted(glob.glob(os.path.join(dossier, "kb_*.jsonl")))
            if not candidats:
                print("[snapshot] Aucun instantane anterieur.")
                return 1
            reference = candidats[-1]
        print(json.dumps(comparer(reference, entrees), ensure_ascii=False, indent=2))
        return 0

    chemin, manifeste = ecrire_snapshot(entrees, dossier)
    print(f"[snapshot] {manifeste['n_entrees']} entrees | version {manifeste['kb_version']}")
    print(f"[snapshot] par statut : {manifeste['par_statut']}")
    print(f"[snapshot] ecrit {chemin}")
    if manifeste["n_entrees"] == 0:
        print("[snapshot] Base vide — attendu tant qu'aucun ticket n'a ete resolu.")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--diff", metavar="FICHIER",
                   help="compare l'etat courant a un instantane ('last' pour le plus recent)")
    p.add_argument("--allow-offline", action="store_true",
                   help="ecrit un instantane vide si ChromaDB est injoignable")
    sys.exit(run(p.parse_args()))
