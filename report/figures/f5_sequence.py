# -*- coding: utf-8 -*-
from style import *
import style
style.XS = 8.5
style.SM = 9.4
XS, SM = 8.5, 9.4

fig, ax = canvas(13.0, 10.1, (0, 19.8), (-1.6, 13.6))

txt(ax, 0.1, 13.25, "Diagramme de séquence — dépôt et qualification d'un ticket", size=TT,
    weight="bold", ha="left")
txt(ax, 0.1, 12.86, "Traits pleins : appels. Traits pointillés : réponses. Les numéros donnent l'ordre chronologique.",
    size=SM, color=MUTED, ha="left")

X = {"dem": 1.40, "tec": 4.05, "ui": 7.00, "api": 10.10, "clf": 13.00,
     "rag": 15.75, "db": 18.30}
HEADS = [("dem", "Demandeur", "external"), ("tec", "Technicien IT", "external"),
         ("ui", "Interface\nAngular", "input"), ("api", "API\nFastAPI", "process"),
         ("clf", "Classifieur", "process"), ("rag", "Moteur\nhybride", "process"),
         ("db", "PostgreSQL", "storage")]
HY, HH, HW = 11.75, 1.05, 2.45
BOT = 0.55

# --- lignes de vie ---
for k, _, _ in HEADS:
    ax.plot([X[k], X[k]], [HY - HH / 2, BOT], color="#9AA3B0", lw=1.0,
            linestyle=(0, (4, 4)), zorder=1)

# --- barres d'activation ---
def bar(k, y0, y1, kind="process"):
    ax.add_patch(Rectangle((X[k] - 0.10, y1), 0.20, y0 - y1,
                           facecolor=PAL[kind][0], edgecolor=PAL[kind][1],
                           lw=0.8, zorder=2))

bar("ui", 10.10, 4.88, "input"); bar("ui", 3.95, 1.05, "input")
bar("api", 9.52, 5.46); bar("api", 3.37, 1.63)
bar("clf", 8.94, 8.36); bar("rag", 7.78, 7.20)
bar("db", 6.62, 6.04, "storage"); bar("db", 2.79, 2.21, "storage")

# --- messages ---
MSGS = [
    ("dem", "ui", "saisit le titre et la description", 0),
    ("ui", "api", "POST /api/v1/tickets", 0),
    ("api", "clf", "classer(titre + description)", 0),
    ("clf", "api", "catégorie, confiance, règle appliquée", 1),
    ("api", "rag", "rechercher(texte, top_k = 3)", 0),
    ("rag", "api", "trois cas voisins et leur score de similarité", 1),
    ("api", "db", "enregistrer le ticket, la prédiction et sa traçabilité", 0),
    ("db", "api", "identifiant attribué", 1),
    ("api", "ui", "201 — catégorie proposée et cas voisins", 1),
    ("ui", "dem", "numéro de suivi et accusé de dépôt", 1),
    ("tec", "ui", "ouvre le ticket et corrige la catégorie", 0),
    ("ui", "api", "PATCH /api/v1/tickets/{id}", 0),
    ("api", "db", "mettre à jour et journaliser chaque champ modifié", 0),
    ("db", "api", "ticket et historique", 1),
    ("api", "ui", "200 — ticket mis à jour", 1),
    ("ui", "tec", "confirmation", 1),
]
ys = [10.10, 9.52, 8.94, 8.36, 7.78, 7.20, 6.62, 6.04, 5.46, 4.88,
      3.95, 3.37, 2.79, 2.21, 1.63, 1.05]

for i, ((a, b, lab, dash), y) in enumerate(zip(MSGS, ys), start=1):
    xa, xb = X[a], X[b]
    d = 0.11 if xb > xa else -0.11
    arrow(ax, [(xa + d, y), (xb - d, y)], dashed=bool(dash), head=9, lw=1.05)
    t = txt(ax, (xa + xb) / 2, y + 0.25, "%d. %s" % (i, lab), size=XS,
            color=FG if not dash else MUTED)
    t.set_bbox(dict(facecolor="white", edgecolor="none", pad=1.5, alpha=0.95))

# --- phases ---
for y, lab in [(10.62, "Dépôt de la demande — une seule requête synchrone"),
               (4.40, "Plus tard, à la qualification par le technicien")]:
    ax.plot([0.35, 19.45], [y, y], color="#B9BFC9", lw=0.8,
            linestyle=(0, (6, 4)), zorder=1)
    t = txt(ax, 0.55, y, lab, size=XS, color=MUTED, weight="bold", ha="left")
    t.set_bbox(dict(facecolor="white", edgecolor="none", pad=2))

# --- en-tetes ---
for k, name, kind in HEADS:
    box(ax, X[k], HY, HW, HH, kind, r=0.06, lw=1.2)
    txt(ax, X[k], HY, name, size=SM, weight="bold")

note(ax, 9.90, -0.82, 16.6, 1.25,
     ["L'appel au modèle de langage ne figure pas dans cette séquence : la reformulation intervient plus tard,",
      "à la demande du technicien, par un chemin distinct décrit à la section Réalisation."])

save(fig, "ch06_sequence.png")
