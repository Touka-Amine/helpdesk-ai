# -*- coding: utf-8 -*-
"""Jusqu'ou peut-on raccourcir la sequence sans abimer le modele ?

Pourquoi cette question
-----------------------
CamemBERT a ete entraine avec `max_length = 128`. Le cout d'un transformeur
croit avec le carre de la longueur pour l'attention et lineairement pour le
reste : diviser la longueur par deux fait plus que diviser le temps par deux.

Mais toute troncature coupe du texte. Ce script mesure les deux cotes a la fois,
pour que le choix se fasse sur des chiffres :

  - combien de tickets seraient tronques a chaque longueur ;
  - ce que la F1-macro devient, sur le jeu de test propre de CamemBERT, celui
    du protocole des experiences ;
  - le cout par ticket, un ticket a la fois, a un et a quatre fils d'execution.

Sortie : metrics/cout_longueur_sequence.json
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "src"))

from sklearn.metrics import f1_score, recall_score
from sklearn.model_selection import StratifiedShuffleSplit

from models.heuristics import apply_heuristics  # noqa: E402

CSV = os.path.join(RACINE, "data", "processed", "HelpDesk1.csv")
ADAPTATEUR = os.path.join(RACINE, "models", "camembert_lora_adapter")
SORTIE = os.path.join(RACINE, "metrics", "cout_longueur_sequence.json")

GRAINE = 42
TEST_SIZE = 0.2
SEUIL = 0.6
LONGUEURS = [48, 64, 96, 128]
N_CHRONO = 30
CLASSIFICATION_PAR_DEFAUT = "demande"


def corps_du_texte(ligne):
    e = str(ligne["text_enriched"])
    p = "type %s priorite %s " % (ligne["classification_simple"], ligne["priorite_simple"])
    return e[len(p):] if e.startswith(p) else e


def main():
    import torch
    from peft import PeftModel
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    df = pd.read_csv(CSV)
    classes = sorted(df["Catégorie"].unique())
    titres = df.groupby("Titre")["Catégorie"].first().reset_index()
    sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=GRAINE)
    _, te = next(sss.split(titres["Titre"], titres["Catégorie"]))
    test = df[df["Titre"].isin(set(titres.iloc[te]["Titre"]))].reset_index(drop=True)
    y = test["Catégorie"].tolist()
    brut = (test["Titre"].fillna("") + " " + test["Description"].fillna("")).tolist()
    entree = ["type %s priorite %s %s" % (CLASSIFICATION_PAR_DEFAUT, enr["priorite_simple"],
                                          corps_du_texte(enr))
              for _, enr in test.iterrows()]

    tok = AutoTokenizer.from_pretrained(ADAPTATEUR)
    base = AutoModelForSequenceClassification.from_pretrained("camembert-base",
                                                              num_labels=len(classes))
    modele = PeftModel.from_pretrained(base, ADAPTATEUR).merge_and_unload().eval().to("cpu")
    arr = np.array(classes)

    # Combien de jetons le corpus demande-t-il reellement ?
    longueurs_reelles = [len(tok(t)["input_ids"]) for t in entree]
    stats_jetons = {
        "mediane": int(np.median(longueurs_reelles)),
        "p90": int(np.percentile(longueurs_reelles, 90)),
        "p99": int(np.percentile(longueurs_reelles, 99)),
        "max": int(np.max(longueurs_reelles)),
    }
    print("jetons par ticket : mediane %d, p90 %d, p99 %d, max %d"
          % (stats_jetons["mediane"], stats_jetons["p90"], stats_jetons["p99"], stats_jetons["max"]))

    resultats = {}
    print("\n%-9s %8s %12s %12s %12s %12s" % ("longueur", "tronques", "F1 seul",
                                              "F1 + regles", "rappel Sec", "ms/ticket"))
    print("-" * 72)
    for L in LONGUEURS:
        tronques = sum(1 for n in longueurs_reelles if n > L)
        out = []
        with torch.no_grad():
            for i in range(0, len(entree), 32):
                e = tok(entree[i:i + 32], padding="max_length", truncation=True,
                        max_length=L, return_tensors="pt")
                out.append(torch.softmax(modele(**e).logits, dim=-1).numpy())
        proba = np.vstack(out)
        pred, conf = arr[proba.argmax(1)], proba.max(1)
        avec = [apply_heuristics(t, p, float(c), threshold=SEUIL)["categorie"]
                for t, p, c in zip(brut, pred, conf)]

        torch.set_num_threads(1)
        with torch.no_grad():
            for i in range(3):
                modele(**tok(entree[i], padding="max_length", truncation=True,
                             max_length=L, return_tensors="pt"))
            t = []
            for i in range(N_CHRONO):
                e = tok(entree[i % len(entree)], padding="max_length", truncation=True,
                        max_length=L, return_tensors="pt")
                t0 = time.perf_counter()
                modele(**e)
                t.append((time.perf_counter() - t0) * 1000)

        resultats[str(L)] = {
            "tickets_tronques": tronques,
            "part_tronquee": round(tronques / len(entree), 4),
            "f1_macro_seul": round(float(f1_score(y, pred, average="macro", labels=classes,
                                                  zero_division=0)), 4),
            "f1_macro_avec_regles": round(float(f1_score(y, avec, average="macro", labels=classes,
                                                         zero_division=0)), 4),
            "rappel_securite": round(float(recall_score(y, avec, labels=["Sécurité"],
                                                        average="macro", zero_division=0)), 4),
            "cout_un_fil": {"median_ms": round(float(np.median(t)), 1),
                            "p95_ms": round(float(np.percentile(t, 95)), 1)},
        }
        r = resultats[str(L)]
        print("%-9d %8d %12.4f %12.4f %12.4f %12.1f"
              % (L, tronques, r["f1_macro_seul"], r["f1_macro_avec_regles"],
                 r["rappel_securite"], r["cout_un_fil"]["median_ms"]))

    # Effet du nombre de fils, a la longueur la plus courte qui tient la qualite.
    print("\neffet du nombre de fils d'execution, longueur 128 et 64 :")
    fils = {}
    for L in (128, 64):
        fils[str(L)] = {}
        for n in (1, 2, 4):
            torch.set_num_threads(n)
            with torch.no_grad():
                for i in range(3):
                    modele(**tok(entree[i], padding="max_length", truncation=True,
                                 max_length=L, return_tensors="pt"))
                t = []
                for i in range(N_CHRONO):
                    e = tok(entree[i % len(entree)], padding="max_length", truncation=True,
                            max_length=L, return_tensors="pt")
                    t0 = time.perf_counter()
                    modele(**e)
                    t.append((time.perf_counter() - t0) * 1000)
            fils[str(L)][str(n)] = {"median_ms": round(float(np.median(t)), 1),
                                    "p95_ms": round(float(np.percentile(t, 95)), 1)}
            print("  longueur %3d, %d fil(s) : mediane %6.1f ms   p95 %6.1f ms"
                  % (L, n, fils[str(L)][str(n)]["median_ms"], fils[str(L)][str(n)]["p95_ms"]))

    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "protocole": "protocole des experiences, graine 42, 355 tickets de test inedits pour CamemBERT",
            "entree": "entree de production, classification fixee a « demande »",
            "jetons_par_ticket": stats_jetons,
            "par_longueur": resultats,
            "par_nombre_de_fils": fils,
            "machine": "processeur de developpement, torch CPU, un ticket a la fois",
        }, f, ensure_ascii=False, indent=2)
    print("\necrit : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
