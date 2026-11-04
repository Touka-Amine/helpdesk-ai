# -*- coding: utf-8 -*-
"""Le corpus porte-t-il une tonalite ? (EF-13)

Ce que l'exigence demande
-------------------------
EF-13, priorite faible : « Analyse de tonalite du message — indicateur d'urgence
affiche ». Elle n'avait pas ete traitee. Avant de la construire, il faut savoir
s'il y a quelque chose a analyser.

Trois mesures suffisent a trancher
-----------------------------------
1. Le vocabulaire d'urgence est-il present ? Un indicateur lexical ne peut rien
   detecter si les mots n'y sont pas.
2. La ponctuation et la casse portent-elles de l'emotion ? Majuscules criees,
   points d'exclamation : c'est ce que detecte un analyseur de tonalite simple.
3. Le vocabulaire qui corrèle avec la priorite haute est-il du vocabulaire
   d'urgence, ou du vocabulaire de scenario ? Si un mot predit la priorite
   seulement parce qu'il appartient a un type de ticket, ce n'est pas une
   tonalite qu'on mesure, c'est un scenario qu'on reconnait.

Le troisieme point se mesure : on compare, pour chaque mot, le nombre de TITRES
DISTINCTS sous lesquels il apparait. Un mot d'urteur veritable (« urgent »,
« bloquant ») traverse les scenarios ; un mot de scenario reste chez lui.

Sortie : metrics/tonalite_eval.json
"""
from __future__ import annotations

import collections
import io
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone

import numpy as np
import pandas as pd

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN = os.path.join(RACINE, "data", "splits", "train.csv")
SORTIE = os.path.join(RACINE, "metrics", "tonalite_eval.json")

# Vocabulaire d'urgence du francais courant, tel qu'un analyseur lexical
# l'emploierait. Liste posee AVANT de regarder le corpus.
LEXIQUE_URGENCE = [
    "urgent", "urgence", "critique", "immediat", "immediatement", "au plus vite",
    "bloquant", "bloque", "bloquee", "paralyse", "arret total", "arrete",
    "impossible", "plus personne", "tout le service", "toute l equipe",
    "production arretee", "perte de donnees", "grave", "severe", "catastrophe",
    "tres grave", "des que possible", "prioritaire", "escalade",
]


def normaliser(t):
    t = unicodedata.normalize("NFKD", str(t).lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def main():
    df = pd.read_csv(TRAIN)
    brut = (df["Titre"].fillna("") + " " + df["Description"].fillna("")).tolist()
    norme = [normaliser(t) for t in brut]
    n = len(df)

    # ── 1. Le vocabulaire d'urgence ──────────────────────────────────────────
    lexique = {}
    for mot in LEXIQUE_URGENCE:
        m = normaliser(mot)
        c = sum(1 for t in norme if re.search(r"\b" + re.escape(m), t))
        lexique[mot] = c
    presents = {k: v for k, v in lexique.items() if v}
    print("vocabulaire d'urgence : %d termes cherches, %d presents dans le corpus"
          % (len(LEXIQUE_URGENCE), len(presents)))
    for k, v in sorted(presents.items(), key=lambda x: -x[1]):
        print("   %-22s %4d tickets (%.1f %%)" % (k, v, 100 * v / n))
    for k in sorted(k for k, v in lexique.items() if not v):
        pass

    # ── 2. La ponctuation et la casse ────────────────────────────────────────
    exclamations = sum(1 for t in brut if "!" in t)
    majuscules = sum(1 for t in brut
                     if re.search(r"\b[A-ZÀ-Ý]{4,}\b",
                                  re.sub(r"\b(VPN|DNS|DHCP|VLAN|NAS|SAN|ERP|CRM|IP|PC|IT|RH|SSL|"
                                         r"FQDN|NETBIOS|PRA|PCA|BSOD|VOIP|IPBX|PBX|OTBS|OTMA|"
                                         r"EOT|OTH|TPI|TTEI|TC|HELIOFLEX|CID)\b", "", t)))
    print("\nponctuation et casse :")
    print("   points d'exclamation   %4d tickets (%.1f %%)" % (exclamations, 100 * exclamations / n))
    print("   mots tout en capitales %4d tickets (%.1f %%)" % (majuscules, 100 * majuscules / n))

    # ── 3. Scenario ou tonalite ? ────────────────────────────────────────────
    haute = (df["priorite_simple"] == "haute").values
    titres_du_mot = collections.defaultdict(set)
    tickets_du_mot = collections.Counter()
    hauts_du_mot = collections.Counter()
    for t, titre, h in zip(norme, df["Titre"], haute):
        for w in set(re.findall(r"[a-z]{4,}", t)):
            titres_du_mot[w].add(titre)
            tickets_du_mot[w] += 1
            if h:
                hauts_du_mot[w] += 1

    n_titres = df["Titre"].nunique()
    discriminants = []
    for w, c in tickets_du_mot.items():
        if c < 25:
            continue
        part = hauts_du_mot[w] / c
        if part >= 0.80 or part <= 0.20:
            discriminants.append({"mot": w, "part_haute": round(part, 3), "tickets": c,
                                  "titres": len(titres_du_mot[w])})
    discriminants.sort(key=lambda d: -d["tickets"])
    transversaux = [d for d in discriminants if d["titres"] >= max(3, n_titres // 10)]
    print("\nmots qui separent la priorite (part haute >= 0,80 ou <= 0,20, "
          "au moins 25 tickets) : %d" % len(discriminants))
    print("   dont presents sous au moins %d titres differents : %d"
          % (max(3, n_titres // 10), len(transversaux)))
    print("   les dix plus frequents :")
    for d in discriminants[:10]:
        print("      %-20s part haute %.2f  %4d tickets  %2d titre(s)"
              % (d["mot"], d["part_haute"], d["tickets"], d["titres"]))

    verdict = ("Le corpus ne porte pas de tonalite exploitable." if not presents
               and not transversaux else "Signal partiel.")
    conclusion = {
        "termes_d_urgence_cherches": len(LEXIQUE_URGENCE),
        "termes_presents": len(presents),
        "termes_presents_detail": presents,
        "tickets_avec_exclamation": exclamations,
        "tickets_avec_capitales": majuscules,
        "mots_discriminants": len(discriminants),
        "mots_discriminants_transversaux": len(transversaux),
        "titres_du_jeu": int(n_titres),
        "verdict": verdict,
    }
    print("\n%s" % verdict)

    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "exigence": "EF-13 — analyse de tonalite du message",
            "jeu": "data/splits/train.csv, %d tickets, %d titres" % (n, n_titres),
            "lexique_pose_avant_mesure": LEXIQUE_URGENCE,
            "resultats": conclusion,
            "mots_discriminants_les_plus_frequents": discriminants[:30],
        }, f, ensure_ascii=False, indent=2)
    print("ecrit : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
