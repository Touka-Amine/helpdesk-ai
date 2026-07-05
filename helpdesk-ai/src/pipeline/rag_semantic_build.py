"""
Reconstruction du RAG sémantique (FAISS + embeddings) — hors pipeline DVC.

Lit rag.csv (tickets résolus), ajuste SemanticRAGEngine (sentence-transformers
+ FAISS), et sauvegarde les artefacts dans models/semantic_rag/.

Note : nécessite le téléchargement du modèle sentence-transformers
(paraphrase-multilingual-mpnet-base-v2, ~420 Mo) au premier lancement.
Non inclus dans dvc.yaml (artefact géré manuellement, cf. rag_build.py).

Usage :
    python src/pipeline/rag_semantic_build.py
"""

import os
import sys
import yaml
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rag.semantic_engine import SemanticRAGEngine

RAG_PATH    = "data/splits/rag.csv"
PARAMS_PATH = "params.yaml"
MODEL_OUT   = "models/semantic_rag"


def run() -> None:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        params = yaml.safe_load(f)
    rag_p = params["rag"]

    print(f"[rag_semantic_build] Lecture : {RAG_PATH}")
    rag_df = pd.read_csv(RAG_PATH, encoding="utf-8")
    print(f"[rag_semantic_build] {len(rag_df)} tickets résolus")

    engine = SemanticRAGEngine(
        top_k               = rag_p["top_k"],
        similarity_threshold= rag_p["similarity_threshold"],
    )
    engine.fit(rag_df)

    os.makedirs(MODEL_OUT, exist_ok=True)
    engine.save(MODEL_OUT)
    print(f"[rag_semantic_build] SemanticRAGEngine sauvegardé : {MODEL_OUT}")
    print(f"[rag_semantic_build] Base de connaissance : {len(engine.knowledge_base)} tickets")


if __name__ == "__main__":
    run()
