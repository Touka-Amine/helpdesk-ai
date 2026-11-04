"""
Monitoring du modele de classification, et evaluation des declencheurs de reentrainement.

Ce script LIT et RAPPORTE. Il ne lance aucun entrainement et ne promeut rien. Il
ecrit metrics/should_retrain.json ; la decision de lancer `dvc repro` reste humaine.
C'est ce qui separe un pipeline controle d'un reentrainement automatique aveugle.

CE QUI EST MESURABLE AVEC LES DONNEES EXISTANTES
    taux de desaccord ML/humain   categorie_predite != categorie_finale sur les
                                  tickets valides. Meilleur indicateur disponible
                                  de la performance reelle en production, puisque
                                  la vraie etiquette est celle que l'admin retient.
    distribution des categories   comparee a celle du corpus d'entrainement (PSI).
    distribution des confiances   une baisse de la confiance moyenne precede
                                  generalement une baisse de performance.
    taux d'heuristiques           part des predictions ecrasees par une regle metier.
    derive lexicale               part des mots des nouvelles descriptions absents
                                  du vocabulaire TF-IDF du modele. Mesure directe :
                                  ces mots sont invisibles pour le modele.
    performance par version       jointure sur model_version.

CE QUI N'EST PAS MESURABLE, ET NE DOIT PAS ETRE INVENTE
    - La F1 reelle en production. Sur les tickets ou l'admin n'a pas touche a la
      categorie, l'etiquette est une confirmation par omission, pas une verite.
      Le taux de desaccord en est un minorant, pas un equivalent.
    - La derive semantique des descriptions au-dela du vocabulaire. Il faudrait
      encoder et comparer des distributions d'embeddings, ce que le pipeline
      actuel ne conserve pas.
    - Le taux d'heuristiques sur les tickets anterieurs a cette version : la
      colonne heuristic_applied n'existait pas, elle vaut NULL.

Usage :
    python src/monitoring/ml_monitor.py
    python src/monitoring/ml_monitor.py --db-url sqlite:///data/tickets.db
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
import yaml

_RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _RACINE)
sys.path.insert(0, os.path.join(_RACINE, "src"))

PARAMS_PATH = "params.yaml"
TRAIN_PATH = "data/splits/train_current.csv"
TRAIN_FALLBACK = "data/splits/train.csv"
MODEL_PATH = "models/best_pipeline.pkl"
OUT_MONITOR = "metrics/ml_monitor.json"
OUT_TRIGGER = "metrics/should_retrain.json"

NON_MESURABLE = [
    "F1 reelle en production : les etiquettes non contestees par un admin sont des "
    "confirmations par omission, pas une verite terrain.",
    "Derive semantique au-dela du vocabulaire : les embeddings des tickets de "
    "production ne sont pas conserves.",
    "Taux d'heuristiques avant l'introduction de la colonne heuristic_applied.",
]


def psi(reference: pd.Series, courant: pd.Series, epsilon: float = 1e-6) -> float:
    """
    Population Stability Index entre deux distributions de categories.

    Lecture usuelle : < 0.10 stable, 0.10-0.25 derive moderee, > 0.25 derive nette.
    Sur de petits effectifs de production, l'indice est bruite : il est reporte avec
    la taille de l'echantillon pour que le lecteur en tienne compte.
    """
    categories = sorted(set(reference.index) | set(courant.index))
    total_ref, total_cur = reference.sum(), courant.sum()
    if total_ref == 0 or total_cur == 0:
        return 0.0
    valeur = 0.0
    for cat in categories:
        p_ref = max(float(reference.get(cat, 0)) / total_ref, epsilon)
        p_cur = max(float(courant.get(cat, 0)) / total_cur, epsilon)
        valeur += (p_cur - p_ref) * math.log(p_cur / p_ref)
    return round(valeur, 4)


def taux_hors_vocabulaire(descriptions: list[str]) -> float | None:
    """
    Part des mots des descriptions de production absents du vocabulaire TF-IDF.

    Un mot hors vocabulaire est litteralement invisible pour le modele : il ne
    contribue a aucune dimension. C'est une mesure de derive directe et honnete,
    contrairement a une distance sur des distributions que le systeme ne stocke pas.
    """
    if not descriptions or not os.path.exists(MODEL_PATH):
        return None
    try:
        import joblib
        from data.preprocess import clean_text

        pipeline = joblib.load(MODEL_PATH)
        vocabulaire = set(pipeline.named_steps["tfidf"].vocabulary_.keys())
        total, hors = 0, 0
        for desc in descriptions:
            for mot in clean_text(desc).split():
                total += 1
                if mot not in vocabulaire:
                    hors += 1
        return round(hors / total, 4) if total else None
    except Exception as exc:
        print(f"[ml_monitor] Vocabulaire illisible ({type(exc).__name__}: {exc})")
        return None


def lire_tickets(db_url: str) -> pd.DataFrame:
    from sqlalchemy import create_engine

    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    engine = create_engine(db_url, connect_args=connect_args)
    with engine.connect() as conn:
        return pd.read_sql("SELECT * FROM tickets", conn)


def run(args: argparse.Namespace) -> int:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        params = yaml.safe_load(f)
    cfg_retrain = params.get("retrain", {})
    cfg_monitor = params.get("monitoring", {})
    fenetre = int(cfg_monitor.get("window_days", 30))

    db_url = args.db_url or os.environ.get("DB_URL")
    if not db_url:
        try:
            from api.config import settings
            db_url = settings.DB_URL
        except Exception:
            db_url = "sqlite:///data/tickets.db"

    try:
        tickets = lire_tickets(db_url)
    except Exception as exc:
        print(f"[ml_monitor] Base injoignable : {type(exc).__name__}: {exc}")
        if not args.allow_offline:
            return 1
        tickets = pd.DataFrame()

    maintenant = datetime.now(timezone.utc)
    rapport: dict = {
        "generated_at": maintenant.isoformat(),
        "fenetre_jours": fenetre,
        "n_tickets_total": int(len(tickets)),
        "non_mesurable": NON_MESURABLE,
    }

    if tickets.empty:
        rapport["etat"] = "aucune donnee de production"
        rapport["note"] = (
            "Aucun ticket en base. Les indicateurs de production ne peuvent pas etre "
            "calcules. Comportement attendu tant que l'application n'a pas de trafic."
        )
        _ecrire(rapport, {"should_retrain": False,
                          "motif": "aucune donnee de production",
                          "declencheurs": []})
        print("[ml_monitor] Aucun ticket — rapport vide ecrit.")
        return 0

    # ── Desaccord ML / humain ────────────────────────────────────────────────
    valides = tickets[
        tickets["statut"].astype(str).eq("Résolu")
        & tickets["categorie_finale"].notna()
        & tickets["categorie_predite"].notna()
    ].copy()

    if not valides.empty:
        desaccord = (
            valides["categorie_predite"].astype(str).str.strip()
            != valides["categorie_finale"].astype(str).str.strip()
        )
        taux_desaccord = round(float(desaccord.mean()) * 100, 2)
        par_categorie = (
            valides.assign(_d=desaccord)
            .groupby(valides["categorie_finale"].astype(str))["_d"]
            .agg(["sum", "count"])
        )
        rapport["desaccord"] = {
            "n_tickets_valides": int(len(valides)),
            "taux_pct": taux_desaccord,
            "par_categorie_finale": {
                str(cat): {"desaccords": int(enr["sum"]), "total": int(enr["count"]),
                           "taux_pct": round(100 * enr["sum"] / enr["count"], 2)}
                for cat, enr in par_categorie.iterrows()
            },
            "interpretation": (
                "Minorant de l'erreur reelle : ne compte que les corrections "
                "explicites d'un administrateur."
            ),
        }
    else:
        taux_desaccord = None
        rapport["desaccord"] = {"n_tickets_valides": 0,
                                "note": "aucun ticket resolu avec categorie predite"}

    # ── Distributions ────────────────────────────────────────────────────────
    dist_prod = tickets["categorie_finale"].astype(str).value_counts()
    rapport["distribution_categories_production"] = {
        str(k): int(v) for k, v in dist_prod.items()
    }

    chemin_train = TRAIN_PATH if os.path.exists(TRAIN_PATH) else TRAIN_FALLBACK
    if os.path.exists(chemin_train):
        dist_train = pd.read_csv(chemin_train, encoding="utf-8")["Catégorie"].value_counts()
        rapport["derive_distribution"] = {
            "psi": psi(dist_train, dist_prod),
            "reference": chemin_train,
            "n_production": int(dist_prod.sum()),
            "lecture": "<0.10 stable | 0.10-0.25 moderee | >0.25 nette",
            "avertissement": (
                "Indice bruite en dessous de quelques centaines de tickets de production."
                if dist_prod.sum() < 200 else None
            ),
        }

    if "confiance" in tickets.columns:
        confiances = pd.to_numeric(tickets["confiance"], errors="coerce").dropna()
        if not confiances.empty:
            rapport["confiance"] = {
                "moyenne": round(float(confiances.mean()), 4),
                "mediane": round(float(confiances.median()), 4),
                "p10": round(float(confiances.quantile(0.10)), 4),
                "part_sous_seuil": round(
                    float((confiances < params["ml"]["confidence_threshold"]).mean()), 4
                ),
                "seuil": params["ml"]["confidence_threshold"],
            }

    if "heuristic_applied" in tickets.columns:
        renseignes = tickets[tickets["heuristic_applied"].notna()]
        rapport["heuristiques"] = {
            "n_tickets_instrumentes": int(len(renseignes)),
            "taux_application": (
                round(float(renseignes["heuristic_applied"].astype(bool).mean()), 4)
                if not renseignes.empty else None
            ),
            "regles_les_plus_frequentes": (
                {str(k): int(v) for k, v in
                 renseignes["heuristic_rule"].dropna().value_counts().head(10).items()}
                if "heuristic_rule" in renseignes.columns and not renseignes.empty else {}
            ),
            "note": ("Les tickets anterieurs a l'instrumentation ont heuristic_applied "
                     "a NULL et sont exclus."),
        }

    if "model_version" in tickets.columns:
        par_version = tickets[tickets["model_version"].notna() & tickets["model_version"].ne("")]
        if not par_version.empty:
            lignes = {}
            for version, bloc in par_version.groupby("model_version"):
                resolus = bloc[bloc["statut"].astype(str).eq("Résolu")]
                d = (
                    (resolus["categorie_predite"].astype(str).str.strip()
                     != resolus["categorie_finale"].astype(str).str.strip()).mean()
                    if not resolus.empty else None
                )
                lignes[str(version)] = {
                    "n_tickets": int(len(bloc)),
                    "n_resolus": int(len(resolus)),
                    "taux_desaccord_pct": round(float(d) * 100, 2) if d is not None else None,
                }
            rapport["par_version_modele"] = lignes

    descriptions = tickets["description"].dropna().astype(str).tolist()
    rapport["derive_lexicale"] = {
        "taux_hors_vocabulaire": taux_hors_vocabulaire(descriptions),
        "n_descriptions": len(descriptions),
        "lecture": "part des mots de production absents du vocabulaire TF-IDF du modele servi",
    }

    # ── Declencheurs de reentrainement ───────────────────────────────────────
    declencheurs = []
    n_nouveaux = int(len(valides)) if not valides.empty else 0
    seuil_nouveaux = int(cfg_retrain.get("min_new_tickets", 150))
    declencheurs.append({
        "nom": "volume_nouveaux_tickets",
        "valeur": n_nouveaux,
        "seuil": seuil_nouveaux,
        "declenche": n_nouveaux >= seuil_nouveaux,
        "justification": (
            "En dessous, reparti sur huit classes, l'apport par classe reste sous le "
            "bruit d'echantillonnage du jeu de test."
        ),
    })

    minoritaires = cfg_retrain.get("minority_categories", [])
    seuil_min = int(cfg_retrain.get("min_new_per_minority", 30))
    for categorie in minoritaires:
        n = int((valides["categorie_finale"].astype(str) == categorie).sum()) if not valides.empty else 0
        declencheurs.append({
            "nom": f"volume_minoritaire_{categorie}",
            "valeur": n,
            "seuil": seuil_min,
            "declenche": n >= seuil_min,
            "justification": "Une classe faible progresse proportionnellement plus vite.",
        })

    reference = cfg_monitor.get("disagreement_baseline")
    hausse = float(cfg_retrain.get("disagreement_increase_pts", 10.0))
    if reference is None:
        declencheurs.append({
            "nom": "hausse_desaccord",
            "valeur": taux_desaccord,
            "seuil": None,
            "declenche": False,
            "justification": (
                "Aucun referentiel etabli (monitoring.disagreement_baseline vaut null). "
                "Conclure a une derive sans point de comparaison serait une invention. "
                "Fixez ce referentiel apres une premiere periode d'exploitation."
            ),
        })
    else:
        depasse = taux_desaccord is not None and taux_desaccord >= float(reference) + hausse
        declencheurs.append({
            "nom": "hausse_desaccord",
            "valeur": taux_desaccord,
            "seuil": round(float(reference) + hausse, 2),
            "declenche": bool(depasse),
            "justification": "Degradation mesuree face au referentiel etabli.",
        })

    verrou = _verrou_temporel(cfg_retrain, maintenant)
    actifs = [d["nom"] for d in declencheurs if d["declenche"]]
    should = bool(actifs) and not verrou["bloque"]

    trigger = {
        "generated_at": maintenant.isoformat(),
        "should_retrain": should,
        "motif": (
            f"Declencheurs actifs : {', '.join(actifs)}." if should
            else (verrou["motif"] if verrou["bloque"]
                  else "Aucun declencheur actif — le modele en production reste en service.")
        ),
        "declencheurs": declencheurs,
        "verrou_temporel": verrou,
        "commande": "python src/pipeline/collect.py && dvc repro" if should else None,
    }

    _ecrire(rapport, trigger)
    print(f"[ml_monitor] {len(tickets)} tickets | desaccord {taux_desaccord}% | "
          f"reentrainement conseille : {should}")
    for d in declencheurs:
        etat = "OUI" if d["declenche"] else "non"
        print(f"[ml_monitor]   [{etat}] {d['nom']} = {d['valeur']} (seuil {d['seuil']})")
    return 0


def _verrou_temporel(cfg: dict, maintenant: datetime) -> dict:
    """
    Empeche deux reentrainements rapproches, meme si les seuils sont mal calibres.

    La date de reference vient de l'historique du REGISTRE, pas de
    metrics/promotion_decision.json. Ce dernier est une sortie de stage DVC : il est
    supprime avant chaque execution de promote, et une execution sans candidat y
    ecrit une entree « sans objet » qui redemarrerait le compteur sans qu'aucun
    arbitrage n'ait eu lieu. L'historique du registre, lui, n'est la sortie d'aucun
    stage et ne conserve que les decisions reellement rendues.
    """
    jours = int(cfg.get("min_days_between_retrains", 7))
    vide = {"bloque": False, "motif": None, "derniere_promotion": None,
            "min_days_between_retrains": jours}
    try:
        with open("models/registry/registry.json", encoding="utf-8") as f:
            historique = json.load(f).get("history", [])
    except (OSError, json.JSONDecodeError):
        return vide

    arbitrages = [h for h in historique
                  if h.get("action") in ("promote", "reject", "rollback")]
    if not arbitrages:
        return vide
    try:
        derniere = datetime.fromisoformat(arbitrages[-1]["at"])
    except (KeyError, ValueError):
        return vide
    if derniere.tzinfo is None:
        derniere = derniere.replace(tzinfo=timezone.utc)
    ecart = maintenant - derniere
    bloque = ecart < timedelta(days=jours)
    return {
        "bloque": bloque,
        "motif": (f"Derniere decision de promotion il y a {ecart.days} jour(s), "
                  f"minimum {jours}." if bloque else None),
        "derniere_promotion": derniere.isoformat(),
        "min_days_between_retrains": jours,
    }


def _ecrire(rapport: dict, trigger: dict) -> None:
    os.makedirs("metrics", exist_ok=True)
    with open(OUT_MONITOR, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)
    with open(OUT_TRIGGER, "w", encoding="utf-8") as f:
        json.dump(trigger, f, ensure_ascii=False, indent=2)
    print(f"[ml_monitor] ecrit {OUT_MONITOR} et {OUT_TRIGGER}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db-url", help="surcharge de l'URL de base")
    p.add_argument("--allow-offline", action="store_true",
                   help="ecrit un rapport vide si la base est injoignable")
    sys.exit(run(p.parse_args()))
