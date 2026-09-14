# -*- coding: utf-8 -*-
"""Palette du systeme de design de l'interface, lue directement dans
frontend/src/styles.css : le bloc @theme (mode clair) et le bloc .dark.

Sortie : report/img/ch06_palette.png
"""
import io
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

CSS = r"C:\projetpfe\helpdesk-ai\frontend\src\styles.css"
SORTIE = r"C:\projetpfe\report\img\ch06_palette.png"


def blocs(texte):
    """Renvoie (roles_clair, roles_sombre) sous forme de dictionnaires ordonnes."""
    def extrait(debut):
        i = texte.index(debut)
        j = texte.index("}", i)
        corps = texte[i:j]
        return dict(re.findall(r"--color-([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})", corps))

    return extrait("@theme {"), extrait(".dark {")


def main():
    source = io.open(CSS, encoding="utf-8").read()
    clair, sombre = blocs(source)

    communs = [r for r in clair if r in sombre]
    print("roles en mode clair  :", len(clair))
    print("roles en mode sombre :", len(sombre))
    print("roles redefinis      :", len(communs))

    accents, surfaces = [], []
    for role in communs:
        racine = role[3:] if role.startswith("on-") else role
        if racine.split("-")[0] in ("primary", "secondary", "tertiary", "error"):
            accents.append(role)
        else:
            surfaces.append(role)

    hauteur = max(len(accents), len(surfaces))
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 0.42 * hauteur + 1.0))

    for ax, roles, titre in zip(axes, (accents, surfaces),
                                ("Couleurs d'accent", "Surfaces et contours")):
        ax.set_title(titre, fontsize=11, fontweight="bold", pad=14, loc="left")
        for k, role in enumerate(roles):
            y = hauteur - k - 1
            for x, table in ((0.0, clair), (1.15, sombre)):
                ax.add_patch(Rectangle((x, y + 0.12), 1.0, 0.76,
                                       facecolor=table[role],
                                       edgecolor="#777587", linewidth=0.6))
            ax.text(2.42, y + 0.5, role, va="center", fontsize=8.5, family="monospace")
        ax.text(0.5, hauteur + 0.15, "clair", ha="center", fontsize=8.5, style="italic")
        ax.text(1.65, hauteur + 0.15, "sombre", ha="center", fontsize=8.5, style="italic")
        ax.set_xlim(-0.1, 6.4)
        ax.set_ylim(-0.2, hauteur + 0.55)
        ax.axis("off")

    fig.tight_layout()
    if not os.path.isdir(os.path.dirname(SORTIE)):
        raise SystemExit("dossier img introuvable")
    fig.savefig(SORTIE, dpi=200, bbox_inches="tight", facecolor="white")
    print("ecrit :", SORTIE)


if __name__ == "__main__":
    main()
