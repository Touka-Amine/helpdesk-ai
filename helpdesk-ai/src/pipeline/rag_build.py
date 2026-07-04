"""
Stage DVC 4/4 — Construction de la base RAG lexicale.

Lit rag.csv (tickets résolus), ajuste RAGEngine (TF-IDF + cosinus),
et sauvegarde le moteur sérialisé.

Note : le RAG sémantique (FAISS + embeddings) requiert le téléchargement
du modèle sentence-transformers et un GPU — il est construit séparément
via le notebook 06_rag_semantique.ipynb et n'est pas inclus dans le
pipeline DVC (artefact géré manuellement).

Usage :
    python src/pipeline/rag_build.py
"""

import os
import sys
import yaml
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rag.engine import RAGEngine

RAG_PATH    = "data/splits/rag.csv"
PARAMS_PATH = "params.yaml"
MODEL_OUT   = "models/rag_engine.pkl"


def run() -> None:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        params = yaml.safe_load(f)
    rag_p = params["rag"]

    print(f"[rag_build] Lecture : {RAG_PATH}")
    rag_df = pd.read_csv(RAG_PATH, encoding="utf-8")
    print(f"[rag_build] {len(rag_df)} tickets résolus")

    engine = RAGEngine(
        top_k               = rag_p["top_k"],
        similarity_threshold= rag_p["similarity_threshold"],
    )
    engine.fit(rag_df)

    os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
    engine.save(MODEL_OUT)
    print(f"[rag_build] RAGEngine lexical sauvegardé : {MODEL_OUT}")
    print(f"[rag_build] Base de connaissance : {len(engine.knowledge_base)} tickets")


if __name__ == "__main__":
    run()
