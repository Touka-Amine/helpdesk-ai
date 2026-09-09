# -*- coding: utf-8 -*-
from style import *

fig, ax = canvas(12.4, 6.7, (0, 15.4), (0, 8.2))

txt(ax, 0.1, 7.85, "Diagramme de contexte — modèle C4, niveau 1", size=TT,
    weight="bold", ha="left")
txt(ax, 0.1, 7.48, "Périmètre du système et entités extérieures avec lesquelles il échange",
    size=SM, color=MUTED, ha="left")

SX, SY, SW, SH = 7.3, 4.9, 4.6, 2.5
L, R = SX - SW / 2, SX + SW / 2

# --- connecteurs, traces avant les noeuds ---
arrow(ax, [(2.3, 5.85), (L - 0.06, 5.55)])
arrow(ax, [(L - 0.06, 4.55), (2.3, 4.25)], dashed=True)
arrow(ax, [(12.7, 5.85), (R + 0.06, 5.55)])
arrow(ax, [(R + 0.06, 4.55), (12.7, 4.25)], dashed=True)
arrow(ax, [(SX, 2.05), (SX, SY - SH / 2 - 0.06)])

# --- entites exterieures ---
actor(ax, 1.55, 5.55, "Employé", "demandeur")
actor(ax, 13.45, 5.55, "Technicien IT", "administrateur")
titled(ax, SX, 1.25, 4.6, 1.3, "external", "Circuit de messagerie existant",
       ["boîte du support et liste SharePoint,", "décrites au chapitre 1"])

# --- systeme ---
box(ax, SX, SY, SW, SH, "process", lw=1.6)
txt(ax, SX, SY + 0.86, "HelpDesk AI", size=13.5, weight="bold")
txt(ax, SX, SY + 0.46, "Classification automatique et assistance", size=SM, color=MUTED)
txt(ax, SX, SY + 0.18, "à la résolution des demandes informatiques", size=SM, color=MUTED)
link(ax, [(L + 0.45, SY - 0.14), (R - 0.45, SY - 0.14)], color=PAL["process"][1], lw=0.8)
txt(ax, SX, SY - 0.50, "Comptes et mots de passe gérés", size=XS, color=MUTED)
txt(ax, SX, SY - 0.76, "par l'application elle-même", size=XS, color=MUTED)
txt(ax, SX, SY - 1.04, "Aucune donnée ne sort de l'infrastructure", size=XS, color=MUTED)

# --- etiquettes des flux ---
elabel(ax, 3.65, 6.42, "dépose une demande, suit l'avancement,", bg=False)
elabel(ax, 3.65, 6.14, "signale si la réponse a été utile", bg=False)
elabel(ax, 3.65, 3.72, "notifie la réponse et", bg=False)
elabel(ax, 3.65, 3.44, "le changement d'état", bg=False)
elabel(ax, 11.35, 6.42, "qualifie, corrige la catégorie,", bg=False)
elabel(ax, 11.35, 6.14, "clôt la demande", bg=False)
elabel(ax, 11.35, 3.72, "propose une catégorie", bg=False)
elabel(ax, 11.35, 3.44, "et des cas comparables", bg=False)
elabel(ax, SX + 0.22, 2.90, "transmet les demandes reçues", ha="left", bg=False)
elabel(ax, SX + 0.22, 2.62, "connecteur d'ingestion", ha="left", bg=False)

# --- note de conception ---
note(ax, 12.55, 1.35, 5.0, 1.5,
     ["Aucun annuaire d'entreprise ne figure ici :",
      "l'authentification est assurée par l'application.",
      "Décision et contrepartie exposées ci-après."],
     anchor=(R - 0.15, SY - SH / 2 + 0.15))

save(fig, "ch06_contexte.png")
