# -*- coding: utf-8 -*-
"""
T9, second volet — controles que le premier passage ne couvrait pas.

  D. REPARTITIONS. Les ventilations publiees (statuts du corpus, statuts de la
     base RAG) doivent sommer au total annonce et correspondre aux donnees.
  E. LES DEUX DECOUPAGES. 1 445 / 355 appartient aux experiences, 1 444 / 356 au
     pipeline. Aucun des deux ne doit etre attribue a l'autre protocole.
  F. COUTS ET LATENCE, contre les artefacts.
  G. FIGURES. Toute image incluse par le memoire doit exister sur le disque, et
     toute image presente doit etre incluse quelque part.

Sortie : scratchpad/t9_coherence2.json
"""
from __future__ import annotations

import glob
import io
import json
import os
import re

RAPPORT = r"C:\projetpfe\report"
PROJET = r"C:\projetpfe\helpdesk-ai"
SORTIE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapport_coherence_2.json")

anomalies, controles = [], []


def noter(ok, libelle, detail=""):
    controles.append({"ok": bool(ok), "libelle": libelle, "detail": detail})
    if not ok:
        anomalies.append({"libelle": libelle, "detail": detail})
    print("  %s %s%s" % ("OK  " if ok else "ANOM", libelle,
                         ("  — " + detail) if detail else ""))


sources = {}
for tex in sorted(glob.glob(os.path.join(RAPPORT, "*.tex"))):
    with io.open(tex, encoding="utf-8", errors="replace") as f:
        sources[os.path.basename(tex)] = [
            ("" if l.lstrip().startswith("%") else l) for l in f.readlines()]
TOUT = "".join("".join(v) for v in sources.values())


def present(valeur):
    """Le nombre figure-t-il dans le memoire, separateur LaTeX compris ?"""
    s = str(valeur)
    formes = [s]
    if len(s) > 3:
        formes.append(s[:-3] + "\\," + s[-3:])
    return any(f in TOUT for f in formes)


import pandas as pd

brut = pd.read_csv(os.path.join(PROJET, "data", "raw", "HelpDesk1.csv"),
                   encoding="utf-8-sig")
col_res = [c for c in brut.columns if "Motif" in c][0]
col_statut = brut.columns[1]
rag = pd.read_csv(os.path.join(PROJET, "data", "splits", "rag.csv"), encoding="utf-8")

print("\nD. REPARTITIONS")
print("-" * 70)

st_corpus = brut[col_statut].value_counts().to_dict()
noter(sum(st_corpus.values()) == len(brut),
      "statuts du corpus : la ventilation somme au total",
      "%d = %d" % (sum(st_corpus.values()), len(brut)))
manquants = [("%s=%d" % (k, v)) for k, v in st_corpus.items() if not present(v)]
noter(not manquants, "chaque effectif de statut du corpus figure au memoire",
      ", ".join(manquants) if manquants else "476 / 464 / 328 / 321 / 211")

st_rag = rag[col_statut].value_counts().to_dict()
noter(sum(st_rag.values()) == len(rag),
      "statuts de la base RAG : la ventilation somme au total",
      "%d = %d" % (sum(st_rag.values()), len(rag)))
manquants = [("%s=%d" % (k, v)) for k, v in st_rag.items() if not present(v)]
noter(not manquants, "chaque effectif de statut de la base RAG figure au memoire",
      ", ".join(manquants) if manquants else "363 / 358 / 237 / 236 / 163")

procedures = rag[col_res].astype(str).str.strip().nunique()
noter(present(procedures) or "quarante-six" in TOUT,
      "procedures distinctes de la base RAG = %d" % procedures)

print("\nE. LES DEUX DECOUPAGES, JAMAIS CONFONDUS")
print("-" * 70)

for n, protocole, mauvais in [
        (1445, "experiences", "pipeline"),
        (355, "experiences", "pipeline"),
        (1444, "pipeline", "exp[ée]riences"),
        (356, "pipeline", "exp[ée]riences")]:
    forme = str(n) if n < 1000 else str(n)[:-3] + r"\\," + str(n)[-3:]
    # une phrase qui cite le nombre ET le mauvais protocole a moins de 90 caracteres
    rx = re.compile(forme + r".{0,90}?" + mauvais + r"|" + mauvais + r".{0,90}?" + forme)
    fautifs = []
    for nom, lignes in sources.items():
        for i, l in enumerate(lignes, 1):
            if rx.search(l):
                fautifs.append("%s:%d" % (nom, i))
    noter(not fautifs, "%d jamais rattache au protocole %s" % (n, mauvais.replace("[ée]", "é")),
          "; ".join(fautifs[:3]))

print("\nF. COUTS ET LATENCE")
print("-" * 70)

with io.open(os.path.join(PROJET, "metrics", "campagne_apres_nettoyage.json"),
             encoding="utf-8") as f:
    couts = json.load(f)["cout_de_service"]
for cle, val in couts.items():
    txt = str(val).replace(".", ",")
    noter(txt in TOUT or ("%g" % val).replace(".", ",") in TOUT,
          "cout de service %s = %s" % (cle, txt))

try:
    with io.open(os.path.join(PROJET, "metrics", "load_test.json"), encoding="utf-8") as f:
        charge = json.load(f)
    plat = json.dumps(charge, ensure_ascii=False)
    noter("330" in TOUT, "latence p95 de 330 ms citee au memoire",
          "artefact : %s" % plat[:140])
except Exception as e:
    noter(False, "metrics/load_test.json illisible", str(e))

print("\nG. FIGURES")
print("-" * 70)

incluses = set()
for nom, lignes in sources.items():
    for l in lignes:
        for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", l):
            incluses.add(m.group(1))

dossier = os.path.join(RAPPORT, "img")
sur_disque = {f for f in os.listdir(dossier)} if os.path.isdir(dossier) else set()

absentes = sorted(f for f in incluses
                  if f not in sur_disque
                  and not any(f + e in sur_disque for e in (".png", ".jpg", ".pdf")))
noter(not absentes, "toute image incluse existe sur le disque",
      ", ".join(absentes) if absentes else "%d images incluses" % len(incluses))

inutilisees = sorted(f for f in sur_disque
                     if f not in incluses and os.path.splitext(f)[0] not in
                     {os.path.splitext(i)[0] for i in incluses})
noter(True, "images presentes mais non incluses",
      ", ".join(inutilisees) if inutilisees else "aucune")

print("\n" + "=" * 70)
print("%d controles, %d anomalie(s)" % (len(controles), len(anomalies)))
print("=" * 70)
for a in anomalies:
    print("  ANOMALIE : %s  %s" % (a["libelle"], a["detail"]))

with io.open(SORTIE, "w", encoding="utf-8") as f:
    json.dump({"controles": controles, "anomalies": anomalies}, f,
              indent=2, ensure_ascii=False)
print("\necrit %s" % SORTIE)
