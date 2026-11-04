# -*- coding: utf-8 -*-
"""La validation tiree au hasard a-t-elle fausse le modele publie ?

La remarque
-----------
L'encadrant releve que la validation de CamemBERT est tiree au hasard alors que
le test est separe par groupes de titres. Verification faite, c'est exact :
le carnet `05_camembert_finetuning.ipynb` decoupe train et test par titre, puis
preleve la validation par

    ds_train.train_test_split(test_size=0.1, seed=RS)

c'est-a-dire ligne a ligne. Le corpus comptant 58 titres repetes une trentaine
de fois chacun, le meme scenario se retrouve des deux cotes : la validation
contient des quasi-doublons de l'entrainement.

Ce que cela touche, et ce que cela ne touche pas
-------------------------------------------------
Le jeu de TEST, lui, reste propre : aucun de ses titres n'apparait a
l'entrainement. La fuite n'affecte donc pas directement le 0,8343 publie, elle
affecte la PROCEDURE qui a choisi l'epoque : `load_best_model_at_end` avec
`metric_for_best_model='f1_macro'` retient l'epoque la meilleure SUR LA
VALIDATION. Si ce signal est optimiste et mal ordonne, l'epoque retenue n'est
pas la bonne.

Reste a savoir si, en pratique, cela change quelque chose. C'est une question
empirique, et ce script y repond plutot que de la trancher par le raisonnement.

Le protocole
------------
Deux entrainements, identiques en tout sauf la facon de prelever la validation :

  A  « au hasard »   ligne a ligne, comme le carnet
  B  « par titre »   aucun titre commun entre entrainement et validation

Pour chacun : le F1-macro de validation a chaque epoque, l'epoque retenue, et
surtout le F1-macro obtenu sur le MEME jeu de test propre. Si les deux
convergent sur le test, le chiffre publie tient et le defaut est de methode. Si
elles divergent, le chiffre publie doit changer.

Sortie : metrics/validation_camembert.json
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

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "src"))

from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupShuffleSplit, StratifiedShuffleSplit

from models.heuristics import apply_heuristics  # noqa: E402

CSV = os.path.join(RACINE, "data", "processed", "HelpDesk1.csv")
SORTIE = os.path.join(RACINE, "metrics", "validation_camembert.json")

GRAINE = 42
TEST_SIZE = 0.2
PART_VALIDATION = 0.1
MAX_LEN = 128          # celle du carnet
SEUIL_REGLES = 0.6
CLASSES = ["Applicatifs", "Backup", "Communication", "Infrastructure",
           "Microsoft", "Réseau", "Système", "Sécurité"]


def decoupage_experiences(df):
    """Le decoupage du chapitre 4 : stratifie sur les titres, graine 42."""
    titres = df.groupby("Titre")["Catégorie"].first().reset_index()
    sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=GRAINE)
    tr, te = next(sss.split(titres["Titre"], titres["Catégorie"]))
    t_train = set(titres.iloc[tr]["Titre"])
    t_test = set(titres.iloc[te]["Titre"])
    assert not (t_train & t_test)
    return (df[df["Titre"].isin(t_train)].reset_index(drop=True),
            df[df["Titre"].isin(t_test)].reset_index(drop=True))


def prelever_validation(train, mode):
    """Retourne (entrainement, validation) selon le mode demande."""
    if mode == "au_hasard":
        # Exactement ce que fait le carnet : un tirage ligne a ligne.
        melange = train.sample(frac=1.0, random_state=GRAINE).reset_index(drop=True)
        n_val = int(round(PART_VALIDATION * len(melange)))
        return melange.iloc[n_val:].reset_index(drop=True), melange.iloc[:n_val].reset_index(drop=True)
    gss = GroupShuffleSplit(n_splits=1, test_size=PART_VALIDATION, random_state=GRAINE)
    i_tr, i_va = next(gss.split(train, groups=train["Titre"]))
    return train.iloc[i_tr].reset_index(drop=True), train.iloc[i_va].reset_index(drop=True)


def entrainer(train, val, test, epochs):
    """Entraine comme le carnet, et rend l'histoire de la validation + le test."""
    import torch
    from datasets import Dataset
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                              EarlyStoppingCallback, Trainer, TrainingArguments, set_seed)

    set_seed(GRAINE)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    label2id = {c: i for i, c in enumerate(CLASSES)}
    tok = AutoTokenizer.from_pretrained("camembert-base")

    def jeu(df):
        d = Dataset.from_dict({"text": df["text_enriched"].fillna("").tolist(),
                               "labels": [label2id[c] for c in df["Catégorie"]]})
        return d.map(lambda b: tok(b["text"], truncation=True, max_length=MAX_LEN,
                                   padding="max_length"), batched=True)

    modele = AutoModelForSequenceClassification.from_pretrained(
        "camembert-base", num_labels=len(CLASSES), torch_dtype=torch.float32,
        ignore_mismatched_sizes=True)
    modele = get_peft_model(modele, LoraConfig(
        task_type=TaskType.SEQ_CLS, r=8, lora_alpha=16, lora_dropout=0.1,
        target_modules=["query", "value"], bias="none", inference_mode=False))

    def metriques(p):
        pred = np.argmax(p.predictions, axis=1)
        return {"f1_macro": f1_score(p.label_ids, pred, average="macro",
                                     labels=list(range(len(CLASSES))), zero_division=0),
                "accuracy": accuracy_score(p.label_ids, pred)}

    args = TrainingArguments(
        output_dir=os.path.join(RACINE, "models", "_validation_travail"),
        num_train_epochs=epochs, per_device_train_batch_size=16,
        per_device_eval_batch_size=32, learning_rate=2e-4, warmup_ratio=0.1,
        weight_decay=0.01, lr_scheduler_type="cosine", fp16=False,
        gradient_checkpointing=(device == "cuda"),
        eval_strategy="epoch", save_strategy="epoch", save_total_limit=1,
        load_best_model_at_end=True, metric_for_best_model="f1_macro",
        greater_is_better=True, logging_strategy="no", report_to="none",
        seed=GRAINE, dataloader_pin_memory=False, disable_tqdm=True)
    trainer = Trainer(model=modele, args=args, train_dataset=jeu(train),
                      eval_dataset=jeu(val), compute_metrics=metriques,
                      callbacks=[EarlyStoppingCallback(early_stopping_patience=3)])
    trainer.train()

    histoire = [{"epoque": round(e["epoch"], 2), "f1_macro": round(e["eval_f1_macro"], 4)}
                for e in trainer.state.log_history if "eval_f1_macro" in e]
    meilleure = max(histoire, key=lambda h: h["f1_macro"]) if histoire else None

    modele.eval()
    textes = test["text_enriched"].fillna("").tolist()
    brut = (test["Titre"].fillna("") + " " + test["Description"].fillna("")).tolist()
    y = test["Catégorie"].tolist()
    sorties = []
    with torch.no_grad():
        for i in range(0, len(textes), 32):
            e = tok(textes[i:i + 32], truncation=True, max_length=MAX_LEN,
                    padding="max_length", return_tensors="pt").to(modele.device)
            sorties.append(torch.softmax(modele(**e).logits, dim=-1).cpu().numpy())
    proba = np.vstack(sorties)
    arr = np.array(CLASSES)
    pred, conf = arr[proba.argmax(1)], proba.max(1)
    avec = [apply_heuristics(t, p, float(c), threshold=SEUIL_REGLES)["categorie"]
            for t, p, c in zip(brut, pred, conf)]
    del modele
    torch.cuda.empty_cache()

    return {
        "histoire_validation": histoire,
        "epoques_evaluees": len(histoire),
        "meilleure_epoque": meilleure,
        "test_f1_macro_seul": round(float(f1_score(y, pred, average="macro",
                                                   labels=CLASSES, zero_division=0)), 4),
        "test_f1_macro_avec_regles": round(float(f1_score(y, avec, average="macro",
                                                          labels=CLASSES, zero_division=0)), 4),
        "test_exactitude_avec_regles": round(float(accuracy_score(y, avec)), 4),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--epochs", type=int, default=10)
    a = ap.parse_args()

    df = pd.read_csv(CSV)
    train_complet, test = decoupage_experiences(df)
    print("protocole des experiences : %d tickets d'entrainement, %d de test"
          % (len(train_complet), len(test)))

    resultats = {}
    for mode, libelle in (("au_hasard", "validation tiree ligne a ligne, comme le carnet"),
                          ("par_titre", "validation separee par groupe de titres")):
        train, val = prelever_validation(train_complet, mode)
        communs = set(train["Titre"]) & set(val["Titre"])
        print("\n--- %s ---" % libelle)
        print("  entrainement %d / validation %d" % (len(train), len(val)))
        print("  titres communs entre entrainement et validation : %d sur %d"
              % (len(communs), val["Titre"].nunique()))
        r = entrainer(train, val, test, a.epochs)
        r.update({"libelle": libelle,
                  "titres_communs_train_validation": len(communs),
                  "titres_de_validation": int(val["Titre"].nunique()),
                  "n_entrainement": len(train), "n_validation": len(val)})
        resultats[mode] = r
        print("  F1-macro de validation a la meilleure epoque : %.4f (epoque %s)"
              % (r["meilleure_epoque"]["f1_macro"], r["meilleure_epoque"]["epoque"]))
        print("  F1-macro sur le TEST, avec regles              : %.4f"
              % r["test_f1_macro_avec_regles"])

    a_, b_ = resultats["au_hasard"], resultats["par_titre"]
    ecart_val = b_["meilleure_epoque"]["f1_macro"] - a_["meilleure_epoque"]["f1_macro"]
    ecart_test = b_["test_f1_macro_avec_regles"] - a_["test_f1_macro_avec_regles"]
    print("\nce que la fuite gonfle en validation : %+.4f" % (-ecart_val))
    print("ce qu'elle change sur le test        : %+.4f" % ecart_test)
    verdict = ("Le chiffre publie tient : la fuite a fausse le signal de selection, "
               "pas la mesure finale." if abs(ecart_test) < 0.02 else
               "Le chiffre publie bouge : la selection d'epoque a eu un effet mesurable.")
    print(verdict)

    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "remarque": ("Validation de CamemBERT tiree au hasard alors que le test est "
                         "separe par groupes de titres."),
            "protocole": "decoupage des experiences, graine 42 ; seul le prelevement "
                         "de la validation change entre les deux bras",
            "max_length": MAX_LEN, "epochs_demandees": a.epochs,
            "resultats": resultats,
            "ecart_validation_du_a_la_fuite": round(float(-ecart_val), 4),
            "ecart_sur_le_test": round(float(ecart_test), 4),
            "verdict": verdict,
        }, f, ensure_ascii=False, indent=2)
    print("\necrit : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
