"""
Registre de modeles — fichier, versionne par DVC.

POURQUOI UN REGISTRE DANS LE DEPOT PLUTOT QUE CELUI DE MLFLOW ?
    Le Model Registry de MLflow fonctionne avec le store "file:./mlruns" utilise
    par le projet — verifie a l'execution, une version y est bien creee — mais
    MLflow 3.6 le declare deprecie et annonce son retrait au profit d'un backend
    SQL. Faire reposer la promotion et le rollback dessus adosserait une fonction
    critique a une API en fin de vie, et migrer vers SQLite orphelinerait les
    53 runs deja enregistres.

    Ce registre-ci fait le travail attendu d'un registre — versions, alias,
    lineage, rollback — dans un format inspectable, diffable en revue de code et
    versionnable avec le code qui l'a produit. promote.py enregistre EN PLUS dans
    le registre MLflow quand c'est possible : les deux coexistent, celui-ci reste
    la reference.

CONTENU
    models/registry/registry.json   index des versions + alias
    models/registry/v{n}/           artefacts figes de la version n
        pipeline.pkl
        model_metadata.json
        metrics.json
        lineage.json

INVARIANT
    L'alias `production` designe toujours une version dont les artefacts existent.
    models/best_pipeline.pkl est une COPIE de la version production : le code de
    service (api/predictor.py) continue de lire ce chemin, inchange.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from typing import Any, Optional


class RegistryError(RuntimeError):
    """Operation impossible sur le registre (version inconnue, artefact manquant)."""


class ModelRegistry:
    """Registre de modeles sur disque. Toutes les ecritures sont atomiques."""

    INDEX_NAME = "registry.json"

    def __init__(self, root: str = "models/registry", served_path: str = "models/best_pipeline.pkl"):
        self.root = root
        self.served_path = served_path
        self.index_path = os.path.join(root, self.INDEX_NAME)

    # ── index ────────────────────────────────────────────────────────────────

    def _empty_index(self) -> dict[str, Any]:
        return {"schema": 1, "versions": [], "aliases": {}, "history": []}

    def load(self) -> dict[str, Any]:
        if not os.path.exists(self.index_path):
            return self._empty_index()
        with open(self.index_path, encoding="utf-8") as f:
            return json.load(f)

    def _save(self, index: dict[str, Any]) -> None:
        os.makedirs(self.root, exist_ok=True)
        tmp = self.index_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.index_path)

    # ── lecture ──────────────────────────────────────────────────────────────

    def next_version(self) -> int:
        index = self.load()
        return max((v["version"] for v in index["versions"]), default=0) + 1

    def get_version(self, version: int) -> Optional[dict[str, Any]]:
        return next((v for v in self.load()["versions"] if v["version"] == version), None)

    def resolve_alias(self, alias: str = "production") -> Optional[int]:
        return self.load()["aliases"].get(alias)

    def get_production(self) -> Optional[dict[str, Any]]:
        v = self.resolve_alias("production")
        return self.get_version(v) if v is not None else None

    def version_dir(self, version: int) -> str:
        return os.path.join(self.root, f"v{version}")

    def list_versions(self) -> list[dict[str, Any]]:
        return sorted(self.load()["versions"], key=lambda v: v["version"], reverse=True)

    # ── ecriture ─────────────────────────────────────────────────────────────

    def register(
        self,
        pipeline_path: str,
        metadata: dict[str, Any],
        metrics: dict[str, Any],
        lineage: dict[str, Any],
        tag: str = "candidate",
    ) -> int:
        """
        Fige une nouvelle version. N'active RIEN : enregistrer n'est pas promouvoir.

        `lineage` repond aux questions de tracabilite : quel dataset, quel jeu de
        test, quel commit, quel run MLflow.
        """
        if not os.path.exists(pipeline_path):
            raise RegistryError(f"Artefact introuvable : {pipeline_path}")

        version = self.next_version()
        vdir = self.version_dir(version)
        os.makedirs(vdir, exist_ok=True)

        shutil.copy2(pipeline_path, os.path.join(vdir, "pipeline.pkl"))
        for name, payload in (
            ("model_metadata.json", metadata),
            ("metrics.json", metrics),
            ("lineage.json", lineage),
        ):
            with open(os.path.join(vdir, name), "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

        index = self.load()
        index["versions"].append({
            "version": version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "tag": tag,
            "model_name": metadata.get("model_name", "inconnu"),
            "primary_metric": metrics.get("f1_macro_heuristiques"),
            "accuracy": metrics.get("accuracy"),
            "dataset_version": lineage.get("dataset_version"),
            "train_size": metadata.get("train_size"),
            "test_size": metadata.get("test_size"),
            "path": vdir.replace("\\", "/"),
        })
        index["history"].append({
            "at": datetime.now(timezone.utc).isoformat(),
            "action": "register",
            "version": version,
            "tag": tag,
        })
        self._save(index)
        return version

    def promote(self, version: int, reason: str, decision: Optional[dict] = None) -> None:
        """
        Deplace l'alias `production` et met a jour l'artefact servi.

        L'ordre est important : la copie du .pkl AVANT l'ecriture de l'index. Si la
        copie echoue, l'alias n'a pas bouge et la production reste coherente.
        """
        entry = self.get_version(version)
        if entry is None:
            raise RegistryError(f"Version inconnue : v{version}")

        src = os.path.join(self.version_dir(version), "pipeline.pkl")
        if not os.path.exists(src):
            raise RegistryError(f"Artefact manquant pour v{version} : {src}")

        os.makedirs(os.path.dirname(self.served_path) or ".", exist_ok=True)
        shutil.copy2(src, self.served_path)

        meta_src = os.path.join(self.version_dir(version), "model_metadata.json")
        meta_dst = os.path.join(os.path.dirname(self.served_path) or ".", "model_metadata.json")
        if os.path.exists(meta_src):
            shutil.copy2(meta_src, meta_dst)

        index = self.load()
        previous = index["aliases"].get("production")
        index["aliases"]["production"] = version
        for v in index["versions"]:
            if v["version"] == version:
                v["tag"] = "production"
            elif v.get("tag") == "production":
                v["tag"] = "archived"
        index["history"].append({
            "at": datetime.now(timezone.utc).isoformat(),
            "action": "promote",
            "version": version,
            "previous": previous,
            "reason": reason,
            "decision": decision or {},
        })
        self._save(index)
        self._write_pointer(version)

    def reject(self, version: int, reason: str, decision: Optional[dict] = None) -> None:
        """Trace un rejet. La production reste strictement inchangee."""
        index = self.load()
        for v in index["versions"]:
            if v["version"] == version:
                v["tag"] = "rejected"
        index["history"].append({
            "at": datetime.now(timezone.utc).isoformat(),
            "action": "reject",
            "version": version,
            "reason": reason,
            "decision": decision or {},
        })
        self._save(index)

    def rollback(self, version: int, reason: str = "rollback manuel") -> None:
        """Retour a une version anterieure. Meme mecanique que promote, tracee comme rollback."""
        entry = self.get_version(version)
        if entry is None:
            raise RegistryError(f"Version inconnue : v{version}")
        self.promote(version, reason=reason)
        index = self.load()
        index["history"][-1]["action"] = "rollback"
        self._save(index)

    # ── pointeur de fraicheur (multi-workers) ────────────────────────────────

    def pointer_path(self) -> str:
        return os.path.join(self.root, "PRODUCTION")

    def _write_pointer(self, version: int) -> None:
        """
        Fichier sentinelle relu par api/predictor.py. L'API tourne avec plusieurs
        workers uvicorn (processus separes) : un rechargement declenche dans un
        worker est invisible aux autres. Chaque worker compare ce pointeur au
        modele qu'il a en memoire et se recharge tout seul si l'ecart apparait.
        """
        with open(self.pointer_path(), "w", encoding="utf-8") as f:
            f.write(str(version))

    def read_pointer(self) -> Optional[int]:
        try:
            with open(self.pointer_path(), encoding="utf-8") as f:
                return int(f.read().strip())
        except (OSError, ValueError):
            return None

    # ── amorcage ─────────────────────────────────────────────────────────────

    def bootstrap_from_existing(
        self,
        pipeline_path: str = "models/best_pipeline.pkl",
        metadata_path: str = "models/model_metadata.json",
        metrics_path: str = "metrics/ml_eval.json",
    ) -> Optional[int]:
        """
        Enregistre le modele deja en production comme v1 si le registre est vide.

        Sans cette etape, la premiere comparaison n'aurait aucun modele de reference
        et le premier candidat serait promu par defaut, ce qui est exactement le
        comportement que la porte de promotion doit empecher.
        """
        if self.load()["versions"]:
            return None
        if not os.path.exists(pipeline_path):
            return None

        metadata = _read_json(metadata_path, default={})
        metrics = _read_json(metrics_path, default={})
        version = self.register(
            pipeline_path=pipeline_path,
            metadata=metadata,
            metrics=metrics,
            lineage={
                "source": "bootstrap",
                "note": "Modele deja en service avant la mise en place du registre.",
                "dataset_version": "pre-registry",
                "test_reference": metadata.get("split_strategy", "inconnu"),
            },
            tag="production",
        )
        index = self.load()
        index["aliases"]["production"] = version
        index["history"].append({
            "at": datetime.now(timezone.utc).isoformat(),
            "action": "bootstrap",
            "version": version,
            "reason": "modele preexistant adopte comme reference de production",
        })
        self._save(index)
        self._write_pointer(version)
        return version


def _read_json(path: str, default: Any = None) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default
