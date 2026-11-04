"""
Tests d'integration du cycle de vie des connaissances (axe 2).

Contrairement a tests/test_kb_quality.py, qui teste la regle seule, ceux-ci font
tourner ChromaDB pour de vrai, dans un repertoire temporaire, et verifient le
comportement de bout en bout : ce qui entre dans la base, ce qui en est refuse,
et ce que le RAG voit ensuite.

Le calcul des embeddings charge sentence-transformers. Les tests sont marques
`slow` pour pouvoir etre exclus d'une execution rapide :

    pytest tests/ -m "not slow"
"""

import os
import sys

import pytest

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.path.insert(0, os.path.join(RACINE, "src"))

pytestmark = pytest.mark.slow

DESCRIPTION = (
    "Impossible de me connecter au VPN depuis ce matin, le client renvoie une "
    "erreur d'authentification alors que le mot de passe est correct."
)
SOLUTION_ADMIN = (
    "Certificat machine expire. Renouvele via la console PKI puis service client "
    "redemarre, la connexion est retablie."
)


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Base ChromaDB isolee. Le client global est reinitialise a chaque test."""
    from api.db import vector_store as vs

    monkeypatch.setattr(vs, "_CHROMA_PATH", str(tmp_path / "chroma"))
    # Les refus sont journalises : sans ce detour, les tests qui provoquent un refus
    # ecriraient dans le vrai data/kb/refus.jsonl du depot.
    monkeypatch.setattr(vs, "_JOURNAL_REFUS", str(tmp_path / "kb" / "refus.jsonl"))
    monkeypatch.setattr(vs, "_client", None)
    yield vs
    vs._client = None


def archiver(vs, ticket_id, titre, description, solution, source, categorie="Réseau"):
    return vs.archive_resolved_ticket(
        ticket_id=ticket_id, titre=titre, description=description,
        categorie=categorie, confiance=0.62, solution=solution, knowledge="",
        approved_by="7", source_solution=source,
    )


def test_solution_admin_indexee(store):
    verdict = archiver(store, 1, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "admin")

    assert verdict["accepte"]
    assert verdict["action"] == "index"
    assert store.count_resolved() == 1

    entree = store.get_all_entries()[0]
    assert entree["statut"] == store.STATUT_ACTIF
    assert entree["source_solution"] == "admin"
    assert entree["kb_schema"] >= 1
    assert entree["indexed_at"]


def test_suggestion_ia_refusee_et_absente_de_la_base(store):
    """
    Le defaut corrige. Une suggestion jamais relue par un humain ne doit pas
    devenir une connaissance de reference, sinon le RAG apprend de lui-meme.
    """
    verdict = archiver(store, 2, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "ia")

    assert not verdict["accepte"]
    assert verdict["action"] == "reject"
    assert store.count_resolved() == 0


def test_solution_trop_courte_refusee(store):
    verdict = archiver(store, 3, "VPN", DESCRIPTION, "ok", "admin")
    assert not verdict["accepte"]
    assert store.count_resolved() == 0


def test_quasi_doublon_remplace_l_entree_precedente(store):
    archiver(store, 10, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "admin")
    verdict = archiver(store, 11, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "admin")

    assert verdict["accepte"]
    assert verdict["action"] == "update"
    assert verdict["near_duplicate_of"] == "10"

    par_id = {e["_id"]: e for e in store.get_all_entries()}
    assert par_id["10"]["statut"] == store.STATUT_REMPLACE
    assert par_id["10"]["superseded_by"] == "11"
    assert par_id["11"]["statut"] == store.STATUT_ACTIF
    # Rien n'est supprime : les deux entrees restent auditables.
    assert store.count_resolved() == 2


def test_le_rag_ne_propose_pas_les_entrees_remplacees(store):
    archiver(store, 20, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "admin")
    archiver(store, 21, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "admin")

    resultats = store.query_similar(DESCRIPTION, top_k=5)
    identifiants = {str(r["ticket_id"]) for r in resultats}

    assert "21" in identifiants
    assert "20" not in identifiants


def test_marquage_obsolete_retire_du_rag_sans_supprimer(store):
    archiver(store, 30, "Partage reseau inaccessible",
             "Le lecteur reseau du service comptabilite n'apparait plus dans "
             "l'explorateur depuis le redemarrage de ce matin.",
             "Service de partage relance et demarrage automatique reconfigure.",
             "admin")
    assert store.query_similar("lecteur reseau inaccessible", top_k=3)

    assert store.marquer_obsolete(30, motif="procedure remplacee")

    assert store.query_similar("lecteur reseau inaccessible", top_k=3) == []
    assert store.count_resolved() == 1                     # toujours present
    entree = store.get_all_entries()[0]
    assert entree["statut"] == store.STATUT_OBSOLETE
    assert entree["obsolete_motif"] == "procedure remplacee"


def test_statistiques_ne_comptent_que_les_entrees_actives(store):
    archiver(store, 40, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "admin")
    archiver(store, 41, "Imprimante bloquee",
             "Les documents partent dans la file mais rien ne sort du bac.",
             "Spouleur redemarre et file d'attente purgee manuellement.",
             "admin", categorie="Système")
    store.marquer_obsolete(41)

    stats = store.get_stats()
    assert stats["total"] == 1
    assert "Système" not in stats["par_categorie"]
    assert store.count_resolved() == 2                     # total brut inchange


def test_snapshot_exporte_tous_les_statuts(store, tmp_path):
    from knowledge.snapshot import ecrire_snapshot

    archiver(store, 50, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "admin")
    archiver(store, 51, "Imprimante bloquee",
             "Les documents partent dans la file mais rien ne sort du bac.",
             "Spouleur redemarre et file d'attente purgee manuellement.",
             "admin", categorie="Système")
    store.marquer_obsolete(51)

    chemin, manifeste = ecrire_snapshot(store.get_all_entries(include_documents=True),
                                        str(tmp_path / "knowledge"))

    assert manifeste["n_entrees"] == 2
    assert manifeste["par_statut"] == {"actif": 1, "obsolete": 1}
    assert len(manifeste["kb_version"]) == 12
    assert os.path.exists(chemin)


def test_diff_entre_deux_instantanes(store, tmp_path):
    from knowledge.snapshot import comparer, ecrire_snapshot

    archiver(store, 60, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "admin")
    avant, _ = ecrire_snapshot(store.get_all_entries(include_documents=True),
                               str(tmp_path / "knowledge"))

    archiver(store, 61, "Imprimante bloquee",
             "Les documents partent dans la file mais rien ne sort du bac.",
             "Spouleur redemarre et file d'attente purgee manuellement.",
             "admin", categorie="Système")

    difference = comparer(avant, store.get_all_entries(include_documents=True))
    assert difference["ajoutees"] == ["61"]
    assert difference["retirees"] == []


# ── Journal des refus et cycle de vie expose aux routes d'administration ──────

DESCRIPTION_OUTLOOK = (
    "Outlook refuse de demarrer depuis la mise a jour, le message indique que le "
    "jeu de dossiers ne peut pas etre ouvert."
)
SOLUTION_OUTLOOK = (
    "Profil de messagerie corrompu. Nouveau profil cree depuis le panneau de "
    "configuration, compte reconfigure, envoi et reception verifies."
)


def test_refus_journalise_avec_son_motif(store):
    """Un refus ne laissait de trace que dans la sortie du serveur."""
    archiver(store, 70, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "ia")

    refus = store.get_refus()
    assert len(refus) == 1
    assert refus[0]["ticket_id"] == 70
    assert refus[0]["source_solution"] == "ia"
    assert "humain" in refus[0]["motif"]
    assert any(c["controle"] == "origine_humaine" and not c["passe"] for c in refus[0]["controles"])
    assert refus[0]["refuse_at"]


def test_refus_repare_disparait_du_journal(store):
    """Refuse avec une suggestion IA, puis accepte une fois la solution ecrite par un humain."""
    archiver(store, 71, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "ia")
    archiver(store, 71, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "admin")

    assert store.get_refus() == []


def test_seul_le_dernier_refus_d_un_ticket_compte(store):
    archiver(store, 72, "VPN inaccessible", DESCRIPTION, "trop court", "admin")
    archiver(store, 72, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "ia")

    refus = store.get_refus()
    assert len(refus) == 1
    assert "humain" in refus[0]["motif"]


def test_reactivation_d_une_connaissance_obsolete(store):
    archiver(store, 80, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "admin")
    assert store.marquer_obsolete(80, motif="procedure depassee", par="3")

    entree = store.get_entry(80)
    assert entree["statut"] == store.STATUT_OBSOLETE
    assert entree["obsolete_par"] == "3"

    assert store.reactiver(80, par="3")
    assert store.get_entry(80)["statut"] == store.STATUT_ACTIF
    assert 80 in {r["ticket_id"] for r in store.query_similar(DESCRIPTION, top_k=5)}

    # Deja active : rien a reactiver.
    assert not store.reactiver(80)


def test_une_connaissance_remplacee_ne_se_reactive_pas(store):
    archiver(store, 81, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "admin")
    archiver(store, 82, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "admin")

    assert store.get_entry(81)["statut"] == store.STATUT_REMPLACE
    assert not store.reactiver(81)


def test_entree_absente(store):
    assert store.get_entry(999) is None
    assert not store.reactiver(999)


def test_cycle_de_vie_compte_chaque_statut(store):
    archiver(store, 90, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "admin")
    archiver(store, 91, "VPN inaccessible", DESCRIPTION, SOLUTION_ADMIN, "admin")
    archiver(store, 92, "Outlook bloque", DESCRIPTION_OUTLOOK, SOLUTION_OUTLOOK, "admin",
             categorie="Microsoft")
    store.marquer_obsolete(92, motif="version d'Outlook retiree")

    vue = store.get_cycle_de_vie()
    assert vue["total"] == 3
    assert vue["par_statut"] == {
        store.STATUT_ACTIF: 1, store.STATUT_REMPLACE: 1, store.STATUT_OBSOLETE: 1,
    }
    statuts = {e["ticket_id"]: e["statut"] for e in vue["entrees"]}
    assert statuts == {90: store.STATUT_REMPLACE, 91: store.STATUT_ACTIF, 92: store.STATUT_OBSOLETE}
