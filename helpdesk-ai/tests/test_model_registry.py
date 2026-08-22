"""
Tests du registre de modeles.

L'enjeu de ces tests est l'invariant central de l'axe 1 : enregistrer un modele
n'est pas le promouvoir, et la production ne change que sur une decision explicite.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from registry.model_registry import ModelRegistry, RegistryError  # noqa: E402


@pytest.fixture
def registre(tmp_path):
    """Registre isole dans un repertoire temporaire, avec un artefact factice."""
    artefact = tmp_path / "candidate.pkl"
    artefact.write_bytes(b"pipeline-factice-v1")
    reg = ModelRegistry(
        root=str(tmp_path / "registry"),
        served_path=str(tmp_path / "best_pipeline.pkl"),
    )
    return reg, artefact


def _enregistrer(reg, artefact, f1, tag="candidate", dataset="ds-1"):
    return reg.register(
        pipeline_path=str(artefact),
        metadata={"model_name": "test", "train_size": 100, "test_size": 20},
        metrics={"f1_macro_heuristiques": f1, "accuracy": f1},
        lineage={"dataset_version": dataset},
        tag=tag,
    )


def test_registre_vide(tmp_path):
    reg = ModelRegistry(root=str(tmp_path / "registry"))
    assert reg.list_versions() == []
    assert reg.get_production() is None
    assert reg.resolve_alias("production") is None
    assert reg.next_version() == 1


def test_enregistrer_ne_promeut_pas(registre):
    reg, artefact = registre
    version = _enregistrer(reg, artefact, 0.80)

    assert version == 1
    assert reg.get_version(1)["tag"] == "candidate"
    # L'invariant : aucune production tant que personne n'a decide.
    assert reg.get_production() is None
    assert not os.path.exists(reg.served_path)


def test_promotion_copie_artefact_et_deplace_alias(registre):
    reg, artefact = registre
    version = _enregistrer(reg, artefact, 0.80)
    reg.promote(version, reason="premiere version")

    assert reg.resolve_alias("production") == version
    assert reg.get_version(version)["tag"] == "production"
    with open(reg.served_path, "rb") as f:
        assert f.read() == b"pipeline-factice-v1"
    assert reg.read_pointer() == version


def test_promotion_archive_la_version_precedente(registre):
    reg, artefact = registre
    v1 = _enregistrer(reg, artefact, 0.80)
    reg.promote(v1, reason="v1")

    artefact.write_bytes(b"pipeline-factice-v2")
    v2 = _enregistrer(reg, artefact, 0.85)
    reg.promote(v2, reason="v2 meilleure")

    assert reg.resolve_alias("production") == v2
    assert reg.get_version(v1)["tag"] == "archived"
    assert reg.get_version(v2)["tag"] == "production"
    with open(reg.served_path, "rb") as f:
        assert f.read() == b"pipeline-factice-v2"


def test_rejet_laisse_la_production_intacte(registre):
    reg, artefact = registre
    v1 = _enregistrer(reg, artefact, 0.80)
    reg.promote(v1, reason="v1")

    artefact.write_bytes(b"pipeline-factice-mauvais")
    v2 = _enregistrer(reg, artefact, 0.50)
    reg.reject(v2, reason="regression")

    assert reg.resolve_alias("production") == v1
    assert reg.get_version(v2)["tag"] == "rejected"
    # L'artefact servi n'a pas ete touche par le rejet.
    with open(reg.served_path, "rb") as f:
        assert f.read() == b"pipeline-factice-v1"


def test_rollback_restaure_une_version_anterieure(registre):
    reg, artefact = registre
    v1 = _enregistrer(reg, artefact, 0.80)
    reg.promote(v1, reason="v1")
    artefact.write_bytes(b"pipeline-factice-v2")
    v2 = _enregistrer(reg, artefact, 0.85)
    reg.promote(v2, reason="v2")

    reg.rollback(v1, reason="regression constatee en production")

    assert reg.resolve_alias("production") == v1
    with open(reg.served_path, "rb") as f:
        assert f.read() == b"pipeline-factice-v1"
    assert reg.load()["history"][-1]["action"] == "rollback"


def test_historique_conserve_le_motif_des_decisions(registre):
    reg, artefact = registre
    v1 = _enregistrer(reg, artefact, 0.80)
    reg.promote(v1, reason="premiere version", decision={"portes": []})
    v2 = _enregistrer(reg, artefact, 0.60)
    reg.reject(v2, reason="gain insuffisant")

    actions = [(h["action"], h.get("reason")) for h in reg.load()["history"]]
    assert ("promote", "premiere version") in actions
    assert ("reject", "gain insuffisant") in actions


def test_version_inconnue_refusee(registre):
    reg, _ = registre
    with pytest.raises(RegistryError):
        reg.promote(99, reason="inexistante")
    with pytest.raises(RegistryError):
        reg.rollback(99)


def test_artefact_absent_refuse(tmp_path):
    reg = ModelRegistry(root=str(tmp_path / "registry"))
    with pytest.raises(RegistryError):
        reg.register(
            pipeline_path=str(tmp_path / "inexistant.pkl"),
            metadata={}, metrics={}, lineage={},
        )


def test_lineage_est_conserve(registre):
    reg, artefact = registre
    version = _enregistrer(reg, artefact, 0.80, dataset="abc123def456")
    chemin = os.path.join(reg.version_dir(version), "lineage.json")

    with open(chemin, encoding="utf-8") as f:
        lineage = json.load(f)
    assert lineage["dataset_version"] == "abc123def456"
    assert reg.get_version(version)["dataset_version"] == "abc123def456"


def test_bootstrap_adopte_le_modele_existant(tmp_path):
    """Sans amorcage, le premier candidat serait promu faute de reference."""
    modele = tmp_path / "best_pipeline.pkl"
    modele.write_bytes(b"modele-preexistant")
    meta = tmp_path / "model_metadata.json"
    meta.write_text(json.dumps({"model_name": "historique"}), encoding="utf-8")
    metriques = tmp_path / "ml_eval.json"
    metriques.write_text(json.dumps({"f1_macro_heuristiques": 0.685}), encoding="utf-8")

    reg = ModelRegistry(root=str(tmp_path / "registry"), served_path=str(modele))
    version = reg.bootstrap_from_existing(str(modele), str(meta), str(metriques))

    assert version == 1
    assert reg.resolve_alias("production") == 1
    assert reg.get_version(1)["primary_metric"] == 0.685
    # Idempotent : un second appel ne cree pas de doublon.
    assert reg.bootstrap_from_existing(str(modele), str(meta), str(metriques)) is None
