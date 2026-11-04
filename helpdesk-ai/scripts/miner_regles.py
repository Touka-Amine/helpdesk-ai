# -*- coding: utf-8 -*-
"""Propose des mots-cles de regles metier, mines sur le SEUL jeu d'entrainement.

Pourquoi ce script existe
-------------------------
L'audit du 2026-08-22 a retire quatre mots-cles de `src/models/heuristics.py`
parce qu'ils avaient ete choisis en regardant des erreurs du jeu de test. La
regle posee en tete de ce fichier est depuis la suivante : un mot-cle n'est
admis que s'il est attesté dans le jeu d'entrainement.

Ce script applique cette regle de facon mecanique, pour qu'on n'ait plus a s'en
remettre au jugement de celui qui ecrit la liste :

  1. il refait le decoupage anti-fuite du protocole des experiences ;
  2. il ne regarde QUE la partie entrainement ;
  3. il enumere les n-grammes de 1 a 3 mots qui y apparaissent ;
  4. il ne retient que ceux dont la categorie est quasi certaine SUR
     L'ENTRAINEMENT (precision >= --precision, support >= --support) ;
  5. il ecarte ceux qu'une regle existante couvre deja.

Le jeu de test n'est ouvert a aucun moment. Ce que le script propose peut donc
etre ajoute aux regles sans contaminer la mesure.

Usage :
    python scripts/miner_regles.py --categorie Securite
    python scripts/miner_regles.py --toutes --precision 0.95 --support 8
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "src"))

from models.heuristics import FORCE_RULES, SOFT_RULES, _normalize  # noqa: E402

CSV = os.path.join(RACINE, "data", "processed", "HelpDesk1.csv")
SORTIE = os.path.join(RACINE, "metrics", "regles_candidates.json")
GRAINE = 42
TEST_SIZE = 0.2

# Mots trop courants pour porter une categorie a eux seuls.
VIDES = {
    "le", "la", "les", "un", "une", "des", "du", "de", "et", "ou", "a", "au",
    "aux", "en", "dans", "sur", "pour", "par", "avec", "sans", "que", "qui",
    "ne", "pas", "plus", "est", "sont", "ete", "etre", "avoir", "il", "elle",
    "nous", "vous", "je", "ce", "cette", "ces", "son", "sa", "ses", "leur",
    "notre", "votre", "mon", "ma", "mes", "se", "y", "d", "l", "s", "n", "c",
    "qu", "bonjour", "merci", "cordialement", "svp", "probleme", "demande",
    "ticket", "utilisateur", "service", "support", "urgent", "aide",
}


def decoupage(df):
    """Le decoupage du protocole des experiences, titre par titre."""
    titres = df.groupby("Titre")["Catégorie"].first().reset_index()
    sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=GRAINE)
    tr, _ = next(sss.split(titres["Titre"], titres["Catégorie"]))
    t_train = set(titres.iloc[tr]["Titre"])
    return df[df["Titre"].isin(t_train)].reset_index(drop=True)


def deja_couvert(ngramme: str) -> str | None:
    """La categorie qu'une regle existante attribuerait deja a ce n-gramme."""
    for keywords, cat in FORCE_RULES:
        for kw in keywords:
            if re.search(r"\b" + re.escape(_normalize(kw)) + r"\b", ngramme):
                return cat
    for keywords, cat, _ in SOFT_RULES:
        for kw in keywords:
            if re.search(r"\b" + re.escape(_normalize(kw)), ngramme):
                return cat
    return None


def ngrammes(texte: str, n_max: int = 3):
    mots = [m for m in re.findall(r"[a-z0-9]+", texte) if len(m) > 2]
    for n in range(1, n_max + 1):
        for i in range(len(mots) - n + 1):
            bout = mots[i:i + n]
            if n == 1 and bout[0] in VIDES:
                continue
            if all(m in VIDES for m in bout):
                continue
            yield " ".join(bout)


def miner(df_train, precision_min: float, support_min: int):
    """Les n-grammes dont la categorie est quasi certaine a l'entrainement."""
    par_ngramme: dict[str, Counter] = defaultdict(Counter)
    for texte, cat in zip(df_train["_norm"], df_train["Catégorie"]):
        for g in set(ngrammes(texte)):
            par_ngramme[g][cat] += 1

    retenus = []
    for g, compte in par_ngramme.items():
        total = sum(compte.values())
        if total < support_min:
            continue
        cat, n = compte.most_common(1)[0]
        precision = n / total
        if precision < precision_min:
            continue
        couvert = deja_couvert(g)
        retenus.append({
            "ngramme": g,
            "categorie": cat,
            "precision_entrainement": round(precision, 4),
            "support_entrainement": total,
            "tickets_de_la_categorie": n,
            "deja_couvert_par_une_regle": couvert,
        })
    retenus.sort(key=lambda r: (-r["support_entrainement"], -r["precision_entrainement"]))
    return retenus


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--categorie", help="ne montrer que cette categorie")
    p.add_argument("--toutes", action="store_true", help="toutes les categories")
    p.add_argument("--precision", type=float, default=1.0,
                   help="precision minimale sur l'entrainement (defaut 1.0)")
    p.add_argument("--support", type=int, default=10,
                   help="nombre minimal de tickets d'entrainement (defaut 10)")
    p.add_argument("--nouveaux", action="store_true",
                   help="n'afficher que ce qu'aucune regle ne couvre deja")
    a = p.parse_args()

    df = pd.read_csv(CSV)
    df["_norm"] = (df["Titre"].fillna("") + " " + df["Description"].fillna("")).map(_normalize)
    df_train = decoupage(df)
    print("entrainement : %d tickets, %d titres — le jeu de test n'est pas lu"
          % (len(df_train), df_train["Titre"].nunique()))

    retenus = miner(df_train, a.precision, a.support)
    if a.categorie:
        cible = _normalize(a.categorie)
        retenus = [r for r in retenus if _normalize(r["categorie"]).startswith(cible)]
    if a.nouveaux:
        retenus = [r for r in retenus if r["deja_couvert_par_une_regle"] is None]

    print("%d n-grammes retenus (precision >= %.2f, support >= %d)\n"
          % (len(retenus), a.precision, a.support))
    print("%-34s %-14s %6s %7s  %s" % ("n-gramme", "categorie", "prec.", "support", "deja couvert par"))
    print("-" * 96)
    for r in retenus[:120]:
        print("%-34s %-14s %6.3f %7d  %s"
              % (r["ngramme"][:34], r["categorie"], r["precision_entrainement"],
                 r["support_entrainement"], r["deja_couvert_par_une_regle"] or ""))

    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({
            "protocole": "n-grammes 1-3 mots mines sur le seul jeu d'entrainement du protocole des experiences",
            "graine": GRAINE,
            "precision_minimale": a.precision,
            "support_minimal": a.support,
            "tickets_entrainement": len(df_train),
            "candidats": retenus,
        }, f, ensure_ascii=False, indent=2)
    print("\necrit : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
