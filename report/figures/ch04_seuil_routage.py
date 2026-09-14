# -*- coding: utf-8 -*-
"""Precision et couverture du routage automatique selon le seuil de confiance.

Source des valeurs
------------------
helpdesk-ai/metrics/calibration_confiance.json, produit par
helpdesk-ai/scripts/calibration_confiance.py. Le script de mesure reproduit le
protocole des experiences (355 tickets, graine 42) et retrouve exactement les
quatre tranches publiees au tableau 4.10 du memoire : 42 / 121 / 110 / 82
tickets, precisions 0 %, 33,9 %, 89,1 %, 81,7 %.

Aucune valeur n'est saisie a la main : la figure lit le fichier.

La courbe porte sur le classifieur seul, avant application des regles metier,
puisque c'est son index de confiance qui commande le routage.

Sortie : report/img/ch04_seuil_routage.png
"""
import io
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ICI = os.path.dirname(os.path.abspath(__file__))
ARTEFACT = os.path.join(ICI, "..", "..", "helpdesk-ai", "metrics",
                        "calibration_confiance.json")
SORTIE = os.path.join(ICI, "..", "img", "ch04_seuil_routage.png")

FG, MUTED = "#1B2430", "#5A6472"
BLEU, VERT, ORANGE = "#1F4E79", "#2E7D52", "#C77700"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["savefig.dpi"] = 200


def main():
    with io.open(ARTEFACT, encoding="utf-8") as f:
        d = json.load(f)
    r = d["resultats"]["ml_seul"]
    pts = [p for p in r["courbe"] if p["precision"] is not None]
    seuils = [p["seuil"] for p in pts]
    couv = [p["couverture"] for p in pts]
    prec = [p["precision"] for p in pts]

    a40, a60 = r["au_seuil_0_40"], r["au_seuil_0_60"]

    fig, ax = plt.subplots(figsize=(9.0, 4.4))
    ax.plot(seuils, couv, color=BLEU, linewidth=2.2,
            label="Couverture : part des tickets routés automatiquement")
    ax.plot(seuils, prec, color=VERT, linewidth=2.2,
            label="Précision des tickets ainsi routés")

    for s, val, libelle in ((0.40, a40, "Seuil initial"), (0.60, a60, "Seuil retenu")):
        ax.axvline(s, color=ORANGE, linestyle="--", linewidth=1.4, zorder=1)
        ax.text(s, 104, libelle + ("\n%.2f" % s).replace(".", ","),
                ha="center", va="bottom", fontsize=8.8, color=ORANGE,
                fontweight="bold")
        ax.plot([s, s], [val["couverture"], val["precision"]], " ")
        for y, coul in ((val["couverture"], BLEU), (val["precision"], VERT)):
            ax.plot(s, y, "o", color=coul, markersize=6, zorder=3)
            ax.annotate(("%.1f %%" % y).replace(".", ","), (s, y),
                        textcoords="offset points", xytext=(9, -4),
                        fontsize=9.0, color=coul, fontweight="bold")

    ax.set_xlabel("Seuil appliqué à l'index de confiance", fontsize=9.8,
                  color=MUTED, labelpad=9)
    ax.set_ylabel("Pourcentage", fontsize=9.8, color=MUTED, labelpad=9)
    ax.set_xlim(0, 1.0)
    ax.set_ylim(0, 113)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.tick_params(labelsize=9.0, colors=MUTED, length=0)
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    for cote in ("bottom", "left"):
        ax.spines[cote].set_color("#C8CED6")
    ax.grid(color="#E6E9EE", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="lower left", fontsize=8.8, frameon=False)

    ax.text(0.0, 1.26, "Ce que coûte et ce que rapporte le seuil de routage",
            transform=ax.transAxes, fontsize=12.0, fontweight="bold",
            color=FG, va="bottom")
    # Virgule decimale : la substitution porte sur les nombres deja formates.
    sous = ("Protocole des expériences, 355 tickets. Relever le seuil de 0,40 à 0,60\n"
            "fait passer la précision de %s à %s, et la couverture de %s à %s."
            % (("%.1f" % a40["precision"]).replace(".", ",") + " %",
               ("%.1f" % a60["precision"]).replace(".", ",") + " %",
               ("%.1f" % a40["couverture"]).replace(".", ",") + " %",
               ("%.1f" % a60["couverture"]).replace(".", ",") + " %"))
    ax.text(0.0, 1.11, sous, transform=ax.transAxes, fontsize=9.0,
            color=MUTED, va="bottom", linespacing=1.5)

    fig.tight_layout()
    fig.savefig(SORTIE, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print("seuil 0,40 : couverture %.1f %%, precision %.1f %%"
          % (a40["couverture"], a40["precision"]))
    print("seuil 0,60 : couverture %.1f %%, precision %.1f %%"
          % (a60["couverture"], a60["precision"]))
    print("ecrit :", os.path.normpath(SORTIE))


if __name__ == "__main__":
    main()
