# -*- coding: utf-8 -*-
"""CamemBERT est-il servable tel qu'il a ete mesure ?

Le probleme
-----------
Le modele CamemBERT a ete entraine sur `text_enriched`, qui prefixe le texte du
ticket par deux champs :

    type <classification_simple> priorite <priorite_simple> + titre + description

Or au moment ou l'API predit, un ticket vient d'etre depose :

  - `priorite` est saisie par le demandeur : elle EST disponible ;
  - `classification` ne l'est pas. `api/services/ticket_service.py` la fixe a
    DEFAULT_CLASSIFICATION, et `classification_finale` n'est renseignee que plus
    tard, par l'administrateur, pendant le traitement.

Le modele recevrait donc en production une entree differente de celle sur
laquelle il a ete mesure. C'est le meme defaut que la remarque T5 (titre non
transmis), a un autre endroit de la chaine.

Ce script mesure l'ecart, sous le protocole des experiences, sans rien changer
au modele :

  A  enrichissement reel          — ce que le memoire publie
  B  classification forcee a la valeur par defaut, priorite reelle — la production
  C  aucun enrichissement         — borne basse

Sortie : metrics/camembert_servable.json
"""
from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "src"))

from sklearn.metrics import f1_score, recall_score, precision_score, accuracy_score
from sklearn.model_selection import StratifiedShuffleSplit

from models.heuristics import apply_heuristics  # noqa: E402

CSV = os.path.join(RACINE, "data", "processed", "HelpDesk1.csv")
ADAPTATEUR = os.path.join(RACINE, "models", "camembert_lora_adapter")
SORTIE = os.path.join(RACINE, "metrics", "camembert_servable.json")

GRAINE = 42
TEST_SIZE = 0.2
SEUIL = 0.6
MAX_LEN = 128
# Valeur que api/services/ticket_service.py attribue a un ticket qui vient d'etre
# depose : l'administrateur n'a pas encore classe la demande.
CLASSIFICATION_PAR_DEFAUT = "demande"


def decoupage(df):
    titres = df.groupby("Titre")["Catégorie"].first().reset_index()
    sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=GRAINE)
    tr, te = next(sss.split(titres["Titre"], titres["Catégorie"]))
    t_train = set(titres.iloc[tr]["Titre"])
    t_test = set(titres.iloc[te]["Titre"])
    assert not (t_train & t_test)
    return df[df["Titre"].isin(t_test)].reset_index(drop=True)


def corps_du_texte(ligne):
    """`text_enriched` prive de son prefixe « type X priorite Y »."""
    enrichi = str(ligne["text_enriched"])
    prefixe = "type %s priorite %s " % (ligne["classification_simple"],
                                        ligne["priorite_simple"])
    return enrichi[len(prefixe):] if enrichi.startswith(prefixe) else enrichi


def scores(y_vrai, y_pred, classes):
    return {
        "f1_macro": round(float(f1_score(y_vrai, y_pred, average="macro",
                                         labels=classes, zero_division=0)), 4),
        "recall_macro": round(float(recall_score(y_vrai, y_pred, average="macro",
                                                 labels=classes, zero_division=0)), 4),
        "accuracy": round(float(accuracy_score(y_vrai, y_pred)), 4),
        "rappel_securite": round(float(recall_score(
            y_vrai, y_pred, labels=["Sécurité"], average="macro", zero_division=0)), 4),
        "precision_securite": round(float(precision_score(
            y_vrai, y_pred, labels=["Sécurité"], average="macro", zero_division=0)), 4),
        "f1_par_classe": {c: round(float(v), 4) for c, v in zip(
            classes, f1_score(y_vrai, y_pred, average=None, labels=classes, zero_division=0))},
    }


def main():
    df = pd.read_csv(CSV)
    classes = sorted(df["Catégorie"].unique())
    test = decoupage(df)
    y = test["Catégorie"].tolist()
    brut = (test["Titre"].fillna("") + " " + test["Description"].fillna("")).tolist()
    corps = [corps_du_texte(l) for _, l in test.iterrows()]

    variantes = {
        "A_enrichissement_reel": [
            "type %s priorite %s %s" % (l["classification_simple"], l["priorite_simple"], c)
            for (_, l), c in zip(test.iterrows(), corps)],
        "B_production_classification_par_defaut": [
            "type %s priorite %s %s" % (CLASSIFICATION_PAR_DEFAUT, l["priorite_simple"], c)
            for (_, l), c in zip(test.iterrows(), corps)],
        "C_sans_enrichissement": corps,
    }

    import torch
    from peft import PeftModel
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(ADAPTATEUR)
    base = AutoModelForSequenceClassification.from_pretrained(
        "camembert-base", num_labels=len(classes))
    modele = PeftModel.from_pretrained(base, ADAPTATEUR).eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    modele = modele.to(device)

    def inferer(textes):
        out = []
        with torch.no_grad():
            for i in range(0, len(textes), 32):
                lot = tok(textes[i:i + 32], padding="max_length", truncation=True,
                          max_length=MAX_LEN, return_tensors="pt").to(device)
                out.append(torch.softmax(modele(**lot).logits, dim=-1).cpu().numpy())
        return np.vstack(out)

    resultats = {}
    for nom, textes in variantes.items():
        proba = inferer(textes)
        pred = np.array(classes)[proba.argmax(axis=1)]
        conf = proba.max(axis=1)
        avec = [apply_heuristics(t, p, float(c), threshold=SEUIL)["categorie"]
                for t, p, c in zip(brut, pred, conf)]
        resultats[nom] = {
            "camembert_seul": scores(y, pred.tolist(), classes),
            "camembert_et_regles": scores(y, avec, classes),
        }
        print("%-42s seul F1 %.4f   + regles F1 %.4f   rappel Securite %.4f"
              % (nom, resultats[nom]["camembert_seul"]["f1_macro"],
                 resultats[nom]["camembert_et_regles"]["f1_macro"],
                 resultats[nom]["camembert_et_regles"]["rappel_securite"]))

    a = resultats["A_enrichissement_reel"]["camembert_et_regles"]["f1_macro"]
    b = resultats["B_production_classification_par_defaut"]["camembert_et_regles"]["f1_macro"]
    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "protocole": "protocole des experiences, StratifiedShuffleSplit graine 42, 355 tickets de test",
            "question": ("Le champ Classification, present dans l'entree d'entrainement, n'est pas "
                         "connu au moment ou l'API predit. Quel est l'ecart ?"),
            "classification_par_defaut": CLASSIFICATION_PAR_DEFAUT,
            "resultats": resultats,
            "ecart_publie_vs_servable": round(a - b, 4),
        }, f, ensure_ascii=False, indent=2)
    print("\necart entre le chiffre publie et le chiffre servable : %.4f" % (a - b))
    print("ecrit : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
