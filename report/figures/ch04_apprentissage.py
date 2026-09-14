# -*- coding: utf-8 -*-
"""Courbes d'apprentissage de CamemBERT adapte par LoRA.

Source des valeurs : sortie du Trainer dans notebooks/05_camembert_finetuning.ipynb,
cellule d'entrainement (tableau HTML « Epoch / Training Loss / Validation Loss /
F1 Macro / Accuracy »), execution de 1 630 pas en 15 min 27 s sur GPU MX130.
Le F1 de test issu du decoupage par groupe de titres vaut 0,5685 (meme notebook,
section 6). Aucune valeur n'est recalculee ici : elles sont transcrites.

Sortie : report/img/ch04_apprentissage.png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

EPOCHS = list(range(1, 11))
TRAIN_LOSS = [1.8887, 1.1875, 0.7291, 0.4691, 0.3594,
              0.3511, 0.2592, 0.2265, 0.2468, 0.2789]
VAL_LOSS = [1.783530, 1.219468, 0.719799, 0.467467, 0.318540,
            0.237847, 0.203848, 0.182602, 0.177274, 0.176297]
VAL_F1 = [0.149718, 0.557426, 0.644577, 0.811445, 0.874733,
          0.967929, 0.967929, 0.982468, 0.967929, 0.967929]
TEST_F1 = 0.5685

BLEU, BRIQUE, VERT, ROUGE = "#2F6DA8", "#A83F3F", "#1E7A64", "#C0392B"
FG, MUTED = "#1B2430", "#5A6472"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["savefig.dpi"] = 200

fig, (g, d) = plt.subplots(1, 2, figsize=(11, 4.1))

# --- Panneau gauche : les deux pertes.
g.plot(EPOCHS, TRAIN_LOSS, "o-", color=BLEU, lw=1.8, ms=4.5,
       label="Perte d'entraînement")
g.plot(EPOCHS, VAL_LOSS, "s--", color=BRIQUE, lw=1.8, ms=4.5,
       label="Perte de validation")
g.set_xlabel("Époque", fontsize=9.5, color=FG)
g.set_ylabel("Perte", fontsize=9.5, color=FG)
g.set_title("Convergence", fontsize=11, fontweight="bold", color=FG)
g.set_xticks(EPOCHS)
g.legend(fontsize=8.6, frameon=False)
g.grid(alpha=0.25, lw=0.6)

# --- Panneau droit : F1 de validation contre F1 de test.
d.plot(EPOCHS, VAL_F1, "o-", color=VERT, lw=1.8, ms=4.5,
       label="F1-macro, jeu de validation")
d.axhline(TEST_F1, color=ROUGE, ls=":", lw=1.8,
          label="F1-macro, jeu de test : 0,5685")
d.set_xlabel("Époque", fontsize=9.5, color=FG)
d.set_ylabel("F1-macro", fontsize=9.5, color=FG)
d.set_title("Validation contre test", fontsize=11, fontweight="bold", color=FG)
d.set_xticks(EPOCHS)
d.set_ylim(0, 1.05)
d.legend(fontsize=8.6, frameon=False, loc="lower right")
d.grid(alpha=0.25, lw=0.6)

for ax in (g, d):
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    ax.tick_params(labelsize=8.6, colors=MUTED)

fig.tight_layout()
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "img", "ch04_apprentissage.png")
fig.savefig(out, bbox_inches="tight")
print("ecrit :", out)
