# -*- coding: utf-8 -*-
from style import *

fig, ax = canvas(12.5, 7.5, (0, 16.6), (-1.3, 8.6))

txt(ax, 0.1, 8.25, "Diagramme d'états du ticket", size=TT, weight="bold", ha="left")
txt(ax, 0.1, 7.86, "Les neuf transitions représentées sont celles que le serveur autorise. Toute autre demande de changement est refusée.",
    size=SM, color=MUTED, ha="left")

ATT, PEC, PRB = (2.80, 4.00), (7.40, 4.00), (14.60, 4.00)
RES, REJ = (11.60, 6.60), (11.60, 1.40)
W, H = 2.60, 1.00

# --- transitions, tracees avant les etats ---
arrow(ax, [(1.00, 4.00), (ATT[0] - W / 2 - 0.06, 4.00)])
arrow(ax, [(ATT[0] + W / 2 + 0.06, 4.20), (PEC[0] - W / 2 - 0.06, 4.20)])
arrow(ax, [(PEC[0] - W / 2 - 0.06, 3.80), (ATT[0] + W / 2 + 0.06, 3.80)])
arrow(ax, [(PEC[0] + W / 2 + 0.06, 4.20), (PRB[0] - W / 2 - 0.06, 4.20)])
arrow(ax, [(PRB[0] - W / 2 - 0.06, 3.80), (PEC[0] + W / 2 + 0.06, 3.80)])
arrow(ax, [(8.75, 4.55), (10.35, 6.15)])
arrow(ax, [(8.75, 3.45), (10.35, 1.85)])
arrow(ax, [(13.45, 4.55), (12.85, 6.15)])
arrow(ax, [(13.45, 3.45), (12.85, 1.85)])
arrow(ax, [(ATT[0], 3.50 - 0.06), (ATT[0], 1.40), (REJ[0] - W / 2 - 0.06, 1.40)])

# --- etat initial ---
ax.add_patch(Circle((0.70, 4.00), 0.17, facecolor=FG, edgecolor=FG, zorder=Z_NODE))

# --- etats ---
for (cx, cy), name, sub, term in [
        (ATT, "En attente", "dépôt enregistré", False),
        (PEC, "Prise en Charge", "un administrateur traite", False),
        (PRB, "Problème", "traitement bloqué", False),
        (RES, "Résolu", "solution appliquée", True),
        (REJ, "Rejeté", "demande écartée", True)]:
    if term:
        box(ax, cx, cy, W + 0.22, H + 0.22, "neutral", r=0.14, lw=1.0)
        ax.patches[-1].set_facecolor("none")
    titled(ax, cx, cy, W, H, "storage" if term else "process", name, [sub],
           tsize=LB, ssize=XS, lw=1.3)

# --- etiquettes des transitions ---
elabel(ax, (ATT[0] + PEC[0]) / 2, 4.68, "prise en charge")
elabel(ax, (ATT[0] + PEC[0]) / 2, 3.32, "remise en file")
elabel(ax, (PEC[0] + PRB[0]) / 2, 4.68, "blocage constaté")
elabel(ax, (PEC[0] + PRB[0]) / 2, 3.32, "reprise du traitement")
elabel(ax, 9.35, 5.72, "solution\nappliquée", ha="right")
elabel(ax, 9.35, 2.28, "demande non\nrecevable", ha="right")
elabel(ax, 13.80, 5.72, "contournement\ntrouvé", ha="left")
elabel(ax, 13.80, 2.28, "abandon", ha="left")
elabel(ax, 6.60, 1.62, "demande non recevable")

note(ax, 8.30, -0.65, 15.4, 1.15,
     ["Double contour : état terminal, sans transition sortante. Un ticket résolu ou rejeté reste néanmoins modifiable —",
      "la catégorie, la priorité et la solution appliquée peuvent être corrigées sans rouvrir le ticket."])

save(fig, "ch06_etats_ticket.png")
