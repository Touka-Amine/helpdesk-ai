# -*- coding: utf-8 -*-
"""L'ecart entre entree mesuree et entree servable tient-il sur plusieurs tirages ?

`camembert_servable.py` mesure sur le seul tirage de graine 42 et trouve que la
configuration reellement servie (classification inconnue, fixee a « demande »)
fait MIEUX que la configuration publiee. Sur 355 tickets de test et 20 tickets
de securite, un tel ecart peut n'etre qu'un hasard de tirage.

Ce script rejoue la comparaison sur dix decoupages differents. Il ne change ni
le modele, ni les regles, ni le seuil : seule la graine du decoupage varie. Le
modele n'est pas re-entraine, donc les titres de test d'une graine donnee ont pu
servir a son entrainement d'origine — ces chiffres ne valent pas comme mesure
absolue de performance. Ils valent comme comparaison appariee : les deux
variantes voient exactement les memes tickets, et c'est leur ECART qui est lu.

Sortie : metrics/camembert_servable_robustesse.json
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

from sklearn.metrics import f1_score, recall_score
from sklearn.model_selection import StratifiedShuffleSplit

from models.heuristics import apply_heuristics  # noqa: E402

CSV = os.path.join(RACINE, "data", "processed", "HelpDesk1.csv")
ADAPTATEUR = os.path.join(RACINE, "models", "camembert_lora_adapter")
SORTIE = os.path.join(RACINE, "metrics", "camembert_servable_robustesse.json")

GRAINES = [42, 1, 7, 13, 21, 55, 77, 101, 202, 303]
TEST_SIZE = 0.2
SEUIL = 0.6
MAX_LEN = 128
CLASSIFICATION_PAR_DEFAUT = "demande"


def corps_du_texte(ligne):
    enrichi = str(ligne["text_enriched"])
    prefixe = "type %s priorite %s " % (ligne["classification_simple"],
                                        ligne["priorite_simple"])
    return enrichi[len(prefixe):] if enrichi.startswith(prefixe) else enrichi


def main():
    df = pd.read_csv(CSV)
    classes = sorted(df["Catégorie"].unique())
    df["_corps"] = [corps_du_texte(l) for _, l in df.iterrows()]
    df["_brut"] = df["Titre"].fillna("") + " " + df["Description"].fillna("")

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
            for i in range(0, len(textes), 64):
                lot = tok(textes[i:i + 64], padding="max_length", truncation=True,
                          max_length=MAX_LEN, return_tensors="pt").to(device)
                out.append(torch.softmax(modele(**lot).logits, dim=-1).cpu().numpy())
        return np.vstack(out)

    # Les deux entrees sont calculees une fois sur tout le corpus : le decoupage
    # ne fait ensuite que selectionner des lignes.
    txt_a = ["type %s priorite %s %s" % (l["classification_simple"], l["priorite_simple"], l["_corps"])
             for _, l in df.iterrows()]
    txt_b = ["type %s priorite %s %s" % (CLASSIFICATION_PAR_DEFAUT, l["priorite_simple"], l["_corps"])
             for _, l in df.iterrows()]
    print("inference sur %d tickets, deux variantes..." % len(df))
    proba_a, proba_b = inferer(txt_a), inferer(txt_b)
    arr = np.array(classes)
    pred_a, conf_a = arr[proba_a.argmax(1)], proba_a.max(1)
    pred_b, conf_b = arr[proba_b.argmax(1)], proba_b.max(1)

    regles_a = np.array([apply_heuristics(t, p, float(c), threshold=SEUIL)["categorie"]
                         for t, p, c in zip(df["_brut"], pred_a, conf_a)])
    regles_b = np.array([apply_heuristics(t, p, float(c), threshold=SEUIL)["categorie"]
                         for t, p, c in zip(df["_brut"], pred_b, conf_b)])

    titres = df.groupby("Titre")["Catégorie"].first().reset_index()
    lignes = []
    print("\n%-7s %10s %10s %9s %12s %12s %9s"
          % ("graine", "F1 publie", "F1 servi", "ecart", "rapp.Sec pub", "rapp.Sec ser", "ecart"))
    print("-" * 78)
    for g in GRAINES:
        sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=g)
        _, te = next(sss.split(titres["Titre"], titres["Catégorie"]))
        t_test = set(titres.iloc[te]["Titre"])
        m = df["Titre"].isin(t_test).values
        y = df.loc[m, "Catégorie"].values
        fa = f1_score(y, regles_a[m], average="macro", labels=classes, zero_division=0)
        fb = f1_score(y, regles_b[m], average="macro", labels=classes, zero_division=0)
        ra = recall_score(y, regles_a[m], labels=["Sécurité"], average="macro", zero_division=0)
        rb = recall_score(y, regles_b[m], labels=["Sécurité"], average="macro", zero_division=0)
        lignes.append({"graine": g, "tickets_test": int(m.sum()),
                       "f1_publie": round(float(fa), 4), "f1_servable": round(float(fb), 4),
                       "ecart_f1": round(float(fb - fa), 4),
                       "rappel_securite_publie": round(float(ra), 4),
                       "rappel_securite_servable": round(float(rb), 4)})
        print("%-7d %10.4f %10.4f %+9.4f %12.4f %12.4f %+9.4f"
              % (g, fa, fb, fb - fa, ra, rb, rb - ra))

    ecarts = [l["ecart_f1"] for l in lignes]
    f1_s = [l["f1_servable"] for l in lignes]
    rs_s = [l["rappel_securite_servable"] for l in lignes]
    resume = {
        "ecart_f1_median": round(float(np.median(ecarts)), 4),
        "ecart_f1_min": round(float(np.min(ecarts)), 4),
        "ecart_f1_max": round(float(np.max(ecarts)), 4),
        "tirages_ou_le_servable_fait_mieux": int(sum(1 for e in ecarts if e > 0)),
        "tirages": len(GRAINES),
        "f1_servable_median": round(float(np.median(f1_s)), 4),
        "f1_servable_min": round(float(np.min(f1_s)), 4),
        "rappel_securite_servable_median": round(float(np.median(rs_s)), 4),
        "rappel_securite_servable_min": round(float(np.min(rs_s)), 4),
        "tirages_au_dessus_de_0_85": int(sum(1 for v in f1_s if v >= 0.85)),
        "tirages_rappel_securite_au_dessus_de_0_70": int(sum(1 for v in rs_s if v >= 0.70)),
    }
    print("\nmediane de l'ecart : %+0.4f   le servable fait mieux sur %d tirages sur %d"
          % (resume["ecart_f1_median"], resume["tirages_ou_le_servable_fait_mieux"], len(GRAINES)))
    print("F1 servable : mediane %.4f, minimum %.4f, au-dessus de 0,85 sur %d tirages sur %d"
          % (resume["f1_servable_median"], resume["f1_servable_min"],
             resume["tirages_au_dessus_de_0_85"], len(GRAINES)))
    print("rappel Securite servable : mediane %.4f, minimum %.4f, au-dessus de 0,70 sur %d tirages sur %d"
          % (resume["rappel_securite_servable_median"], resume["rappel_securite_servable_min"],
             resume["tirages_rappel_securite_au_dessus_de_0_70"], len(GRAINES)))

    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "avertissement": ("Le modele n'est pas re-entraine par tirage : seules les graines 42 "
                              "donnent un jeu de test entierement inedit. Ces chiffres mesurent la "
                              "STABILITE DE L'ECART entre les deux entrees, non la performance absolue."),
            "graines": GRAINES, "seuil_regles": SEUIL,
            "par_tirage": lignes, "resume": resume,
        }, f, ensure_ascii=False, indent=2)
    print("\necrit : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
