# -*- coding: utf-8 -*-
"""Oriente un ticket vers la revue humaine ou vers le traitement ordinaire (EF-07).

Ce que l'exigence demande
-------------------------
EF-07, priorite elevee : « Orientation selon l'index de confiance — cas peu
assures diriges vers une revue humaine ». La version precedente calculait l'index
et l'affichait ; aucune decision ne s'en servait, et le bilan du chapitre 6
declarait l'exigence partielle pour cette raison.

Ce que la decision regarde
--------------------------
L'index de confiance ne suffit pas a lui seul. Un ticket peut etre mal assure
pour trois raisons differentes, et les trois meritent un regard humain :

  1. le modele hesite              confiance sous le seuil de `params.yaml` ;
  2. une regle metier a tranche    la categorie ne vient alors pas du modele
                                   mais d'un mot-cle, et un humain doit confirmer
                                   que le mot-cle ne s'est pas trompe de contexte ;
  3. aucun cas comparable          le moteur de recherche n'a rien rendu au-dessus
                                   de son seuil : le consultant part de zero, et
                                   le ticket n'est pas routinier.

Les trois motifs sont enregistres en clair sur le ticket. Un administrateur qui
voit un ticket dans sa file sait pourquoi il y est.

Ce que la decision NE fait PAS
-------------------------------
Elle ne ferme aucune porte. Un ticket oriente « automatique » reste visible,
modifiable et rejetable comme les autres : l'orientation trie une file, elle ne
remplace pas une validation. Le principe pose au cadrage — le systeme propose,
le consultant tranche — n'est pas entame.
"""
from __future__ import annotations

REVUE_HUMAINE = "revue_humaine"
AUTOMATIQUE = "automatique"


def decider(prediction: dict, seuil_confiance: float, seuil_rag: float) -> tuple[str, str]:
    """Retourne (routage, motif) pour un ticket qui vient d'etre predit.

    Args:
        prediction      : la sortie de `predict_and_recommend`
        seuil_confiance : `ml.confidence_threshold` de params.yaml
        seuil_rag       : `rag.similarity_threshold` de params.yaml

    Returns:
        ("revue_humaine" | "automatique", motif lisible)
    """
    motifs = []
    confiance = float(prediction.get("confiance") or 0.0)
    if confiance < seuil_confiance:
        motifs.append("confiance %.0f %% sous le seuil de %.0f %%"
                      % (100 * confiance, 100 * seuil_confiance))
    if prediction.get("heuristic_applied"):
        regle = prediction.get("heuristic_rule") or "regle metier"
        motifs.append("categorie imposee par la regle « %s »" % regle)
    score_rag = prediction.get("rag_score")
    if score_rag is None or float(score_rag) < seuil_rag:
        motifs.append("aucun cas comparable au-dessus du seuil de recherche")

    if motifs:
        return REVUE_HUMAINE, " ; ".join(motifs)
    return AUTOMATIQUE, "confiance %.0f %% et cas comparable trouve" % (100 * confiance)
