# -*- coding: utf-8 -*-
"""Matrice de confusion de CamemBERT adapte par LoRA, protocole stratifie.

Source des valeurs
------------------
Effectifs repris de la figure produite par notebooks/05_camembert_finetuning.ipynb
(notebooks/figures/cam_01_confusion.png), corroborés terme a terme par le texte
du chapitre 4 :
  - « La totalite des 21 tickets Infrastructure y est versee [dans Reseau], ainsi
    que 19 des 20 tickets Securite et 45 des 93 tickets Microsoft » ;
  - « le modele classe correctement 48 tickets [Microsoft] » ;
  - « Quatre categories sont parfaitement traitees : Applicatifs, Backup, Reseau
    et Systeme » ;
  - support du jeu de test : Applicatifs 68, Microsoft 93, Reseau 78,
    Communication 31, Systeme 29, Infrastructure 21, Securite 20, Backup 15.

Controle arithmetique automatique en fin de script :
  - total = 355, soit test_size de models/camembert_metadata.json ;
  - exactitude = 244/355 = 0,6873, soit accuracy du meme fichier.

Ce modele est pris SANS les regles metier : son F1-macro vaut 0,5685. La
configuration avec regles, a 0,8343, n'est pas celle representee ici.

Sortie : report/img/ch04_confusion_camembert.png
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CATEGORIES = ["Applicatifs", "Backup", "Communication", "Infrastructure",
              "Microsoft", "Réseau", "Système", "Sécurité"]

# Lignes = categorie reelle, colonnes = categorie predite.
M = np.array([
    [68,  0,  0, 0,  0,  0,  0, 0],   # Applicatifs
    [ 0, 15,  0, 0,  0,  0,  0, 0],   # Backup
    [ 0,  0,  6, 0, 23,  2,  0, 0],   # Communication
    [ 0,  0,  0, 0,  0, 21,  0, 0],   # Infrastructure
    [ 0,  0,  0, 0, 48, 45,  0, 0],   # Microsoft
    [ 0,  0,  0, 0,  0, 78,  0, 0],   # Réseau
    [ 0,  0,  0, 0,  0,  0, 29, 0],   # Système
    [ 0,  0,  0, 0,  1, 19,  0, 0],   # Sécurité
], dtype=int)

F1_MACRO, EXACTITUDE, TOTAL = 0.5685, 0.6873, 355

FG, MUTED = "#1B2430", "#5A6472"
BLEU_FONCE, BLEU_CLAIR = "#1F4E79", "#DCE9F8"
ROUGE = "#A83F3F"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["savefig.dpi"] = 200


def rendre(matrice, categories, titre, sous_titre, sortie,
           largeur=10.4, hauteur=7.1):
    n = len(categories)
    support = matrice.sum(axis=1)
    # Rappel : indefini pour une categorie sans aucun ticket de test.
    rappel = np.array([matrice[i, i] / support[i] if support[i] else np.nan
                       for i in range(n)])

    fig, ax = plt.subplots(figsize=(largeur, hauteur))
    vmax = matrice.max()
    ax.imshow(matrice, cmap="Blues", vmin=0, vmax=vmax, aspect="auto")

    for i in range(n):
        for j in range(n):
            v = matrice[i, j]
            if v == 0:
                # Les zeros restent lisibles sans attirer l'oeil.
                ax.text(j, i, "0", ha="center", va="center",
                        fontsize=8, color="#B8C0CC")
                continue
            sombre = v > 0.55 * vmax
            ax.text(j, i, str(v), ha="center", va="center",
                    fontsize=10.5, fontweight="bold" if i == j else "normal",
                    color="white" if sombre else FG)

    # Encadrement de la diagonale : ce sont les predictions correctes.
    for i in range(n):
        ax.add_patch(plt.Rectangle((i - 0.5, i - 0.5), 1, 1, fill=False,
                                   edgecolor=BLEU_FONCE, linewidth=2.0,
                                   zorder=3))

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(categories, fontsize=8.2, color=FG, rotation=18,
                       ha="right", rotation_mode="anchor")
    ax.set_yticklabels(["%s  (%d)" % (c, s) for c, s in zip(categories, support)],
                       fontsize=8.6, color=FG)
    ax.set_xlabel("Catégorie prédite par le modèle", fontsize=9.6,
                  color=MUTED, labelpad=9)
    ax.set_ylabel("Catégorie réelle  (nombre de tickets)", fontsize=9.6,
                  color=MUTED, labelpad=9)
    ax.tick_params(length=0)
    for bord in ax.spines.values():
        bord.set_visible(False)

    # Colonne de rappel, posee a droite de la grille.
    x_rappel = n - 0.15
    ax.text(x_rappel + 0.55, -0.82, "Rappel", fontsize=9.2, fontweight="bold",
            color=FG, ha="center", va="center")
    for i in range(n):
        if np.isnan(rappel[i]):
            libelle, couleur = "sans objet", MUTED
        else:
            libelle = ("%.2f" % rappel[i]).replace(".", ",")
            couleur = ROUGE if rappel[i] < 0.70 else FG
        ax.text(x_rappel + 0.55, i, libelle, fontsize=9.2, color=couleur,
                ha="center", va="center",
                fontweight="bold" if couleur == ROUGE else "normal")
    ax.set_xlim(-0.5, x_rappel + 1.15)

    # Titre et sous-titre poses a la main : set_title les superposerait.
    ax.text(0.5, 1.135, titre, transform=ax.transAxes, fontsize=12.4,
            fontweight="bold", color=FG, ha="center", va="bottom")
    ax.text(0.5, 1.055, sous_titre, transform=ax.transAxes, fontsize=9.2,
            color=MUTED, ha="center", va="bottom", linespacing=1.5)

    fig.tight_layout()
    fig.savefig(sortie, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return support, rappel


if __name__ == "__main__":
    ici = os.path.dirname(os.path.abspath(__file__))
    sortie = os.path.join(ici, "..", "img", "ch04_confusion_camembert.png")

    # Controles avant trace : les chiffres doivent reproduire les metadonnees.
    total = int(M.sum())
    justes = int(np.trace(M))
    exactitude = justes / float(total)
    assert total == TOTAL, "total %d, attendu %d" % (total, TOTAL)
    assert abs(exactitude - EXACTITUDE) < 5e-4, "exactitude %.4f" % exactitude

    titre = "Matrice de confusion de CamemBERT adapté par LoRA"
    sous = ("355 tickets de test, 8 catégories, modèle pris sans les règles métier\n"
            "F1-macro 0,5685, exactitude 68,7 %")
    support, rappel = rendre(M, CATEGORIES, titre, sous, sortie)

    print("total %d, corrects %d, exactitude %.4f" % (total, justes, exactitude))
    for c, s, r in zip(CATEGORIES, support, rappel):
        print("  %-15s support %3d  rappel %s"
              % (c, s, "sans objet" if np.isnan(r) else "%.2f" % r))
    print("ecrit :", os.path.normpath(sortie))
