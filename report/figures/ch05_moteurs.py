# -*- coding: utf-8 -*-
"""Comparaison des trois moteurs de recherche.

Source des valeurs
------------------
helpdesk-ai/metrics/rag_eval.json, produit par src/pipeline/rag_eval.py sous le
protocole d'approximation : 80 requetes du jeu de test, trois passages demandes,
est juge pertinent tout passage de la meme categorie que la requete.

Aucune valeur n'est saisie a la main : la figure lit le fichier. La version
precedente de cette image avait ete produite hors du depot, ce qui empechait de
la regenerer apres une recalibration.

Deux precisions, et la distinction compte
-----------------------------------------
precision@3 divise par trois, donc penalise une liste tronquee par le seuil.
La precision de ce qui est affiche porte sur les passages reellement rendus :
c'est elle qui dit ce que vaut la liste que l'administrateur lit. Les montrer
ensemble evite de prendre pour une regression un seuil qui ameliore la qualite
des suggestions en les raccourcissant.

Le taux de repli n'est volontairement pas trace : il s'exprime par rapport a un
seuil unique applique a trois echelles de scores differentes (moyennes 0,18 /
0,61 / 0,31), et n'est donc pas comparable d'un moteur a l'autre.

Sortie : report/img/ch05_moteurs.png
"""
import io
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
ARTEFACT = os.path.join(ICI, "..", "..", "helpdesk-ai", "metrics", "rag_eval.json")
SORTIE = os.path.join(ICI, "..", "img", "ch05_moteurs.png")

FG, MUTED = "#1B2430", "#5A6472"
GRIS, BLEU, ORANGE = "#8D9AAE", "#1F4E79", "#C77700"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["savefig.dpi"] = 200

MOTEURS = [("lexical", "Lexical", GRIS),
           ("semantique", "Sémantique", BLEU),
           ("hybride", "Hybride (servi)", ORANGE)]
INDICATEURS = [("precision_at_3", "Précision@3"),
               ("precision_sur_rendus", "Précision de\nce qui est affiché"),
               ("mrr_at_3", "MRR@3"),
               ("ndcg_at_3", "nDCG@3")]


def virgule(x, chiffres=3):
    return ("%.*f" % (chiffres, x)).replace(".", ",")


def main():
    with io.open(ARTEFACT, encoding="utf-8") as f:
        donnees = json.load(f)
    m = donnees["moteurs"]

    fig, (g, d) = plt.subplots(1, 2, figsize=(12.0, 4.6),
                               gridspec_kw={"width_ratios": [2.5, 1.0]})

    # ── gauche : les quatre indicateurs de qualite ──────────────────────────
    x = np.arange(len(INDICATEURS))
    largeur = 0.26
    for i, (cle, libelle, couleur) in enumerate(MOTEURS):
        valeurs = [m[cle][ind] or 0.0 for ind, _ in INDICATEURS]
        pos = x + (i - 1) * largeur
        g.bar(pos, valeurs, largeur, label=libelle, color=couleur,
              edgecolor="white", linewidth=0.8)
        for px, v in zip(pos, valeurs):
            g.annotate(virgule(v), (px, v), textcoords="offset points",
                       xytext=(0, 3), ha="center", fontsize=8.2, color=FG)

    g.set_xticks(x)
    g.set_xticklabels([lib for _, lib in INDICATEURS], fontsize=9.5)
    g.set_ylabel("Valeur", fontsize=9.5, color=MUTED)
    g.set_ylim(0, 0.70)
    g.set_yticks([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
    g.set_yticklabels([virgule(v, 1) for v in
                       [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]], fontsize=9)
    g.set_title("Qualité des passages retenus", fontsize=11.5,
                color=FG, fontweight="bold")
    g.legend(fontsize=9.5, frameon=False, loc="upper right", ncol=3)
    g.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.5)
    g.set_axisbelow(True)
    for bord in ("top", "right"):
        g.spines[bord].set_visible(False)

    # ── droite : longueur de la liste rendue ────────────────────────────────
    libelles = [lib.split(" ")[0] for _, lib, _ in MOTEURS]
    valeurs = [m[cle]["resultats_par_requete"] for cle, _, _ in MOTEURS]
    couleurs = [c for _, _, c in MOTEURS]
    barres = d.bar(libelles, valeurs, 0.55, color=couleurs,
                   edgecolor="white", linewidth=0.8)
    for b, v in zip(barres, valeurs):
        d.annotate(virgule(v, 2), (b.get_x() + b.get_width() / 2, v),
                   textcoords="offset points", xytext=(0, 3),
                   ha="center", fontsize=8.6, color=FG)
    d.axhline(donnees["top_k"], color=MUTED, linestyle="--", linewidth=1.0)
    d.text(2.45, donnees["top_k"] - 0.08, "%d demandés" % donnees["top_k"],
           fontsize=8.6, color=MUTED, style="italic", ha="right", va="top")
    d.set_ylim(0, 3.5)
    d.set_ylabel("Suggestions par requête", fontsize=9.5, color=MUTED)
    d.set_title("Longueur de la liste rendue", fontsize=11.5,
                color=FG, fontweight="bold")
    d.tick_params(axis="x", labelsize=9.5)
    d.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.5)
    d.set_axisbelow(True)
    for bord in ("top", "right"):
        d.spines[bord].set_visible(False)

    fig.tight_layout()
    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    fig.savefig(SORTIE, bbox_inches="tight")
    print("ecrit %s" % os.path.normpath(SORTIE))


if __name__ == "__main__":
    main()
