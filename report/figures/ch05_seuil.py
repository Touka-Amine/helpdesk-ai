# -*- coding: utf-8 -*-
"""Calibration du seuil de pertinence du moteur de recherche hybride.

Source des valeurs
------------------
helpdesk-ai/metrics/rag_seuil_balayage.json, produit par

    python src/pipeline/rag_eval.py --balayage-seuil

Le balayage rejoue le protocole d'evaluation (80 requetes du jeu de test, trois
passages demandes) pour chaque valeur de seuil, et releve en plus la distribution
brute des scores de chaque moteur.

Aucune valeur n'est saisie a la main : la figure lit le fichier.

Ce qu'elle montre
-----------------
A gauche, la distribution du meilleur score hybride par requete, avec l'ancien
seuil de 0,50 et le seuil recalibre. L'ancien se situe hors de la plage atteignable
par le score : il ne filtrait rien et marquait « repli » toutes les suggestions.

A droite, ce que le seuil coute et ce qu'il rapporte : la precision de ce qui est
reellement affiche monte, le nombre de suggestions rendues baisse.

Sortie : report/img/ch05_seuil.png
"""
import io
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ICI = os.path.dirname(os.path.abspath(__file__))
ARTEFACT = os.path.join(ICI, "..", "..", "helpdesk-ai", "metrics",
                        "rag_seuil_balayage.json")
SORTIE = os.path.join(ICI, "..", "img", "ch05_seuil.png")

FG, MUTED = "#1B2430", "#5A6472"
BLEU, ORANGE, ROUGE = "#1F4E79", "#C77700", "#A83F3F"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["savefig.dpi"] = 200

ANCIEN_SEUIL = 0.50


def virgule(x, _pos=None):
    return ("%.2f" % x).replace(".", ",")


def main():
    with io.open(ARTEFACT, encoding="utf-8") as f:
        donnees = json.load(f)

    hyb = donnees["moteurs"]["hybride"]
    meilleurs = hyb["distribution"]["meilleur_par_requete"]
    seuil_retenu = donnees["seuil_retenu"]
    seuils = hyb["seuils"]
    precisions = [e["precision_sur_rendus"] for e in hyb["par_seuil"]]
    rendus = [e["resultats_par_requete"] for e in hyb["par_seuil"]]

    fig, (g, d) = plt.subplots(1, 2, figsize=(11.6, 4.3),
                               gridspec_kw={"width_ratios": [1.0, 1.15]})

    # ── gauche : distribution des meilleurs scores ──────────────────────────
    effectifs, _, _ = g.hist(meilleurs, bins=16, color=ORANGE,
                             edgecolor="white", linewidth=0.7)
    g.axvline(ANCIEN_SEUIL, color=ROUGE, linestyle="--", linewidth=1.6)
    g.axvline(seuil_retenu, color=BLEU, linestyle="-", linewidth=1.6)
    # Marge en hauteur pour que les etiquettes ne chevauchent aucune barre.
    haut = max(effectifs) * 1.42
    g.set_ylim(0, haut)
    g.text(ANCIEN_SEUIL - 0.006, haut * 0.97,
           "ancien seuil 0,50 — jamais atteint", color=ROUGE,
           fontsize=9, style="italic", ha="right", va="top")
    g.text(seuil_retenu - 0.006, haut * 0.82,
           "seuil retenu %s" % virgule(seuil_retenu), color=BLEU,
           fontsize=9, style="italic", ha="right", va="top")
    g.set_title("Meilleur score hybride, par requête", fontsize=11,
                color=FG, fontweight="bold")
    g.set_xlabel("Score", fontsize=9.5, color=MUTED)
    g.set_ylabel("Nombre de requêtes", fontsize=9.5, color=MUTED)
    g.set_xlim(0.26, 0.55)
    g.xaxis.set_major_formatter(plt.FuncFormatter(virgule))
    g.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.5)
    g.set_axisbelow(True)
    for bord in ("top", "right"):
        g.spines[bord].set_visible(False)

    # ── droite : ce que le seuil coute et ce qu'il rapporte ─────────────────
    d.plot(seuils, precisions, marker="o", markersize=4, color=BLEU,
           linewidth=1.7, label="Précision de ce qui est affiché")
    d.set_xlabel("Seuil de pertinence", fontsize=9.5, color=MUTED)
    d.set_ylabel("Précision", fontsize=9.5, color=BLEU)
    d.tick_params(axis="y", labelcolor=BLEU)
    d.set_ylim(0.30, 0.52)
    d.xaxis.set_major_formatter(plt.FuncFormatter(virgule))
    d.yaxis.set_major_formatter(plt.FuncFormatter(virgule))

    d2 = d.twinx()
    d2.plot(seuils, rendus, marker="s", markersize=4, color=ORANGE,
            linewidth=1.7, linestyle="--", label="Suggestions rendues")
    d2.set_ylabel("Suggestions par requête", fontsize=9.5, color=ORANGE)
    d2.tick_params(axis="y", labelcolor=ORANGE)
    d2.set_ylim(0.0, 3.4)

    d.axvline(seuil_retenu, color=MUTED, linestyle=":", linewidth=1.2)
    d.set_title("Effet du seuil sur le moteur hybride", fontsize=11,
                color=FG, fontweight="bold")
    d.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.5)
    d.set_axisbelow(True)
    for bord in ("top",):
        d.spines[bord].set_visible(False)
        d2.spines[bord].set_visible(False)

    lignes = d.get_lines()[:1] + d2.get_lines()[:1]
    d.legend(lignes, [l.get_label() for l in lignes], loc="lower left",
             fontsize=9, frameon=False)

    fig.tight_layout()
    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    fig.savefig(SORTIE, bbox_inches="tight")
    print("ecrit %s" % os.path.normpath(SORTIE))


if __name__ == "__main__":
    main()
