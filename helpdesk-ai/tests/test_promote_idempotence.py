"""
Tests de robustesse de la porte de promotion.

Ces tests couvrent le defaut trouve en relecture : `promote.py` sortait en erreur
quand il n'y avait rien a arbitrer. Comme models/best_pipeline.pkl est une SORTIE
du stage DVC `promote`, et que DVC supprime les sorties d'un stage avant de
l'executer, un `dvc repro` sans nouveau candidat laissait l'artefact servi absent
et l'API incapable de demarrer, alors que le registre en detenait une copie.
"""

import json
import os
import subprocess
import sys

import pytest

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "src"))
from pipeline.promote import comparer, metrique_effective  # noqa: E402
from registry.model_registry import ModelRegistry  # noqa: E402

PARAMS = {
    "promotion": {
        "primary_metric": "f1_macro_heuristiques",
        "min_improvement": 0.005,
        "max_class_regression": 0.05,
        "allow_accuracy_regression": False,
        "ignore_zero_support_classes": True,
    }
}

CONFUSION = {
    "labels": ["Microsoft", "Réseau"],
    "support": {"Microsoft": 135, "Réseau": 45},
    "classes_sans_support": [],
}


# ── metrique absente ─────────────────────────────────────────────────────────

def test_metrique_absente_refuse_d_arbitrer():
    """
    Une metrique manquante ne doit jamais etre lue comme un zero : la production
    vaudrait 0.0 et le candidat gagnerait par defaut, soit l'inverse exact de ce
    que la porte protege.
    """
    metrique = metrique_effective(PARAMS)
    candidat = {metrique: 0.90, "accuracy": 0.9, "f1_Microsoft": 0.9, "f1_Réseau": 0.9}
    production = {"accuracy": 0.9, "f1_Microsoft": 0.9, "f1_Réseau": 0.9}  # metrique absente

    with pytest.raises(KeyError) as erreur:
        comparer(candidat, production, CONFUSION, PARAMS)
    assert metrique in str(erreur.value)


def test_metrique_absente_du_candidat_refuse_aussi():
    metrique = metrique_effective(PARAMS)
    production = {metrique: 0.80, "accuracy": 0.9, "f1_Microsoft": 0.9, "f1_Réseau": 0.9}
    with pytest.raises(KeyError):
        comparer({"accuracy": 0.9}, production, CONFUSION, PARAMS)


# ── idempotence du stage ─────────────────────────────────────────────────────

PARAMS_YAML = """
data:
  random_state: 42
nlp:
  max_features: 200
  ngram_range: [1, 1]
  min_df: 1
ml:
  confidence_threshold: 0.60
promotion:
  primary_metric: f1_macro_heuristiques
  min_improvement: 0.005
  max_class_regression: 0.05
  allow_accuracy_regression: false
  ignore_zero_support_classes: true
registry:
  dir: models/registry
  mlflow_register: false
split:
  reference_manifest: data/reference/test_reference_manifest.json
"""

LIGNES_TEST = [
    ("Probleme de connexion au reseau wifi", "Réseau"),
    ("Le wifi du batiment coupe sans arret", "Réseau"),
    ("Impossible de joindre le reseau local", "Réseau"),
    ("Connexion reseau instable au bureau", "Réseau"),
    ("Outlook ne demarre plus du tout", "Microsoft"),
    ("Excel plante a chaque ouverture", "Microsoft"),
    ("Outlook affiche une erreur de profil", "Microsoft"),
    ("Excel refuse d'enregistrer le fichier", "Microsoft"),
]


def _pipeline_reel(random_state=42):
    """Un vrai pipeline sklearn : promote charge et evalue l'artefact pour de bon."""
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.pipeline import Pipeline
    from sklearn.svm import LinearSVC

    textes = [t for t, _ in LIGNES_TEST] * 3
    labels = [c for _, c in LIGNES_TEST] * 3
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=200, min_df=1)),
        ("clf", CalibratedClassifierCV(
            LinearSVC(class_weight="balanced", max_iter=2000, random_state=random_state),
            cv=3)),
    ])
    pipeline.fit(textes, labels)
    return pipeline


@pytest.fixture
def depot(tmp_path, monkeypatch):
    """Dépôt minimal mais réel : params, jeu de test, et un modèle en production."""
    import joblib
    import pandas as pd

    (tmp_path / "models").mkdir()
    (tmp_path / "metrics").mkdir()
    (tmp_path / "data" / "splits").mkdir(parents=True)
    (tmp_path / "params.yaml").write_text(PARAMS_YAML, encoding="utf-8")

    pd.DataFrame([
        {"Titre": t, "Description": t, "text_clean": t.lower(), "Catégorie": c}
        for t, c in LIGNES_TEST
    ]).to_csv(tmp_path / "data" / "splits" / "test.csv", index=False, encoding="utf-8")

    servi = tmp_path / "models" / "best_pipeline.pkl"
    joblib.dump(_pipeline_reel(), servi)
    (tmp_path / "models" / "model_metadata.json").write_text(
        json.dumps({"model_name": "test"}), encoding="utf-8"
    )

    registre = ModelRegistry(root=str(tmp_path / "models" / "registry"),
                             served_path=str(servi))
    version = registre.register(
        pipeline_path=str(servi),
        metadata={"model_name": "test"},
        metrics={"f1_macro_heuristiques": 0.685, "f1_macro_classes_evaluables": 0.822},
        lineage={"dataset_version": "abc"},
        tag="candidate",
    )
    registre.promote(version, reason="mise en service initiale")
    # Le journal du jeu gele est resolu depuis l'emplacement du module, pas
    # depuis le repertoire courant : sans cette redirection, promote.py lance en
    # sous-processus inscrirait ses lectures d'essai dans le journal du depot.
    # Un monkeypatch d'attribut n'y suffit pas, le sous-processus ne le voit pas.
    (tmp_path / "data" / "reference").mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("JOURNAL_JEU_GELE",
                       str(tmp_path / "data" / "reference" / "journal_jeu_gele.json"))
    monkeypatch.setenv("CHEMIN_JEU_GELE",
                       str(tmp_path / "data" / "splits" / "test.csv"))
    monkeypatch.chdir(tmp_path)
    return tmp_path, registre


def _lancer_promote():
    return subprocess.run(
        [sys.executable, os.path.join(RACINE, "src", "pipeline", "promote.py")],
        capture_output=True, text=True,
    )


def test_sans_candidat_le_stage_restaure_et_sort_en_succes(depot):
    """
    Reproduit exactement ce que fait DVC : suppression des sorties du stage, puis
    execution. Le stage doit se terminer en succes et l'artefact servi doit etre
    de nouveau present, restaure depuis le registre. Avant correction, il sortait
    en erreur et laissait l'API sans modele.
    """
    racine, registre = depot
    reference = (racine / "models" / "best_pipeline.pkl").read_bytes()
    os.remove(racine / "models" / "best_pipeline.pkl")
    os.remove(racine / "models" / "model_metadata.json")

    resultat = _lancer_promote()

    assert resultat.returncode == 0, resultat.stdout + resultat.stderr
    assert (racine / "models" / "best_pipeline.pkl").exists()
    assert (racine / "models" / "model_metadata.json").exists()
    assert (racine / "models" / "best_pipeline.pkl").read_bytes() == reference
    assert registre.resolve_alias("production") == 1


def test_sans_candidat_les_metriques_decrivent_le_modele_en_service(depot):
    """metrics/ml_eval.json doit toujours decrire le modele servi, jamais un vide."""
    racine, _ = depot
    os.remove(racine / "models" / "best_pipeline.pkl")

    assert _lancer_promote().returncode == 0

    with open(racine / "metrics" / "ml_eval.json", encoding="utf-8") as f:
        metriques = json.load(f)
    assert "f1_macro_classes_evaluables" in metriques
    assert metriques["n_classes_evaluables"] == 2


def test_relance_sans_rien_changer_reste_stable(depot):
    """Deux executions consecutives laissent le depot dans le meme etat."""
    racine, registre = depot
    assert _lancer_promote().returncode == 0
    empreinte = (racine / "models" / "best_pipeline.pkl").read_bytes()
    historique = len(registre.load()["history"])

    assert _lancer_promote().returncode == 0

    assert (racine / "models" / "best_pipeline.pkl").read_bytes() == empreinte
    assert registre.resolve_alias("production") == 1
    # Aucun arbitrage n'a eu lieu : l'historique du registre ne bouge pas.
    assert len(registre.load()["history"]) == historique


def test_sans_production_ni_candidat_echoue_franchement(tmp_path, monkeypatch):
    """Un depot reellement vide doit echouer, pas restaurer un modele inexistant."""
    (tmp_path / "models").mkdir()
    (tmp_path / "metrics").mkdir()
    (tmp_path / "data" / "splits").mkdir(parents=True)
    (tmp_path / "params.yaml").write_text(PARAMS_YAML, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    resultat = _lancer_promote()
    assert resultat.returncode == 1
    assert "train.py" in resultat.stdout


def test_le_registre_survit_a_la_suppression_des_sorties_du_stage(depot):
    """
    L'historique des decisions ne doit dependre d'aucune sortie DVC. C'est la
    raison pour laquelle models/registry/ n'est declare dans aucun stage.
    """
    racine, registre = depot
    for sortie in ("models/best_pipeline.pkl", "models/model_metadata.json"):
        chemin = racine / sortie
        if chemin.exists():
            os.remove(chemin)

    index = registre.load()
    assert index["aliases"]["production"] == 1
    assert [h["action"] for h in index["history"]] == ["register", "promote"]
    assert registre.read_pointer() == 1
