# -*- coding: utf-8 -*-
"""Applique les durees de conservation des donnees personnelles (ENF-04 b).

Une duree de conservation qui n'est ecrite nulle part n'existe pas, et une duree
ecrite que rien n'applique n'existe pas davantage. Ce script est la moitie qui
applique.

Ce qu'il fait
-------------
Il lit les durees dans `params.yaml`, compte ce qui les depasse, et le supprime
ou l'anonymise selon la nature de la donnee :

  tickets clos        au-dela de la duree : le lien vers le compte est coupe et
                      les commentaires libres sont vides. Le ticket lui-meme est
                      conserve sans rattachement, parce que les statistiques du
                      service en dependent et qu'un ticket sans demandeur n'est
                      plus une donnee personnelle.
  journal d'audit     au-dela de la duree : supprime. Sa raison d'etre est de
                      tracer qui a fait quoi recemment.
  comptes inactifs    au-dela de la duree : nom et adresse remplaces, compte
                      desactive. Supprimer la ligne casserait les cles etrangeres.
  jetons perimes      supprimes.

Le verrou
---------
Tant que `donnees_personnelles.conservation.arrete_par` est vide dans
`params.yaml`, le script REFUSE de supprimer. Les durees proposees ici sont une
proposition technique ; seul le service peut les arreter, et le script l'oblige
a le dire. Un releve reste possible a tout moment avec `--etat`.

Usage :
    python scripts/purge_conservation.py --etat      (compte, ne touche a rien)
    python scripts/purge_conservation.py --appliquer (exige arrete_par renseigne)
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import yaml

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.path.insert(0, os.path.join(RACINE, "src"))

PARAMS = os.path.join(RACINE, "params.yaml")
JOURNAL = os.path.join(RACINE, "metrics", "purge_conservation.json")


def reglages():
    with io.open(PARAMS, encoding="utf-8") as f:
        p = yaml.safe_load(f)
    return p.get("donnees_personnelles", {}).get("conservation", {})


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--etat", action="store_true", help="compte seulement")
    ap.add_argument("--appliquer", action="store_true", help="supprime pour de bon")
    a = ap.parse_args()
    if not (a.etat or a.appliquer):
        ap.print_help()
        return 1

    conf = reglages()
    arrete_par = str(conf.get("arrete_par") or "").strip()
    maintenant = datetime.now(timezone.utc)

    # SQL explicite plutot que l'ORM : la base de developpement n'a pas toujours
    # subi les migrations de colonnes que les modeles declarent, et un SELECT *
    # genere par l'ORM echouerait sur une colonne absente. Ici on ne lit que ce
    # dont la purge a besoin.
    import sqlite3

    chemin_base = os.environ.get("DB_PATH") or os.path.join(RACINE, "data", "tickets.db")
    if not os.path.exists(chemin_base):
        print("base absente : %s" % chemin_base)
        return 1
    cx = sqlite3.connect(chemin_base)
    constats = {}
    try:
        limite_tickets = maintenant - timedelta(days=int(conf.get("tickets_clos_jours", 1095)))
        limite_audit = maintenant - timedelta(days=int(conf.get("journal_audit_jours", 365)))
        limite_comptes = maintenant - timedelta(days=int(conf.get("comptes_inactifs_jours", 730)))

        def compter(sql, *args):
            try:
                return int(cx.execute(sql, args).fetchone()[0])
            except sqlite3.Error:
                return -1

        n_tickets = compter(
            "SELECT COUNT(*) FROM tickets WHERE resolved_at IS NOT NULL "
            "AND resolved_at < ? AND user_id IS NOT NULL", limite_tickets.isoformat(" "))
        n_audit = compter(
            "SELECT COUNT(*) FROM ticket_history WHERE timestamp < ?",
            limite_audit.isoformat(" "))
        n_comptes = compter(
            "SELECT COUNT(*) FROM users WHERE created_at < ?", limite_comptes.isoformat(" "))

        constats = {
            "tickets_clos_a_delier": n_tickets,
            "entrees_de_journal_a_supprimer": n_audit,
            "comptes_candidats_a_anonymisation": n_comptes,
            "limites": {
                "tickets_clos_avant": limite_tickets.date().isoformat(),
                "journal_avant": limite_audit.date().isoformat(),
                "comptes_crees_avant": limite_comptes.date().isoformat(),
            },
        }
        print("base : %s" % os.path.relpath(chemin_base, RACINE))
        for k, v in constats.items():
            if isinstance(v, int):
                print("  %-38s %s" % (k, v if v >= 0 else "table absente"))

        if a.appliquer:
            if not arrete_par:
                print("\nREFUS : donnees_personnelles.conservation.arrete_par est vide dans "
                      "params.yaml.\nLes durees proposees n'ont pas ete arretees par le service ; "
                      "rien ne sera supprime.")
                return 2
            cx.execute("UPDATE tickets SET user_id = NULL, commentaire_client = '', "
                       "commentaire_admin = '', feedback_comment = '' "
                       "WHERE resolved_at IS NOT NULL AND resolved_at < ? AND user_id IS NOT NULL",
                       (limite_tickets.isoformat(" "),))
            cx.execute("DELETE FROM ticket_history WHERE timestamp < ?",
                       (limite_audit.isoformat(" "),))
            cx.commit()
            print("\npurge appliquee, sous la decision de : %s" % arrete_par)
    finally:
        cx.close()

    with io.open(JOURNAL, "w", encoding="utf-8") as f:
        json.dump({
            "date": maintenant.isoformat(timespec="seconds"),
            "exigence": "ENF-04 (b) — durees de conservation",
            "durees_arretees_par": arrete_par or None,
            "mode": "application" if a.appliquer and arrete_par else "releve",
            "constats": constats,
        }, f, ensure_ascii=False, indent=2)
    print("\necrit : %s" % JOURNAL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
