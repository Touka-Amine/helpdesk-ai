# -*- coding: utf-8 -*-
"""Le moteur sémantique doit trouver assez de réponses DIFFÉRENTES (remarque du 2026-10-09).

Le défaut corrigé
-----------------
La base compte 1 357 passages pour 46 résolutions distinctes, soit une trentaine
de copies par réponse. Le moteur lisait `top_k * 3` voisins avant de filtrer les
doublons — neuf pour trois suggestions demandées. Les neuf plus proches voisins
d'une requête étant presque toujours neuf copies de la même résolution, il n'en
restait qu'une : 1,57 réponse distincte par requête, et une seule requête sur
quarante servie au complet.

L'élargissement double désormais jusqu'à ce que `top_k` résolutions différentes
soient en vue. Ces tests vérifient qu'il le fait, qu'il s'arrête, et qu'il ne
parcourt pas la base ligne à ligne en le faisant.
"""
import os

import numpy as np
import pandas as pd

os.environ.setdefault("DB_URL", "sqlite:///./data/tickets_test.db")

from src.rag.semantic_engine import SemanticRAGEngine


class IndexFactice:
    """Un index qui rend les voisins dans un ordre imposé, sans FAISS."""

    def __init__(self, ordre):
        self._ordre = list(ordre)
        self.ntotal = len(self._ordre)
        self.appels = []

    def search(self, q_vec, k):
        self.appels.append(k)
        ids = self._ordre[:k]
        scores = np.array([[1.0 - i * 0.001 for i in range(len(ids))]], dtype="float32")
        return scores, np.array([ids], dtype="int64")


def moteur_sur(resolutions, top_k=3):
    """Un moteur dont la base porte exactement ces résolutions, dans cet ordre."""
    m = SemanticRAGEngine.__new__(SemanticRAGEngine)
    m.top_k = top_k
    m.similarity_threshold = 0.0
    m.knowledge_base = pd.DataFrame({
        "Résolution/Motif": list(resolutions),
        "knowledge Base": ["" for _ in resolutions],
        "Catégorie": ["Réseau" for _ in resolutions],
        "Titre": ["t%d" % i for i in range(len(resolutions))],
    })
    return m


def test_il_elargit_quand_les_premiers_voisins_sont_des_copies():
    """Le cas du corpus : trente copies avant la deuxième réponse."""
    resolutions = ["A"] * 30 + ["B"] * 30 + ["C"] * 30
    m = moteur_sur(resolutions)
    index = IndexFactice(range(len(resolutions)))
    ids, _ = m._voisins_jusqu_a_k_reponses(np.zeros((1, 768), dtype="float32"), index, None)
    distinctes = {m._resolution_de(i) for i in ids}
    assert {"A", "B", "C"} <= distinctes
    assert index.appels[0] == 9, "le premier essai reste celui d'avant"
    assert len(index.appels) > 1, "il doit avoir élargi"


def test_il_n_elargit_pas_quand_c_est_inutile():
    """Une base variée ne doit pas coûter plus cher qu'avant."""
    m = moteur_sur(["A", "B", "C", "D", "E", "F", "G", "H", "I"])
    index = IndexFactice(range(9))
    m._voisins_jusqu_a_k_reponses(np.zeros((1, 768), dtype="float32"), index, None)
    assert index.appels == [9], "une seule recherche suffisait"


def test_il_s_arrete_a_l_index_entier_sans_boucler():
    """Si la base n'a pas trois réponses différentes, il ne cherche pas indéfiniment."""
    resolutions = ["A"] * 40 + ["B"] * 40
    m = moteur_sur(resolutions)
    index = IndexFactice(range(len(resolutions)))
    ids, _ = m._voisins_jusqu_a_k_reponses(np.zeros((1, 768), dtype="float32"), index, None)
    assert index.appels[-1] == index.ntotal
    assert len({m._resolution_de(i) for i in ids}) == 2


def test_l_elargissement_reste_borne():
    """Le doublement doit atteindre le total en un nombre de pas logarithmique."""
    resolutions = ["A"] * 1000 + ["B", "C"]
    m = moteur_sur(resolutions)
    index = IndexFactice(range(len(resolutions)))
    m._voisins_jusqu_a_k_reponses(np.zeros((1, 768), dtype="float32"), index, None)
    assert len(index.appels) <= 9, "au plus neuf recherches pour mille passages"


def test_les_positions_de_categorie_sont_respectees():
    """Avec un filtre de catégorie, les identifiants rendus sont les globaux."""
    m = moteur_sur(["A"] * 10 + ["B"] * 10)
    positions = list(range(10, 20))        # le sous-index ne couvre que les « B »
    index = IndexFactice(range(10))
    ids, _ = m._voisins_jusqu_a_k_reponses(np.zeros((1, 768), dtype="float32"),
                                           index, positions)
    assert all(10 <= i < 20 for i in ids)


def test_les_resolutions_ne_sont_lues_qu_une_fois():
    """Sans cache, l'élargissement coûterait un accès par ligne et par requête."""
    m = moteur_sur(["A"] * 50 + ["B"] * 50)
    premier = m._resolutions_indexees()
    second = m._resolutions_indexees()
    assert premier is second, "la liste doit être conservée, non reconstruite"
    assert len(premier) == 100


def test_un_repli_vide_est_traite_comme_une_absence_de_reponse():
    """Une ligne sans résolution ni base de connaissances ne compte pas."""
    m = moteur_sur(["", "nan", "A"])
    assert m._resolution_de(0) == ""
    assert m._resolution_de(1) == ""
    assert m._resolution_de(2) == "A"
