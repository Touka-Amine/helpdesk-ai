# -*- coding: utf-8 -*-
"""Compte la suite de tests, pour que le memoire cite un chiffre mesure.

Pourquoi ce script
------------------
Le memoire annonçait « cent quatre-vingt-un tests », « cent cinquante-cinq
rejoues par l'integration continue » et « 44 % de couverture ». Ces trois
nombres etaient justes quand ils ont ete ecrits et ne l'etaient plus : la suite
en compte 260. Un nombre recopie a la main vieillit sans prevenir ; celui-ci est
releve par une commande et ecrit dans un fichier que le memoire cite.

Les trois perimetres, et pourquoi ils different
-----------------------------------------------
  - TOTAL : tout ce que `pytest` collecte ;
  - INTEGRATION : `tests/test_api_integration.py`, qui charge le pipeline au
    demarrage et ne peut donc pas tourner la ou le modele n'est pas publie ;
  - CONTINU : ce que l'integration continue rejoue, soit le total moins les
    tests d'integration — c'est exactement la commande de .github/workflows/ci.yml.

La couverture est relevee separement par
`pytest --cov`, dans metrics/couverture_tests.txt (perimetre `src/`, celui que
la figure du chapitre 7 montre) et metrics/couverture_tests_service_entier.txt
(perimetre `api/` + `src/`).

Sortie : metrics/suite_tests.json
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, "metrics", "suite_tests.json")
COUVERTURE = os.path.join(RACINE, "metrics", "couverture_tests.txt")
COUVERTURE_ENTIERE = os.path.join(RACINE, "metrics",
                                  "couverture_tests_service_entier.txt")


def compter(args: list[str]) -> int:
    r = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"] + args,
                       cwd=RACINE, capture_output=True, text=True)
    # Avec une deselection, pytest ecrit « 244/260 tests collected (16 deselected) » :
    # c'est le premier nombre qui compte, et un motif trop large y lirait 260.
    m = re.search(r"(\d+)(?:/\d+)?\s+tests? collected", r.stdout)
    if not m:
        raise SystemExit("collecte illisible : %s" % r.stdout[-400:])
    return int(m.group(1))


def total_couverture(chemin: str):
    if not os.path.exists(chemin):
        return None
    for ligne in io.open(chemin, encoding="utf-8", errors="replace"):
        m = re.match(r"^TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%", ligne.strip())
        if m:
            return {"instructions": int(m.group(1)), "non_couvertes": int(m.group(2)),
                    "couverture_pourcent": int(m.group(3))}
    return None


def main() -> int:
    total = compter(["tests/"])
    integration = compter(["tests/test_api_integration.py"])
    continu = compter(["tests/", "--ignore=tests/test_api_integration.py"])
    lents = total - compter(["tests/", "-m", "not slow"])

    releve = {
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "objet": "Decompte mesure de la suite de tests, cite par le memoire.",
        "total": total,
        "integration_api": integration,
        "rejoues_par_l_integration_continue": continu,
        "lents_deselectionnables": lents,
        "commande_de_l_integration_continue":
            "pytest tests/ --ignore=tests/test_api_integration.py",
        "couverture_src": total_couverture(COUVERTURE),
        "couverture_api_et_src": total_couverture(COUVERTURE_ENTIERE),
    }
    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump(releve, f, ensure_ascii=False, indent=2)

    print("total                 %d" % total)
    print("dont integration API  %d  (ecartes de l'integration continue)" % integration)
    print("rejoues par la CI     %d" % continu)
    print("lents                 %d" % lents)
    for cle in ("couverture_src", "couverture_api_et_src"):
        c = releve[cle]
        print("%-22s%s" % (cle, "%d %%" % c["couverture_pourcent"] if c else "non mesuree"))
    print("\necrit : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
