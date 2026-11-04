# -*- coding: utf-8 -*-
"""Toute lecture du jeu de test gele doit s'inscrire au journal.

L'ecart corrige
---------------
Le chapitre 7 annonçait que « chaque lecture s'inscrit dans un journal
versionne ». C'etait faux : seule `promote.py` s'inscrivait. Neuf autres points
d'entree ouvraient `data/splits/test.csv` sans rien declarer, dont deux qui
TRANCHENT :

  - `scripts/arbitrage_modele_servi.py`, qui choisit la configuration servie ;
  - le balayage de seuil de `rag_eval.py`, qui a retenu 0,35.

Le second est le plus instructif : il ne lit pas `test.csv` directement, mais le
gabarit annote, lui-meme tire du jeu gele. La remarque de l'encadrant sur le
seuil choisi sur le jeu d'evaluation et sa remarque sur le jeu gele qui devient
un jeu de validation ne font donc qu'une.

Ce que ce test garde
--------------------
Un fichier qui ouvre le jeu gele passe par `jeu_gele.lire` (ou declare sa lecture
par `jeu_gele.inscrire`), ou figure dans la liste des dispenses avec son motif.
La liste est le point important : elle rend l'inventaire complet et verifiable,
au lieu de reposer sur la memoire de celui qui a ecrit le journal.
"""
import ast
import glob
import io
import os

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FICHIERS_DU_JEU = ("test.csv", "test_reference.csv")

# Chaque dispense porte son motif. Une dispense sans motif defendable est un
# oubli deguise.
DISPENSES = {
    os.path.join("src", "pipeline", "jeu_gele.py"):
        "c'est le lecteur journalisant lui-meme",
    os.path.join("src", "pipeline", "split.py"):
        "il ECRIT le jeu gele, il ne le consulte pas",
    os.path.join("src", "pipeline", "build_dataset.py"):
        "il ne le lit que pour EXCLURE ses lignes du corpus d'entrainement : "
        "aucune mesure, aucun choix, c'est l'inverse d'une fuite",
}


def _noms_du_jeu_gele(arbre) -> set:
    """Les noms de module qui designent un chemin vers le jeu gele."""
    noms = set()

    def est_le_jeu(valeur) -> bool:
        if isinstance(valeur, ast.Constant) and isinstance(valeur.value, str):
            return valeur.value.replace("\\", "/").endswith(FICHIERS_DU_JEU)
        if isinstance(valeur, ast.Call):
            nom = getattr(valeur.func, "attr", None)
            if nom == "join" and valeur.args:
                return est_le_jeu(valeur.args[-1])
        return False

    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.Assign) and est_le_jeu(noeud.value):
            for cible in noeud.targets:
                if isinstance(cible, ast.Name):
                    noms.add(cible.id)
    return noms


def _lectures_nues(chemin: str) -> list[str]:
    """Les `read_csv` du jeu gele qui ne passent pas par le journal."""
    source = io.open(chemin, encoding="utf-8").read()
    try:
        arbre = ast.parse(source)
    except SyntaxError:
        return []

    noms = _noms_du_jeu_gele(arbre)
    if not noms:
        return []

    journalise = "jeu_gele.lire(" in source or "jeu_gele.inscrire(" in source
    nues = []
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.Call):
            continue
        if getattr(noeud.func, "attr", None) != "read_csv" or not noeud.args:
            continue
        cible = noeud.args[0]
        touche = (isinstance(cible, ast.Name) and cible.id in noms) or (
            isinstance(cible, ast.Constant) and isinstance(cible.value, str)
            and cible.value.replace("\\", "/").endswith(FICHIERS_DU_JEU))
        if touche and not journalise:
            nues.append("%d : read_csv du jeu gele sans inscription" % noeud.lineno)
    return nues


def test_aucune_lecture_du_jeu_gele_hors_du_journal():
    """Garde : un nouveau lecteur doit declarer sa lecture ou sa dispense."""
    manquants = []
    for motif in ("src/**/*.py", "scripts/**/*.py"):
        for chemin in glob.glob(os.path.join(RACINE, *motif.split("/")), recursive=True):
            rel = os.path.relpath(chemin, RACINE)
            if rel in DISPENSES or "__pycache__" in rel:
                continue
            for faute in _lectures_nues(chemin):
                manquants.append("%s:%s" % (rel, faute))
    assert not manquants, (
        "lecture du jeu de test gele sans inscription au journal — le journal "
        "cesserait de dire l'usage du fichier : " + "; ".join(manquants))


def test_chaque_dispense_porte_un_motif():
    """Une liste de dispenses sans motifs redevient une liste d'oublis."""
    for rel, raison in DISPENSES.items():
        assert os.path.exists(os.path.join(RACINE, rel)), \
            "dispense pour un fichier disparu : %s" % rel
        assert raison and len(raison) > 20, "motif trop court pour %s" % rel


def test_les_deux_natures_de_lecture_existent_toujours():
    """Si la distinction disparaissait, le budget perdrait son sens."""
    from src.pipeline import jeu_gele

    assert jeu_gele.POUR_DECIDER != jeu_gele.POUR_RAPPORTER
    assert callable(jeu_gele.lire)


def test_le_journal_se_laisse_deplacer_par_l_environnement():
    """Sans cela, le harnais d'essai ecrit dans le journal du depot.

    C'est arrive : `test_promote_idempotence.py` lance promote.py en
    sous-processus, ou aucun monkeypatch ne porte.
    """
    source = io.open(os.path.join(RACINE, "src", "pipeline", "jeu_gele.py"),
                     encoding="utf-8").read()
    assert 'os.environ.get("JOURNAL_JEU_GELE")' in source
    assert 'os.environ.get("CHEMIN_JEU_GELE")' in source


def test_le_balayage_de_seuil_se_declare_comme_une_decision():
    """Le choix du seuil RAG est une lecture decisionnelle du jeu gele.

    Il passe par le gabarit annote, donc aucun `read_csv` ne le trahit : seule
    une inscription explicite le rend visible.
    """
    source = io.open(os.path.join(RACINE, "src", "pipeline", "rag_eval.py"),
                     encoding="utf-8").read()
    debut = source.index("def balayer_seuil")
    corps = source[debut:debut + 3000]
    assert "jeu_gele.inscrire(" in corps, \
        "balayer_seuil doit inscrire sa lecture au journal"
    assert "POUR_DECIDER" in corps, \
        "le balayage choisit un seuil : c'est une lecture decisionnelle"
