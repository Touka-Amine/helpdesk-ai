# -*- coding: utf-8 -*-
"""Peut-on servir CamemBERT ? Mesure de qualite et de cout, sur le jeu gele.

L'arbitrage d'origine
---------------------
Le memoire explique que le meilleur modele mesure (CamemBERT + regles) n'est pas
celui qui est servi, et donne pour motif le cout d'inference : 325,8 ms par
ticket contre 5,0 ms pour la chaine lexicale. L'exigence ENF-01 plafonne la
reponse a 300 ms au quatre-vingt-quinzieme centile, et la chaine complete est
deja mesuree a 330 ms. Servir CamemBERT tel quel ferait echouer ENF-01 plus
lourdement encore.

Ce que ce script mesure
-----------------------
1. QUALITE sur le jeu de test GELE du pipeline, celui qui juge la production,
   avec l'entree reellement disponible au moment de la prediction (la
   classification n'est pas connue : voir scripts/camembert_servable.py).
2. COUT du meme modele exporte en ONNX puis quantifie en entiers 8 bits, qui est
   la facon habituelle de faire tenir un transformeur sur un processeur.
3. FIDELITE de la version quantifiee : si elle ne predit pas la meme chose, le
   gain de temps ne vaut rien.

Aucune decision n'est prise ici. Le script produit les trois chiffres qui
permettent de la prendre.

Sorties : models/camembert_onnx/, metrics/arbitrage_modele_servi.json
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

from sklearn.metrics import accuracy_score, f1_score, recall_score

from models.heuristics import apply_heuristics  # noqa: E402
from pipeline import jeu_gele  # noqa: E402

TEST = os.path.join(RACINE, "data", "splits", "test.csv")
ADAPTATEUR = os.path.join(RACINE, "models", "camembert_lora_adapter")
DOSSIER_ONNX = os.path.join(RACINE, "models", "camembert_onnx")
SORTIE = os.path.join(RACINE, "metrics", "arbitrage_modele_servi.json")

SEUIL = 0.6
MAX_LEN = 128
CLASSIFICATION_PAR_DEFAUT = "demande"
N_CHRONO = 40


def corps_du_texte(ligne):
    enrichi = str(ligne["text_enriched"])
    prefixe = "type %s priorite %s " % (ligne["classification_simple"], ligne["priorite_simple"])
    return enrichi[len(prefixe):] if enrichi.startswith(prefixe) else enrichi


def scores(y, p, classes, presentes):
    return {
        "f1_macro_classes_presentes": round(float(f1_score(
            y, p, average="macro", labels=presentes, zero_division=0)), 4),
        "f1_macro_huit_classes": round(float(f1_score(
            y, p, average="macro", labels=classes, zero_division=0)), 4),
        "accuracy": round(float(accuracy_score(y, p)), 4),
        "rappel_securite": round(float(recall_score(
            y, p, labels=["Sécurité"], average="macro", zero_division=0)), 4),
    }


def main():
    import torch
    from peft import PeftModel
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    # Lecture qui TRANCHE : cet arbitrage choisit la configuration servie.
    # Elle s'inscrit donc au journal du jeu gele et consomme son budget.
    test = jeu_gele.lire(
        jeu_gele.POUR_DECIDER,
        motif="arbitrage de la configuration du modele servi",
        lecteur="scripts/arbitrage_modele_servi.py",
    )
    classes = ["Applicatifs", "Backup", "Communication", "Infrastructure",
               "Microsoft", "Réseau", "Système", "Sécurité"]
    presentes = sorted(test["Catégorie"].unique())
    y = test["Catégorie"].tolist()
    brut = (test["Titre"].fillna("") + " " + test["Description"].fillna("")).tolist()
    entree = ["type %s priorite %s %s" % (CLASSIFICATION_PAR_DEFAUT, l["priorite_simple"],
                                          corps_du_texte(l))
              for _, l in test.iterrows()]
    print("jeu de test gele : %d tickets, %d categories presentes sur 8"
          % (len(test), len(presentes)))

    tok = AutoTokenizer.from_pretrained(ADAPTATEUR)
    base = AutoModelForSequenceClassification.from_pretrained("camembert-base",
                                                              num_labels=len(classes))
    # LoRA fusionne dans les poids de base : le modele exporte est un CamemBERT
    # ordinaire, sans dependance a peft au moment de servir.
    modele = PeftModel.from_pretrained(base, ADAPTATEUR).merge_and_unload().eval()

    def inferer_torch(textes, device="cpu", lot=32):
        m = modele.to(device)
        out = []
        with torch.no_grad():
            for i in range(0, len(textes), lot):
                e = tok(textes[i:i + lot], padding="max_length", truncation=True,
                        max_length=MAX_LEN, return_tensors="pt").to(device)
                out.append(torch.softmax(m(**e).logits, dim=-1).cpu().numpy())
        return np.vstack(out)

    # ── 1. Qualite ───────────────────────────────────────────────────────────
    proba = inferer_torch(entree)
    arr = np.array(classes)
    pred, conf = arr[proba.argmax(1)], proba.max(1)
    avec = [apply_heuristics(t, p, float(c), threshold=SEUIL)["categorie"]
            for t, p, c in zip(brut, pred, conf)]
    qualite = {
        "camembert_seul": scores(y, pred.tolist(), classes, presentes),
        "camembert_et_regles": scores(y, avec, classes, presentes),
    }
    print("  CamemBERT seul        F1(presentes) %.4f  rappel Securite %.4f"
          % (qualite["camembert_seul"]["f1_macro_classes_presentes"],
             qualite["camembert_seul"]["rappel_securite"]))
    print("  CamemBERT + regles    F1(presentes) %.4f  rappel Securite %.4f"
          % (qualite["camembert_et_regles"]["f1_macro_classes_presentes"],
             qualite["camembert_et_regles"]["rappel_securite"]))

    # ── 2. Export ONNX puis quantification en entiers 8 bits ─────────────────
    os.makedirs(DOSSIER_ONNX, exist_ok=True)
    chemin_fp32 = os.path.join(DOSSIER_ONNX, "modele.onnx")
    chemin_int8 = os.path.join(DOSSIER_ONNX, "modele_int8.onnx")
    exemple = tok("exemple de ticket", padding="max_length", truncation=True,
                  max_length=MAX_LEN, return_tensors="pt")
    modele.to("cpu")
    print("\nexport ONNX...")
    torch.onnx.export(
        modele, (exemple["input_ids"], exemple["attention_mask"]), chemin_fp32,
        input_names=["input_ids", "attention_mask"], output_names=["logits"],
        dynamic_axes={"input_ids": {0: "lot"}, "attention_mask": {0: "lot"},
                      "logits": {0: "lot"}},
        opset_version=14, do_constant_folding=True)

    from onnxruntime.quantization import quantize_dynamic, QuantType
    print("quantification en entiers 8 bits...")
    quantize_dynamic(chemin_fp32, chemin_int8, weight_type=QuantType.QInt8)

    import onnxruntime as ort
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 1  # un ticket a la fois, comme en service
    sessions = {
        "onnx_fp32": ort.InferenceSession(chemin_fp32, opts, providers=["CPUExecutionProvider"]),
        "onnx_int8": ort.InferenceSession(chemin_int8, opts, providers=["CPUExecutionProvider"]),
    }

    def inferer_onnx(sess, textes, lot=32):
        out = []
        for i in range(0, len(textes), lot):
            e = tok(textes[i:i + lot], padding="max_length", truncation=True,
                    max_length=MAX_LEN, return_tensors="np")
            logits = sess.run(["logits"], {"input_ids": e["input_ids"].astype(np.int64),
                                           "attention_mask": e["attention_mask"].astype(np.int64)})[0]
            e_x = np.exp(logits - logits.max(axis=-1, keepdims=True))
            out.append(e_x / e_x.sum(axis=-1, keepdims=True))
        return np.vstack(out)

    # ── 3. Fidelite de la version quantifiee ─────────────────────────────────
    fidelite = {}
    for nom, sess in sessions.items():
        p = arr[inferer_onnx(sess, entree).argmax(1)]
        a = [apply_heuristics(t, pp, float(c), threshold=SEUIL)["categorie"]
             for t, pp, c in zip(brut, p, conf)]
        fidelite[nom] = {
            "predictions_identiques_a_torch": int((p == pred).sum()),
            "sur": len(pred),
            "accord": round(float((p == pred).mean()), 4),
            "qualite_avec_regles": scores(y, a, classes, presentes),
        }
        print("  %-10s accord avec torch %.4f   F1(presentes) %.4f"
              % (nom, fidelite[nom]["accord"],
                 fidelite[nom]["qualite_avec_regles"]["f1_macro_classes_presentes"]))

    # ── 4. Cout, un ticket a la fois ─────────────────────────────────────────
    def chrono_torch():
        e = tok(entree[0], padding="max_length", truncation=True, max_length=MAX_LEN,
                return_tensors="pt")
        with torch.no_grad():
            for _ in range(3):
                modele(**e)
            t = []
            for i in range(N_CHRONO):
                ee = tok(entree[i % len(entree)], padding="max_length", truncation=True,
                         max_length=MAX_LEN, return_tensors="pt")
                t0 = time.perf_counter(); modele(**ee); t.append((time.perf_counter() - t0) * 1000)
        return t

    def chrono_onnx(sess):
        def un(i):
            e = tok(entree[i % len(entree)], padding="max_length", truncation=True,
                    max_length=MAX_LEN, return_tensors="np")
            return {"input_ids": e["input_ids"].astype(np.int64),
                    "attention_mask": e["attention_mask"].astype(np.int64)}
        for i in range(3):
            sess.run(["logits"], un(i))
        t = []
        for i in range(N_CHRONO):
            x = un(i)
            t0 = time.perf_counter(); sess.run(["logits"], x); t.append((time.perf_counter() - t0) * 1000)
        return t

    print("\ncout par ticket, un a la fois, %d mesures :" % N_CHRONO)
    cout = {}
    for nom, mesures in (("torch_fp32_cpu", chrono_torch()),
                         ("onnx_fp32_cpu", chrono_onnx(sessions["onnx_fp32"])),
                         ("onnx_int8_cpu", chrono_onnx(sessions["onnx_int8"]))):
        cout[nom] = {"median_ms": round(float(np.median(mesures)), 1),
                     "p95_ms": round(float(np.percentile(mesures, 95)), 1),
                     "min_ms": round(float(np.min(mesures)), 1)}
        print("  %-16s mediane %7.1f ms   p95 %7.1f ms" % (nom, cout[nom]["median_ms"],
                                                           cout[nom]["p95_ms"]))
    cout["taille_Mo"] = {
        "onnx_fp32": round(os.path.getsize(chemin_fp32) / 1e6, 1),
        "onnx_int8": round(os.path.getsize(chemin_int8) / 1e6, 1),
    }
    print("  taille : fp32 %.1f Mo, int8 %.1f Mo"
          % (cout["taille_Mo"]["onnx_fp32"], cout["taille_Mo"]["onnx_int8"]))

    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "protocole": "jeu de test GELE du pipeline (data/splits/test.csv), 356 tickets, 5 categories sur 8",
            "entree": "entree de production : classification inconnue, fixee a « demande », priorite saisie reelle",
            "classes_presentes": presentes,
            "qualite": qualite,
            "fidelite_onnx": fidelite,
            "cout_par_ticket": cout,
            "note_f1": ("f1_macro_huit_classes compte zero pour les trois categories absentes du jeu "
                        "gele : c'est la convention du memoire pour le modele servi. "
                        "f1_macro_classes_presentes ne moyenne que les cinq categories tirees."),
        }, f, ensure_ascii=False, indent=2)
    print("\necrit : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
