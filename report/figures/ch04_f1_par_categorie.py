# -*- coding: utf-8 -*-
"""F1 par categorie des deux modeles pris seuls, sans les regles metier.

Source des valeurs : metrics/campagne_avant_nettoyage.json, entrees
« 02_tfidf_seul » et « 05_camembert_seul », toutes deux marquees « defendable »
dans ce fichier. Ces deux configurations n'emploient aucune regle metier, elles
sont donc insensibles a l'audit du 2026-08-22. Les F1-macro correspondants,
0,3753 et 0,5685, sont ceux publies au chapitre 4.

Les configurations avec regles du meme fichier ne sont PAS reprises ici : elles
datent d'avant le nettoyage des regles et ne correspondent pas aux 0,5827 et
0,8343 du memoire.

Sortie : report/img/ch04_f1_par_categorie.png
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Ordre du referentiel, par frequence decroissante dans le corpus (chapitre 3).
CATEGORIES = ["Microsoft", "Réseau", "Applicatifs", "Infrastructure",
              "Système", "Communication", "Sécurité", "Backup"]

TFIDF = {"Applicatifs": 1.0, "Backup": 0.0, "Communication": 0.5636,
         "Infrastructure": 0.0, "Microsoft": 0.0, "Réseau": 0.6446,
         "Système": 0.7945, "Sécurité": 0.0}

CAMEMBERT = {"Applicatifs": 1.0, "Backup": 1.0, "Communication": 0.3243,
             "Infrastructure": 0.0, "Microsoft": 0.5818, "Réseau": 0.642,
             "Système": 1.0, "Sécurité": 0.0}

BLEU, VERT, MUTED, FG = "#2F6DA8", "#1E7A64", "#5A6472", "#1B2430"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["savefig.dpi"] = 200

y = np.arange(len(CATEGORIES))
h = 0.38
a = [TFIDF[c] for c in CATEGORIES]
b = [CAMEMBERT[c] for c in CATEGORIES]

fig, ax = plt.subplots(figsize=(9.4, 4.6))
ax.barh(y + h / 2, a, h, color=BLEU, label="TF-IDF seul, F1-macro 0,3753")
ax.barh(y - h / 2, b, h, color=VERT, label="CamemBERT seul, F1-macro 0,5685")

for i, (va, vb) in enumerate(zip(a, b)):
    for v, dy in ((va, h / 2), (vb, -h / 2)):
        etiquette = "0,00" if v == 0 else ("%.2f" % v).replace(".", ",")
        ax.text(v + 0.015, i + dy, etiquette, va="center", ha="left",
                fontsize=8.2, color=MUTED)

ax.set_yticks(y)
ax.set_yticklabels(CATEGORIES, fontsize=9.4, color=FG)
ax.invert_yaxis()
ax.set_xlim(0, 1.16)
ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_xticklabels(["0", "0,2", "0,4", "0,6", "0,8", "1"], fontsize=8.6,
                   color=MUTED)
ax.set_xlabel("F1 par catégorie, jeu de test de 355 tickets", fontsize=9.5,
              color=FG)
ax.legend(fontsize=8.8, frameon=False, ncol=2, loc="lower center",
          bbox_to_anchor=(0.5, 1.01))
ax.grid(axis="x", alpha=0.22, lw=0.6)
ax.set_axisbelow(True)
for cote in ("top", "right", "left"):
    ax.spines[cote].set_visible(False)
ax.tick_params(axis="y", length=0)

fig.tight_layout()
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "img", "ch04_f1_par_categorie.png")
fig.savefig(out, bbox_inches="tight")
print("ecrit :", out)
