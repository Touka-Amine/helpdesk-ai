# -*- coding: utf-8 -*-
"""Execution de la suite de tests et couverture mesuree.

Source des valeurs
------------------
helpdesk-ai/metrics/couverture_tests.txt, produit par

    python -m pytest tests/ --ignore=tests/test_api_integration.py --cov=src -q

depuis helpdesk-ai/. Les tests d'integration de l'API sont ecartes de cette
commande parce que c'est le perimetre que rejoue l'integration continue.

Aucune valeur n'est saisie a la main : la figure lit le fichier. La version
precedente de cette image etait un JPEG produit hors du depot, qui annoncait
encore 132 tests alors que la suite en compte davantage.

Le rapport de couverture complet liste une quarantaine de modules. La figure
n'en montre qu'une selection, la meme que l'image d'origine : les modules que le
memoire commente, du mieux couvert au moins couvert. Le TOTAL porte, lui, sur
l'ensemble des modules.

Sortie : report/img/ch07_tests.png
"""
import io
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ICI = os.path.dirname(os.path.abspath(__file__))
ARTEFACT = os.path.join(ICI, "..", "..", "helpdesk-ai", "metrics",
                        "couverture_tests.txt")
SORTIE = os.path.join(ICI, "..", "img", "ch07_tests.png")

FOND, TEXTE, VERT, GRIS = "#1F2430", "#E6E8EC", "#8FE3A5", "#9AA3B2"

COMMANDE = "pytest tests/ --ignore=tests/test_api_integration.py --cov=src -q"

# Modules commentes par le memoire, dans l'ordre d'affichage.
MODULES = [
    "src/models/heuristics.py",
    "src/knowledge/quality.py",
    "src/registry/model_registry.py",
    "src/rag/hybrid_engine.py",
    "src/rag/engine.py",
    "src/pipeline/collect.py",
    "src/monitoring/ml_monitor.py",
]

plt.rcParams["font.family"] = "DejaVu Sans Mono"
plt.rcParams["savefig.dpi"] = 200


def lire():
    with io.open(ARTEFACT, encoding="utf-8", errors="replace") as f:
        lignes = f.read().splitlines()

    mesures, total, resume = {}, None, None
    for ligne in lignes:
        nette = ligne.replace("\\", "/").strip()
        m = re.match(r"^(\S+\.py)\s+(\d+)\s+(\d+)\s+(\d+%)$", nette)
        if m:
            mesures[m.group(1)] = (m.group(2), m.group(3), m.group(4))
            continue
        m = re.match(r"^TOTAL\s+(\d+)\s+(\d+)\s+(\d+%)$", nette)
        if m:
            total = (m.group(1), m.group(2), m.group(3))
            continue
        m = re.match(r"^(\d+) passed in ([\d.]+)s", nette)
        if m:
            resume = "%s passed in %ss" % (m.group(1), m.group(2))

    manquants = [c for c in MODULES if c not in mesures]
    if manquants or total is None or resume is None:
        raise SystemExit("artefact incomplet : %s" % (manquants or "TOTAL/resume"))
    return mesures, total, resume


def main():
    mesures, total, resume = lire()

    gauche = max([len(c) for c in MODULES] + [len("TOTAL"), len("Name")]) + 2
    def rang(nom, a, b, c):
        return "%-*s %7s %6s %6s" % (gauche, nom, a, b, c)

    lignes = [("$ " + COMMANDE, "cmd"), ("", "n")]
    lignes.append((rang("Name", "Stmts", "Miss", "Cover"), "n"))
    lignes.append(("-" * (gauche + 21), "d"))
    for cle in MODULES:
        a, b, c = mesures[cle]
        lignes.append((rang(cle, a, b, c), "n"))
    lignes.append(("-" * (gauche + 21), "d"))
    lignes.append((rang("TOTAL", *total), "n"))
    lignes.append(("", "n"))
    lignes.append((resume, "n"))

    hauteur = 0.30 * len(lignes) + 0.55
    fig = plt.figure(figsize=(11.2, hauteur))
    fig.patch.set_facecolor(FOND)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(FOND)
    ax.axis("off")

    y = 1.0 - 0.30 / hauteur
    pas = 0.30 / hauteur
    for contenu, genre in lignes:
        if genre == "cmd":
            ax.text(0.018, y, "$", color=VERT, fontsize=11,
                    fontweight="bold", va="top", ha="left")
            ax.text(0.038, y, contenu[2:], color=TEXTE, fontsize=11,
                    fontweight="bold", va="top", ha="left")
        else:
            ax.text(0.018, y, contenu, color=GRIS if genre == "d" else TEXTE,
                    fontsize=11, va="top", ha="left")
        y -= pas

    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    fig.savefig(SORTIE, facecolor=FOND, bbox_inches="tight", pad_inches=0.22)
    print("ecrit %s — %s" % (os.path.normpath(SORTIE), resume))


if __name__ == "__main__":
    main()
