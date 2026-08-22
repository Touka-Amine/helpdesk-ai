"""
Stage DVC — AXE 2 : evaluation de la qualite de recuperation du RAG.

DEUX PROTOCOLES, ET POURQUOI LA DISTINCTION COMPTE
    annote  Chaque requete d'evaluation est accompagnee de la liste des tickets
            reellement pertinents, designes par un administrateur. C'est le seul
            protocole qui autorise a parler de rappel.

    proxy   A defaut d'annotation, on considere pertinent tout ticket de la meme
            categorie. C'est le protocole utilise par l'evaluation historique du
            projet, et il a un defaut structurel : une categorie comme Microsoft
            compte plusieurs centaines de tickets, donc plusieurs centaines de
            "pertinents". Un rappel@3 y vaut mecaniquement 3/300, soit 0.01, quelle
            que soit la qualite du moteur. Le rappel@3 de 0.0277 figurant dans
            metrics/rag_eval.json est un artefact de ce protocole, pas une mesure
            du systeme.

            En mode proxy, ce script laisse donc le rappel a null et ne rapporte
            que les indicateurs qui gardent un sens : precision@k, MRR, taux de
            reponse. Afficher un rappel connu comme non interpretable serait
            fabriquer un chiffre.

CONSTRUIRE LE JEU ANNOTE
    python src/pipeline/rag_eval.py --build-template

    Produit data/knowledge/rag_eval_set.json avec un echantillon stratifie de
    requetes issues du jeu de test, chacune accompagnee des dix meilleurs candidats
    proposes par le moteur. Un administrateur ouvre le fichier et, pour chaque
    requete, ne garde dans "pertinents" que les identifiants des solutions qui
    auraient reellement aide. Compter environ une demi-journee pour 60 a 80
    requetes. Sans ce fichier, toute metrique de pertinence reste indicative.

Usage :
    python src/pipeline/rag_eval.py
    python src/pipeline/rag_eval.py --build-template --n-queries 80
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone

import pandas as pd
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

PARAMS_PATH = "params.yaml"
TEST_PATH = "data/splits/test.csv"
RAG_ENGINE_PATH = "models/rag_engine.pkl"
SEM_RAG_DIR = "models/semantic_rag"
OUT = "metrics/rag_eval.json"


# ── chargement des moteurs ───────────────────────────────────────────────────

def charger_moteurs(params: dict) -> dict:
    """Retourne les moteurs disponibles. Un moteur absent est signale, pas simule."""
    moteurs: dict = {}
    try:
        import joblib
        import __main__
        from rag.engine import RAGEngine
        __main__.RAGEngine = RAGEngine     # compat pickle des notebooks
        moteurs["lexical"] = joblib.load(RAG_ENGINE_PATH)
        print("[rag_eval] moteur lexical (TF-IDF) charge")
    except Exception as exc:
        print(f"[rag_eval] moteur lexical indisponible : {type(exc).__name__}: {exc}")

    try:
        from rag.semantic_engine import SemanticRAGEngine
        moteurs["semantique"] = SemanticRAGEngine.load(SEM_RAG_DIR)
        print("[rag_eval] moteur semantique (FAISS) charge")
    except Exception as exc:
        print(f"[rag_eval] moteur semantique indisponible : {type(exc).__name__}: {exc}")

    if "lexical" in moteurs and "semantique" in moteurs:
        try:
            from rag.hybrid_engine import HybridRAGEngine
            hybride = HybridRAGEngine(
                alpha=params["rag"]["hybrid_alpha"],
                top_k=params["rag"]["top_k"],
                similarity_threshold=params["rag"]["similarity_threshold"],
            )
            hybride._sem = moteurs["semantique"]
            hybride._lex = moteurs["lexical"]
            hybride._fitted = True
            moteurs["hybride"] = hybride
            print("[rag_eval] moteur hybride construit — c'est celui servi en production")
        except Exception as exc:
            print(f"[rag_eval] moteur hybride indisponible : {type(exc).__name__}: {exc}")
    return moteurs


def interroger(moteur, titre: str, description: str, top_k: int) -> list[dict]:
    """
    Interroge le moteur exactement comme le fait la production.

    allow_fallback reste a True parce que c'est la valeur utilisee par
    api/predictor.py. Le desactiver mesurerait une configuration que personne
    n'execute : le seuil de similarite de 0.50 est rarement atteint par le moteur
    lexical, dont les scores cosinus tournent autour de 0.18, et l'evaluation
    renverrait zero resultat partout. Le taux de repli est rapporte a part.
    """
    from data.preprocess import build_text_for_rag
    texte = build_text_for_rag(description, titre=titre)
    try:
        resultats = moteur.recommend(query_text=texte, category_filter=None, allow_fallback=True)
    except TypeError:
        resultats = moteur.recommend(texte, None, True)
    return list(resultats or [])[:top_k]


# ── metriques ────────────────────────────────────────────────────────────────

def dcg(pertinences: list[int]) -> float:
    return sum(p / math.log2(i + 2) for i, p in enumerate(pertinences))


def evaluer_moteur(moteur, requetes: list[dict], top_k: int, mode: str,
                   seuil: float) -> dict:
    precisions, rangs_reciproques, ndcgs, rappels, scores, reponses = [], [], [], [], [], 0
    replis = 0

    for requete in requetes:
        resultats = interroger(moteur, requete["titre"], requete["description"], top_k)
        if resultats:
            reponses += 1
            scores.extend(float(r.get("score", 0.0)) for r in resultats)
            # Une requete dont aucun resultat n'atteint le seuil de pertinence n'a
            # ete servie que grace au repli. La distinguer evite de confondre
            # "le moteur a repondu" et "le moteur a trouve quelque chose de pertinent".
            if all(float(r.get("score", 0.0)) < seuil for r in resultats):
                replis += 1

        pertinents = set(requete.get("pertinents") or [])
        marques = []
        for resultat in resultats:
            if mode == "annote":
                cle = str(resultat.get("ticket_id") or resultat.get("index") or
                          resultat.get("resolution", "")[:80])
                marques.append(1 if cle in pertinents else 0)
            else:
                marques.append(1 if resultat.get("categorie") == requete["categorie"] else 0)

        precisions.append(sum(marques) / top_k if marques else 0.0)
        premier = next((i for i, m in enumerate(marques) if m), None)
        rangs_reciproques.append(1.0 / (premier + 1) if premier is not None else 0.0)
        ideal = dcg(sorted(marques, reverse=True))
        ndcgs.append(dcg(marques) / ideal if ideal else 0.0)
        if mode == "annote" and pertinents:
            rappels.append(sum(marques) / len(pertinents))

    n = max(len(requetes), 1)
    resultat = {
        f"precision_at_{top_k}": round(sum(precisions) / n, 4),
        f"mrr_at_{top_k}": round(sum(rangs_reciproques) / n, 4),
        f"ndcg_at_{top_k}": round(sum(ndcgs) / n, 4),
        "taux_reponse": round(reponses / n, 4),
        "taux_repli": round(replis / n, 4),
        "seuil_pertinence": seuil,
        "score_similarite_moyen": round(sum(scores) / len(scores), 4) if scores else 0.0,
        "n_requetes": len(requetes),
    }
    if mode == "annote":
        resultat[f"recall_at_{top_k}"] = round(sum(rappels) / n, 4) if rappels else 0.0
    else:
        resultat[f"recall_at_{top_k}"] = None
        resultat["note_rappel"] = (
            "Non calcule en mode proxy : l'ensemble des pertinents est la categorie "
            "entiere, ce qui rend le rappel@k mecaniquement proche de zero et sans "
            "rapport avec la qualite du moteur."
        )
    return resultat


# ── jeu de requetes ──────────────────────────────────────────────────────────

def echantillon_stratifie(test_df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    par_categorie = max(1, n // max(test_df["Catégorie"].nunique(), 1))
    morceaux = [
        bloc.sample(min(par_categorie, len(bloc)), random_state=seed)
        for _, bloc in test_df.groupby("Catégorie")
    ]
    return pd.concat(morceaux, ignore_index=True).head(n)


def construire_gabarit(params: dict, n: int) -> int:
    chemin = params.get("knowledge", {}).get("eval_set_path", "data/knowledge/rag_eval_set.json")
    if os.path.exists(chemin):
        print(f"[rag_eval] {chemin} existe deja — non ecrase.")
        return 1

    test_df = pd.read_csv(TEST_PATH, encoding="utf-8")
    moteurs = charger_moteurs(params)
    moteur = moteurs.get("hybride") or moteurs.get("semantique") or moteurs.get("lexical")
    if moteur is None:
        print("[rag_eval] Aucun moteur disponible — impossible de proposer des candidats.")
        return 1

    echantillon = echantillon_stratifie(test_df, n, params["data"]["random_state"])
    requetes = []
    for i, ligne in echantillon.iterrows():
        candidats = interroger(moteur, str(ligne["Titre"]), str(ligne["Description"]), 10)
        requetes.append({
            "query_id": f"Q{i:03d}",
            "titre": str(ligne["Titre"]),
            "description": str(ligne["Description"]),
            "categorie": str(ligne["Catégorie"]),
            "candidats_a_annoter": [
                {
                    "cle": str(c.get("ticket_id") or c.get("index") or
                               str(c.get("resolution", ""))[:80]),
                    "score_moteur": round(float(c.get("score", 0.0)), 4),
                    "categorie": c.get("categorie", ""),
                    "resolution": str(c.get("resolution", ""))[:400],
                }
                for c in candidats
            ],
            "pertinents": [],
        })

    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump({
            "created_at": datetime.now(timezone.utc).isoformat(),
            "mode_attendu": "annote",
            "consigne": (
                "Pour chaque requete, reportez dans 'pertinents' la cle des candidats "
                "qui auraient reellement aide a resoudre le ticket. Laissez la liste "
                "vide si aucun ne convient : c'est une information utile, pas un echec "
                "de l'annotation. Les requetes viennent du jeu de test, jamais vues "
                "par la base de connaissances."
            ),
            "requetes": requetes,
        }, f, ensure_ascii=False, indent=2)
    print(f"[rag_eval] Gabarit ecrit : {chemin} ({len(requetes)} requetes a annoter)")
    return 0


def charger_requetes(params: dict) -> tuple[list[dict], str]:
    chemin = params.get("knowledge", {}).get("eval_set_path", "data/knowledge/rag_eval_set.json")
    if os.path.exists(chemin):
        with open(chemin, encoding="utf-8") as f:
            donnees = json.load(f)
        requetes = donnees.get("requetes", [])
        annotees = [r for r in requetes if r.get("pertinents")]
        if annotees:
            print(f"[rag_eval] Jeu annote : {len(annotees)}/{len(requetes)} requetes annotees")
            return annotees, "annote"
        print(f"[rag_eval] {chemin} present mais aucune requete annotee — "
              f"repli sur le protocole proxy.")

    test_df = pd.read_csv(TEST_PATH, encoding="utf-8")
    echantillon = echantillon_stratifie(test_df, 80, params["data"]["random_state"])
    requetes = [
        {"query_id": f"Q{i:03d}", "titre": str(r["Titre"]),
         "description": str(r["Description"]), "categorie": str(r["Catégorie"]),
         "pertinents": []}
        for i, r in echantillon.iterrows()
    ]
    return requetes, "proxy"


# ── pipeline ─────────────────────────────────────────────────────────────────

def run(args: argparse.Namespace) -> int:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        params = yaml.safe_load(f)

    if args.build_template:
        return construire_gabarit(params, args.n_queries)

    top_k = params["rag"]["top_k"]
    requetes, mode = charger_requetes(params)
    moteurs = charger_moteurs(params)

    if not moteurs:
        print("[rag_eval] Aucun moteur RAG disponible — evaluation impossible.")
        return 1

    print(f"[rag_eval] protocole={mode} | {len(requetes)} requetes | top_k={top_k}")

    seuil = float(params["rag"]["similarity_threshold"])
    resultats = {
        nom: evaluer_moteur(moteur, requetes, top_k, mode, seuil)
        for nom, moteur in moteurs.items()
    }

    rapport = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "protocole": mode,
        "avertissement_protocole": (
            "Protocole proxy : est considere pertinent tout resultat de la meme "
            "categorie que la requete. Indicatif seulement. Construisez le jeu annote "
            "avec --build-template pour obtenir des mesures interpretables."
            if mode == "proxy" else
            "Protocole annote : pertinence designee par un administrateur."
        ),
        "top_k": top_k,
        "n_requetes": len(requetes),
        "source_requetes": TEST_PATH,
        "moteurs": resultats,
        "moteur_en_production": (
            "hybride" if "hybride" in moteurs
            else ("semantique" if "semantique" in moteurs else "lexical")
        ),
        "non_mesure": [
            "Fidelite de la generation : le chemin de classification n'appelle aucun "
            "LLM, la synthese admin est un appel separe et facultatif.",
            "Utilite reelle percue : necessiterait un retour explicite par "
            "recommandation, que l'interface ne collecte pas.",
        ],
    }

    os.makedirs("metrics", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)

    for nom, valeurs in resultats.items():
        print(f"[rag_eval] {nom:11s} precision@{top_k}={valeurs[f'precision_at_{top_k}']:.4f} "
              f"| mrr={valeurs[f'mrr_at_{top_k}']:.4f} "
              f"| ndcg={valeurs[f'ndcg_at_{top_k}']:.4f} "
              f"| taux_reponse={valeurs['taux_reponse']:.4f}")
    print(f"[rag_eval] ecrit {OUT}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build-template", action="store_true",
                   help="genere le gabarit d'annotation et sort")
    p.add_argument("--n-queries", type=int, default=80,
                   help="nombre de requetes du gabarit (defaut 80)")
    sys.exit(run(p.parse_args()))
