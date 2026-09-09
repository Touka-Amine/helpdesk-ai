# -*- coding: utf-8 -*-
from style import *

fig, ax = canvas(13.0, 7.9, (0, 18.0), (-1.0, 10.0))

txt(ax, 0.1, 9.65, "Diagramme de cas d'utilisation — sprint 4", size=TT,
    weight="bold", ha="left")
txt(ax, 0.1, 9.25, "Chaque cas porte l'identifiant de l'exigence correspondante du backlog",
    size=SM, color=MUTED, ha="left")

bx0, by0, bx1, by1 = 3.50, 1.75, 14.50, 8.90
EW, EH = 3.90, 1.24
LX, RX = 6.00, 12.00
DEM, ADM, USR = 1.50, 16.50, 9.00

gauche = [(8.00, "Déposer une demande", "EF-02"),
          (6.70, "Suivre l'avancement", "EF-08"),
          (5.40, "Signaler si la réponse\na été utile", "EF-13")]
droite = [(8.00, "Examiner les cas\npeu assurés", "EF-05"),
          (6.70, "Qualifier et clôturer\nla demande", "EF-06"),
          (5.40, "Consulter l'historique\ndes modifications", "EF-07"),
          (4.10, "Consulter le tableau\nde bord", "EF-15")]
partages = [(7.40, 2.45, "S'authentifier", "EF-01"),
            (11.40, 2.45, "Gérer son profil", "")]

# --- associations et generalisations, tracees avant les noeuds ---
for y, _, _ in gauche:
    link(ax, [(2.05, 6.70), (LX - EW / 2 + 0.06, y)])
for y, _, _ in droite:
    link(ax, [(15.95, 6.70), (RX + EW / 2 - 0.06, y)])
for x, y, _, _ in partages:
    link(ax, [(USR + (0.55 if x > USR else -0.55), 1.30), (x, y - EH / 2 + 0.06)])

for xa, xo, xb in [(DEM, 0.50, USR - 1.05), (ADM, 17.50, USR + 1.05)]:
    g = arrow(ax, [(xa + (-0.31 if xo < xa else 0.31), 6.87), (xo, 6.87),
                   (xo, -0.30), (xb, -0.30)], style="-|>", head=16)
    g.set_facecolor("white"); g.set_edgecolor(LINE)

# --- frontiere du systeme ---
box(ax, (bx0 + bx1) / 2, (by0 + by1) / 2, bx1 - bx0, by1 - by0, "neutral",
    r=0.12, lw=1.1, z=1)
ax.patches[-1].set_facecolor("#FAFBFC")
txt(ax, (bx0 + bx1) / 2, by1 - 0.32, "HelpDesk AI", size=LB, weight="bold",
    color=MUTED)

def cas(cx, cy, label, code):
    ax.add_patch(Ellipse((cx, cy), EW, EH, facecolor=PAL["input"][0],
                         edgecolor=PAL["input"][1], lw=1.1, zorder=Z_NODE))
    if code:
        txt(ax, cx, cy + (0.10 if "\n" in label else 0.14), label, size=SM,
            weight="bold")
        txt(ax, cx, cy - 0.36, code, size=XS, color=MUTED)
    else:
        txt(ax, cx, cy, label, size=SM, weight="bold")

for y, lab, code in gauche:
    cas(LX, y, lab, code)
for y, lab, code in droite:
    cas(RX, y, lab, code)
for x, y, lab, code in partages:
    cas(x, y, lab, code)

actor(ax, DEM, 6.70, "Demandeur", "employé", s=0.95)
actor(ax, ADM, 6.70, "Administrateur", "technicien IT", s=0.95)
actor(ax, USR, 1.00, "Utilisateur authentifié", None, s=0.80)
txt(ax, USR, -0.72, "généralisation : les deux rôles héritent des cas communs",
    size=XS, color=MUTED, style="italic")

save(fig, "ch06_cas_utilisation.png")
