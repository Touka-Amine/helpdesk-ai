# -*- coding: utf-8 -*-
"""Repartition des tickets entre les huit filiales desservies par le service.

Source des valeurs
------------------
helpdesk-ai/data/processed/HelpDesk1.csv, colonne « Filiale », comptage direct.
Le script lit le corpus et trace ce qu'il contient ; aucune valeur n'est saisie
a la main. Total controle : 1800 tickets, 8 filiales, aucun champ manquant.

Libelles
--------
Les filiales sont nommees par le code qu'elles portent dans la colonne
« Filiale » du fichier d'export, sur decision de l'auteur du memoire. Les codes
sont lus dans le fichier, jamais saisis ici, et sont ranges par volume
decroissant. Aucun nom de personne n'apparait sur la figure.

Sortie : report/img/ch01_repartition_entites.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ICI = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(ICI, "..", "..", "helpdesk-ai", "data", "processed", "HelpDesk1.csv")
SORTIE = os.path.join(ICI, "..", "img", "ch01_repartition_entites.png")

TOTAL, NB_FILIALES = 1800, 8

FG, MUTED = "#1B2430", "#5A6472"
BLEU = "#1F4E79"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["savefig.dpi"] = 200


def main():
    df = pd.read_csv(CSV)
    v = df["Filiale"].value_counts().sort_values(ascending=False)
    assert int(v.sum()) == TOTAL, "total %d, attendu %d" % (v.sum(), TOTAL)
    assert len(v) == NB_FILIALES, "%d filiales, attendu %d" % (len(v), NB_FILIALES)

    libelles = v.index.tolist()
    valeurs = v.tolist()

    fig, ax = plt.subplots(figsize=(8.6, 4.0))
    barres = ax.barh(libelles[::-1], valeurs[::-1], color=BLEU, height=0.62)

    for barre, val in zip(barres, valeurs[::-1]):
        part = 100.0 * val / TOTAL
        etiquette = ("%d   (%.1f %%)" % (val, part)).replace(".", ",")
        ax.text(val + 4, barre.get_y() + barre.get_height() / 2, etiquette,
                va="center", fontsize=9, color=MUTED)

    ax.set_xlabel("Nombre de tickets déposés sur la période couverte",
                  fontsize=9.6, color=MUTED, labelpad=9)
    ax.set_xlim(0, max(valeurs) * 1.22)
    ax.tick_params(length=0, labelsize=9.4, colors=FG)
    for cote in ("top", "right", "left"):
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color("#C8CED6")
    ax.grid(axis="x", color="#E6E9EE", linewidth=0.8)
    ax.set_axisbelow(True)

    ecart = max(valeurs) - min(valeurs)
    ax.text(0.0, 1.10,
            "Les huit filiales du groupe desservies par le service support",
            transform=ax.transAxes, fontsize=12.0, fontweight="bold",
            color=FG, va="bottom")
    ax.text(0.0, 1.02,
            ("%d tickets au total, de %d à %d par filiale, soit %d tickets d'écart"
             % (TOTAL, min(valeurs), max(valeurs), ecart)),
            transform=ax.transAxes, fontsize=9.2, color=MUTED, va="bottom")

    fig.tight_layout()
    fig.savefig(SORTIE, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print("total %d, %d filiales, de %d a %d (ecart %d)"
          % (TOTAL, len(v), min(valeurs), max(valeurs), ecart))
    print("ecrit :", os.path.normpath(SORTIE))


if __name__ == "__main__":
    main()
