# -*- coding: utf-8 -*-
"""Volumetrie mensuelle des tickets deposes, telle que le corpus brut la donne.

Source unique : helpdesk-ai/data/raw/HelpDesk1.csv, colonne « Date de creation ».
Les 1 800 lignes portent toutes une date exploitable. La periode couverte va du
1er janvier 2025 au 17 fevrier 2026, soit quatorze mois calendaires.

Le dernier mois est partiel : l'export s'arrete au 17 fevrier 2026. La figure le
signale plutot que de laisser croire a une chute d'activite.

Cette figure remplace une version anterieure dont les valeurs ne correspondaient
a aucun fichier du depot (total de 828 tickets au lieu de 1 800) et dont le
script source n'existait pas.

Sortie : report/img/ch01_volumetrie_mensuelle.png
"""
import csv
import io
import os
import collections
import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE = os.path.join(RACINE, "helpdesk-ai", "data", "raw", "HelpDesk1.csv")
SORTIE = os.path.join(RACINE, "report", "img", "ch01_volumetrie_mensuelle.png")

BLEU, GRIS, TEXTE = "#1F4E79", "#9AA3AD", "#5A6472"
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin",
        "juil.", "août", "sept.", "oct.", "nov.", "déc."]

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["savefig.dpi"] = 200

brut = io.open(SOURCE, encoding="utf-8-sig").read()
lignes = list(csv.DictReader(io.StringIO(brut)))
colonne = [c for c in lignes[0].keys() if "cr" in c.lower() and "ation" in c.lower()][0]

dates = []
for r in lignes:
    v = (r.get(colonne) or "").strip()
    if not v:
        continue
    # Le fichier source melange deux formats : 972 lignes en JJ/MM/AAAA HH:MM
    # et 828 en AAAA-MM-JJ HH:MM:SS. Une version anterieure de cette figure ne
    # lisait que le second, d'ou un total de 828 tickets au lieu de 1 800.
    for f in ("%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            dates.append(datetime.datetime.strptime(v, f))
            break
        except ValueError:
            pass

assert len(dates) == 1800, "dates exploitables : %d" % len(dates)

compte = collections.Counter((d.year, d.month) for d in dates)
cles = sorted(compte)
valeurs = [compte[k] for k in cles]
etiquettes = ["%s\n%d" % (MOIS[m - 1], a) for a, m in cles]

fig, ax = plt.subplots(figsize=(11.5, 3.9))
barres = ax.bar(range(len(cles)), valeurs, color=BLEU, width=0.62)
barres[-1].set_color(GRIS)

for i, v in enumerate(valeurs):
    ax.text(i, v + 3, str(v), ha="center", va="bottom", fontsize=8.6, color=TEXTE)

ax.set_xticks(range(len(cles)))
ax.set_xticklabels(etiquettes, fontsize=8.4, color=TEXTE)
ax.set_ylabel("Tickets déposés", fontsize=9.5, color=TEXTE)
ax.set_ylim(0, max(valeurs) * 1.18)
ax.tick_params(axis="y", labelsize=8.4, colors=TEXTE)
for bord in ("top", "right"):
    ax.spines[bord].set_visible(False)
for bord in ("left", "bottom"):
    ax.spines[bord].set_color(GRIS)

moyenne = sum(valeurs) / float(len(valeurs))
ax.axhline(moyenne, color=GRIS, linewidth=1.0, linestyle="--")
ax.text(len(cles) - 0.4, moyenne + 3, "moyenne %.0f" % moyenne,
        ha="right", va="bottom", fontsize=8.0, color=TEXTE)
ax.text(len(cles) - 1, 6, "mois partiel\n(export au 17)", ha="center", va="bottom",
        fontsize=7.6, color=TEXTE, style="italic")

fig.tight_layout()
fig.savefig(SORTIE, bbox_inches="tight", facecolor="white")
print("ecrit :", SORTIE)
print("total :", sum(valeurs), "| mois :", len(cles), "| moyenne : %.1f" % moyenne)
