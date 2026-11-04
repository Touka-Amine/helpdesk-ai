# -*- coding: utf-8 -*-
"""Choisit la force de ponderation par validation croisee, sans ouvrir le jeu gele.

Le probleme que ce script resout
---------------------------------
Deux configurations se tiennent :

  sans ponderation   F1 sur les classes presentes 0,8299  rappel Securite 0,6061
  ponderation pleine F1 sur les classes presentes 0,6985  rappel Securite 1,0000

La ponderation sauve la categorie dont l'erreur coute le plus cher et sacrifie
une categorie frequente. Choisir entre les deux en regardant ces chiffres-la
reviendrait a regler le modele sur le jeu qui sert a le juger : le score
cesserait de mesurer la generalisation. C'est exactement la faute que l'audit du
2026-08-22 avait relevee sur les regles metier.

La validation simple ne suffit pas non plus : elle ne compte que 156 tickets
repartis sur cinq titres, et un seul scenario y deplace une classe entiere. Elle
a d'ailleurs classe la ponderation pleine en tete, ce que le jeu gele contredit.

D'ou une validation croisee PAR GROUPE DE TITRES sur le seul jeu d'entrainement :
chaque configuration est evaluee sur plusieurs decoupages, et c'est la moyenne
qui decide. Le jeu gele n'est pas lu.

La force de ponderation
------------------------
Le poids d'une categorie vaut (N / (k * n_c)) ** alpha.
  alpha = 0    aucune ponderation
  alpha = 0.5  racine carree : corrige le desequilibre sans l'inverser
  alpha = 1    ponderation pleine, celle qui a effondre Reseau

Sortie : metrics/selection_camembert.json
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RACINE, "src"))

from sklearn.metrics import f1_score, recall_score
from sklearn.model_selection import GroupKFold

from models.heuristics import apply_heuristics  # noqa: E402

TRAIN = os.path.join(RACINE, "data", "splits", "train.csv")
SORTIE = os.path.join(RACINE, "metrics", "selection_camembert.json")

GRAINE = 42
MAX_LEN = 64
SEUIL_REGLES = 0.6
CLASSES = ["Applicatifs", "Backup", "Communication", "Infrastructure",
           "Microsoft", "Réseau", "Système", "Sécurité"]
ALPHAS = [0.0, 0.5, 1.0]
N_PLIS = 3


def entree_de_production(df):
    corps = []
    for _, l in df.iterrows():
        e = str(l["text_enriched"])
        p = "type %s priorite %s " % (l["classification_simple"], l["priorite_simple"])
        corps.append(e[len(p):] if e.startswith(p) else e)
    return ["priorite %s %s" % (p, c) for p, c in zip(df["priorite_simple"], corps)]


def entrainer_et_predire(train, eval_, alpha, epochs, device):
    import torch
    from datasets import Dataset
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                              Trainer, TrainingArguments, set_seed)

    set_seed(GRAINE)
    label2id = {c: i for i, c in enumerate(CLASSES)}
    tok = AutoTokenizer.from_pretrained("camembert-base")

    def jeu(df):
        d = Dataset.from_dict({"text": entree_de_production(df),
                               "labels": [label2id[c] for c in df["Catégorie"]]})
        return d.map(lambda b: tok(b["text"], truncation=True, max_length=MAX_LEN,
                                   padding="max_length"), batched=True)

    modele = AutoModelForSequenceClassification.from_pretrained(
        "camembert-base", num_labels=len(CLASSES), torch_dtype=torch.float32,
        ignore_mismatched_sizes=True)
    modele = get_peft_model(modele, LoraConfig(
        task_type=TaskType.SEQ_CLS, r=8, lora_alpha=16, lora_dropout=0.1,
        target_modules=["query", "value"], bias="none", inference_mode=False))

    poids = None
    if alpha > 0:
        compte = train["Catégorie"].value_counts()
        brut = [len(train) / (len(CLASSES) * max(compte.get(c, 0), 1)) for c in CLASSES]
        poids = torch.tensor([b ** alpha for b in brut], dtype=torch.float32).to(device)

    class Pondere(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False, **kw):
            y = inputs.pop("labels")
            s = model(**inputs)
            perte = torch.nn.functional.cross_entropy(
                s.logits.view(-1, len(CLASSES)), y.view(-1), weight=poids)
            return (perte, s) if return_outputs else perte

    args = TrainingArguments(
        output_dir=os.path.join(RACINE, "models", "_selection_travail"),
        num_train_epochs=epochs, per_device_train_batch_size=16,
        per_device_eval_batch_size=32, learning_rate=2e-4, warmup_ratio=0.1,
        weight_decay=0.01, lr_scheduler_type="cosine", fp16=False,
        gradient_checkpointing=(device == "cuda"), eval_strategy="no",
        save_strategy="no", logging_strategy="no", report_to="none",
        seed=GRAINE, dataloader_pin_memory=False, disable_tqdm=True)
    (Pondere if poids is not None else Trainer)(
        model=modele, args=args, train_dataset=jeu(train)).train()

    modele.eval()
    textes = entree_de_production(eval_)
    sorties = []
    with torch.no_grad():
        for i in range(0, len(textes), 32):
            e = tok(textes[i:i + 32], truncation=True, max_length=MAX_LEN,
                    padding="max_length", return_tensors="pt").to(modele.device)
            sorties.append(torch.softmax(modele(**e).logits, dim=-1).cpu().numpy())
    proba = np.vstack(sorties)
    del modele
    torch.cuda.empty_cache()
    arr = np.array(CLASSES)
    return arr[proba.argmax(1)], proba.max(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--epochs", type=int, default=8)
    a = ap.parse_args()

    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    train = pd.read_csv(TRAIN)
    gkf = GroupKFold(n_splits=N_PLIS)
    plis = list(gkf.split(train, groups=train["Titre"]))
    print("validation croisee %d plis par groupe de titres, sur %d tickets d'entrainement"
          % (N_PLIS, len(train)))
    print("le jeu de test gele n'est pas lu.\n")

    resultats = {}
    for alpha in ALPHAS:
        mesures = []
        for n, (i_tr, i_va) in enumerate(plis, 1):
            tr, va = train.iloc[i_tr], train.iloc[i_va]
            pred, conf = entrainer_et_predire(tr, va, alpha, a.epochs, device)
            brut = (va["Titre"].fillna("") + " " + va["Description"].fillna("")).tolist()
            avec = [apply_heuristics(t, p, float(c), threshold=SEUIL_REGLES)["categorie"]
                    for t, p, c in zip(brut, pred, conf)]
            y = va["Catégorie"].tolist()
            presentes = sorted(set(y))
            m = {
                "f1_presentes": round(float(f1_score(y, avec, average="macro",
                                                     labels=presentes, zero_division=0)), 4),
                "rappel_securite": (round(float(recall_score(y, avec, labels=["Sécurité"],
                                                             average="macro", zero_division=0)), 4)
                                    if "Sécurité" in presentes else None),
                "categories_au_pli": len(presentes),
            }
            mesures.append(m)
            print("  alpha %.1f  pli %d/%d : F1 %.4f  rappel Securite %s"
                  % (alpha, n, N_PLIS, m["f1_presentes"],
                     "n/a" if m["rappel_securite"] is None else "%.4f" % m["rappel_securite"]))
        f1s = [m["f1_presentes"] for m in mesures]
        secs = [m["rappel_securite"] for m in mesures if m["rappel_securite"] is not None]
        resultats[str(alpha)] = {
            "plis": mesures,
            "f1_moyen": round(float(np.mean(f1s)), 4),
            "f1_ecart_type": round(float(np.std(f1s)), 4),
            "rappel_securite_moyen": round(float(np.mean(secs)), 4) if secs else None,
        }
        print("  alpha %.1f  MOYENNE F1 %.4f (ecart-type %.4f)  rappel Securite %s\n"
              % (alpha, resultats[str(alpha)]["f1_moyen"], resultats[str(alpha)]["f1_ecart_type"],
                 "n/a" if not secs else "%.4f" % resultats[str(alpha)]["rappel_securite_moyen"]))

    # Le critere est pose avant de regarder : la configuration retenue est celle
    # dont le rappel Securite moyen atteint 0,70, et parmi celles-la, celle dont
    # le F1 moyen est le plus haut. ENF-03 n'est pas negociable contre ENF-02 :
    # une alerte de securite ratee ne se rattrape pas.
    eligibles = {k: v for k, v in resultats.items()
                 if v["rappel_securite_moyen"] is not None and v["rappel_securite_moyen"] >= 0.70}
    if eligibles:
        retenu = max(eligibles, key=lambda k: eligibles[k]["f1_moyen"])
        motif = "rappel Securite >= 0,70 et meilleur F1 parmi les eligibles"
    else:
        retenu = max(resultats, key=lambda k: resultats[k]["rappel_securite_moyen"] or 0)
        motif = "aucune configuration n'atteint 0,70 : celle qui s'en approche le plus"
    print("configuration retenue : alpha = %s (%s)" % (retenu, motif))

    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "protocole": "GroupKFold %d plis sur les titres du jeu d'entrainement ; "
                         "le jeu de test gele n'est pas lu" % N_PLIS,
            "epochs": a.epochs, "max_length": MAX_LEN,
            "critere": "rappel Securite moyen >= 0,70, puis meilleur F1 moyen",
            "resultats": resultats,
            "alpha_retenu": float(retenu),
            "motif": motif,
        }, f, ensure_ascii=False, indent=2)
    print("ecrit : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
