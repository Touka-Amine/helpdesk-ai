# -*- coding: utf-8 -*-
"""Correcteur orthographique du memoire, sur le dictionnaire francais de MiKTeX.

Pourquoi ce script existe
-------------------------
Aucun correcteur n'est installe sur la machine : ni hunspell, ni aspell, ni le
moindre paquet Python. Dire « le rapport ne contient pas de fautes » sans l'avoir
verifie serait une affirmation gratuite, et c'est exactement ce que cette
campagne de corrections s'efforce de bannir.

MiKTeX, lui, embarque le dictionnaire francais de Dicollecte :
`hunspell/dicts/fr.dic` (75 475 entrees) et `fr.aff` (ses regles d'affixes). Ce
script fait ce que ferait hunspell : il developpe les entrees par leurs affixes,
puis confronte le texte du memoire au vocabulaire obtenu.

Ce qu'il sait faire, et ce qu'il ne sait pas
--------------------------------------------
Il developpe les suffixes et prefixes declares, y compris leurs conditions de
terminaison. Il ne gere pas la composition recursive ni les regles de
remplacement fines ; il reste donc un peu plus severe que hunspell, et signale
quelques formes correctes. C'est le bon sens de l'erreur : mieux vaut relire
trois mots justes que d'en laisser passer un faux.

Il ne juge NI la grammaire, NI l'accord, NI le sens. Un « ces » pour « ses »
passe sans bruit. La relecture humaine reste necessaire ; ce script lui retire
seulement le travail mecanique.

Le lexique du projet
--------------------
Les noms propres, sigles et termes techniques du domaine vivent dans
`scripts/verification/lexique_memoire.txt`, une ligne par mot. Y ajouter un mot
est une decision a prendre en connaissance de cause : le fichier est suivi en
version, et chaque ajout se relit dans un diff.

Sortie : scripts/verification/rapport_orthographe.json
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys
from datetime import datetime, timezone

ICI = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(ICI))
MEMOIRE = os.path.join(os.path.dirname(CODE), "report")
LEXIQUE = os.path.join(ICI, "lexique_memoire.txt")
SORTIE = os.path.join(ICI, "rapport_orthographe.json")

DICOS = [
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "MiKTeX",
                 "hunspell", "dicts"),
    r"C:\Users\Amin\AppData\Local\Programs\MiKTeX\hunspell\dicts",
    "/usr/share/hunspell",
]


# ── dictionnaire ─────────────────────────────────────────────────────────────

def trouver_dictionnaire() -> str | None:
    for d in DICOS:
        if d and os.path.exists(os.path.join(d, "fr.dic")):
            return d
    return None


def lire_affixes(chemin: str) -> dict:
    """Rend {drapeau: [(type, strip, add, condition), ...]}."""
    regles: dict = {}
    for ligne in io.open(chemin, encoding="utf-8", errors="replace"):
        bouts = ligne.split()
        if len(bouts) < 4 or bouts[0] not in ("SFX", "PFX"):
            continue
        # En-tete de groupe : SFX <drapeau> <Y|N> <nombre>
        if bouts[2] in ("Y", "N") and bouts[3].isdigit():
            continue
        genre, drapeau, strip, add = bouts[0], bouts[1], bouts[2], bouts[3]
        condition = bouts[4] if len(bouts) > 4 else "."
        add = add.split("/")[0]          # un affixe peut porter ses propres drapeaux
        regles.setdefault(drapeau, []).append(
            (genre, "" if strip == "0" else strip, "" if add == "0" else add, condition))
    return regles


def lire_alias(chemin: str) -> list:
    """La table AF du fichier d'affixes.

    Ce dictionnaire n'ecrit pas ses drapeaux en clair : `champ/1` renvoie a la
    premiere ligne `AF`, qui vaut `S.()`. Sans resoudre ces alias, l'expansion
    ne produit rien — la premiere version de ce script rendait 73 237 formes
    pour 75 475 entrees, donc MOINS que le dictionnaire, et signalait « champs »
    et « celles » comme inconnus. Un resultat absurde est un resultat a creuser.
    """
    alias = [""]                            # l'index 1 est la premiere ligne AF
    entete_vue = False
    for ligne in io.open(chemin, encoding="utf-8", errors="replace"):
        if not ligne.startswith("AF "):
            continue
        valeur = ligne[3:].strip()
        if not entete_vue and valeur.isdigit():
            entete_vue = True               # « AF 273 » annonce le nombre d'entrees
            continue
        alias.append(valeur)
    return alias


def decouper_drapeaux(champ: str, alias: list) -> list:
    """FLAG long : les drapeaux vont par deux caracteres, alias resolus."""
    champ = champ.strip()
    if champ.isdigit():
        i = int(champ)
        champ = alias[i] if 0 < i < len(alias) else ""
    return [champ[i:i + 2] for i in range(0, len(champ) - 1, 2)]


def condition_tenue(mot: str, condition: str, genre: str) -> bool:
    if condition in (".", ""):
        return True
    motif = condition.replace("[^", "[^").replace("]", "]")
    try:
        return bool(re.search(motif + "$" if genre == "SFX" else "^" + motif, mot))
    except re.error:
        return True


def construire_vocabulaire(dossier: str) -> set:
    regles = lire_affixes(os.path.join(dossier, "fr.aff"))
    alias = lire_alias(os.path.join(dossier, "fr.aff"))
    mots = set()
    with io.open(os.path.join(dossier, "fr.dic"), encoding="utf-8",
                 errors="replace") as f:
        next(f, None)                      # la premiere ligne porte le compte
        for ligne in f:
            ligne = ligne.strip()
            if not ligne:
                continue
            base, _, champ = ligne.partition("/")
            base = base.split("\t")[0].strip()
            if not base:
                continue
            mots.add(base.lower())
            for drapeau in decouper_drapeaux(champ.split("\t")[0], alias):
                for genre, strip, add, cond in regles.get(drapeau, []):
                    if genre == "SFX":
                        if strip and not base.endswith(strip):
                            continue
                        if not condition_tenue(base, cond, genre):
                            continue
                        mots.add((base[:len(base) - len(strip)] + add).lower()
                                 if strip else (base + add).lower())
                    else:
                        if strip and not base.startswith(strip):
                            continue
                        if not condition_tenue(base, cond, genre):
                            continue
                        mots.add((add + base[len(strip):]).lower())
    return mots


# ── texte du memoire ─────────────────────────────────────────────────────────

SANS_ARGUMENT = re.compile(
    r"\\(?:label|ref|pageref|autoref|nameref|cite|includegraphics|input|include|"
    r"usepackage|documentclass|newcolumntype|renewcommand|newcommand|rowcolor|"
    r"cellcolor|columncolor|arrayrulecolor|"
    r"texttt|url|href|bibliography|addcontentsline|markboth|setboolean|"
    r"setcounter|stepcounter|setlength|pretocmd|PackageWarning|definecolor|"
    r"company[A-Za-z]*|pro[A-Z][A-Za-z]*|academic[A-Za-z]*)\s*"
    r"(?:\[[^\]]*\])?(?:\{[^{}]*\})*")
# Les noms d'environnements et les specificateurs de placement ne sont pas du
# texte : sans cette coupe, le correcteur signale « htbp » quatre-vingt-cinq
# fois et « longtable » huit, ce qui noie les vraies candidates.
ENVIRONNEMENT = re.compile(r"\\(?:begin|end)\s*\{[^{}]*\}(?:\[[^\]]*\])?")
PLACEMENT = re.compile(r"(?<=\])\s*|\[[!htbpHP]{1,5}\]")
ENVIRONNEMENTS_IGNORES = re.compile(
    r"\\begin\{(verbatim|lstlisting|minted|tabular|align|equation)\*?\}.*?"
    r"\\end\{\1\*?\}", re.S)
MATHS = re.compile(r"\$[^$]*\$")
COMMANDE = re.compile(r"\\[a-zA-Z@]+\*?")
MOT = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿŒœÆæ][A-Za-zÀ-ÖØ-öø-ÿŒœÆæ'’\-]*")


def _blanchir(m) -> str:
    """Remplace par du blanc en gardant les sauts de ligne.

    Sans cela, un environnement de dix lignes efface dix lignes du compte et le
    correcteur renvoie le relecteur a la mauvaise ligne — « enteteTab » etait
    annonce ligne 920, qui est une phrase ordinaire.
    """
    t = m.group(0)
    return "\n" * t.count("\n") + " "


def texte_lisible(brut: str) -> str:
    t = re.sub(r"(?<!\\)%[^\n]*", " ", brut)
    for motif in (ENVIRONNEMENTS_IGNORES, MATHS, SANS_ARGUMENT, ENVIRONNEMENT):
        t = motif.sub(_blanchir, t)
    t = re.sub(r"\[[!htbpHP]{1,5}\]", " ", t)
    t = COMMANDE.sub(" ", t)
    return t.replace("~", " ").replace("\\", " ")


def charger_lexique() -> set:
    if not os.path.exists(LEXIQUE):
        return set()
    return {lgn.strip().lower() for lgn in io.open(LEXIQUE, encoding="utf-8")
            if lgn.strip() and not lgn.startswith("#")}


def connu(mot: str, vocabulaire: set, lexique: set) -> bool:
    m = mot.lower().replace("’", "'")
    if m in vocabulaire or m in lexique:
        return True
    # Elision : l'administrateur, d'abord, qu'il
    if "'" in m:
        suite = m.split("'", 1)[1]
        if suite and (suite in vocabulaire or suite in lexique):
            return True
    # Mot compose : chaque membre doit etre connu
    if "-" in m:
        membres = [x for x in m.split("-") if x]
        if membres and all(x in vocabulaire or x in lexique for x in membres):
            return True
    return False


def main() -> int:
    dossier = trouver_dictionnaire()
    if not dossier:
        print("dictionnaire fr.dic introuvable ; cherche dans :")
        for d in DICOS:
            print("   %s" % d)
        return 1
    print("dictionnaire : %s" % dossier)
    vocabulaire = construire_vocabulaire(dossier)
    lexique = charger_lexique()
    print("%d formes connues, %d mots au lexique du projet"
          % (len(vocabulaire), len(lexique)))

    suspects: dict = {}
    for chemin in sorted(glob.glob(os.path.join(MEMOIRE, "*.tex"))):
        nom = os.path.basename(chemin)
        brut = io.open(chemin, encoding="utf-8", errors="replace").read()
        for no, ligne in enumerate(texte_lisible(brut).split("\n"), 1):
            for m in MOT.finditer(ligne):
                mot = m.group(0).strip("'’-")
                if len(mot) < 3 or mot.isupper():
                    continue
                if connu(mot, vocabulaire, lexique):
                    continue
                suspects.setdefault(mot, []).append("%s:%d" % (nom, no))

    par_frequence = sorted(suspects.items(), key=lambda kv: (len(kv[1]), kv[0]))
    print("\n%d forme(s) inconnue(s) du dictionnaire\n" % len(par_frequence))
    print("Les moins frequentes d'abord : un mot vu une seule fois et inconnu")
    print("est le meilleur candidat a la faute de frappe.\n")
    for mot, ou in par_frequence[:60]:
        print("  %-26s x%-3d  %s" % (mot, len(ou), ", ".join(sorted(set(ou))[:3])))
    if len(par_frequence) > 60:
        print("  ... et %d autres, voir le rapport JSON" % (len(par_frequence) - 60))

    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({"date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "dictionnaire": dossier,
                   "formes_connues": len(vocabulaire),
                   "lexique_du_projet": len(lexique),
                   "n_formes_inconnues": len(par_frequence),
                   "formes": [{"mot": m, "occurrences": len(o),
                               "emplacements": sorted(set(o))}
                              for m, o in par_frequence]},
                  f, ensure_ascii=False, indent=2)
    print("\necrit %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
