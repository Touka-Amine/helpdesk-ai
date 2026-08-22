"""
Stage DVC — AXE 1, etape 2 : construction de la version courante du dataset ML.

Fusionne le corpus historique d'entrainement (data/splits/train.csv) avec les lots
valides collectes en production (data/curated/validated_*.csv) pour produire
data/splits/train_current.csv, qui est ce que train.py entraine reellement.

TROIS GARDE-FOUS ANTI-FUITE
    1. Aucune ligne de production ne peut porter un Titre present dans le jeu de
       test gele. Les tickets de production ont des titres libres, saisis par le
       client : rien ne garantit qu'ils ne recopient pas un scenario de test.
    2. Aucune ligne de production ne peut avoir une description identique (apres
       normalisation) a une description du jeu de test.
    3. Le jeu de test n'est jamais lu autrement qu'en comparaison. Ce script ne
       l'ecrit pas et ne le modifie pas.

    Une proximite semantique plus fine (paraphrase d'un ticket de test) n'est pas
    detectee ici. C'est une limite assumee : la detecter demanderait d'encoder le
    jeu de test a chaque construction, et l'exposer au processus de selection est
    precisement ce qu'un jeu de test gele cherche a eviter.

VERSION DU DATASET
    L'empreinte SHA-256 du fichier produit sert d'identifiant. Elle est reportee
    dans le lineage du modele (src/registry/), ce qui repond a la question
    "quelle version du dataset correspond a quel modele".

Usage :
    python src/pipeline/build_dataset.py
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import unicodedata
from datetime import datetime, timezone

import pandas as pd
import yaml

PARAMS_PATH = "params.yaml"
BASE_TRAIN = "data/splits/train.csv"
TEST_PATH = "data/splits/test.csv"
OUT_TRAIN = "data/splits/train_current.csv"
OUT_MANIFEST = "data/splits/train_current.manifest.json"

# Colonnes de provenance : utiles au suivi, retirees avant l'entrainement.
COLONNES_PROVENANCE = [
    "source", "ticket_id", "label_strength", "sample_weight",
    "approved_by", "model_version", "categorie_predite",
]


def normaliser(texte: str) -> str:
    t = unicodedata.normalize("NFKD", str(texte).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip()


def sha256_fichier(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloc in iter(lambda: f.read(65536), b""):
            h.update(bloc)
    return h.hexdigest()


def charger_lots(dossier: str) -> tuple[pd.DataFrame, list[str]]:
    fichiers = sorted(glob.glob(os.path.join(dossier, "validated_*.csv")))
    lots, retenus = [], []
    for f in fichiers:
        try:
            lot = pd.read_csv(f, encoding="utf-8")
        except pd.errors.EmptyDataError:
            continue
        if lot.empty:
            continue
        lots.append(lot)
        retenus.append(f.replace("\\", "/"))
    if not lots:
        return pd.DataFrame(), retenus
    return pd.concat(lots, ignore_index=True), retenus


def run() -> None:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        params = yaml.safe_load(f)
    dossier_curated = params.get("collect", {}).get("curated_dir", "data/curated")

    base = pd.read_csv(BASE_TRAIN, encoding="utf-8")
    base["source"] = "corpus_historique"
    base["sample_weight"] = 1.0
    base["label_strength"] = "historique"
    print(f"[build_dataset] corpus historique : {len(base)} lignes | "
          f"{base['Titre'].nunique()} Titres")

    curated, fichiers = charger_lots(dossier_curated)
    print(f"[build_dataset] lots de production : {len(fichiers)} fichier(s), "
          f"{len(curated)} lignes")

    rejets = {"titre_dans_test": 0, "description_dans_test": 0, "doublon_ticket": 0}

    if not curated.empty and os.path.exists(TEST_PATH):
        test = pd.read_csv(TEST_PATH, encoding="utf-8")
        titres_test = set(test["Titre"].astype(str))
        desc_test = {normaliser(d) for d in test["Description"].astype(str)}

        avant = len(curated)
        curated = curated[~curated["Titre"].astype(str).isin(titres_test)]
        rejets["titre_dans_test"] = avant - len(curated)

        avant = len(curated)
        curated = curated[
            ~curated["Description"].astype(str).map(normaliser).isin(desc_test)
        ]
        rejets["description_dans_test"] = avant - len(curated)

        if "ticket_id" in curated.columns:
            avant = len(curated)
            curated = curated.drop_duplicates(subset=["ticket_id"], keep="last")
            rejets["doublon_ticket"] = avant - len(curated)

    for motif, n in rejets.items():
        if n:
            print(f"[build_dataset]   ecarte — {motif} : {n} ligne(s)")

    if curated.empty:
        dataset = base.copy()
    else:
        # Aligner les colonnes : la base fait foi, les colonnes de provenance sont
        # conservees en plus pour les deux origines.
        colonnes = list(dict.fromkeys(list(base.columns) + COLONNES_PROVENANCE))
        dataset = pd.concat(
            [base.reindex(columns=colonnes), curated.reindex(columns=colonnes)],
            ignore_index=True,
        )

    dataset["sample_weight"] = pd.to_numeric(
        dataset.get("sample_weight", 1.0), errors="coerce"
    ).fillna(1.0)
    dataset["source"] = dataset["source"].fillna("corpus_historique")

    os.makedirs(os.path.dirname(OUT_TRAIN), exist_ok=True)
    dataset.to_csv(OUT_TRAIN, index=False, encoding="utf-8")

    empreinte = sha256_fichier(OUT_TRAIN)
    par_source = dataset["source"].value_counts().to_dict()
    par_categorie = dataset["Catégorie"].value_counts().to_dict()

    manifeste = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_version": empreinte[:12],
        "sha256": empreinte,
        "n_rows": int(len(dataset)),
        "n_titres": int(dataset["Titre"].nunique()),
        "base_train": {"fichier": BASE_TRAIN, "n_rows": int(len(base))},
        "lots_production": fichiers,
        "n_production_retenues": int(par_source.get("production", 0)),
        "rejets_anti_fuite": rejets,
        "par_source": {str(k): int(v) for k, v in par_source.items()},
        "par_categorie": {str(k): int(v) for k, v in par_categorie.items()},
        "test_reference": TEST_PATH,
    }
    with open(OUT_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifeste, f, ensure_ascii=False, indent=2)

    print(f"[build_dataset] ecrit {OUT_TRAIN}")
    print(f"[build_dataset] version {manifeste['dataset_version']} | "
          f"{manifeste['n_rows']} lignes "
          f"({manifeste['n_production_retenues']} de production)")

    if os.path.exists(TEST_PATH):
        test = pd.read_csv(TEST_PATH, encoding="utf-8")
        fuite = set(dataset["Titre"].astype(str)) & set(test["Titre"].astype(str))
        assert not fuite, f"Fuite — {len(fuite)} Titres communs train/test : {sorted(fuite)[:5]}"
        print("[build_dataset] Anti-fuite OK — aucun Titre commun avec le jeu de test.")


if __name__ == "__main__":
    run()
