"""
Stage DVC 1/4 — Prétraitement.

Lit le CSV brut (UTF-8 BOM — utf-8-sig), applique le nettoyage textuel,
ajoute les colonnes dérivées, et sauvegarde un CSV propre (UTF-8 sans BOM).

Usage :
    python src/pipeline/preprocess.py
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.preprocess import (
    build_text_for_model,
    build_text_for_rag,
    build_text_enriched,
    simplify_priorite,
    simplify_classification,
)

RAW_PATH  = "data/raw/HelpDesk1.csv"
OUT_PATH  = "data/processed/HelpDesk1.csv"


def run() -> None:
    print(f"[preprocess] Lecture : {RAW_PATH}")
    # utf-8-sig retire automatiquement le BOM en début de fichier
    df = pd.read_csv(RAW_PATH, encoding="utf-8-sig")

    print(f"[preprocess] {len(df)} lignes | {df.shape[1]} colonnes")

    # ── Colonnes de texte enrichies ────────────────────────────────────────────
    df["text_clean"] = df.apply(
        lambda r: build_text_for_model(
            str(r.get("Titre", "") or ""),
            str(r.get("Description", "") or ""),
        ),
        axis=1,
    )

    df["text_rag"] = df.apply(
        lambda r: build_text_for_rag(
            str(r.get("Description", "") or ""),
            resolution=str(r.get("Résolution/Motif", "") or ""),
            knowledge=str(r.get("knowledge Base", "") or ""),
            titre=str(r.get("Titre", "") or ""),
        ),
        axis=1,
    )

    df["text_enriched"] = df.apply(
        lambda r: build_text_enriched(
            str(r.get("Titre", "") or ""),
            str(r.get("Description", "") or ""),
            classification=str(r.get("Classification", "") or ""),
            priorite=str(r.get("Priorité", "") or ""),
        ),
        axis=1,
    )

    df["priorite_simple"]       = df["Priorité"].apply(simplify_priorite)
    df["classification_simple"] = df["Classification"].apply(simplify_classification)

    # ── Sauvegarde ─────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    df.to_csv(OUT_PATH, index=False, encoding="utf-8")
    print(f"[preprocess] Sauvegardé : {OUT_PATH} ({len(df)} lignes, {df.shape[1]} colonnes)")


if __name__ == "__main__":
    run()
