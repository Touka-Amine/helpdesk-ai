# -*- coding: utf-8 -*-
"""Ce que vaut le seuil 0,35 ailleurs que là où il a été choisi.

La remarque
-----------
L'encadrant demande de préciser que le seuil de 0,35 a été choisi sur le jeu
d'évaluation, et que sa performance doit donc être présentée avec cette
réserve. C'est exact : le mémoire retient 0,35 parce que c'est la valeur où la
précision de l'affiché est la plus haute sur les quarante requêtes annotées, et
il rapporte ensuite cette même précision, relue sur ces mêmes quarante requêtes.
Un seuil choisi et jugé sur les mêmes données est forcément flatteur.

Poser la réserve en une phrase serait déjà mieux que rien. La chiffrer vaut
mieux encore, et c'est ce que fait ce script.

Ce qu'il mesure
---------------
1. LE POUVOIR DISCRIMINANT du score, indépendamment de tout seuil : la
   probabilité qu'un passage jugé utile soit mieux noté qu'un passage jugé
   inutile tiré au hasard. Un score sans pouvoir discriminant ne mérite aucun
   seuil, quel qu'il soit.

2. LA PRÉCISION PAR TRANCHE de score, qui dit si la coupure a un endroit
   naturel ou si elle est arbitraire.

3. CE QUE LE SEUIL VAUT HORS DE SON ÉCHANTILLON. Les quarante requêtes sont
   découpées en plis ; sur chaque pli, le seuil est choisi sur les requêtes des
   autres plis, puis mesuré sur celles-ci, qui n'ont pas servi à le choisir.
   L'écart entre cette précision-là et celle que le mémoire publie est
   exactement la part d'optimisme que la remarque vise.

Sortie : metrics/seuil_rag_hors_echantillon.json
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import yaml

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.path.insert(0, os.path.join(RACINE, "src"))

from pipeline.rag_eval import charger_moteurs, charger_requetes  # noqa: E402

SORTIE = os.path.join(RACINE, "metrics", "seuil_rag_hors_echantillon.json")
PARAMS = os.path.join(RACINE, "params.yaml")
GRAINE = 42
TOP_K_LARGE = 3
TRANCHES = [(0.0, 0.30), (0.30, 0.35), (0.35, 0.40), (0.40, 1.01)]


def candidats_notes(moteur, requetes, top_k):
    """Pour chaque requête : la liste (score, jugé utile) de ses candidats.

    Le filtre de pertinence est retiré : on veut la liste complète, puisque
    c'est sur elle que tout seuil se calcule.
    """
    from data.preprocess import build_text_for_rag

    ancien = getattr(moteur, "similarity_threshold", None)
    if ancien is not None:
        moteur.similarity_threshold = 0.0
    try:
        par_requete = []
        for q in requetes:
            texte = build_text_for_rag(q["description"], titre=q["titre"])
            sortie = list(moteur.recommend(query_text=texte, category_filter=None,
                                           allow_fallback=True) or [])[:top_k]
            # Même clé que `rag_eval.evaluer_moteur` en mode annoté : l'identifiant
            # du ticket s'il existe, sinon les quatre-vingts premiers caractères
            # de la résolution. Toute autre convention ne retrouverait aucun
            # jugement, et le script conclurait à l'absence de pertinents.
            pertinents = set(q.get("pertinents") or [])
            lignes = []
            for r in sortie:
                cle = str(r.get("ticket_id") or r.get("index") or
                          r.get("resolution", "")[:80])
                lignes.append((float(r.get("score", 0.0)), cle in pertinents))
            par_requete.append(lignes)
    finally:
        if ancien is not None:
            moteur.similarity_threshold = ancien
    return par_requete


def precision_au_seuil(par_requete, seuil):
    """La précision de ce qui serait affiché à ce seuil, et la longueur des listes."""
    rendus = pertinents = 0
    for lignes in par_requete:
        gardes = [(s, u) for s, u in lignes if s >= seuil]
        # Repli : si le seuil ne laisse rien passer, le moteur rend quand même
        # le meilleur candidat, comme en service.
        if not gardes and lignes:
            gardes = [max(lignes, key=lambda x: x[0])]
        rendus += len(gardes)
        pertinents += sum(1 for _, u in gardes if u)
    return (pertinents / rendus if rendus else 0.0), (rendus / max(len(par_requete), 1))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plis", type=int, default=5)
    a = ap.parse_args()

    with io.open(PARAMS, encoding="utf-8") as f:
        params = yaml.safe_load(f)
    seuil_servi = params["rag"]["similarity_threshold"]

    requetes, protocole = charger_requetes(params)
    moteur = charger_moteurs(params)["hybride"]
    par_requete = candidats_notes(moteur, requetes, TOP_K_LARGE)
    tous = [(s, u) for lignes in par_requete for s, u in lignes]
    scores_utiles = [s for s, u in tous if u]
    scores_inutiles = [s for s, u in tous if not u]
    print("\n%d requêtes, %d passages notés, dont %d jugés utiles"
          % (len(requetes), len(tous), len(scores_utiles)))

    # ── 1. Pouvoir discriminant ──────────────────────────────────────────────
    if scores_utiles and scores_inutiles:
        gagnes = sum(1.0 if a_ > b_ else 0.5 if a_ == b_ else 0.0
                     for a_ in scores_utiles for b_ in scores_inutiles)
        discrimination = gagnes / (len(scores_utiles) * len(scores_inutiles))
    else:
        discrimination = float("nan")
    print("pouvoir discriminant du score : %.4f" % discrimination)
    print("  (probabilité qu'un passage utile soit mieux noté qu'un passage inutile)")

    # ── 2. Précision par tranche ─────────────────────────────────────────────
    print("\nprécision par tranche de score :")
    tranches = []
    for bas, haut in TRANCHES:
        dedans = [(s, u) for s, u in tous if bas <= s < haut]
        p = (sum(1 for _, u in dedans if u) / len(dedans)) if dedans else None
        tranches.append({"de": bas, "a": min(haut, 1.0), "passages": len(dedans),
                         "precision": None if p is None else round(p, 4)})
        print("  [%.2f ; %.2f[  %3d passages  précision %s"
              % (bas, haut, len(dedans), "n/a" if p is None else "%.4f" % p))

    # ── 3. Le seuil hors de son échantillon ──────────────────────────────────
    grille = [round(x, 2) for x in np.arange(0.20, 0.51, 0.01)]
    dans_echantillon, _ = precision_au_seuil(par_requete, seuil_servi)
    meilleur_global = max(grille, key=lambda s: precision_au_seuil(par_requete, s)[0])
    print("\nseuil servi %.2f : précision de l'affiché %.4f, mesurée sur les requêtes "
          "qui ont servi à le choisir" % (seuil_servi, dans_echantillon))
    print("meilleur seuil sur ces mêmes requêtes : %.2f" % meilleur_global)

    rng = np.random.default_rng(GRAINE)
    ordre = rng.permutation(len(par_requete))
    plis = np.array_split(ordre, a.plis)
    hors, seuils_choisis = [], []
    for i, pli in enumerate(plis, 1):
        dehors = [par_requete[j] for j in ordre if j not in set(pli.tolist())]
        dedans = [par_requete[j] for j in pli.tolist()]
        choisi = max(grille, key=lambda s: precision_au_seuil(dehors, s)[0])
        p_hors, n_hors = precision_au_seuil(dedans, choisi)
        hors.append(p_hors)
        seuils_choisis.append(choisi)
        print("  pli %d : seuil choisi sur les %d autres requêtes = %.2f  ->  "
              "précision %.4f sur les %d requêtes réservées"
              % (i, len(dehors), choisi, p_hors, len(dedans)))

    moyenne_hors = float(np.mean(hors))
    print("\nprécision hors échantillon : %.4f  (contre %.4f publiée)"
          % (moyenne_hors, dans_echantillon))
    print("part d'optimisme du chiffre publié : %+.4f" % (dans_echantillon - moyenne_hors))
    print("seuils choisis selon le pli : %s" % sorted(set(seuils_choisis)))

    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "remarque": ("Le seuil 0,35 a été choisi sur le jeu d'évaluation ; sa performance "
                         "doit être présentée avec cette réserve."),
            "protocole": protocole,
            "n_requetes": len(requetes),
            "seuil_servi": seuil_servi,
            "pouvoir_discriminant": round(float(discrimination), 4),
            "precision_par_tranche": tranches,
            "lecture": (
                "Les precisions absolues de ce fichier viennent d'un rejeu simplifie du "
                "filtrage (le repli y garde le meilleur candidat), et different de quelques "
                "centiemes de celles que le moteur produit reellement dans "
                "metrics/rag_seuil_balayage.json. C'est l'ECART entre dans et hors "
                "echantillon qui doit etre lu, les deux etant calcules de la meme facon."),
            "precision_dans_l_echantillon": round(dans_echantillon, 4),
            "meilleur_seuil_dans_l_echantillon": meilleur_global,
            "validation_croisee": {
                "plis": a.plis,
                "seuils_choisis": seuils_choisis,
                "precisions_hors_echantillon": [round(float(p), 4) for p in hors],
                "precision_moyenne_hors_echantillon": round(moyenne_hors, 4),
                "optimisme": round(dans_echantillon - moyenne_hors, 4),
            },
        }, f, ensure_ascii=False, indent=2)
    print("\nécrit : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
