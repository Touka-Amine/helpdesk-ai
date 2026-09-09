# -*- coding: utf-8 -*-
from style import *

STEP = 0.285
fig, ax = canvas(11.6, 9.6, (0, 14.8), (-0.75, 11.5))

txt(ax, 0.1, 11.15, "Diagramme de classes — sprint 4", size=TT, weight="bold", ha="left")
txt(ax, 0.1, 10.78, "Trois entités persistées. Les attributs de Ticket sont regroupés selon l'étape du traitement qui les écrit.",
    size=SM, color=MUTED, ha="left")


def uml_class(cx, top, w, name, blocks, kind="storage"):
    """blocks : liste de (titre_de_groupe|None, [attributs])."""
    n = sum(1 + len(a) if t else len(a) for t, a in blocks)
    h = 0.68 + n * STEP + 0.14
    cy = top - h / 2
    box(ax, cx, cy, w, h, kind, r=0.06, lw=1.3)
    txt(ax, cx, top - 0.34, name, size=LB + 0.5, weight="bold")
    x0 = cx - w / 2
    link(ax, [(x0, top - 0.68), (x0 + w, top - 0.68)], color=PAL[kind][1],
         lw=1.1, z=Z_TEXT)
    y = top - 0.68 - 0.22
    for t, attrs in blocks:
        if t:
            link(ax, [(x0 + 0.18, y + 0.16), (x0 + w - 0.18, y + 0.16)],
                 color=PAL[kind][1], lw=0.5, z=Z_TEXT)
            txt(ax, x0 + 0.26, y - 0.03, t, size=XS, color=PAL[kind][1],
                style="italic", ha="left")
            y -= STEP
        for a in attrs:
            txt(ax, x0 + 0.34, y - 0.03, "\u2212 " + a, size=XS, ha="left")
            y -= STEP
    return cy, h


TX, TW, TTOP = 10.90, 6.40, 10.20
UX, UW, UTOP = 3.50, 5.60, 10.20
HX, HW, HTOP = 3.50, 5.60, 4.10
TL, TR = TX - TW / 2, TX + TW / 2
UR = UX + UW / 2

# --- associations, tracees avant les classes ---
link(ax, [(UR, 9.30), (TL, 9.30)])
link(ax, [(UX, UTOP - 3.62), (UX, HTOP)])
link(ax, [(HX + HW / 2, 2.70), (TL, 2.70)])

uml_class(UX, UTOP, UW, "User", [
    (None, ["id : int  {PK}", "email : str  {unique}", "nom : str", "prenom : str",
            "hashed_password : str", "role : str  {client | admin}", "filiale : str",
            "is_active : bool", "first_login : bool", "created_at : datetime"])],
    kind="input")

uml_class(HX, HTOP, HW, "TicketHistory", [
    (None, ["id : int  {PK}", "ticket_id : int  {FK}", "changed_by : int  {FK}",
            "champ_modifie : str", "ancienne_valeur : text", "nouvelle_valeur : text",
            "timestamp : datetime"])],
    kind="input")

uml_class(TX, TTOP, TW, "Ticket", [
    (None, ["id : int  {PK}", "user_id : int  {FK}"]),
    ("« demande »", ["titre : str", "description : text", "priorite_saisie : str",
                     "filiale : str", "equipement : str", "created_at : datetime"]),
    ("« prédiction du système »", ["categorie_predite : str", "confiance : float",
                                   "model_version : str", "heuristic_applied : bool",
                                   "heuristic_rule : str"]),
    ("« recommandation »", ["solution_rag : text", "knowledge_rag : text",
                            "rag_score : float"]),
    ("« décision humaine »", ["categorie_finale : str", "priorite_finale : str",
                              "classification_finale : str", "statut : str",
                              "assigne_a : str", "approved_by : str",
                              "commentaire_admin : text", "resolved_at : datetime"]),
    ("« retour du demandeur »", ["commentaire_client : text", "feedback_vote : str",
                                 "feedback_comment : text"])],
    kind="storage")

# --- roles et cardinalites ---
elabel(ax, (UR + TL) / 2, 9.52, "dépose")
elabel(ax, UR + 0.16, 9.12, "1", ha="left"); elabel(ax, TL - 0.16, 9.12, "0..*", ha="right")
elabel(ax, UX + 0.18, 5.35, "auteur du changement", ha="left")
elabel(ax, UX - 0.16, 6.30, "1", ha="right"); elabel(ax, UX - 0.16, 4.35, "0..*", ha="right")
elabel(ax, (HX + HW / 2 + TL) / 2, 2.92, "journalise")
elabel(ax, HX + HW / 2 + 0.16, 2.52, "0..*", ha="left")
elabel(ax, TL - 0.16, 2.52, "1", ha="right")

note(ax, 3.50, 0.28, 5.4, 1.25,
     ["La catégorie n'est pas une entité :",
      "elle reste une chaîne de caractères.",
      "Coût de ce choix exposé ci-après."])

save(fig, "ch06_classes.png")
