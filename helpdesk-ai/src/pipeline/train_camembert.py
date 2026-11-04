# -*- coding: utf-8 -*-
"""Entraine CamemBERT + LoRA sur le decoupage du pipeline, pour etre SERVI.

Ce que ce script change par rapport au carnet 05
------------------------------------------------
Le carnet `05_camembert_finetuning.ipynb` a entraine CamemBERT pour comparer des
approches, sur le protocole des experiences. L'adaptateur qu'il a produit reste
en place et les chiffres du chapitre 4 continuent de s'y rapporter. Ce script
produit un AUTRE modele, destine lui a la production, et deux choses l'en
distinguent.

1. LE DECOUPAGE. Il s'entraine sur `data/splits/train.csv` et ne voit jamais le
   jeu de test gele. Les deux jeux de test ne partagent que quatre titres sur
   douze : un modele entraine sur le protocole des experiences a donc vu huit
   des douze scenarios du jeu gele, et tout chiffre qu'il y obtiendrait serait
   contamine. C'est la raison d'etre de ce script.

2. L'ENTREE. Le carnet entraine sur `text_enriched`, qui prefixe le texte par
   « type <classification> priorite <priorite> ». Or `api/services/ticket_service.py`
   fixe la classification a « Demande » pour tout ticket qui vient d'etre depose :
   l'administrateur ne la renseigne que plus tard. Le modele du carnet recevrait
   donc en service une entree qu'il n'a pas connue a l'entrainement. Ici le champ
   est simplement retire. La priorite, elle, est saisie par le demandeur et reste.

3. LA LONGUEUR. 64 jetons au lieu de 128. Le ticket le plus long du corpus en
   compte 48 (metrics/cout_longueur_sequence.json) : les 64 restants etaient du
   rembourrage, et ils coutaient 62 % du temps de calcul.

Protocole d'evaluation
----------------------
  - validation decoupee dans le train PAR TITRE, pour choisir l'epoque sans
    regarder le test ;
  - test = le jeu gele, lu une seule fois, a la fin ;
  - metrique F1-macro, comme pour toutes les decisions du memoire.

Sorties : models/camembert_servi/, metrics/camembert_servi_eval.json

Usage :
    python src/pipeline/train_camembert.py
    python src/pipeline/train_camembert.py --epochs 3        (essai rapide)
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

from sklearn.metrics import accuracy_score, f1_score, recall_score, classification_report
from sklearn.model_selection import GroupShuffleSplit

from models.heuristics import apply_heuristics  # noqa: E402
from pipeline import jeu_gele  # noqa: E402

TRAIN = os.path.join(RACINE, "data", "splits", "train.csv")
TEST = os.path.join(RACINE, "data", "splits", "test.csv")
SORTIE_MODELE = os.path.join(RACINE, "models", "camembert_servi")
SORTIE_METRIQUES = os.path.join(RACINE, "metrics", "camembert_servi_eval.json")

GRAINE = 42
MAX_LEN = 64
SEUIL_REGLES = 0.6
PART_VALIDATION = 0.1
CLASSES = ["Applicatifs", "Backup", "Communication", "Infrastructure",
           "Microsoft", "Réseau", "Système", "Sécurité"]


def entree_de_production(df):
    """L'entree que l'API peut reellement fournir : priorite saisie + texte.

    La classification est volontairement absente : elle n'est pas connue quand
    la prediction est demandee.
    """
    corps = []
    for _, enr in df.iterrows():
        e = str(enr["text_enriched"])
        p = "type %s priorite %s " % (enr["classification_simple"], enr["priorite_simple"])
        corps.append(e[len(p):] if e.startswith(p) else e)
    return ["priorite %s %s" % (p, c) for p, c in zip(df["priorite_simple"], corps)]


def prelever_validation_par_titre(train_complet, part=PART_VALIDATION, graine=GRAINE):
    """Preleve la validation par GROUPE DE TITRES, jamais ligne a ligne.

    C'est la correction de la remarque du 2026-10-09. Un tirage ligne a ligne
    place des lignes du meme titre des deux cotes : la validation mesure alors
    la reconnaissance d'un scenario deja vu, et comme `load_best_model_at_end`
    choisit l'epoque sur elle, un signal fausse commande la selection. Mesure
    faite, l'ecart vaut 0,45 point de F1 de validation
    (`metrics/validation_camembert.json`).

    Cette fonction est au niveau du module pour etre verifiable sans charger
    torch ni transformers : la garde est dans `tests/test_validation_par_titre.py`.
    """
    gss = GroupShuffleSplit(n_splits=1, test_size=part, random_state=graine)
    i_tr, i_va = next(gss.split(train_complet, groups=train_complet["Titre"]))
    train, val = train_complet.iloc[i_tr], train_complet.iloc[i_va]
    fuite = set(train["Titre"]) & set(val["Titre"])
    assert not fuite, "fuite de titre train/validation : %s" % sorted(fuite)[:3]
    return train, val


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--rang", type=int, default=8, help="rang des adaptateurs LoRA")
    ap.add_argument("--ponderer", action="store_true",
                    help="pondere la perte par l'inverse de la frequence des categories")
    ap.add_argument("--sans-test", action="store_true",
                    help="ne touche pas au jeu gele : pour comparer des configurations")
    ap.add_argument("--etiquette", default="", help="nom de la configuration, pour le journal")
    a = ap.parse_args()

    import torch
    from datasets import Dataset
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                              EarlyStoppingCallback, Trainer, TrainingArguments,
                              set_seed)

    set_seed(GRAINE)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("device : %s" % device)

    train_complet = pd.read_csv(TRAIN)
    # Lecture de RAPPORT : l'epoque se choisit sur la validation prelevee par
    # titre, pas ici.
    test = jeu_gele.lire(
        jeu_gele.POUR_RAPPORTER,
        motif="evaluation du transformer servi sur le jeu gele",
        lecteur="src/pipeline/train_camembert.py",
    )
    assert not (set(train_complet["Titre"]) & set(test["Titre"])), "fuite de titre train/test"

    # Validation prelevee dans le train, par titre : choisir l'epoque sur des
    # scenarios que l'entrainement n'a pas vus.
    train, val = prelever_validation_par_titre(train_complet)
    print("train %d (%d titres) / validation %d (%d titres) / test gele %d (%d titres)"
          % (len(train), train["Titre"].nunique(), len(val), val["Titre"].nunique(),
             len(test), test["Titre"].nunique()))

    label2id = {c: i for i, c in enumerate(CLASSES)}
    tok = AutoTokenizer.from_pretrained("camembert-base")

    def jeu(df):
        d = Dataset.from_dict({"text": entree_de_production(df),
                               "labels": [label2id[c] for c in df["Catégorie"]]})
        return d.map(lambda b: tok(b["text"], truncation=True, max_length=MAX_LEN,
                                   padding="max_length"), batched=True)

    ds_train, ds_val = jeu(train), jeu(val)

    modele = AutoModelForSequenceClassification.from_pretrained(
        "camembert-base", num_labels=len(CLASSES),
        id2label={i: c for c, i in label2id.items()}, label2id=label2id,
        torch_dtype=torch.float32, ignore_mismatched_sizes=True)
    modele = get_peft_model(modele, LoraConfig(
        task_type=TaskType.SEQ_CLS, r=a.rang, lora_alpha=2 * a.rang, lora_dropout=0.1,
        target_modules=["query", "value"], bias="none", inference_mode=False))
    modele.print_trainable_parameters()

    def metriques(p):
        pred = np.argmax(p.predictions, axis=1)
        # `labels` explicite : sans lui, la moyenne porterait sur l'union des
        # categories vraies et predites du pli de validation, donc sur un
        # denominateur qui change d'une epoque a l'autre. Le choix de l'epoque
        # cesserait alors d'etre comparable.
        return {"f1_macro": f1_score(p.label_ids, pred, average="macro",
                                     labels=list(range(len(CLASSES))), zero_division=0),
                "accuracy": accuracy_score(p.label_ids, pred)}

    # Perte ponderee : sur un corpus ou la categorie la plus frequente depasse la
    # plus rare d'un facteur 5,93, une perte uniforme laisse le modele abandonner
    # les categories rares. La ponderation leur rend le poids que le F1-macro leur
    # donne deja dans l'evaluation.
    poids = None
    if a.ponderer:
        compte = train["Catégorie"].value_counts()
        poids = torch.tensor([len(train) / (len(CLASSES) * max(compte.get(c, 0), 1))
                              for c in CLASSES], dtype=torch.float32).to(device)
        print("ponderation des categories : %s"
              % {c: round(float(w), 2) for c, w in zip(CLASSES, poids)})

    class EntraineurPondere(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False, **kw):
            etiquettes = inputs.pop("labels")
            sorties = model(**inputs)
            perte = torch.nn.functional.cross_entropy(
                sorties.logits.view(-1, len(CLASSES)), etiquettes.view(-1), weight=poids)
            return (perte, sorties) if return_outputs else perte

    args = TrainingArguments(
        output_dir=os.path.join(RACINE, "models", "_camembert_servi_travail"),
        num_train_epochs=a.epochs, per_device_train_batch_size=a.batch,
        per_device_eval_batch_size=32, learning_rate=a.lr, warmup_ratio=0.1,
        weight_decay=0.01, lr_scheduler_type="cosine", fp16=False,
        gradient_checkpointing=(device == "cuda"),
        eval_strategy="epoch", save_strategy="epoch", save_total_limit=1,
        load_best_model_at_end=True, metric_for_best_model="f1_macro",
        greater_is_better=True, logging_steps=25, report_to="none", seed=GRAINE,
        dataloader_pin_memory=False)
    classe_entraineur = EntraineurPondere if a.ponderer else Trainer
    trainer = classe_entraineur(model=modele, args=args, train_dataset=ds_train,
                                eval_dataset=ds_val, compute_metrics=metriques,
                                callbacks=[EarlyStoppingCallback(early_stopping_patience=3)])
    trainer.train()
    val_scores = trainer.evaluate()
    print("[%s] validation : F1-macro %.4f   exactitude %.4f"
          % (a.etiquette or "config", val_scores["eval_f1_macro"], val_scores["eval_accuracy"]))

    if a.sans_test:
        # Le jeu gele n'est pas ouvert : cette execution ne sert qu'a comparer des
        # configurations entre elles. Le modele n'est pas conserve non plus.
        print("--sans-test : le jeu gele n'a pas ete lu, rien n'est ecrit.")
        return 0

    # ── Le jeu gele, lu une seule fois ───────────────────────────────────────
    modele.eval()
    textes = entree_de_production(test)
    brut = (test["Titre"].fillna("") + " " + test["Description"].fillna("")).tolist()
    y = test["Catégorie"].tolist()
    presentes = sorted(set(y))
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

    def sc(p):
        return {
            "f1_macro_huit_classes": round(float(f1_score(y, p, average="macro",
                                                          labels=CLASSES, zero_division=0)), 4),
            "f1_macro_classes_presentes": round(float(f1_score(y, p, average="macro",
                                                               labels=presentes, zero_division=0)), 4),
            "accuracy": round(float(accuracy_score(y, p)), 4),
            "rappel_securite": round(float(recall_score(y, p, labels=["Sécurité"],
                                                        average="macro", zero_division=0)), 4),
            "f1_par_classe": {c: round(float(v), 4) for c, v in zip(
                CLASSES, f1_score(y, p, average=None, labels=CLASSES, zero_division=0))},
        }

    resultat = {"camembert_seul": sc(pred.tolist()), "camembert_et_regles": sc(avec)}
    print("\njeu de test gele, %d tickets, %d categories presentes" % (len(test), len(presentes)))
    for nom, r in resultat.items():
        print("  %-22s F1(8 classes) %.4f   F1(presentes) %.4f   rappel Securite %.4f"
              % (nom, r["f1_macro_huit_classes"], r["f1_macro_classes_presentes"],
                 r["rappel_securite"]))
    print()
    print(classification_report(y, avec, labels=presentes, zero_division=0))

    os.makedirs(SORTIE_MODELE, exist_ok=True)
    modele.save_pretrained(SORTIE_MODELE)
    tok.save_pretrained(SORTIE_MODELE)
    with io.open(os.path.join(SORTIE_MODELE, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump({"base": "camembert-base", "lora_r": 8, "lora_alpha": 16,
                   "max_length": MAX_LEN, "classes": CLASSES,
                   "entree": "priorite <priorite_simple> + titre + description, sans classification",
                   "decoupage": "data/splits/train.csv, jeu de test gele jamais vu",
                   "epochs_demandees": a.epochs, "learning_rate": a.lr}, f,
                  ensure_ascii=False, indent=2)

    with io.open(SORTIE_METRIQUES, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "protocole": "decoupage du pipeline, jeu de test GELE (data/splits/test.csv)",
            "entree": "priorite saisie + titre + description, classification absente",
            "max_length": MAX_LEN,
            "train": len(train), "validation": len(val), "taille_test": len(test),
            "classes_presentes_au_test": presentes,
            "validation_f1_macro": round(float(val_scores["eval_f1_macro"]), 4),
            "test": resultat,
        }, f, ensure_ascii=False, indent=2)
    print("\necrit : %s" % SORTIE_MODELE)
    print("ecrit : %s" % SORTIE_METRIQUES)
    return 0


if __name__ == "__main__":
    sys.exit(main())
