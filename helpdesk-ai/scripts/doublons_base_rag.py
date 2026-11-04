# -*- coding: utf-8 -*-
"""Que valent « trois suggestions » quand la base n'a que 46 reponses ?

La remarque
-----------
L'encadrant releve que les 1 357 tickets de la base RAG ne correspondent qu'a
46 resolutions distinctes. Verification faite, le chiffre est exact : la
colonne `Resolution/Motif` de `data/splits/rag.csv` prend 46 valeurs, repetees
31 fois en mediane et jusqu'a 49 fois.

La question qui compte n'est pas la redondance de la base — le chapitre 2
l'etablit deja pour le corpus entier — mais son EFFET sur ce que le moteur
rend. Si les trois passages rendus pour une requete portent la meme resolution
ecrite trois fois, alors « trois suggestions » en vaut une, et la precision@3
publiee mesure autre chose que ce qu'elle annonce.

Ce que ce script mesure
------------------------
  1. combien de resolutions DISTINCTES chaque requete recoit reellement ;
  2. la precision recalculee sur les resolutions distinctes ;
  3. ce que rendrait un moteur qui ecarte les doublons et complete avec le
     candidat suivant — c'est-a-dire s'il existe de quoi completer.

Le troisieme point est le seul actionnable : si la base peut fournir trois
reponses differentes et que le moteur n'en donne qu'une repetee, c'est un
defaut du moteur. Si elle ne le peut pas, c'est une limite du corpus, et il
faut le dire plutot que d'afficher trois lignes qui n'en font qu'une.

Sortie : metrics/doublons_base_rag.json
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yaml

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.path.insert(0, os.path.join(RACINE, "src"))

from pipeline.rag_eval import charger_moteurs, charger_requetes, interroger  # noqa: E402

RAG_CSV = os.path.join(RACINE, "data", "splits", "rag.csv")
SORTIE = os.path.join(RACINE, "metrics", "doublons_base_rag.json")
PARAMS = os.path.join(RACINE, "params.yaml")

# Au-dela de ce rang, on cesse de chercher un candidat different : si le moteur
# doit descendre tres loin pour trouver une autre reponse, celle-ci n'a plus
# grand-chose a voir avec la demande.
RANG_MAX_POUR_COMPLETER = 20


def empreinte(resolution: str) -> str:
    """Deux resolutions identiques au blanc pres sont la meme reponse."""
    return " ".join(str(resolution or "").split()).lower()


def composition_de_la_base() -> dict:
    df = pd.read_csv(RAG_CSV)
    res = df["Résolution/Motif"].fillna("").map(empreinte)
    res = res[res != ""]
    compte = res.value_counts()
    return {
        "lignes": int(len(df)),
        "resolutions_distinctes": int(res.nunique()),
        "repetition_mediane": int(compte.median()),
        "repetition_maximale": int(compte.max()),
        "titres_distincts": int(df["Titre"].nunique()),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top-k", type=int, default=None)
    a = ap.parse_args()

    with io.open(PARAMS, encoding="utf-8") as f:
        params = yaml.safe_load(f)
    top_k = a.top_k or params["rag"]["top_k"]

    base = composition_de_la_base()
    print("base RAG : %d lignes pour %d resolutions distinctes "
          "(repetition mediane %d, maximale %d)"
          % (base["lignes"], base["resolutions_distinctes"],
             base["repetition_mediane"], base["repetition_maximale"]))

    requetes, protocole = charger_requetes(params)
    moteurs = charger_moteurs(params)
    print("\n%d requetes, protocole « %s »\n" % (len(requetes), protocole))

    # Les trois moteurs ecartent deja les resolutions deja vues
    # (src/rag/engine.py:83, semantic_engine.py:147, hybrid_engine.py:124). La
    # question n'est donc pas « rendent-ils des doublons » mais « reste-t-il
    # assez de reponses differentes une fois les doublons ecartes ». Le seuil de
    # pertinence masque cet effet en coupant avant lui : la seconde passe le
    # retire pour voir le comportement nu du classement.
    resultats = {}
    for nom, moteur in moteurs.items():
        distinctes, rendus, pertinents_distincts, pertinents_bruts = [], [], [], []
        profondeur_necessaire = []
        for q in requetes:
            sortie = interroger(moteur, q["titre"], q["description"], top_k)
            empreintes = [empreinte(r.get("resolution") or r.get("knowledge") or "")
                          for r in sortie]
            vues, uniques = set(), []
            for e, r in zip(empreintes, sortie):
                if e and e not in vues:
                    vues.add(e)
                    uniques.append(r)
            rendus.append(len(sortie))
            distinctes.append(len(uniques))

            # Ce que le protocole d'approximation compte comme pertinent.
            cat = q.get("categorie")
            pertinents_bruts.append(sum(1 for r in sortie if r.get("categorie") == cat))
            pertinents_distincts.append(sum(1 for r in uniques if r.get("categorie") == cat))

            # Jusqu'ou faudrait-il descendre pour obtenir top_k reponses differentes ?
            large = interroger(moteur, q["titre"], q["description"], RANG_MAX_POUR_COMPLETER)
            vues2, rang = set(), 0
            for i, r in enumerate(large, 1):
                e = empreinte(r.get("resolution") or r.get("knowledge") or "")
                if e and e not in vues2:
                    vues2.add(e)
                    if len(vues2) == min(top_k, len(large)):
                        rang = i
                        break
            profondeur_necessaire.append(rang or RANG_MAX_POUR_COMPLETER)

        r = {
            "suggestions_rendues_par_requete": round(float(np.mean(rendus)), 4),
            "reponses_distinctes_par_requete": round(float(np.mean(distinctes)), 4),
            "part_de_doublons": round(1 - float(np.mean(distinctes)) / max(float(np.mean(rendus)), 1e-9), 4),
            "requetes_sans_aucun_doublon": int(sum(1 for d, n in zip(distinctes, rendus) if d == n)),
            "requetes_a_reponse_unique": int(sum(1 for d in distinctes if d == 1)),
            "repartition_reponses_distinctes": dict(collections.Counter(distinctes)),
            "precision_sur_rendus": round(float(np.sum(pertinents_bruts) / max(np.sum(rendus), 1)), 4),
            "precision_sur_reponses_distinctes": round(
                float(np.sum(pertinents_distincts) / max(np.sum(distinctes), 1)), 4),
            "rang_median_pour_k_reponses_differentes": int(np.median(profondeur_necessaire)),
        }
        resultats[nom] = r
        print("  %-11s %4.2f rendues -> %4.2f distinctes (%.0f %% de doublons) ; "
              "%d requete(s) n'en recoivent qu'une"
              % (nom, r["suggestions_rendues_par_requete"],
                 r["reponses_distinctes_par_requete"], 100 * r["part_de_doublons"],
                 r["requetes_a_reponse_unique"]))
        print("  %-11s precision : %.4f sur les rendues, %.4f sur les distinctes ; "
              "il faut descendre au rang %d pour %d reponses differentes"
              % ("", r["precision_sur_rendus"], r["precision_sur_reponses_distinctes"],
                 r["rang_median_pour_k_reponses_differentes"], top_k))

    # ── Seconde passe : seuil retire ─────────────────────────────────────────
    print("\nsans le filtre de pertinence, pour voir le classement nu :")
    sans_filtre = {}
    for nom, moteur in moteurs.items():
        ancien = getattr(moteur, "similarity_threshold", None)
        if ancien is None:
            continue
        moteur.similarity_threshold = 0.0
        try:
            distinctes, rendus = [], []
            for q in requetes:
                sortie = interroger(moteur, q["titre"], q["description"], top_k)
                vues = {empreinte(r.get("resolution") or r.get("knowledge") or "")
                        for r in sortie}
                vues.discard("")
                rendus.append(len(sortie))
                distinctes.append(len(vues))
        finally:
            moteur.similarity_threshold = ancien
        sans_filtre[nom] = {
            "suggestions_rendues_par_requete": round(float(np.mean(rendus)), 4),
            "reponses_distinctes_par_requete": round(float(np.mean(distinctes)), 4),
            "requetes_servies_au_complet": int(sum(1 for d in distinctes if d >= top_k)),
            "requetes_a_moins_de_k_reponses": int(sum(1 for d in distinctes if d < top_k)),
        }
        s = sans_filtre[nom]
        print("  %-11s %4.2f rendues -> %4.2f distinctes ; %d/%d requetes obtiennent "
              "les %d reponses differentes demandees"
              % (nom, s["suggestions_rendues_par_requete"],
                 s["reponses_distinctes_par_requete"], s["requetes_servies_au_complet"],
                 len(requetes), top_k))

    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "remarque": "1 357 tickets de base RAG pour 46 resolutions distinctes : quel effet ?",
            "reponse_courte": ("Les trois moteurs ecartent deja les resolutions deja vues avant "
                               "de rendre leur liste ; aucun doublon n'atteint l'utilisateur. "
                               "L'effet des doublons se lit ailleurs : sur le nombre de reponses "
                               "DIFFERENTES que la base peut encore fournir."),
            "ou_se_fait_le_dedoublonnage": ["src/rag/engine.py:83",
                                            "src/rag/semantic_engine.py:147",
                                            "src/rag/hybrid_engine.py:124"],
            "composition_de_la_base": base,
            "protocole": protocole,
            "n_requetes": len(requetes),
            "top_k": top_k,
            "par_moteur": resultats,
            "par_moteur_sans_filtre": sans_filtre,
            # Releve conserve de ce que les memes 40 requetes donnaient AVANT
            # l'elargissement variable de src/rag/semantic_engine.py, mesure le
            # 2026-10-09 par ce meme script. Il n'est pas recalculable, puisque
            # le defaut est corrige : il est conserve ici pour que les chiffres
            # « avant » cites au memoire restent tracables a une mesure.
            "avant_correction_de_l_elargissement": {
                "mesure_le": "2026-10-09",
                "note": "facteur fixe top_k*3 = 9 voisins lus avant dedoublonnage",
                "semantique": {"suggestions_rendues_par_requete": 1.57,
                               "precision_sur_rendus": 0.5556},
                "hybride": {"suggestions_rendues_par_requete": 1.75,
                            "precision_sur_rendus": 0.4429},
                "elargissement_necessaire": {"9": 1.57, "18": 1.85, "36": 2.25,
                                             "75": 2.75, "150": 3.00},
            },
        }, f, ensure_ascii=False, indent=2)
    print("\necrit : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
