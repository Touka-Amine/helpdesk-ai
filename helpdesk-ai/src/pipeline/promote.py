"""
Stage DVC — AXE 1, etape 4 : porte de promotion.

Compare le modele CANDIDAT au modele actuellement EN PRODUCTION, sur le meme jeu
de test gele, et ne remplace la production que si le candidat passe toutes les
portes. C'est le seul endroit du projet qui ecrit models/best_pipeline.pkl.

POURQUOI REEVALUER LE MODELE DE PRODUCTION
    Les metriques stockees avec une version ont ete calculees au moment de son
    entrainement, potentiellement sur un jeu de test different. Comparer deux
    chiffres issus de deux jeux differents ne veut rien dire. Les deux modeles
    sont donc reevalues ici, dans la meme execution, sur data/splits/test.csv.

CE QUE LE JEU GELE EST, ET CE QU'IL N'EST PAS
    Remarque de l'encadrant du 2026-10-09 : le jeu de test gele ne doit pas
    devenir progressivement un jeu de validation servant a selectionner les
    modeles.

    Elle vise un risque reel et connu. Un jeu de test ne se degrade pas d'un
    coup, il se degrade par usage : chaque lecture qui TRANCHE fait passer un
    peu de son information dans le modele retenu, et le chiffre qu'il rendra la
    fois suivante mesure un peu moins la generalisation. Au bout de quelques
    dizaines de lectures il ne mesure plus rien, sans qu'aucune ligne de code
    n'ait change.

    Le jeu gele est ici une PORTE, pas un SELECTEUR. Il repond a « ce candidat
    peut-il remplacer la production », une fois par candidat. Il ne sert pas a
    choisir un hyperparametre, un seuil, une variante de texte ni une epoque :
    ces choix-la se font sur l'entrainement, par validation croisee par groupe
    de titres (voir src/pipeline/selection_camembert.py, qui ne lit jamais ce
    fichier).

    Trois garde-fous rendent la regle verifiable plutot que declarative :
      - chaque lecture s'inscrit dans data/reference/journal_jeu_gele.json,
        avec sa date, son motif et ce qu'elle a servi a decider ;
      - les lectures qui DECIDENT sont distinguees de celles qui RAPPORTENT,
        car recalculer un chiffre pour un tableau n'influence aucun choix ;
      - un budget declare dans params.yaml arrete la porte une fois atteint.
        Elle renvoie alors a une decision humaine : constituer une nouvelle
        reference a partir de tickets de production recents, ou assumer la
        lecture par ecrit avec --force, qui l'inscrit comme hors budget.

    Etat au 2026-10-09 : trois lectures decisionnelles, reconstituees depuis le
    registre (candidats v2, v3 et v4, tous trois rejetes). Le budget est fixe a
    dix.

LES PORTES
    1. Gain minimum sur la metrique principale.
    2. Aucune classe ayant du support au test ne perd plus que max_class_regression.
       Une F1-macro peut progresser globalement tout en effondrant une classe
       minoritaire. Cette porte l'empeche.
    3. L'accuracy ne regresse pas.
    Les classes sans support au test sont exclues des comparaisons : leur F1 vaut
    0.0 par construction, dans les deux modeles, et n'informe sur rien.

PREMIERE VERSION
    S'il n'existe aucun modele en production, le candidat est promu sans
    comparaison possible, et la decision le dit explicitement.

ROLLBACK
    python src/pipeline/promote.py --rollback 3
    Repositionne l'alias production sur la version 3 et restaure son artefact.

Usage :
    python src/pipeline/promote.py
    python src/pipeline/promote.py --dry-run
    python src/pipeline/promote.py --force        # promotion manuelle, tracee
    python src/pipeline/promote.py --rollback 2
    python src/pipeline/promote.py --list
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import joblib
import pandas as pd
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pipeline import jeu_gele                           # noqa: E402
from pipeline.train import evaluer                      # noqa: E402
from registry.model_registry import ModelRegistry, RegistryError   # noqa: E402

PARAMS_PATH = "params.yaml"
TEST_PATH = "data/splits/test.csv"
CANDIDATE_PATH = "models/candidate_pipeline.pkl"
SERVED_PATH = "models/best_pipeline.pkl"
METRICS_PROD = "metrics/ml_eval.json"
DECISION_OUT = "metrics/promotion_decision.json"


def charger_params() -> dict:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def metrique_effective(params: dict) -> str:
    """
    Resout la metrique de decision.

    Avec ignore_zero_support_classes, la F1-macro de reference devient celle
    calculee sur les seules classes presentes au test. Sur le jeu actuel, trois
    categories sur huit n'ont aucun ticket de test : les inclure ferait dependre
    la decision de la composition du jeu plutot que du modele.
    """
    promo = params.get("promotion", {})
    demandee = promo.get("primary_metric", "f1_macro_heuristiques")
    if promo.get("ignore_zero_support_classes", True) and demandee == "f1_macro_heuristiques":
        return "f1_macro_classes_evaluables"
    return demandee


def evaluer_artefact(chemin: str, test_df: pd.DataFrame, threshold: float) -> tuple[dict, dict]:
    pipeline = joblib.load(chemin)
    return evaluer(pipeline, test_df, threshold)


def comparer(metriques_candidat: dict, metriques_prod: dict, confusion: dict,
             params: dict) -> dict:
    """Applique les portes. Retourne le detail de la decision, porte par porte."""
    promo = params.get("promotion", {})
    metrique = metrique_effective(params)
    gain_min = float(promo.get("min_improvement", 0.005))
    regression_max = float(promo.get("max_class_regression", 0.05))
    accuracy_libre = bool(promo.get("allow_accuracy_regression", False))

    # Une metrique absente ne doit JAMAIS etre lue comme un zero : le modele de
    # production vaudrait 0.0 et le candidat gagnerait par defaut, soit exactement
    # l'inverse de ce que cette porte protege. On refuse d'arbitrer plutot que
    # d'arbitrer sur une valeur inventee.
    for nom, source in (("candidat", metriques_candidat), ("production", metriques_prod)):
        if metrique not in source:
            raise KeyError(
                f"Metrique de decision '{metrique}' absente des metriques du {nom}. "
                f"Comparaison impossible — aucune promotion n'est prononcee. "
                f"Cles disponibles : {sorted(k for k in source if k.startswith('f1_macro'))}"
            )

    val_candidat = float(metriques_candidat[metrique])
    val_prod = float(metriques_prod[metrique])
    delta = round(val_candidat - val_prod, 4)

    portes = []
    portes.append({
        "porte": "metrique_principale",
        "detail": f"{metrique} : {val_prod:.4f} -> {val_candidat:.4f} (delta {delta:+.4f}), "
                  f"gain minimum requis {gain_min}",
        "passe": delta >= gain_min,
    })

    evaluables = [c for c in confusion["labels"] if confusion["support"].get(c, 0) > 0]
    regressions = []
    for classe in evaluables:
        cle = f"f1_{classe.replace(' ', '_')}"
        chute = round(float(metriques_prod.get(cle, 0.0)) - float(metriques_candidat.get(cle, 0.0)), 4)
        if chute > regression_max:
            regressions.append({"classe": classe, "chute": chute})
    portes.append({
        "porte": "aucune_regression_par_classe",
        "detail": (f"chute maximale toleree {regression_max} sur {len(evaluables)} classes evaluees"
                   + (f" — depassements : {regressions}" if regressions else "")),
        "passe": not regressions,
    })

    delta_acc = round(
        float(metriques_candidat.get("accuracy", 0.0)) - float(metriques_prod.get("accuracy", 0.0)), 4
    )
    portes.append({
        "porte": "accuracy_non_regressive",
        "detail": f"accuracy delta {delta_acc:+.4f}"
                  + (" (regression autorisee)" if accuracy_libre else ""),
        "passe": accuracy_libre or delta_acc >= 0,
    })

    echecs = [p["porte"] for p in portes if not p["passe"]]
    return {
        "metrique_decision": metrique,
        "valeur_production": val_prod,
        "valeur_candidat": val_candidat,
        "delta": delta,
        "delta_accuracy": delta_acc,
        "classes_evaluees": evaluables,
        "classes_sans_support": confusion["classes_sans_support"],
        "regressions_par_classe": regressions,
        "portes": portes,
        "accepte": not echecs,
        "portes_en_echec": echecs,
    }


def ecrire_decision(decision: dict) -> None:
    os.makedirs(os.path.dirname(DECISION_OUT), exist_ok=True)
    with open(DECISION_OUT, "w", encoding="utf-8") as f:
        json.dump(decision, f, ensure_ascii=False, indent=2)
    print(f"[promote] Decision tracee : {DECISION_OUT}")


def enregistrer_mlflow(version: int, registre: ModelRegistry, params: dict) -> str | None:
    """
    Enregistrement dans le Model Registry MLflow, en complement du registre du depot.

    Le store "file:./mlruns" accepte le registre, avec un avertissement de
    depreciation. L'appel reste donc tente, mais son echec n'est jamais bloquant :
    la reference du projet est models/registry/, qui ne depend d'aucune API en
    cours de retrait.
    """
    mode = str(params.get("registry", {}).get("mlflow_register", "auto")).lower()
    if mode == "false" or os.environ.get("HELPDESK_SKIP_MLFLOW_REGISTRY") == "1":
        return None
    entree = registre.get_version(version)
    lineage_path = os.path.join(registre.version_dir(version), "lineage.json")
    try:
        with open(lineage_path, encoding="utf-8") as f:
            run_id = json.load(f).get("mlflow_run_id")
    except (OSError, json.JSONDecodeError):
        run_id = None
    if not run_id:
        return None
    try:
        import mlflow
        mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "file:./mlruns"))
        resultat = mlflow.register_model(f"runs:/{run_id}/model", "helpdesk-classification")
        print(f"[promote] MLflow Model Registry : version {resultat.version}")
        return str(resultat.version)
    except Exception as exc:
        if mode == "true":
            print(f"[promote] Enregistrement MLflow demande mais impossible : {exc}")
        else:
            print(f"[promote] Model Registry MLflow indisponible ({type(exc).__name__}) "
                  f"— sans consequence, le registre du depot fait foi "
                  f"(entree v{entree['version'] if entree else '?'}).")
        return None


def run(args: argparse.Namespace) -> int:
    params = charger_params()
    registre = ModelRegistry(root=params.get("registry", {}).get("dir", "models/registry"),
                             served_path=SERVED_PATH)
    threshold = params["ml"]["confidence_threshold"]

    if args.list:
        prod = registre.resolve_alias("production")
        # Deux colonnes de F1-macro, parce qu'il y a deux portees et qu'une seule
        # tranche. « decision » est celle que comparent les portes ; « ref-8 »
        # est la moyenne sur le referentiel entier, suivie d'un « ? » quand
        # l'entree precede la correction du 2026-10-09 et que sa portee est donc
        # inconnue — une telle valeur ne se compare a aucune autre.
        print(f"{'ver':>4}  {'tag':<12} {'decision':>9} {'ref-8':>10} "
              f"{'accuracy':>9}  dataset       cree")
        for v in registre.list_versions():
            marque = " <- production" if v["version"] == prod else ""
            ref8 = v.get("primary_metric")
            ref8_txt = "n/a" if ref8 is None else (
                "%.4f%s" % (ref8, "" if v.get("primary_metric_portee") else "?"))
            decision = v.get("metrique_de_decision")
            decision_txt = "n/a" if decision is None else "%.4f" % decision
            print(f"v{v['version']:<3}  {v['tag']:<12} "
                  f"{decision_txt:>9} {ref8_txt:>10} {(v.get('accuracy') or 0):>9.4f}  "
                  f"{str(v.get('dataset_version'))[:12]:<12}  {v['created_at'][:19]}{marque}")
        return 0

    if args.rollback is not None:
        try:
            registre.rollback(args.rollback, reason=args.reason or "rollback manuel")
        except RegistryError as exc:
            print(f"[promote] {exc}")
            return 1
        print(f"[promote] Production ramenee a v{args.rollback}. "
              f"Rechargez l'API : POST /api/v1/admin/model/reload")
        return 0

    registre.bootstrap_from_existing()

    # Rien a arbitrer : soit l'artefact candidat manque, soit le registre n'a plus de
    # version en attente parce qu'une execution precedente a deja tranche.
    #
    # Ce cas DOIT rester idempotent et sortir en succes. models/best_pipeline.pkl est
    # une sortie de ce stage DVC, or DVC supprime les sorties d'un stage avant de
    # l'executer : sortir en erreur ici laisserait l'artefact servi absent et l'API
    # incapable de demarrer, alors meme que le registre en detient une copie intacte.
    manque_artefact = not os.path.exists(CANDIDATE_PATH)
    candidats = [v for v in registre.list_versions() if v["tag"] == "candidate"]
    if manque_artefact or not candidats:
        motif = (f"artefact candidat absent ({CANDIDATE_PATH})" if manque_artefact
                 else "aucune version en attente dans le registre")
        production = registre.get_production()
        if production is None:
            print(f"[promote] {motif.capitalize()}, et aucun modele en production.")
            print("[promote] Lancez d'abord : python src/pipeline/train.py")
            return 1
        print(f"[promote] Rien a arbitrer — {motif}.")
        _restaurer_production(registre, production["version"])
        # Lecture de RAPPORT : on rafraichit les metriques publiees du modele en
        # service, aucun choix n'en depend. Elle n'entame pas le budget, mais
        # elle est inscrite : le journal doit dire tout ce qui a touche au jeu.
        jeu_gele.inscrire(
            jeu_gele.POUR_RAPPORTER,
            motif="rafraichissement des metriques du modele en service, sans arbitrage",
            lecteur="src/pipeline/promote.py",
            version_concernee=production["version"],
        )
        metriques_prod, _ = evaluer_artefact(
            os.path.join(registre.version_dir(production["version"]), "pipeline.pkl"),
            pd.read_csv(TEST_PATH, encoding="utf-8"), threshold,
        )
        _ecrire_metriques_production(metriques_prod)
        if not os.path.exists(DECISION_OUT):
            ecrire_decision({
                "at": datetime.now(timezone.utc).isoformat(),
                "resultat": "sans objet",
                "version_production_precedente": production["version"],
                "motif": f"Aucun arbitrage a rendre : {motif}.",
            })
        print(f"[promote] La production reste v{production['version']}.")
        return 0

    candidat = candidats[0]
    production = registre.get_production()

    # ── Avant de lire le jeu gele ────────────────────────────────────────────
    # Cet arbitrage va s'en servir pour TRANCHER, donc l'eroder. Le budget est
    # verifie d'abord, et la lecture inscrite au journal ensuite : une sortie en
    # erreur ne doit pas laisser une lecture non comptee, ni l'inverse.
    budget = params.get("jeu_gele", {}).get("lectures_de_decision_max")
    etat_jeu = jeu_gele.etat()
    print(f"[promote] Jeu gele : {etat_jeu['lectures_de_decision']} lecture(s) de decision "
          f"deja inscrites" + (f", budget {budget}" if budget else ", pas de budget declare"))
    try:
        jeu_gele.verifier_budget(budget)
    except jeu_gele.BudgetEpuise as exc:
        if not args.force:
            print("[promote] REFUS\n%s" % exc)
            ecrire_decision({
                "at": datetime.now(timezone.utc).isoformat(),
                "resultat": "refuse",
                "version_candidate": candidat["version"],
                "motif": "Budget de lecture du jeu de test gele epuise ; "
                         "aucun arbitrage rendu.",
                "jeu_gele": etat_jeu,
            })
            return 2
        print("[promote] Budget depasse, poursuite forcee (--force) : la lecture est "
              "inscrite au journal comme telle.")

    test_df = pd.read_csv(TEST_PATH, encoding="utf-8")
    jeu_gele.inscrire(
        jeu_gele.POUR_DECIDER,
        motif="arbitrage de promotion du candidat v%s" % candidat["version"],
        lecteur="src/pipeline/promote.py",
        version_concernee=candidat["version"],
        hors_budget=bool(args.force and budget
                         and etat_jeu["lectures_de_decision"] >= int(budget)) or None,
    )
    print(f"[promote] Jeu de test gele : {TEST_PATH} ({len(test_df)} lignes, "
          f"{test_df['Catégorie'].nunique()} categories)")

    metriques_candidat, confusion = evaluer_artefact(CANDIDATE_PATH, test_df, threshold)
    print(f"[promote] Candidat v{candidat['version']} : "
          f"{metrique_effective(params)} = "
          f"{metriques_candidat[metrique_effective(params)]:.4f}")

    horodatage = datetime.now(timezone.utc).isoformat()

    if production is None:
        decision = {
            "at": horodatage,
            "resultat": "promu",
            "version_candidate": candidat["version"],
            "version_production_precedente": None,
            "motif": "Aucun modele en production : premiere version, aucune comparaison possible.",
            "metriques_candidat": metriques_candidat,
            "metriques_production": None,
            "comparaison": None,
        }
        if not args.dry_run:
            registre.promote(candidat["version"], reason=decision["motif"], decision=decision)
            _ecrire_metriques_production(metriques_candidat)
            enregistrer_mlflow(candidat["version"], registre, params)
        ecrire_decision(decision)
        print(f"[promote] PROMU — v{candidat['version']} (premiere version)")
        return 0

    artefact_prod = os.path.join(registre.version_dir(production["version"]), "pipeline.pkl")
    metriques_prod, _ = evaluer_artefact(artefact_prod, test_df, threshold)
    print(f"[promote] Production v{production['version']} : "
          f"{metrique_effective(params)} = "
          f"{metriques_prod[metrique_effective(params)]:.4f}")

    comparaison = comparer(metriques_candidat, metriques_prod, confusion, params)

    print("[promote] Portes :")
    for porte in comparaison["portes"]:
        print(f"[promote]   [{'OK ' if porte['passe'] else 'NON'}] {porte['porte']}")
        print(f"[promote]        {porte['detail']}")

    accepte = comparaison["accepte"] or args.force
    motif = (
        "Promotion forcee manuellement (--force)." if (args.force and not comparaison["accepte"])
        else ("Toutes les portes de promotion sont passees." if comparaison["accepte"]
              else f"Portes en echec : {', '.join(comparaison['portes_en_echec'])}.")
    )

    decision = {
        "at": horodatage,
        "resultat": "promu" if accepte else "rejete",
        "version_candidate": candidat["version"],
        "version_production_precedente": production["version"],
        "motif": motif,
        "force": bool(args.force),
        "metriques_candidat": metriques_candidat,
        "metriques_production": metriques_prod,
        "comparaison": comparaison,
        "test_reference": TEST_PATH,
        "n_test": int(len(test_df)),
        # Combien de fois le jeu gele a servi a trancher, celle-ci comprise.
        # Un lecteur de ce fichier doit pouvoir juger si le chiffre qui le
        # precede mesure encore la generalisation.
        "jeu_gele": jeu_gele.etat(),
        "jeu_gele_budget": budget,
    }

    if args.dry_run:
        print(f"[promote] DRY-RUN — decision qui aurait ete prise : {decision['resultat']}")
        ecrire_decision(decision)
        return 0

    if accepte:
        registre.promote(candidat["version"], reason=motif, decision=decision)
        _ecrire_metriques_production(metriques_candidat)
        enregistrer_mlflow(candidat["version"], registre, params)
        print(f"[promote] PROMU — v{production['version']} -> v{candidat['version']}")
        print("[promote] Rechargez l'API : POST /api/v1/admin/model/reload")
    else:
        registre.reject(candidat["version"], reason=motif, decision=decision)
        _restaurer_production(registre, production["version"])
        _ecrire_metriques_production(metriques_prod)
        print(f"[promote] REJETE — la production reste v{production['version']}")
        print(f"[promote] {motif}")

    ecrire_decision(decision)
    return 0


def _restaurer_production(registre: ModelRegistry, version: int) -> None:
    """
    Remet en place l'artefact servi apres un rejet.

    DVC supprime les sorties d'un stage avant de l'executer. models/best_pipeline.pkl
    etant une sortie de ce stage, un rejet le laisserait absent et l'API ne
    demarrerait plus. On le restaure donc depuis le registre, a l'identique.
    """
    import shutil
    source = os.path.join(registre.version_dir(version), "pipeline.pkl")
    if not os.path.exists(source):
        raise RegistryError(f"Artefact de production introuvable pour v{version} : {source}")
    shutil.copy2(source, SERVED_PATH)
    meta_src = os.path.join(registre.version_dir(version), "model_metadata.json")
    if os.path.exists(meta_src):
        shutil.copy2(meta_src, "models/model_metadata.json")
    print(f"[promote] Artefact de production v{version} restaure ({SERVED_PATH}).")


def _ecrire_metriques_production(metriques: dict) -> None:
    """metrics/ml_eval.json decrit toujours le modele EN SERVICE, jamais un candidat."""
    os.makedirs(os.path.dirname(METRICS_PROD), exist_ok=True)
    with open(METRICS_PROD, "w", encoding="utf-8") as f:
        json.dump(metriques, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true", help="evalue et trace sans rien promouvoir")
    p.add_argument("--force", action="store_true", help="promeut malgre un echec, trace comme force")
    p.add_argument("--rollback", type=int, metavar="N", help="revenir a la version N")
    p.add_argument("--reason", help="motif consigne dans l'historique du registre")
    p.add_argument("--list", action="store_true", help="liste les versions du registre")
    sys.exit(run(p.parse_args()))
