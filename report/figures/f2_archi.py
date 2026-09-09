# -*- coding: utf-8 -*-
from style import *

fig, ax = canvas(14.2, 8.7, (0, 18.6), (0, 11.4))

txt(ax, 0.1, 11.05, "Architecture générale — modèle C4, niveau 2", size=TT,
    weight="bold", ha="left")
txt(ax, 0.1, 10.65, "Cinq conteneurs orchestrés par une composition Docker unique, sur un hôte unique",
    size=SM, color=MUTED, ha="left")

# --- zone de confiance ---
zx0, zy0, zx1, zy1 = 3.3, 0.75, 18.2, 10.15
box(ax, (zx0 + zx1) / 2, (zy0 + zy1) / 2, zx1 - zx0, zy1 - zy0, "neutral",
    r=0.15, lw=1.0, ls=(0, (5, 4)), z=1)
ax.patches[-1].set_facecolor("none")
txt(ax, zx0 + 0.25, zy1 - 0.32,
    "Infrastructure OTBS — aucune donnée de ticket ne quitte le réseau interne",
    size=XS, color=MUTED, ha="left")

APIX, APIY, APIW, APIH = 10.9, 5.9, 4.8, 5.6
AL, AR, AT, AB = APIX - APIW / 2, APIX + APIW / 2, APIY + APIH / 2, APIY - APIH / 2

# --- connecteurs, traces avant les noeuds ---
arrow(ax, [(2.00, 8.15), (4.14, 8.05)])
arrow(ax, [(2.00, 6.35), (4.14, 7.45)])
arrow(ax, [(2.00, 5.75), (4.14, 5.55)])
arrow(ax, [(7.26, 7.85), (AL - 0.06, 7.55)])
arrow(ax, [(7.26, 5.15), (AL - 0.06, 5.35)])
arrow(ax, [(3.06, 2.30), (7.80, 2.30), (7.80, 3.90), (AL - 0.06, 3.90)])
arrow(ax, [(AR + 0.06, 8.00), (14.54, 8.00)])
arrow(ax, [(AR + 0.06, 5.20), (14.54, 5.20)])
arrow(ax, [(APIX, AB - 0.06), (APIX, 2.46)])

# --- entites exterieures, hors zone ---
actor(ax, 1.50, 8.05, "Employé", "demandeur", s=0.82)
actor(ax, 1.50, 5.95, "Technicien IT", "administrateur", s=0.82)
titled(ax, 1.62, 2.30, 2.88, 1.2, "external", "Messagerie",
       ["boîte du support,", "liste SharePoint"], tsize=SM)

# --- interfaces ---
titled(ax, 5.70, 8.00, 3.0, 1.5, "input", "Application Angular",
       ["espaces client et", "administration", "port 8081"], tsize=SM)
titled(ax, 5.70, 5.30, 3.0, 1.5, "input", "Tableau de bord",
       ["Streamlit, indicateurs", "de supervision", "port 8501"], tsize=SM)

# --- service applicatif ---
box(ax, APIX, APIY, APIW, APIH, "process", lw=1.5)
txt(ax, APIX, AT - 0.44, "API FastAPI", size=LB + 0.5, weight="bold")
txt(ax, APIX, AT - 0.78, "contrat /api/v1, port 8000", size=XS, color=MUTED)
txt(ax, APIX, AT - 1.04, "routers → services → repositories", size=XS, color=MUTED)
txt(ax, APIX, AT - 1.30, "JWT, contrôle de rôle, limitation de débit", size=XS, color=MUTED)

for cy, name, sub in [(6.40, "Classifieur", "TF-IDF + règles métier"),
                      (5.05, "Moteur de recherche hybride", "FAISS + TF-IDF, α = 0,5")]:
    titled(ax, APIX, cy, 4.1, 1.05, "process", name, [sub], tsize=SM, r=0.06, lw=1.0)
    ax.patches[-1].set_facecolor("#F1F2FB")
txt(ax, APIX, 4.16, "chargés en mémoire dans le processus, sans conteneur distinct",
    size=XS, color=MUTED, style="italic")

# --- conteneur d'inference et persistance ---
titled(ax, 16.30, 8.00, 3.3, 1.5, "process", "Ollama",
       ["llama3.2:3b, 2 Go", "reformulation à la demande"], tsize=SM)
titled(ax, 16.30, 5.20, 3.3, 1.5, "storage", "PostgreSQL",
       ["utilisateurs, tickets,", "historique des modifications"], tsize=SM)
titled(ax, APIX, 1.76, 4.1, 1.4, "storage", "ChromaDB",
       ["base de connaissances,", "1 357 tickets indexés"], tsize=SM)

# --- etiquettes des liens ---
elabel(ax, 3.07, 8.30, "dépose", bg=False)
elabel(ax, 2.95, 7.30, "qualifie", bg=False)
elabel(ax, 3.07, 5.32, "supervise", bg=False)
elabel(ax, 7.86, 7.95, "REST + JWT", bg=False)
elabel(ax, 7.72, 5.60, "lecture seule", bg=False)
elabel(ax, 5.60, 2.90, "connecteur d'ingestion,", bg=False)
elabel(ax, 5.60, 2.62, "en-tête X-Api-Key", bg=False)
elabel(ax, 13.94, 8.28, "HTTP local", bg=False)
elabel(ax, 13.94, 5.48, "SQLAlchemy", bg=False)
elabel(ax, APIX + 0.25, 2.78, "mode embarqué, volume api-data", ha="left", bg=False)

legend(ax, 0.1, 0.05,
       [("external", "Acteur ou système tiers"), ("input", "Interface"),
        ("process", "Traitement"), ("storage", "Persistance")], dx=4.4)

save(fig, "ch06_architecture.png")
