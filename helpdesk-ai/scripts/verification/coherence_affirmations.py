# -*- coding: utf-8 -*-
"""Troisieme controleur : les AFFIRMATIONS du memoire contre l'etat du depot.

Ce que les deux premiers ne voyaient pas
----------------------------------------
`coherence_memoire.py` et `tracabilite_chiffres.py` comparent des NOMBRES. Ils
ne voient pas une phrase. Le memoire pouvait donc ecrire « ni anonymisation ni
pseudonymisation » six fois pendant que le depot portait un module de
pseudonymisation, un script de purge et un audit rendant « conforme : true »,
sans qu'aucun controle ne bronche.

Ce controleur verifie des affirmations. Chacune a :
  - une VERITE lue dans le depot — un fichier qui existe, une cle d'un fichier
    de mesure, un compte releve par commande ;
  - des motifs INTERDITS au memoire si cette verite tient ;
  - un motif ATTENDU, pour que supprimer la phrase fautive sans la remplacer ne
    suffise pas a faire passer le controle.

Un controle qui ne sait pas etablir sa verite s'annonce « indecidable » et ne
conclut pas. Il vaut mieux un trou declare qu'un vert de complaisance.

Sortie : scripts/verification/rapport_affirmations.json
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys
from datetime import datetime, timezone

ICI = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(ICI))          # helpdesk-ai
MEMOIRE = os.path.join(os.path.dirname(CODE), "report")
SORTIE = os.path.join(ICI, "rapport_affirmations.json")


# ── lecture du depot ─────────────────────────────────────────────────────────

def fichier(rel: str) -> bool:
    return os.path.exists(os.path.join(CODE, rel.replace("/", os.sep)))


def mesure(rel: str):
    chemin = os.path.join(CODE, rel.replace("/", os.sep))
    if not os.path.exists(chemin):
        return None
    try:
        with io.open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except (ValueError, OSError):
        return None


def textes_du_memoire() -> dict:
    out = {}
    for chemin in sorted(glob.glob(os.path.join(MEMOIRE, "*.tex"))):
        out[os.path.basename(chemin)] = io.open(
            chemin, encoding="utf-8", errors="replace").read()
    return out


def occurrences(textes: dict, motif: str) -> list:
    """Les endroits ou le motif apparait, en numeros de ligne."""
    trouves = []
    rx = re.compile(motif, re.IGNORECASE)
    for nom, t in textes.items():
        for i, ligne in enumerate(t.split("\n"), 1):
            if rx.search(ligne):
                trouves.append("%s:%d" % (nom, i))
    return trouves


# ── les affirmations controlees ──────────────────────────────────────────────

def construire_controles(textes: dict) -> list:
    suite = mesure("metrics/suite_tests.json")
    audit = mesure("scripts/verification/rapport_donnees_personnelles.json")
    priorite = mesure("metrics/priorite_eval.json")
    tonalite = mesure("metrics/tonalite_eval.json")
    resume_eval = mesure("metrics/resume_eval.json")

    c = []

    # 1. Decompte de la suite de tests
    if suite:
        total, ci = suite["total"], suite["rejoues_par_l_integration_continue"]
        c.append({
            "nom": "nombre de tests de la suite",
            "verite": "%d tests collectes, %d rejoues par l'integration continue"
                      % (total, ci),
            "interdits": [r"cent quatre-vingt-un", r"\b181 tests",
                          r"cent cinquante-cinq", r"\b155 rejou"],
            "attendu": r"\b%d\b" % total,
        })
        cov = suite.get("couverture_src")
        if cov:
            c.append({
                "nom": "couverture de la suite",
                "verite": "%d %% sur le perimetre src/" % cov["couverture_pourcent"],
                "interdits": [r"44\\?,?\s*\\?%\s*de couverture", r"pour 44\\,%"],
                "attendu": r"%d\\?,?\s*\\?%%" % cov["couverture_pourcent"],
            })
    else:
        c.append({"nom": "nombre de tests de la suite", "indecidable":
                  "metrics/suite_tests.json absent — lancer scripts/releve_suite_tests.py"})

    # 2. Donnees personnelles
    pseudo_livree = (fichier("src/data/pseudonymisation.py")
                     and fichier("scripts/pseudonymiser_corpus.py")
                     and audit is not None and audit.get("conforme") is True)
    if pseudo_livree:
        c.append({
            "nom": "pseudonymisation du corpus",
            "verite": "module livre, audit sur %s fragments : conforme"
                      % audit.get("fragments_recherches"),
            "interdits": [r"[Nn]i anonymisation ni pseudonymisation",
                          r"sans\s+anonymisation",
                          r"noms? des demandeurs (?:figurent|en clair)",
                          r"portent les noms des demandeurs en clair",
                          r"porte des noms de demandeurs en clair"],
            "attendu": r"pseudonymis",
        })
    else:
        c.append({"nom": "pseudonymisation du corpus", "indecidable":
                  "le depot ne permet pas de conclure que la pseudonymisation est livree"})

    # 3 a 5. Les exigences fonctionnelles traitees depuis la redaction.
    #
    # Le motif doit porter sur la LIGNE entiere et dans les DEUX sens : la
    # premiere version de ce controle cherchait « EF-11 ... non traitee » et
    # laissait passer « les exigences non traitees sont EF-11, EF-12 et EF-13 »,
    # qui est la forme exacte employee au chapitre 6. Un controle qui ne trouve
    # pas la faute qu'il vise est pire qu'un controle absent.
    negatifs = r"(?:non trait|non tenue|pas (?:ete )?trait|n'oriente pas|non abord)"

    def interdits_pour(ref: str) -> list:
        return [r"%s[^\n]{0,160}%s" % (ref, negatifs),
                r"%s[^\n]{0,160}%s" % (negatifs, ref)]

    if fichier("api/services/routage_service.py") and fichier("tests/test_routage.py"):
        c.append({
            "nom": "EF-07, orientation selon la confiance",
            "verite": "api/services/routage_service.py livre et teste",
            "interdits": interdits_pour("EF-07"),
            "attendu": r"EF-07",
        })
    if fichier("src/models/resume.py") and resume_eval:
        c.append({
            "nom": "EF-11, resume automatique",
            "verite": "src/models/resume.py livre, gain mesure dans resume_eval.json",
            "interdits": interdits_pour("EF-11"),
            "attendu": r"EF-11",
        })
    if priorite is not None and priorite.get("modele_retenu") is False:
        c.append({
            "nom": "EF-12, suggestion de priorite",
            "verite": "mesuree et NON retenue (metrics/priorite_eval.json)",
            "interdits": interdits_pour("EF-12"),
            "attendu": r"EF-12",
        })
    if tonalite is not None:
        c.append({
            "nom": "EF-13, analyse de tonalite",
            "verite": "mesuree, impossible sur ce corpus (metrics/tonalite_eval.json)",
            "interdits": interdits_pour("EF-13"),
            "attendu": r"EF-13",
        })
    return c


def main() -> int:
    textes = textes_du_memoire()
    if not textes:
        print("aucun .tex trouve dans %s" % MEMOIRE)
        return 1
    controles = construire_controles(textes)

    resultats, anomalies, indecidables = [], 0, 0
    print("=" * 70)
    for ctrl in controles:
        if "indecidable" in ctrl:
            indecidables += 1
            print("  ????  %-38s %s" % (ctrl["nom"], ctrl["indecidable"]))
            resultats.append({"nom": ctrl["nom"], "etat": "indecidable",
                              "detail": ctrl["indecidable"]})
            continue
        fautes = []
        for motif in ctrl["interdits"]:
            fautes += occurrences(textes, motif)
        manque_attendu = not occurrences(textes, ctrl["attendu"])
        if fautes or manque_attendu:
            anomalies += 1
            print("  NON   %-38s %s" % (ctrl["nom"], ctrl["verite"]))
            if fautes:
                print("        affirmations contraires : %s" % ", ".join(sorted(set(fautes))))
            if manque_attendu:
                print("        le memoire ne dit nulle part ce qui est vrai")
        else:
            print("  OK    %-38s %s" % (ctrl["nom"], ctrl["verite"]))
        resultats.append({
            "nom": ctrl["nom"],
            "verite_du_depot": ctrl["verite"],
            "etat": "anomalie" if (fautes or manque_attendu) else "ok",
            "occurrences_contraires": sorted(set(fautes)),
            "affirmation_attendue_absente": manque_attendu,
        })

    print("=" * 70)
    print("%d controles, %d anomalie(s), %d indecidable(s)"
          % (len(controles), anomalies, indecidables))
    with io.open(SORTIE, "w", encoding="utf-8") as f:
        json.dump({"date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "objet": "Affirmations du memoire confrontees a l'etat du depot.",
                   "n_controles": len(controles), "n_anomalies": anomalies,
                   "n_indecidables": indecidables, "controles": resultats},
                  f, ensure_ascii=False, indent=2)
    print("ecrit %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
