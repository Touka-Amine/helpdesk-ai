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

from pipeline import jeu_gele  # noqa: E402

PARAMS_PATH = "params.yaml"
TEST_PATH = "data/splits/test.csv"
RAG_ENGINE_PATH = "models/rag_engine.pkl"
SEM_RAG_DIR = "models/semantic_rag"
OUT = "metrics/rag_eval.json"
OUT_BALAYAGE = "metrics/rag_seuil_balayage.json"
OUT_PROTOCOLES = "metrics/rag_protocoles.json"


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
                fallback_threshold=params["rag"].get("fallback_threshold", 0.20),
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
    n'execute : le seuil de pertinence n'est pas atteint par tous les moteurs — le
    lexical plafonne a 0.31 — et l'evaluation renverrait zero resultat pour eux.
    Le taux de repli est rapporte a part, et n'est pas comparable d'un moteur a
    l'autre puisqu'un seuil unique s'applique a trois echelles de scores
    differentes.
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
    rendus_total = pertinents_rendus = 0

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

        # Deux precisions, et la distinction compte des que le seuil filtre.
        #   precision@k  divise par k, donc penalise une liste tronquee : rendre
        #                deux bons resultats au lieu de trois en moyens vaut moins
        #                que trois resultats dont un bon.
        #   precision sur les resultats rendus : ce que vaut ce que l'utilisateur
        #                voit reellement. C'est elle qui arbitre un reglage de seuil.
        precisions.append(sum(marques) / top_k if marques else 0.0)
        if marques:
            rendus_total += len(marques)
            pertinents_rendus += sum(marques)
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
        # Precision de ce qui est reellement affiche, et longueur moyenne de la
        # liste rendue. Sans ces deux valeurs, un seuil qui ameliore la qualite
        # des suggestions en les raccourcissant apparait comme une regression.
        "precision_sur_rendus": (round(pertinents_rendus / rendus_total, 4)
                                 if rendus_total else None),
        "resultats_par_requete": (round(rendus_total / reponses, 2)
                                  if reponses else 0.0),
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

    # Lecture qui TRANCHE : elle affecte durablement des tickets du jeu gele au
    # role de jeu d'evaluation du moteur de recherche. Tout ce qui sera ensuite
    # choisi sur ces requetes — le seuil, en particulier — l'est sur le jeu gele.
    test_df = jeu_gele.lire(
        jeu_gele.POUR_DECIDER,
        motif="constitution du jeu d'evaluation annote du moteur de recherche",
        lecteur="src/pipeline/rag_eval.py --build-template",
        budget=(params.get("jeu_gele") or {}).get("lectures_de_decision_max"),
    )
    moteurs = charger_moteurs(params)
    moteur = moteurs.get("hybride") or moteurs.get("semantique") or moteurs.get("lexical")
    if moteur is None:
        print("[rag_eval] Aucun moteur disponible — impossible de proposer des candidats.")
        return 1

    echantillon = echantillon_stratifie(test_df, n, params["data"]["random_state"])

    # L'annotateur doit voir un vrai vivier, pas la sortie deja filtree du service.
    # Avec le seuil servi et top_k=3, le gabarit ne proposerait que trois candidats
    # par requete : on ne pourrait juger que ce que le moteur a deja retenu, et le
    # rappel resterait hors de portee. On elargit donc a dix candidats sans seuil,
    # puis on restaure les reglages.
    N_CANDIDATS = 10
    sauve_k = getattr(moteur, "top_k", None)
    sauve_s = getattr(moteur, "similarity_threshold", None)
    if sauve_k is not None:
        moteur.top_k = N_CANDIDATS
    if sauve_s is not None:
        moteur.similarity_threshold = 0.0

    requetes = []
    try:
        for i, ligne in echantillon.iterrows():
            candidats = interroger(moteur, str(ligne["Titre"]), str(ligne["Description"]),
                                   N_CANDIDATS)
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
                        "rang": rang,
                        "categorie": c.get("categorie", ""),
                        "resolution": str(c.get("resolution", ""))[:400],
                    }
                    for rang, c in enumerate(candidats, 1)
                ],
                "pertinents": [],
            })
    finally:
        if sauve_k is not None:
            moteur.top_k = sauve_k
        if sauve_s is not None:
            moteur.similarity_threshold = sauve_s

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
            "protocole_d_annotation": [
                "Qui annote : un consultant du service support, qui connait le metier. "
                "L'auteur du memoire ne s'annote pas lui-meme, et un modele de langage "
                "ne remplace pas ce jugement : ce serait mesurer le systeme avec le "
                "systeme.",
                "Critere : la resolution proposee aurait-elle fait gagner du temps sur "
                "CE ticket ? Pas 'parle-t-elle du meme domaine', mais 'aurait-elle "
                "servi'. C'est precisement sur ce point que le protocole d'approximation "
                "est suspect : il compte pertinent tout ce qui partage la categorie.",
                "Ne pas juger sur la categorie affichee. Elle est donnee comme contexte, "
                "au meme titre que l'aurait un consultant devant le ticket, mais deux "
                "tickets 'Reseau' peuvent decrire des incidents sans rapport.",
                "Ne pas juger sur le rang ni sur le score du moteur : ce sont eux que "
                "l'annotation doit evaluer.",
                "Zero pertinent est une reponse valide et frequente : les scenarios du "
                "jeu de test sont absents de la base par construction anti-fuite.",
                "Compter environ une demi-journee pour quarante requetes.",
            ],
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
        # Une requete pour laquelle l'annotateur n'a retenu AUCUN candidat est
        # annotee, et son resultat est zero. La confondre avec une requete non
        # annotee reviendrait a retirer de la mesure les cas les plus difficiles,
        # donc a surestimer le moteur. Le drapeau `annote` tranche explicitement ;
        # a defaut, on retombe sur l'ancienne heuristique.
        if any("annote" in r for r in requetes):
            annotees = [r for r in requetes if r.get("annote")]
            vides = sum(1 for r in annotees if not r.get("pertinents"))
        else:
            annotees = [r for r in requetes if r.get("pertinents")]
            vides = 0
        if annotees:
            print(f"[rag_eval] Jeu annote : {len(annotees)}/{len(requetes)} requetes annotees, "
                  f"dont {vides} sans aucun candidat pertinent")
            return annotees, "annote"
        print(f"[rag_eval] {chemin} present mais aucune requete annotee — "
              f"repli sur le protocole proxy.")

    test_df = jeu_gele.lire(
        jeu_gele.POUR_RAPPORTER,
        motif="tirage du jeu de requetes du protocole d'approximation",
        lecteur="src/pipeline/rag_eval.py (repli proxy)",
    )
    echantillon = echantillon_stratifie(test_df, 80, params["data"]["random_state"])
    requetes = [
        {"query_id": f"Q{i:03d}", "titre": str(r["Titre"]),
         "description": str(r["Description"]), "categorie": str(r["Catégorie"]),
         "pertinents": []}
        for i, r in echantillon.iterrows()
    ]
    return requetes, "proxy"


# ── pipeline ─────────────────────────────────────────────────────────────────

def _evaluer_au_seuil(moteur, requetes, top_k, mode, seuil):
    """Evalue le moteur avec SON seuil positionne, puis le restaure."""
    sauve = getattr(moteur, "similarity_threshold", None)
    if sauve is not None:
        moteur.similarity_threshold = seuil
    try:
        return evaluer_moteur(moteur, requetes, top_k, mode, seuil)
    finally:
        if sauve is not None:
            moteur.similarity_threshold = sauve


def balayer_seuil(params: dict) -> int:
    """
    Mesure chaque moteur sur toute la plage de seuils, et releve la distribution
    brute des scores du moteur servi.

    Sans ce balayage, un seuil ne peut pas etre justifie : on ne sait ni s'il
    filtre quelque chose, ni ce que le filtrage coute. Il a mis en evidence que
    l'ancien seuil de 0.50 etait hors de portee du score hybride, dont le maximum
    observe est 0.4886.

    Ce balayage est une LECTURE DECISIONNELLE du jeu gele, et le journal doit le
    dire. Les requetes ne viennent pas de `test.csv` directement mais du gabarit
    annote — lequel a ete tire du jeu gele. Choisir un seuil sur ce balayage,
    c'est donc le choisir sur le jeu gele, et c'est la remarque de l'encadrant sur
    le seuil de 0,35 : elle et celle sur le jeu gele ne font qu'une.

    Ecrit metrics/rag_seuil_balayage.json, lu par report/figures/ch05_seuil.py.
    """
    top_k = params["rag"]["top_k"]
    plancher = float(params["rag"].get("fallback_threshold", 0.20))
    requetes, mode = charger_requetes(params)
    jeu_gele.inscrire(
        jeu_gele.POUR_DECIDER,
        motif="balayage du seuil de pertinence du moteur de recherche "
              "(%d requetes, protocole %s)" % (len(requetes), mode),
        lecteur="src/pipeline/rag_eval.py --balayage-seuil",
        provenance="indirecte : requetes tirees du jeu gele via le gabarit annote",
    )
    moteurs = charger_moteurs(params)
    if not moteurs:
        print("[rag_eval] Aucun moteur RAG disponible — balayage impossible.")
        return 1

    seuils = [round(x / 100.0, 2) for x in range(0, 75, 5)]
    rapport = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "protocole": mode,
        "n_requetes": len(requetes),
        "top_k": top_k,
        "fallback_threshold": plancher,
        "seuil_retenu": float(params["rag"]["similarity_threshold"]),
        "moteurs": {},
    }

    for nom, moteur in moteurs.items():
        # Distribution brute : tous les scores rendus, seuil neutralise.
        sauve = getattr(moteur, "similarity_threshold", None)
        if sauve is not None:
            moteur.similarity_threshold = 0.0
        try:
            tous, tops = [], []
            for requete in requetes:
                res = interroger(moteur, requete["titre"], requete["description"], top_k)
                scores = [float(r.get("score", 0.0)) for r in res]
                tous.extend(scores)
                if scores:
                    tops.append(scores[0])
        finally:
            if sauve is not None:
                moteur.similarity_threshold = sauve

        rapport["moteurs"][nom] = {
            "distribution": {
                "n": len(tous),
                "min": round(min(tous), 4) if tous else None,
                "max": round(max(tous), 4) if tous else None,
                "moyenne": round(sum(tous) / len(tous), 4) if tous else None,
                "meilleur_par_requete": [round(v, 4) for v in tops],
            },
            # evaluer_moteur n'utilise `seuil` que pour compter les replis : le
            # filtrage reel est fait par le moteur avec son propre attribut. Il
            # faut donc le positionner, sinon le balayage mesurerait un seul point.
            "par_seuil": [_evaluer_au_seuil(moteur, requetes, top_k, mode, s)
                          for s in seuils],
            "seuils": seuils,
        }
        d = rapport["moteurs"][nom]["distribution"]
        print(f"[rag_eval] {nom:11s} scores de {d['min']} a {d['max']} "
              f"(moyenne {d['moyenne']})")

    # Balayage d'alpha : l'autre correction envisageable pour le taux de repli
    # etait de relever la part semantique. Mesuree ici pour que le mmoire puisse
    # dire pourquoi elle a ete ecartee, plutot que de l'affirmer.
    if "hybride" in moteurs:
        hybride = moteurs["hybride"]
        alpha_initial = hybride.alpha
        seuil_retenu = float(params["rag"]["similarity_threshold"])
        rapport["balayage_alpha"] = {
            "seuil": seuil_retenu,
            "note": ("Chaque ligne est mesuree au seuil servi. Relever alpha "
                     "rapproche l'echelle hybride de l'echelle semantique et fait "
                     "tomber le repli, au prix de la precision."),
            "par_alpha": [],
        }
        try:
            for a in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
                hybride.alpha = a
                mesure = _evaluer_au_seuil(hybride, requetes, top_k, mode, seuil_retenu)
                mesure["alpha"] = a
                rapport["balayage_alpha"]["par_alpha"].append(mesure)
                print(f"[rag_eval] alpha={a:.1f}  repli={mesure['taux_repli']:.3f} "
                      f"| precision@{top_k}={mesure[f'precision_at_{top_k}']:.4f}")
        finally:
            hybride.alpha = alpha_initial

    os.makedirs("metrics", exist_ok=True)
    with open(OUT_BALAYAGE, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)
    print(f"[rag_eval] ecrit {OUT_BALAYAGE}")
    return 0


def comparer_protocoles(params: dict) -> int:
    """
    Confronte le jugement humain au protocole d'approximation, sur les MEMES
    requetes et le meme moteur.

    C'est la seule mesure qui dit ce que vaut l'approximation. Le protocole proxy
    compte pertinent tout passage de la meme categorie que la requete ; un
    consultant, lui, juge si la resolution aurait fait gagner du temps. Les deux
    peuvent diverger dans les deux sens : une resolution d'impression classee
    Applicatifs aide un ticket Infrastructure (le proxy la rejette a tort), deux
    tickets Reseau sans rapport se valident mutuellement (le proxy les accepte a
    tort).

    Exige que data/knowledge/rag_eval_set.json porte des annotations.
    Ecrit metrics/rag_protocoles.json.
    """
    top_k = params["rag"]["top_k"]
    seuil = float(params["rag"]["similarity_threshold"])
    requetes, mode = charger_requetes(params)
    if mode != "annote":
        print("[rag_eval] Aucune requete annotee — comparaison impossible.")
        print("[rag_eval] Remplissez les listes 'pertinents' de "
              f"{params.get('knowledge', {}).get('eval_set_path')}, puis relancez.")
        return 1

    moteurs = charger_moteurs(params)
    if not moteurs:
        print("[rag_eval] Aucun moteur disponible.")
        return 1

    resultats = {}
    for nom, moteur in moteurs.items():
        humain = evaluer_moteur(moteur, requetes, top_k, "annote", seuil)
        approx = evaluer_moteur(moteur, requetes, top_k, "proxy", seuil)
        resultats[nom] = {
            "annote": humain,
            "proxy": approx,
            "ecart_precision_at_%d" % top_k: round(
                approx["precision_at_%d" % top_k] - humain["precision_at_%d" % top_k], 4),
            "ecart_precision_sur_rendus": (
                round(approx["precision_sur_rendus"] - humain["precision_sur_rendus"], 4)
                if approx["precision_sur_rendus"] is not None
                and humain["precision_sur_rendus"] is not None else None),
        }
        print("[rag_eval] %-11s humain P@%d=%.4f | approx P@%d=%.4f | ecart=%+.4f"
              % (nom, top_k, humain["precision_at_%d" % top_k],
                 top_k, approx["precision_at_%d" % top_k],
                 resultats[nom]["ecart_precision_at_%d" % top_k]))

    rapport = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_requetes_annotees": len(requetes),
        "top_k": top_k,
        "seuil": seuil,
        "lecture": (
            "Un ecart positif signifie que l'approximation surestime la pertinence : "
            "elle compte bons des passages que l'annotateur a rejetes. Un ecart negatif "
            "signifie qu'elle en rejette que l'annotateur a juges utiles."
        ),
        "moteurs": resultats,
    }
    os.makedirs("metrics", exist_ok=True)
    with open(OUT_PROTOCOLES, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)
    print(f"[rag_eval] ecrit {OUT_PROTOCOLES}")
    return 0


def run(args: argparse.Namespace) -> int:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        params = yaml.safe_load(f)

    if args.build_template:
        return construire_gabarit(params, args.n_queries)

    if args.balayage_seuil:
        return balayer_seuil(params)

    if args.comparer_protocoles:
        return comparer_protocoles(params)

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
    p.add_argument("--comparer-protocoles", action="store_true",
                   help="confronte le jugement humain au protocole d'approximation "
                        "sur les memes requetes, puis sort")
    p.add_argument("--balayage-seuil", action="store_true",
                   help="mesure chaque moteur sur toute la plage de seuils et "
                        "releve la distribution des scores, puis sort")
    sys.exit(run(p.parse_args()))
