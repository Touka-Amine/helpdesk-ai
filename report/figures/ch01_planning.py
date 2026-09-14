# -*- coding: utf-8 -*-
"""Deroulement effectif du projet, reconstitue depuis l'historique du depot Git.

Source des valeurs
------------------
`git log --format=%ad --date=short -- <chemins>` pour chaque volet de travail.
La figure compte les commits par mois et par volet. Aucune date n'est estimee :
le script interroge le depot et trace ce qu'il trouve.

Pourquoi un compte d'activite plutot qu'un diagramme de Gantt classique
------------------------------------------------------------------------
Les bornes brutes du premier et du dernier commit ne distinguent rien : le
commit initial touche tous les repertoires, et les corrections de fin de projet
aussi. Les cinq volets s'etalent alors du 05/05 au 08/09 sans que la figure
apprenne quoi que ce soit. Le compte mensuel, lui, fait apparaitre le
sequencement reel du travail.

Ce que la figure ne dit pas : un commit n'est pas une unite de charge. Le nombre
traduit un rythme d'activite, non un effort.

Sortie : report/img/ch01_planning.png
"""
import os
import subprocess
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.abspath(os.path.join(ICI, "..", ".."))
SORTIE = os.path.join(ICI, "..", "img", "ch01_planning.png")

FG, MUTED = "#1B2430", "#5A6472"

VOLETS = [
    ("Analyse et préparation des données", [
        "helpdesk-ai/src/data", "helpdesk-ai/src/pipeline/build_dataset.py",
        "helpdesk-ai/notebooks/01_eda.ipynb",
        "helpdesk-ai/notebooks/02_preprocessing.ipynb"]),
    ("Classification et règles métier", [
        "helpdesk-ai/src/models", "helpdesk-ai/notebooks/03_modeling.ipynb",
        "helpdesk-ai/notebooks/05_camembert_finetuning.ipynb"]),
    ("Recherche de cas et modèle de langage", [
        "helpdesk-ai/src/rag", "helpdesk-ai/src/knowledge",
        "helpdesk-ai/api/services/llm_service.py",
        "helpdesk-ai/notebooks/04_rag.ipynb",
        "helpdesk-ai/notebooks/06_rag_semantique.ipynb",
        "helpdesk-ai/notebooks/07_rag_evaluation.ipynb"]),
    ("Application web et intégration", [
        "helpdesk-ai/api", "helpdesk-ai/frontend"]),
    ("Industrialisation et tests", [
        "helpdesk-ai/docker", "helpdesk-ai/dvc.yaml",
        "helpdesk-ai/src/registry", "helpdesk-ai/src/monitoring",
        "helpdesk-ai/tests"]),
    ("Rédaction du mémoire", ["report"]),
]

MOIS = {"2026-05": "Mai", "2026-06": "Juin", "2026-07": "Juillet",
        "2026-08": "Août", "2026-09": "Septembre"}


def commits(chemins):
    dates = []
    for c in chemins:
        out = subprocess.run(
            ["git", "log", "--format=%ad", "--date=short", "--", c],
            cwd=DEPOT, capture_output=True, text=True)
        dates += [l.strip() for l in out.stdout.splitlines() if l.strip()]
    return Counter(d[:7] for d in dates)


def main():
    cles = sorted(MOIS)
    matrice = []
    for nom, chemins in VOLETS:
        c = commits(chemins)
        matrice.append([c.get(m, 0) for m in cles])
    M = np.array(matrice)
    total = int(M.sum())

    fig, ax = plt.subplots(figsize=(9.0, 3.9))
    vmax = M.max()
    ax.imshow(M, cmap="Blues", vmin=0, vmax=vmax, aspect="auto")

    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            if v == 0:
                ax.text(j, i, "·", ha="center", va="center",
                        fontsize=11, color="#B8C0CC")
            else:
                ax.text(j, i, str(v), ha="center", va="center", fontsize=10.5,
                        fontweight="bold" if v > 0.55 * vmax else "normal",
                        color="white" if v > 0.55 * vmax else FG)

    ax.set_xticks(range(len(cles)))
    ax.set_xticklabels([MOIS[m] for m in cles], fontsize=9.4, color=FG)
    ax.set_yticks(range(len(VOLETS)))
    ax.set_yticklabels([v[0] for v in VOLETS], fontsize=9.2, color=FG)
    ax.tick_params(length=0)
    ax.xaxis.set_ticks_position("top")
    for bord in ax.spines.values():
        bord.set_visible(False)

    ax.text(0.0, 1.30, "Déroulement effectif du projet",
            transform=ax.transAxes, fontsize=12.0, fontweight="bold",
            color=FG, va="bottom")
    ax.text(0.0, 1.21,
            "Nombre de modifications enregistrées dans le dépôt, "
            "par volet de travail et par mois (%d au total)" % total,
            transform=ax.transAxes, fontsize=9.0, color=MUTED, va="bottom")

    fig.tight_layout()
    fig.savefig(SORTIE, bbox_inches="tight", facecolor="white", dpi=200)
    plt.close(fig)

    for (nom, _), ligne in zip(VOLETS, M):
        print("%-40s %s" % (nom, "  ".join("%s:%2d" % (MOIS[m], v)
                                           for m, v in zip(cles, ligne))))
    print("total %d commits" % total)
    print("ecrit :", os.path.normpath(SORTIE))


if __name__ == "__main__":
    main()
