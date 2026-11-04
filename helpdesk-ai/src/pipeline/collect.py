"""
Stage DVC — AXE 1, etape 1 : collecte des tickets valides en production.

PostgreSQL est la verite metier. Ce script en extrait les tickets reellement
traites par un administrateur et les ecrit dans data/curated/, versionne par DVC.
Il ne modifie jamais la base : lecture seule.

LES QUATRE ETATS D'UNE DONNEE
    collectee  toutes les lignes de la table tickets
    eligible   statut terminal + validee par un humain + description exploitable
    validee    eligible ET dont l'etiquette a une force suffisante
    entrainee  ce que build_dataset.py verse effectivement dans le train

FORCE DE L'ETIQUETTE
    Le point delicat de toute boucle de reapprentissage : un ticket "valide" ne
    porte pas forcement une etiquette fiable.

    corrected  un admin a explicitement change categorie_finale.
               Journalise avec changed_by renseigne (api/routers/tickets.py:306).
               Etiquette de meilleure qualite disponible : un expert a tranche.

    confirmed  un admin a traite le ticket jusqu'a la resolution sans toucher a
               la categorie. Il l'a vue et ne l'a pas contestee. Signal reel mais
               plus faible : c'est en partie le modele qui se confirme lui-meme.

    weak       ticket resolu sans admin identifiable. Aucune garantie qu'un
               humain ait regarde l'etiquette. Exclu par defaut
               (params.yaml → collect.include_weak_labels).

    Sans cette distinction, reentrainer sur "les tickets valides" revient
    largement a reentrainer le modele sur ses propres sorties, ce qui amplifie
    ses erreurs au lieu de les corriger.

Usage :
    python src/pipeline/collect.py
    python src/pipeline/collect.py --db-url sqlite:///data/tickets.db
    python src/pipeline/collect.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import pandas as pd
import yaml

_RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _RACINE)
sys.path.insert(0, os.path.join(_RACINE, "src"))

from data.pseudonymisation import CleManquante, pseudonyme


def pseudonyme_sur(valeur) -> str:
    """Le pseudonyme d'un consultant, ou une chaine vide si la cle manque.

    La collecte doit pouvoir tourner sans la cle — sur une machine
    d'integration continue, par exemple. Dans ce cas le nom n'est pas remplace
    par un pseudonyme : il est retire. Jamais laisse en clair.
    """
    if not valeur:
        return ""
    try:
        return pseudonyme(str(valeur), "AGT")
    except CleManquante:
        return ""


PARAMS_PATH = "params.yaml"

# Colonnes du corpus historique, pour que la fusion avec data/splits/train.csv
# n'introduise aucune colonne inconnue (cf. build_dataset.py).
COLONNES_CORPUS = [
    "ID", "STATUT", "Titre", "Description", "Demandeur", "Classification",
    "Catégorie", "Date de création", "Date de résolution", "CID", "Filiale",
    "Priorité", "Assigné à", "Résolution/Motif", "Analyse", "knowledge Base",
    "Type d'élément", "Chemin d'accès", "text_clean", "text_rag", "text_enriched",
    "priorite_simple", "classification_simple",
]


def charger_params() -> dict:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def resoudre_db_url(explicite: str | None) -> str:
    if explicite:
        return explicite
    if os.environ.get("DB_URL"):
        return os.environ["DB_URL"]
    try:
        from api.config import settings
        return settings.DB_URL
    except Exception:
        return "sqlite:///data/tickets.db"


# ── lecture de la base ───────────────────────────────────────────────────────

def lire_production(db_url: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retourne (tickets, historique). Leve une exception si la base est injoignable."""
    from sqlalchemy import create_engine

    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    engine = create_engine(db_url, connect_args=connect_args)

    with engine.connect() as conn:
        tickets = pd.read_sql("SELECT * FROM tickets", conn)
        try:
            histo = pd.read_sql("SELECT * FROM ticket_history", conn)
        except Exception:
            histo = pd.DataFrame(columns=["ticket_id", "changed_by", "champ_modifie"])
    return tickets, histo


# ── qualification ────────────────────────────────────────────────────────────

def force_etiquette(ticket_id: int, histo: pd.DataFrame) -> str:
    """
    corrected / confirmed / weak, deduit de ticket_history.

    A la creation, categorie_finale est journalisee avec changed_by = NULL
    (api/routers/tickets.py:79). Seule une intervention d'admin renseigne ce champ.
    """
    if histo.empty:
        return "weak"
    lignes = histo[histo["ticket_id"] == ticket_id]
    if lignes.empty:
        return "weak"

    par_admin = lignes[lignes["changed_by"].notna()]
    if par_admin.empty:
        return "weak"

    cat_par_admin = par_admin[par_admin["champ_modifie"] == "categorie_finale"]
    if not cat_par_admin.empty:
        return "corrected"
    return "confirmed"


def qualifier(tickets: pd.DataFrame, histo: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Ajoute les colonnes eligible / motif_rejet / label_strength."""
    cfg = params.get("collect", {})
    statuts_ok = set(cfg.get("eligible_statuts", ["Résolu"]))
    exiger_approbateur = cfg.get("require_approved_by", True)
    min_mots = int(cfg.get("min_description_words", 5))

    df = tickets.copy()
    if df.empty:
        for c in ("eligible", "motif_rejet", "label_strength"):
            df[c] = pd.Series(dtype="object")
        return df

    motifs: list[str | None] = []
    for _, t in df.iterrows():
        statut = str(t.get("statut") or "")
        if statut not in statuts_ok:
            motifs.append(f"statut non terminal ({statut or 'vide'})")
            continue
        categorie = str(t.get("categorie_finale") or "").strip()
        if not categorie:
            motifs.append("categorie_finale vide")
            continue
        if exiger_approbateur and not str(t.get("approved_by") or "").strip():
            motifs.append("aucun approbateur")
            continue
        description = str(t.get("description") or "")
        if len(description.split()) < min_mots:
            motifs.append(f"description trop courte (<{min_mots} mots)")
            continue
        motifs.append(None)

    df["motif_rejet"] = motifs
    df["eligible"] = df["motif_rejet"].isna()
    df["label_strength"] = [
        force_etiquette(int(tid), histo) if elig else None
        for tid, elig in zip(df["id"], df["eligible"])
    ]
    return df


# ── mise au format corpus ────────────────────────────────────────────────────

def vers_format_corpus(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Traduit les lignes PostgreSQL vers le schema du corpus d'entrainement.

    text_clean est RECALCULE avec la meme fonction que le corpus historique
    (src/data/preprocess.py). Reprendre le champ tel quel introduirait un ecart
    de pretraitement entre les donnees historiques et les donnees de production,
    que le modele lirait comme un signal.
    """
    from data.preprocess import clean_text, build_text_for_rag, build_text_enriched

    poids = params.get("collect", {}).get("label_weights", {})
    lignes = []
    for _, t in df.iterrows():
        titre = str(t.get("titre") or "")
        description = str(t.get("description") or "")
        solution = str(t.get("commentaire_admin") or "")
        ligne = {c: "" for c in COLONNES_CORPUS}
        ligne.update({
            "ID": f"PROD-{int(t['id'])}",
            "STATUT": str(t.get("statut") or ""),
            "Titre": titre,
            "Description": description,
            "Demandeur": "",                       # donnee nominative, jamais exportee
            "Classification": str(t.get("classification_finale") or ""),
            "Catégorie": str(t.get("categorie_finale") or "").strip(),
            "Date de création": str(t.get("created_at") or ""),
            "Date de résolution": str(t.get("resolved_at") or ""),
            "Filiale": str(t.get("filiale") or ""),
            "Priorité": str(t.get("priorite_finale") or t.get("priorite_saisie") or ""),
            # Le consultant qui a traite le ticket est une personne nommee : son
            # nom part en pseudonyme, comme dans le corpus historique (ENF-04 b).
            "Assigné à": pseudonyme_sur(t.get("assigne_a")),
            "Résolution/Motif": solution,
            "knowledge Base": str(t.get("knowledge_rag") or ""),
            "Type d'élément": str(t.get("equipement") or ""),
            "text_clean": clean_text(description),
            "text_rag": build_text_for_rag(description, titre=titre),
            "text_enriched": build_text_enriched(titre, description),
        })
        # Provenance : ces colonnes ne sont pas dans le corpus historique, elles
        # servent au suivi et sont retirees avant l'entrainement.
        ligne["source"] = "production"
        ligne["ticket_id"] = int(t["id"])
        ligne["label_strength"] = t.get("label_strength")
        ligne["sample_weight"] = float(poids.get(t.get("label_strength"), 0.0))
        ligne["approved_by"] = str(t.get("approved_by") or "")
        ligne["model_version"] = str(t.get("model_version") or "")
        ligne["categorie_predite"] = str(t.get("categorie_predite") or "")
        lignes.append(ligne)

    return pd.DataFrame(lignes)


# ── pipeline ─────────────────────────────────────────────────────────────────

def run(args: argparse.Namespace) -> int:
    params = charger_params()
    cfg = params.get("collect", {})
    dossier = cfg.get("curated_dir", "data/curated")
    inclure_faibles = bool(cfg.get("include_weak_labels", False))
    db_url = resoudre_db_url(args.db_url)

    affichable = db_url.split("@")[-1] if "@" in db_url else db_url
    print(f"[collect] Base : {affichable}")

    try:
        tickets, histo = lire_production(db_url)
    except Exception as exc:
        print(f"[collect] Base injoignable : {type(exc).__name__}: {exc}")
        if not args.allow_offline:
            print("[collect] Utilisez --allow-offline pour ecrire un lot vide et "
                  "laisser le pipeline continuer.")
            return 1
        tickets = pd.DataFrame()
        histo = pd.DataFrame(columns=["ticket_id", "changed_by", "champ_modifie"])

    print(f"[collect] collectees : {len(tickets)} lignes | historique : {len(histo)} evenements")

    qualifie = qualifier(tickets, histo, params)
    eligibles = qualifie[qualifie["eligible"]] if not qualifie.empty else qualifie

    repartition = (
        eligibles["label_strength"].value_counts().to_dict() if not eligibles.empty else {}
    )
    print(f"[collect] eligibles  : {len(eligibles)}")
    for force in ("corrected", "confirmed", "weak"):
        print(f"[collect]   {force:10s} : {repartition.get(force, 0)}")

    if not eligibles.empty and not inclure_faibles:
        validees = eligibles[eligibles["label_strength"] != "weak"]
    else:
        validees = eligibles
    print(f"[collect] validees   : {len(validees)} "
          f"(etiquettes faibles {'incluses' if inclure_faibles else 'exclues'})")

    if not qualifie.empty:
        rejets = qualifie[~qualifie["eligible"]]["motif_rejet"].value_counts().to_dict()
        for motif, n in rejets.items():
            print(f"[collect]   rejet — {motif} : {n}")

    corpus = vers_format_corpus(validees, params) if not validees.empty else pd.DataFrame(
        columns=COLONNES_CORPUS + ["source", "ticket_id", "label_strength",
                                   "sample_weight", "approved_by", "model_version",
                                   "categorie_predite"]
    )

    if args.dry_run:
        print("[collect] DRY-RUN — aucune ecriture")
        if not corpus.empty:
            print(corpus[["ID", "Titre", "Catégorie", "label_strength", "sample_weight"]].to_string())
        return 0

    os.makedirs(dossier, exist_ok=True)
    horodatage = datetime.now(timezone.utc).strftime("%Y%m%d")
    chemin = os.path.join(dossier, f"validated_{horodatage}.csv")
    corpus.to_csv(chemin, index=False, encoding="utf-8")

    manifeste = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "db": affichable,
        "collectees": int(len(tickets)),
        "eligibles": int(len(eligibles)),
        "validees": int(len(corpus)),
        "repartition_force_etiquette": {k: int(v) for k, v in repartition.items()},
        "motifs_rejet": {
            str(k): int(v)
            for k, v in (
                qualifie[~qualifie["eligible"]]["motif_rejet"].value_counts().to_dict().items()
                if not qualifie.empty else []
            )
        },
        "include_weak_labels": inclure_faibles,
        "categories": (
            {str(k): int(v) for k, v in corpus["Catégorie"].value_counts().to_dict().items()}
            if not corpus.empty else {}
        ),
        "fichier": chemin.replace("\\", "/"),
    }
    chemin_manifeste = os.path.join(dossier, f"validated_{horodatage}.manifest.json")
    with open(chemin_manifeste, "w", encoding="utf-8") as f:
        json.dump(manifeste, f, ensure_ascii=False, indent=2)

    print(f"[collect] ecrit {chemin} ({len(corpus)} lignes)")
    print(f"[collect] manifeste {chemin_manifeste}")
    if corpus.empty:
        print("[collect] Aucun ticket valide en production a ce jour — comportement "
              "attendu tant que l'application n'a pas de trafic reel.")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db-url", help="surcharge de l'URL de base")
    p.add_argument("--dry-run", action="store_true", help="affiche sans ecrire")
    p.add_argument("--allow-offline", action="store_true",
                   help="ecrit un lot vide si la base est injoignable")
    sys.exit(run(p.parse_args()))
