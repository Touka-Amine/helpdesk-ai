# -*- coding: utf-8 -*-
"""Relecture mecanique du memoire : les fautes qu'un oeil ne voit plus.

Ce que ce controleur cherche
----------------------------
Pas l'orthographe — aucun dictionnaire n'est installe sur la machine, et un
controleur qui pretendrait la verifier sans dictionnaire mentirait. Il cherche
les fautes qui se reperent par leur FORME, et qui survivent le mieux a la
relecture humaine parce que l'oeil les lit comme correctes :

  1. mots doubles consecutifs (« de de », « la la »), y compris par-dessus un
     saut de ligne, qui est le cas le plus frequent et le plus invisible ;
  2. guillemets francais ouvrants sans fermant, ou l'inverse, dans un paragraphe ;
  3. accolades et parentheses desequilibrees dans un paragraphe ;
  4. espace manquante avant une unite en \\, ou nombre colle a son unite ;
  5. doubles espaces et espaces en fin de ligne, invisibles au rendu mais qui
     trahissent une reecriture bâclee ;
  6. ponctuation doublee (« ,, », « .. » hors points de suspension).

Chaque signalement donne fichier, ligne et extrait, pour etre juge a la main :
un controleur typographique propose, il ne corrige pas.

Sortie : scripts/verification/rapport_typographie.json
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
SORTIE = os.path.join(ICI, "rapport_typographie.json")

# Les mots qui se repetent legitimement en francais.
REPETITIONS_LEGITIMES = {"nous nous", "vous vous", "se se", "si si", "a a",
                         "que que", "plus plus", "tout tout"}

# Commandes dont l'argument n'est PAS du texte courant : on retire la commande
# et son argument.
SANS_ARGUMENT_LISIBLE = re.compile(
    r"\\(?:label|ref|pageref|autoref|nameref|cite|includegraphics|input|include|"
    r"usepackage|newcolumntype|renewcommand|newcommand|rowcolor)\s*(?:\[[^\]]*\])?"
    r"(?:\{[^{}]*\})+")
# Les autres commandes encadrent du texte a relire : on retire le nom de la
# commande et on GARDE l'argument. La premiere version mangeait la fin de la
# ligne apres \texttt, ce qui collait deux mots eloignes et faisait voir un
# « champ champ » qui n'existe pas (chap_03.tex, 2026-10-10).
NOM_DE_COMMANDE = re.compile(r"\\[a-zA-Z]+\*?")


def paragraphes(texte: str):
    """Rend (numero exact de la premiere ligne, texte du paragraphe).

    Le decoupage doit conserver les separateurs pour que le compte de lignes
    reste juste : une version anterieure ajoutait deux lignes par paragraphe au
    jugé et derivait de quelques lignes sur un fichier long, ce qui envoie le
    relecteur au mauvais endroit.
    """
    morceaux = re.split(r"(\n\s*\n)", texte)
    ligne = 1
    for i in range(0, len(morceaux), 2):
        bloc = morceaux[i]
        yield ligne, bloc
        ligne += bloc.count("\n")
        if i + 1 < len(morceaux):
            ligne += morceaux[i + 1].count("\n")


def nettoyer(bloc: str) -> str:
    """Ne garde que le texte a relire, en preservant les sauts de ligne.

    Les numeros de ligne sont comptes sur ce texte nettoye : remplacer par des
    espaces plutot que supprimer, et ne jamais toucher aux « \\n ».
    """
    sans_commentaire = re.sub(r"(?<!\\)%[^\n]*", "", bloc)

    def espaces(m):
        return " " * len(m.group(0))

    t = SANS_ARGUMENT_LISIBLE.sub(espaces, sans_commentaire)
    return NOM_DE_COMMANDE.sub(espaces, t)


def controler(nom: str, texte: str) -> list:
    faits = []
    lignes = texte.split("\n")

    # 1. mots doubles, y compris par-dessus un retour a la ligne
    plat = nettoyer(texte)
    for m in re.finditer(r"\b([A-Za-zÀ-ÿ']{2,})\s+\1\b", plat, re.IGNORECASE):
        if m.group(0).lower().replace("\n", " ") in REPETITIONS_LEGITIMES:
            continue
        no = plat[:m.start()].count("\n") + 1
        faits.append({"type": "mot double", "fichier": nom, "ligne": no,
                      "extrait": " ".join(m.group(0).split())})

    # 2. guillemets francais, par paragraphe
    for no, bloc in paragraphes(texte):
        if bloc.count("«") != bloc.count("»"):
            faits.append({"type": "guillemets desequilibres", "fichier": nom,
                          "ligne": no,
                          "extrait": "%d ouvrants, %d fermants"
                                     % (bloc.count("«"), bloc.count("»"))})

    # 3. accolades et parentheses, par paragraphe
    for no, bloc in paragraphes(texte):
        sans_echap = bloc.replace("\\{", "").replace("\\}", "").replace("\\%", "")
        for ouvre, ferme, quoi in (("{", "}", "accolades"), ("(", ")", "parentheses")):
            if sans_echap.count(ouvre) != sans_echap.count(ferme):
                faits.append({"type": "%s desequilibrees" % quoi, "fichier": nom,
                              "ligne": no,
                              "extrait": "%d ouvrantes, %d fermantes"
                                         % (sans_echap.count(ouvre),
                                            sans_echap.count(ferme))})

    # 4. nombre colle a une unite
    for i, l in enumerate(lignes, 1):
        for m in re.finditer(r"\b\d+(?:[.,]\d+)?(ms|s|Mo|Go|ko|%)\b", l):
            faits.append({"type": "unite collee au nombre", "fichier": nom, "ligne": i,
                          "extrait": m.group(0)})

    # 5. doubles espaces et espaces finales, hors commentaires : les en-tetes de
    # fichier alignent leurs cadres avec des espaces, et c'est voulu.
    for i, l in enumerate(lignes, 1):
        if l.lstrip().startswith("%"):
            continue
        if re.search(r"\S  +\S", l):
            faits.append({"type": "double espace", "fichier": nom, "ligne": i,
                          "extrait": l.strip()[:70]})
        if l != l.rstrip():
            faits.append({"type": "espace en fin de ligne", "fichier": nom,
                          "ligne": i, "extrait": l.strip()[:70]})

    # 6. ponctuation doublee
    for i, l in enumerate(lignes, 1):
        for m in re.finditer(r"(?<!\.)(,,|;;|::|!!|\?\?)(?!\.)", l):
            faits.append({"type": "ponctuation doublee", "fichier": nom, "ligne": i,
                          "extrait": m.group(0)})
    return faits


def main() -> int:
    fichiers = sorted(glob.glob(os.path.join(MEMOIRE, "*.tex")))
    if not fichiers:
        print("aucun .tex dans %s" % MEMOIRE)
        return 1

    tous = []
    for chemin in fichiers:
        tous += controler(os.path.basename(chemin),
                          io.open(chemin, encoding="utf-8", errors="replace").read())

    par_type = {}
    for f in tous:
        par_type.setdefault(f["type"], []).append(f)

    print("=" * 70)
    for t in sorted(par_type):
        print("\n%s — %d" % (t, len(par_type[t])))
        for f in par_type[t][:12]:
            print("   %-18s l.%-5d %s" % (f["fichier"], f["ligne"], f["extrait"]))
        if len(par_type[t]) > 12:
            print("   ... et %d autres" % (len(par_type[t]) - 12))
    print("\n" + "=" * 70)
    print("%d fichiers, %d signalement(s)" % (len(fichiers), len(tous)))

    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({"date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "objet": "Relecture mecanique : formes fautives, pas orthographe.",
                   "n_fichiers": len(fichiers), "n_signalements": len(tous),
                   "par_type": {t: par_type[t] for t in sorted(par_type)}},
                  f, ensure_ascii=False, indent=2)
    print("ecrit %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
