"""
Tests de la construction du dataset (axe 1, etape 2).

L'objet de ces tests est la frontiere anti-fuite : aucune ligne de production ne
doit pouvoir atteindre le jeu de test gele, ni directement ni par recopie.
"""

import json
import os
import subprocess
import sys

import pandas as pd
import pytest

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "src"))
from pipeline.build_dataset import normaliser, sha256_fichier  # noqa: E402

COLONNES = ["ID", "Titre", "Description", "Catégorie", "text_clean", "Résolution/Motif"]


def ecrire_csv(chemin, lignes):
    pd.DataFrame(lignes).to_csv(chemin, index=False, encoding="utf-8")


@pytest.fixture
def projet(tmp_path, monkeypatch):
    """Arborescence minimale d'un projet, isolee dans tmp_path."""
    (tmp_path / "data" / "splits").mkdir(parents=True)
    (tmp_path / "data" / "curated").mkdir(parents=True)

    ecrire_csv(tmp_path / "data" / "splits" / "train.csv", [
        {"ID": "H1", "Titre": "Probleme VPN", "Description": "vpn hs",
         "Catégorie": "Réseau", "text_clean": "vpn hs", "Résolution/Motif": "reboot"},
        {"ID": "H2", "Titre": "Outlook bloque", "Description": "outlook fige",
         "Catégorie": "Microsoft", "text_clean": "outlook fige", "Résolution/Motif": "profil"},
    ])
    ecrire_csv(tmp_path / "data" / "splits" / "test.csv", [
        {"ID": "T1", "Titre": "Imprimante HS", "Description": "spooler plante",
         "Catégorie": "Système", "text_clean": "spooler plante", "Résolution/Motif": "spooler"},
    ])
    (tmp_path / "params.yaml").write_text(
        "collect:\n  curated_dir: data/curated\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    return tmp_path


def lancer():
    resultat = subprocess.run(
        [sys.executable, os.path.join(RACINE, "src", "pipeline", "build_dataset.py")],
        capture_output=True, text=True,
    )
    return resultat


def test_sans_production_le_dataset_est_le_corpus_historique(projet):
    resultat = lancer()
    assert resultat.returncode == 0, resultat.stderr

    dataset = pd.read_csv(projet / "data" / "splits" / "train_current.csv")
    assert len(dataset) == 2
    assert set(dataset["source"]) == {"corpus_historique"}

    with open(projet / "data" / "splits" / "train_current.manifest.json", encoding="utf-8") as f:
        manifeste = json.load(f)
    assert manifeste["n_production_retenues"] == 0
    assert len(manifeste["dataset_version"]) == 12


def test_les_lignes_de_production_sont_fusionnees(projet):
    ecrire_csv(projet / "data" / "curated" / "validated_20260101.csv", [
        {"ID": "PROD-1", "Titre": "Wifi instable", "Description": "coupures wifi",
         "Catégorie": "Réseau", "text_clean": "coupures wifi",
         "Résolution/Motif": "canal change", "source": "production",
         "ticket_id": 1, "sample_weight": 1.0, "label_strength": "corrected"},
    ])
    assert lancer().returncode == 0

    dataset = pd.read_csv(projet / "data" / "splits" / "train_current.csv")
    assert len(dataset) == 3
    assert (dataset["source"] == "production").sum() == 1


def test_un_titre_du_jeu_de_test_est_ecarte(projet):
    """Un ticket de production qui recopie un titre de test serait une fuite."""
    ecrire_csv(projet / "data" / "curated" / "validated_20260101.csv", [
        {"ID": "PROD-2", "Titre": "Imprimante HS", "Description": "autre souci",
         "Catégorie": "Système", "text_clean": "autre souci",
         "Résolution/Motif": "x", "source": "production", "ticket_id": 2,
         "sample_weight": 1.0, "label_strength": "corrected"},
    ])
    resultat = lancer()
    assert resultat.returncode == 0

    dataset = pd.read_csv(projet / "data" / "splits" / "train_current.csv")
    assert (dataset["source"] == "production").sum() == 0
    with open(projet / "data" / "splits" / "train_current.manifest.json", encoding="utf-8") as f:
        assert json.load(f)["rejets_anti_fuite"]["titre_dans_test"] == 1


def test_une_description_du_jeu_de_test_est_ecartee(projet):
    ecrire_csv(projet / "data" / "curated" / "validated_20260101.csv", [
        {"ID": "PROD-3", "Titre": "Autre titre", "Description": "Spooler  PLANTE",
         "Catégorie": "Système", "text_clean": "spooler plante",
         "Résolution/Motif": "x", "source": "production", "ticket_id": 3,
         "sample_weight": 1.0, "label_strength": "corrected"},
    ])
    assert lancer().returncode == 0

    with open(projet / "data" / "splits" / "train_current.manifest.json", encoding="utf-8") as f:
        assert json.load(f)["rejets_anti_fuite"]["description_dans_test"] == 1


def test_un_ticket_collecte_deux_fois_n_est_pris_qu_une_fois(projet):
    for jour in ("20260101", "20260201"):
        ecrire_csv(projet / "data" / "curated" / f"validated_{jour}.csv", [
            {"ID": "PROD-4", "Titre": "Wifi instable", "Description": "coupures",
             "Catégorie": "Réseau", "text_clean": "coupures",
             "Résolution/Motif": "canal", "source": "production", "ticket_id": 4,
             "sample_weight": 1.0, "label_strength": "corrected"},
        ])
    assert lancer().returncode == 0

    dataset = pd.read_csv(projet / "data" / "splits" / "train_current.csv")
    assert (dataset["source"] == "production").sum() == 1


def test_la_version_du_dataset_change_avec_le_contenu(projet):
    lancer()
    version_1 = sha256_fichier(str(projet / "data" / "splits" / "train_current.csv"))

    ecrire_csv(projet / "data" / "curated" / "validated_20260101.csv", [
        {"ID": "PROD-5", "Titre": "Nouveau cas", "Description": "un souci inedit",
         "Catégorie": "Réseau", "text_clean": "souci inedit",
         "Résolution/Motif": "y", "source": "production", "ticket_id": 5,
         "sample_weight": 1.0, "label_strength": "corrected"},
    ])
    lancer()
    version_2 = sha256_fichier(str(projet / "data" / "splits" / "train_current.csv"))
    assert version_1 != version_2


def test_normalisation_insensible_aux_accents_et_espaces():
    assert normaliser("  Spooler   PLANTÉ  ") == "spooler plante"
    assert normaliser("VPN\tHS") == "vpn hs"
