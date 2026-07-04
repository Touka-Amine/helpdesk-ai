"""
Stage DVC 2/4 — Split anti-fuite.

Stratégie : GroupShuffleSplit par Titre (colonne de groupe).
Garantit qu'aucun Titre de test n'a été vu à l'entraînement.

Sorties :
  - data/splits/train.csv  — tickets d'entraînement (ML)
  - data/splits/test.csv   — tickets de test (ML)
  - data/splits/rag.csv    — tickets résolus pour la base RAG

Usage :
    python src/pipeline/split.py
"""

import os
import yaml
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

PROC_PATH   = "data/processed/HelpDesk1.csv"
PARAMS_PATH = "params.yaml"
OUT_TRAIN   = "data/splits/train.csv"
OUT_TEST    = "data/splits/test.csv"
OUT_RAG     = "data/splits/rag.csv"


def run() -> None:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        params = yaml.safe_load(f)
    test_size    = params["data"]["test_size"]
    random_state = params["data"]["random_state"]

    print(f"[split] Lecture : {PROC_PATH}")
    df = pd.read_csv(PROC_PATH, encoding="utf-8")
    print(f"[split] {len(df)} lignes | test_size={test_size} | random_state={random_state}")

    groups = df["Titre"]
    gss    = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(gss.split(df, groups=groups))

    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df  = df.iloc[test_idx].reset_index(drop=True)

    # Base RAG : tickets résolus dans le train uniquement
    # (anti-leakage : les résolutions de test ne doivent pas être dans la base RAG)
    rag_mask = (
        train_df["Résolution/Motif"].notna()
        & (train_df["Résolution/Motif"].str.strip() != "")
        & (train_df["Résolution/Motif"].str.lower() != "nan")
    )
    rag_df = train_df[rag_mask].reset_index(drop=True)

    os.makedirs(os.path.dirname(OUT_TRAIN), exist_ok=True)
    train_df.to_csv(OUT_TRAIN, index=False, encoding="utf-8")
    test_df.to_csv(OUT_TEST,  index=False, encoding="utf-8")
    rag_df.to_csv(OUT_RAG,   index=False, encoding="utf-8")

    print(f"[split] train={len(train_df)} | test={len(test_df)} | rag={len(rag_df)}")
    print(f"[split] Titres uniques — train: {train_df['Titre'].nunique()} | test: {test_df['Titre'].nunique()}")
    overlap = set(train_df["Titre"]) & set(test_df["Titre"])
    assert not overlap, f"Fuite détectée — {len(overlap)} Titres communs train/test !"
    print("[split] Anti-fuite OK — aucun Titre commun train/test.")


if __name__ == "__main__":
    run()
