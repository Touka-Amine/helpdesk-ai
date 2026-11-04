# -*- coding: utf-8 -*-
"""Cherche les donnees personnelles la ou elles ne devraient plus etre.

Ce script ne fait pas confiance a la pseudonymisation : il la verifie. Il lit la
liste des personnes nommees dans l'export d'origine, puis balaie tout ce que le
projet a produit — tableaux intermediaires, jeux de donnees, base applicative,
base vectorielle, metriques — et signale chaque endroit ou un nom reel subsiste.

Il cherche aussi ce qu'une liste de noms ne couvre pas : adresses de courriel,
numeros de telephone, adresses IP.

Un rapport vide est le resultat attendu une fois la pseudonymisation passee.
C'est ce rapport qui justifie l'etat de l'exigence ENF-04 (b) au chapitre 6.

Usage :
    python scripts/verification/audit_donnees_personnelles.py
    python scripts/verification/audit_donnees_personnelles.py --verbeux
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sqlite3
import sys
import unicodedata
from datetime import datetime, timezone

import pandas as pd

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT_ORIGINE = os.path.join(RACINE, "data", "raw", "HelpDesk1.csv")
SORTIE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "rapport_donnees_personnelles.json")

COLONNES_IDENTIFIANTES = ("Demandeur", "Assigné à")
# Le numero du support, repete a l'identique dans 48 tickets : donnee de
# l'entreprise, pas d'une personne. Il n'est pas compte comme une fuite.
NUMEROS_DE_SERVICE = {"80080300"}
# Fragments trop courts ou trop communs pour etre cherches seuls : « Ines »
# apparait dans « machines », « Touj » dans « toujours ».
LONGUEUR_MINIMALE_FRAGMENT = 4
MOTS_NON_PERSONNELS = {"helpdesk", "otbs", "admin", "user", "test", "support"}
# Des fragments de patronymes entrent en collision avec des mots du metier. Les
# sigles des huit filiales du groupe en font partie — « OTMA » est une filiale,
# pas la personne dont le nom commence pareil — et « sondes » designe ici des
# sondes de supervision. Ces mots sont lus dans les donnees plutot qu'ecrits en
# dur, pour que la liste suive le corpus.
MOTS_TECHNIQUES = {"sondes"}


def mots_de_l_organisation() -> set[str]:
    """Les sigles de filiales, a ne pas confondre avec des noms de personnes."""
    try:
        df = pd.read_csv(EXPORT_ORIGINE, usecols=["Filiale"])
        return {normaliser(v) for v in df["Filiale"].dropna().unique()}
    except (OSError, ValueError):
        return set()

MOTIFS = {
    "adresse_de_courriel": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "adresse_ip": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

# Un numero de telephone, et rien d'autre. Une recherche naive de « huit chiffres
# avec des separateurs » attrape les horodatages (2026-05-31 15) et les nombres
# decimaux des fichiers de metriques (11.964020). D'ou deux precautions : le point
# n'est pas accepte comme separateur, et tout ce qui commence par une annee est
# ecarte.
MOTIF_TELEPHONE = re.compile(r"(?<![\w.-])(\+?\d(?: ?\d){7,13})(?![\w.-])")
MOTIF_HORODATAGE = re.compile(r"^(?:19|20)\d{2}[ -]")


def numeros_de_telephone(texte: str) -> list[str]:
    out = []
    for brut in MOTIF_TELEPHONE.findall(texte):
        if MOTIF_HORODATAGE.match(brut):
            continue
        chiffres = re.sub(r"\D", "", brut)
        if not (8 <= len(chiffres) <= 14):
            continue
        if chiffres in NUMEROS_DE_SERVICE:
            continue
        out.append(brut.strip())
    return out


# Deux zones, deux regles.
#   « corpus »      : les 1 800 tickets historiques et tout ce qui en derive.
#                     Aucune personne ne doit y etre nommee : ce sont des donnees
#                     d'etude, la pseudonymisation suffit a les rendre exploitables.
#   « application » : les comptes de l'application. Un nom et une adresse y sont
#                     la raison d'etre de la table. Ils ne se pseudonymisent pas ;
#                     ils relevent de la duree de conservation et du controle d'acces.
TABLES_DE_COMPTES = {"users", "password_reset_tokens"}


def normaliser(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t).lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def fragments_de_noms() -> set[str]:
    """Les morceaux de noms a chercher, tires de l'export d'origine."""
    if not os.path.exists(EXPORT_ORIGINE):
        print("export d'origine absent (%s) — impossible de construire la liste des noms."
              % EXPORT_ORIGINE)
        return set()
    df = pd.read_csv(EXPORT_ORIGINE)
    noms = set()
    for col in COLONNES_IDENTIFIANTES:
        if col in df.columns:
            noms |= set(df[col].dropna().astype(str).unique())
    exclus = MOTS_NON_PERSONNELS | MOTS_TECHNIQUES | mots_de_l_organisation()
    frags = set()
    for n in noms:
        for part in re.split(r"[\s._-]+", normaliser(n)):
            if len(part) >= LONGUEUR_MINIMALE_FRAGMENT and part not in exclus:
                frags.add(part)
    return frags


def fouiller_texte(texte: str, frags: set[str]) -> dict:
    """Ce que ce texte contient d'identifiant."""
    t = normaliser(texte)
    trouve = {}
    atteints = sorted(f for f in frags if re.search(r"\b" + re.escape(f) + r"\b", t))
    if atteints:
        trouve["fragments_de_noms"] = atteints[:20]
        trouve["n_fragments"] = len(atteints)
    for nom, motif in MOTIFS.items():
        occurrences = sorted({m.strip() for m in motif.findall(texte)})
        if occurrences:
            trouve[nom] = occurrences[:10]
    tels = sorted(set(numeros_de_telephone(texte)))
    if tels:
        trouve["numero_de_telephone"] = tels[:10]
    return trouve


def cibles() -> list[str]:
    """Tout ce que le projet produit et qui pourrait porter un nom."""
    motifs = [
        "data/processed/*.csv", "data/prcessed/*.csv", "data/splits/*.csv",
        "data/reference/*.csv", "data/curated/*.csv", "data/knowledge/*.json",
        "data/external/*.csv", "metrics/*.json",
    ]
    out = []
    for m in motifs:
        out.extend(sorted(glob.glob(os.path.join(RACINE, *m.split("/")))))
    return out


def fouiller_base(chemin: str, frags: set[str]) -> dict:
    """Les colonnes textuelles de chaque table d'une base SQLite."""
    resultat = {}
    try:
        cx = sqlite3.connect("file:%s?mode=ro" % chemin.replace("\\", "/"), uri=True)
        tables = [r[0] for r in cx.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for table in tables:
            try:
                lignes = cx.execute("SELECT * FROM %s LIMIT 5000" % table).fetchall()
            except sqlite3.Error:
                continue
            blob = "\n".join(" ".join(str(v) for v in l if isinstance(v, str)) for l in lignes)
            t = fouiller_texte(blob, frags)
            if t:
                t["zone"] = "application" if table in TABLES_DE_COMPTES else "corpus"
                resultat[table] = t
        cx.close()
    except sqlite3.Error as e:
        resultat["_erreur"] = str(e)
    return resultat


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verbeux", action="store_true")
    a = ap.parse_args()

    frags = fragments_de_noms()
    print("liste de reference : %d fragments de noms tires de l'export d'origine" % len(frags))
    if not frags:
        return 1

    constats = {}

    for chemin in cibles():
        rel = os.path.relpath(chemin, RACINE).replace("\\", "/")
        # L'export d'origine est la piece justificative, conservee en clair et
        # couverte par la duree de conservation. Le jeu public externe n'est pas
        # une donnee de l'entreprise : ce qu'il contient ne lui appartient pas.
        if rel.startswith("data/raw") or rel.startswith("data/external"):
            continue
        try:
            with io.open(chemin, encoding="utf-8", errors="replace") as f:
                contenu = f.read()
        except OSError as e:
            constats[rel] = {"_erreur": str(e)}
            continue
        t = fouiller_texte(contenu, frags)
        if t:
            constats[rel] = t
        if a.verbeux:
            print("  %-56s %s" % (rel, "RIEN" if not t else "A CORRIGER"))

    for chemin in sorted(glob.glob(os.path.join(RACINE, "data", "*.db"))):
        rel = os.path.relpath(chemin, RACINE).replace("\\", "/")
        t = fouiller_base(chemin, frags)
        if t:
            constats[rel] = t
        if a.verbeux:
            print("  %-56s %s" % (rel, "RIEN" if not t else "A CORRIGER"))

    chroma = os.path.join(RACINE, "data", "chroma")
    if os.path.isdir(chroma):
        for chemin in sorted(glob.glob(os.path.join(chroma, "**", "*.sqlite3"), recursive=True)):
            rel = os.path.relpath(chemin, RACINE).replace("\\", "/")
            t = fouiller_base(chemin, frags)
            if t:
                constats[rel] = t

    # Les bases de test ne sont pas un livrable : elles sont signalees a part,
    # et leur place est hors du depot.
    bases_de_test = {r for r in constats if re.search(r"tickets_\w*test\w*\.db|tickets_ci\.db", r)}
    zone_application = {r for r in constats
                        if r.endswith(".db") and r not in bases_de_test
                        and all(v.get("zone") == "application"
                                for v in constats[r].values() if isinstance(v, dict))}
    en_defaut = {r: t for r, t in constats.items()
                 if r not in bases_de_test and r not in zone_application}

    print()
    if en_defaut:
        print("%d emplacement(s) du corpus portent encore des donnees personnelles :" % len(en_defaut))
        for rel, t in sorted(en_defaut.items()):
            detail = ", ".join("%s=%s" % (k, v if not isinstance(v, list) else len(v))
                               for k, v in t.items() if not k.startswith("_") and k != "zone")
            print("  %-56s %s" % (rel, detail))
    else:
        print("corpus : aucune donnee personnelle hors de l'export d'origine.")
    if zone_application:
        print("\nzone applicative (comptes, legitime — releve de la conservation, pas de la "
              "pseudonymisation) : %s" % ", ".join(sorted(zone_application)))
    if bases_de_test:
        print("bases de test presentes dans le depot, a retirer : %s"
              % ", ".join(sorted(bases_de_test)))

    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "exigence": "ENF-04 (b) — traitement des donnees personnelles",
            "reference": os.path.relpath(EXPORT_ORIGINE, RACINE).replace("\\", "/"),
            "fragments_recherches": len(frags),
            "numeros_consideres_comme_de_service": sorted(NUMEROS_DE_SERVICE),
            "emplacements_en_defaut": en_defaut,
            "zone_applicative_comptes": sorted(zone_application),
            "bases_de_test_a_retirer": sorted(bases_de_test),
            "tout_examine": constats,
            "conforme": not en_defaut,
        }, f, ensure_ascii=False, indent=2)
    print("\necrit : %s" % SORTIE)
    return 0 if not en_defaut else 2


if __name__ == "__main__":
    sys.exit(main())
