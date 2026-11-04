# -*- coding: utf-8 -*-
"""
T9 — relecture finale de coherence des chiffres du memoire.

Trois controles :

  A. VERITE TERRAIN. Chaque quantite structurante du memoire est recalculee
     depuis les donnees et les artefacts du depot, puis confrontee a ce que le
     texte affirme.

  B. COHERENCE INTERNE. Une meme quantite enoncee a plusieurs endroits doit y
     porter la meme valeur. Le script releve chaque mention et signale les
     divergences.

  C. FORMULATIONS PERIMEES. Les tournures remplacees par les corrections T1 a T8
     ne doivent plus apparaitre nulle part.

Sortie : scratchpad/t9_coherence.json + rapport sur la sortie standard.
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys

RAPPORT = r"C:\projetpfe\report"
PROJET = r"C:\projetpfe\helpdesk-ai"
SORTIE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapport_coherence.json")

anomalies, controles = [], []


def noter(ok, libelle, detail=""):
    controles.append({"ok": bool(ok), "libelle": libelle, "detail": detail})
    if not ok:
        anomalies.append({"libelle": libelle, "detail": detail})
    print("  %s %s%s" % ("OK  " if ok else "ANOM", libelle,
                         ("  — " + detail) if detail else ""))


# ── sources ─────────────────────────────────────────────────────────────────
sources = {}
for tex in sorted(glob.glob(os.path.join(RAPPORT, "*.tex"))):
    with io.open(tex, encoding="utf-8", errors="replace") as f:
        lignes = f.readlines()
    # on ignore les lignes de commentaire LaTeX
    sources[os.path.basename(tex)] = [
        ("" if l.lstrip().startswith("%") else l) for l in lignes
    ]

TOUT = "".join("".join(v) for v in sources.values())


def mentions(motif):
    """Retourne [(fichier, ligne, extrait)] pour chaque occurrence du motif."""
    out = []
    rx = re.compile(motif)
    for nom, lignes in sources.items():
        for i, l in enumerate(lignes, 1):
            if rx.search(l):
                out.append((nom, i, l.strip()[:110]))
    return out


def nombre(n):
    """Ecriture LaTeX d'un entier : 1800 -> 1\\,800."""
    s = str(n)
    return s if len(s) <= 3 else s[:-3] + r"\\," + s[-3:]


# ══════════════════════════════════════════════════════════════════════
print("\nA. VERITE TERRAIN — le texte contre les donnees et les artefacts")
print("-" * 70)

import pandas as pd

brut = pd.read_csv(os.path.join(PROJET, "data", "raw", "HelpDesk1.csv"),
                   encoding="utf-8-sig")
col_res = [c for c in brut.columns if "Motif" in c][0]
col_statut = brut.columns[1]
documente = brut[col_res].notna() & (brut[col_res].astype(str).str.strip() != "")
statuts = brut[col_statut].value_counts().to_dict()

verite = {
    "corpus": len(brut),
    "titres_uniques": brut["Titre"].nunique(),
    "documentes": int(documente.sum()),
    "resolus": int([v for k, v in statuts.items() if "solu" in k][0]),
}
for nom_statut, n in statuts.items():
    verite["statut_" + nom_statut] = int(n)

rag = pd.read_csv(os.path.join(PROJET, "data", "splits", "rag.csv"), encoding="utf-8")
train = pd.read_csv(os.path.join(PROJET, "data", "splits", "train.csv"), encoding="utf-8")
test = pd.read_csv(os.path.join(PROJET, "data", "splits", "test.csv"), encoding="utf-8")
verite.update({
    "rag_lignes": len(rag),
    "rag_procedures": rag[col_res].astype(str).str.strip().nunique(),
    "train": len(train), "test": len(test),
    "titres_train": train["Titre"].nunique(), "titres_test": test["Titre"].nunique(),
})


def artefact(chemin):
    with io.open(os.path.join(PROJET, chemin), encoding="utf-8") as f:
        return json.load(f)


camp = artefact("metrics/campagne_apres_nettoyage.json")
mle = artefact("metrics/ml_eval.json")
rev = artefact("metrics/rag_eval.json")
coh = artefact("metrics/coherence_entree_modele.json")

# (libelle, valeur attendue, motif LaTeX a chercher dans le memoire)
a_verifier = [
    ("corpus", verite["corpus"], nombre(verite["corpus"]) + r"\s+tickets"),
    ("base RAG", verite["rag_lignes"], nombre(verite["rag_lignes"]) + r"\s+(tickets|documents)"),
    ("jeu d'entrainement du pipeline", verite["train"], nombre(verite["train"])),
    ("jeu de test gele", verite["test"], nombre(verite["test"])),
    ("tickets resolus", verite["resolus"], r"\b476\b"),
    ("tickets documentes", verite["documentes"], nombre(verite["documentes"])),
]
for libelle, attendu, motif in a_verifier:
    occ = mentions(motif)
    noter(len(occ) > 0, "%s = %s cite dans le memoire" % (libelle, attendu),
          "%d mention(s)" % len(occ))

# F1 publies contre artefacts
f1 = [
    ("CamemBERT + regles (experiences)", camp["resultats"]["05_camembert_regles"]["f1_macro"]),
    ("TF-IDF + regles (experiences)", camp["resultats"]["03_tfidf_regles"]["f1_macro"]),
    ("CamemBERT seul (experiences)", camp["resultats"]["04_camembert_seul"]["f1_macro"]),
    ("TF-IDF seul (experiences)", camp["resultats"]["02_tfidf_seul"]["f1_macro"]),
    ("modele servi, avec regles (pipeline)", mle["f1_macro_heuristiques"]),
    ("modele servi, sans regles (pipeline)", mle["f1_macro_ml"]),
    ("precision affichee, hybride", rev["moteurs"]["hybride"]["precision_sur_rendus"]),
    ("suggestions par requete, hybride", rev["moteurs"]["hybride"]["resultats_par_requete"]),
]
for libelle, val in f1:
    txt = ("%.4f" % val).replace(".", ",") if isinstance(val, float) and val < 1 \
        else str(val).replace(".", ",")
    occ = mentions(re.escape(txt))
    noter(len(occ) > 0, "%s = %s present dans le memoire" % (libelle, txt),
          "%d mention(s)" % len(occ))

# le seuil RAG servi
import yaml
with io.open(os.path.join(PROJET, "params.yaml"), encoding="utf-8") as f:
    params = yaml.safe_load(f)
seuil = params["rag"]["similarity_threshold"]
occ = mentions(re.escape(("%.2f" % seuil).replace(".", ",")))
noter(len(occ) > 0, "seuil RAG servi = %s present dans le memoire" % seuil,
      "%d mention(s)" % len(occ))

# tests
couverture = io.open(os.path.join(PROJET, "metrics", "couverture_tests.txt"),
                     encoding="utf-8", errors="replace").read()
m = re.search(r"(\d+) passed", couverture)
n_ci = int(m.group(1)) if m else None
noter(str(n_ci) in TOUT, "tests rejoues par l'integration continue = %s" % n_ci)


# ══════════════════════════════════════════════════════════════════════
print("\nB. COHERENCE INTERNE — une quantite, une valeur")
print("-" * 70)

# Pour chaque quantite, le motif capture le nombre ; toutes les captures doivent
# etre identiques.
uniques = [
    ("taille du corpus", r"(\d\\,\d{3}) tickets (?:historiques |)(?:cr[ée]{2}s|d[ée]pos[ée]s|du corpus)"),
    ("titres distincts du corpus", r"(?:que |compte |)(cinquante-huit|58) (?:titres|valeurs|types|sc[ée]narios)"),
    ("consultants du service", r"(onze|11) consultants"),
    ("filiales", r"(huit|8) filiales"),
    ("ecrans de la plateforme", r"(dix-sept|17) [ée]crans"),
    ("budget de latence", r"budget de (\d{3})"),
]
for libelle, motif in uniques:
    vals = re.findall(motif, TOUT)
    distinctes = sorted(set(vals))
    noter(len(distinctes) <= 1,
          "%s : %s" % (libelle, distinctes if distinctes else "aucune mention"),
          "" if len(distinctes) <= 1 else "VALEURS DIVERGENTES")

# decompte du bilan de conformite : le tableau contre la phrase
chap6 = "".join(sources["chap_06.tex"])
verdicts = re.findall(r"&\s*(Tenue|Partielle|Non tenue)\s*&", chap6)
compte = {v: verdicts.count(v) for v in set(verdicts)}
# « l'est partiellement » au singulier, « le sont partiellement » au pluriel :
# le controle doit suivre la langue, pas imposer une faute d'accord. Il a signale
# une anomalie le 2026-10-10 parce qu'une ligne du tableau etait passee de
# « Non tenue » a « Partielle », faisant passer le decompte de une a deux.
phrase = re.search(
    r"Sur les (\w+) lignes, (\w+) sont tenues, (\w+) (?:l'est|le sont) partiellement "
    r"et (\w+) ne (?:l'est|le sont) pas",
    chap6)
mots = {"une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6,
        "sept": 7, "huit": 8, "neuf": 9}
if phrase:
    attendu = (mots.get(phrase.group(1)), mots.get(phrase.group(2)),
               mots.get(phrase.group(3)), mots.get(phrase.group(4)))
    reel = (len(verdicts), compte.get("Tenue", 0),
            compte.get("Partielle", 0), compte.get("Non tenue", 0))
    noter(attendu == reel,
          "bilan de conformite : phrase %s contre tableau %s" % (str(attendu), str(reel)))
else:
    noter(False, "bilan de conformite : phrase de decompte introuvable")

# exigences chiffrees non tenues : le nombre annonce contre les lignes "Non tenue"
annonces = set(re.findall(r"(Deux|Trois|Quatre) exigences chiffr[ée]{2}s ne sont pas tenues", TOUT))
noter(len(annonces) <= 1,
      "nombre d'exigences chiffrees non tenues annonce : %s" % sorted(annonces),
      "" if len(annonces) <= 1 else "ANNONCES DIVERGENTES")


# ══════════════════════════════════════════════════════════════════════
print("\nC. FORMULATIONS PERIMEES")
print("-" * 70)

perimees = [
    ("T1 : « 1 800 tickets résolus »", r"1\\,800 tickets r[ée]solus(?! » serait)"),
    ("T2 : « cas déjà résolus les plus proches »", r"cas d[ée]j[àa] r[ée]solus les plus proches"),
    ("T2 : « tickets déjà résolus les plus proches »", r"tickets d[ée]j[àa] r[ée]solus les plus proches"),
    ("T4 : seuil de pertinence encore à 0,50", r"seuil de pertinence (?:de |à |)0,50(?! a| valait| et)"),
    ("T4 : alpha 0,8 présenté comme dégradant", r"0,2875"),
    ("T6 : « 0,5829 contre 0,8343 »", r"0,5829 contre 0,8343"),
    ("T6 : ENF-02 « presque atteint »", r"[Pp]resque atteint"),
    ("T8 : GroupShuffleSplit dans le mémoire", r"GroupShuffleSplit"),
    ("tests : « cent cinquante »", r"cent cinquante tests"),
    ("figure obsolète ch07_tests.jpg", r"ch07_tests\.jpg"),
    ("tests : « cent trente-deux »", r"cent trente-deux"),
    ("tests : « dix-huit tests d'intégration »", r"dix-huit tests d'int[ée]gration"),
    ("couverture : moteur sémantique à 20 %", r"moteur s[ée]mantique l'est à 20"),
    ("diagramme : seuil 0,50", r"Seuil 0,50"),
]
for libelle, motif in perimees:
    occ = mentions(motif)
    noter(not occ, "absente : %s" % libelle,
          "" if not occ else "; ".join("%s:%d" % (f, l) for f, l, _ in occ[:4]))


# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("%d controles, %d anomalie(s)" % (len(controles), len(anomalies)))
print("=" * 70)
for a in anomalies:
    print("  ANOMALIE : %s  %s" % (a["libelle"], a["detail"]))

with io.open(SORTIE, "w", encoding="utf-8") as f:
    json.dump({"verite_terrain": verite, "controles": controles,
               "anomalies": anomalies}, f, indent=2, ensure_ascii=False)
print("\necrit %s" % SORTIE)
sys.exit(0)
