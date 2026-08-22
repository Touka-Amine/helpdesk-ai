"""
Demonstration de bout en bout du cycle MLOps.

Prouve que la boucle production -> donnees validees -> nouvelle version ->
evaluation -> promotion ou rejet fonctionne reellement, sans attendre que
l'application ait du trafic.

CE QUE LA DEMONSTRATION FAIT
    1. Cree une base SQLite temporaire au schema de production.
    2. Y insere des tickets resolus, avec un historique realiste : corrections
       explicites d'un admin, confirmations tacites, resolutions sans admin.
    3. Lance collect.py sur cette base et verifie la qualification des etiquettes.
    4. Lance build_dataset.py et verifie les garde-fous anti-fuite.
    5. Lance train.py puis promote.py, et affiche la decision.
    6. Restaure l'etat initial du depot.

CE QU'ELLE NE FAIT PAS
    Elle n'invente pas de resultat. Si le candidat entraine sur ces quelques
    tickets synthetiques n'ameliore pas la production, il est rejete, et c'est le
    comportement attendu : la porte fait son travail.

Usage :
    python scripts/mlops_e2e_demo.py
    python scripts/mlops_e2e_demo.py --keep     # ne restaure pas l'etat initial
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)

CURATED_DIR = "data/curated"
TRAIN_CURRENT = "data/splits/train_current.csv"
SERVED = "models/best_pipeline.pkl"

# Scenarios de production. Chacun porte un titre libre, comme un client l'ecrirait,
# et une resolution redigee par un administrateur.
SCENARIOS = [
    ("Le VPN refuse ma connexion depuis ce matin",
     "Depuis 8h je n'arrive plus a ouvrir le tunnel VPN, le client me renvoie une "
     "erreur d'authentification alors que mon mot de passe est correct.",
     "Réseau", "Sécurité",
     "Certificat machine expire. Renouvele via la console PKI puis service client "
     "redemarre, la connexion est retablie.", "corrected"),
    ("Outlook reste bloque sur le chargement du profil",
     "Outlook affiche le message de chargement du profil pendant plusieurs minutes "
     "puis se ferme tout seul, impossible de consulter la messagerie.",
     "Microsoft", "Microsoft",
     "Profil Outlook corrompu. Recree depuis le panneau de configuration, les "
     "donnees ont ete resynchronisees depuis le serveur.", "confirmed"),
    ("Impossible d'imprimer sur l'imprimante du deuxieme etage",
     "Les documents partent dans la file d'attente mais rien ne sort, la file se "
     "remplit et bloque tous les postes du plateau.",
     "Système", "Système",
     "Spouleur d'impression bloque. Service arrete, file purgee manuellement, "
     "service relance et impression testee.", "confirmed"),
    ("Alerte antivirus sur mon poste ce matin",
     "L'antivirus a affiche une alerte au demarrage sur un fichier telecharge hier "
     "depuis une piece jointe, je n'ai rien ouvert depuis.",
     "Système", "Sécurité",
     "Fichier mis en quarantaine et analyse. Faux positif confirme par l'editeur, "
     "exclusion ajoutee et poste rescanne sans detection.", "corrected"),
    ("La sauvegarde du serveur de fichiers a echoue cette nuit",
     "Le rapport de sauvegarde indique un echec sur le volume partage, aucune "
     "sauvegarde complete n'a ete produite depuis deux jours.",
     "Infrastructure", "Backup",
     "Espace disque insuffisant sur la cible. Anciens points de restauration "
     "purges selon la politique de retention, sauvegarde relancee avec succes.",
     "corrected"),
    ("Connexion Teams impossible en visioconference",
     "Teams se connecte mais la visio coupe au bout de quelques secondes, le chat "
     "fonctionne normalement.",
     "Microsoft", "Communication",
     "Ports UDP bloques par la nouvelle regle de filtrage. Exception ajoutee sur "
     "le pare-feu du site, visio testee et stable.", "corrected"),
    ("Le partage reseau du service comptabilite est inaccessible",
     "Le lecteur reseau n'apparait plus dans l'explorateur depuis le redemarrage "
     "de ce matin, plusieurs collegues ont le meme souci.",
     "Réseau", "Infrastructure",
     "Service de partage arrete apres la mise a jour du serveur. Service relance "
     "et demarrage automatique reconfigure.", "corrected"),
    ("Mon poste est tres lent depuis la mise a jour",
     "Depuis la mise a jour de la semaine derniere le poste met plusieurs minutes "
     "a demarrer et les applications repondent mal.",
     "Système", "Système",
     "Pilote graphique incompatible avec la version installee. Retour a la version "
     "precedente du pilote, performances revenues a la normale.", "confirmed"),
    ("Erreur de licence au lancement de l'ERP",
     "Sage refuse de s'ouvrir et affiche un message d'erreur de licence expiree "
     "alors que le renouvellement a ete fait.",
     "Microsoft", "Applicatifs",
     "Cle de licence non propagee sur le poste. Cache licence vide et cle "
     "reappliquee depuis le serveur d'activation.", "corrected"),
    ("Acces refuse au dossier des ressources humaines",
     "J'obtiens un message d'acces refuse sur le dossier partage RH alors que "
     "j'avais les droits la semaine derniere.",
     "Réseau", "Sécurité",
     "Groupe de securite retire lors du menage des habilitations. Utilisateur "
     "reintegre au groupe apres validation du responsable RH.", "corrected"),
]

SCHEMA = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY, email TEXT, nom TEXT, prenom TEXT,
    hashed_password TEXT, role TEXT, filiale TEXT, is_active BOOLEAN,
    first_login BOOLEAN, created_at TEXT
);
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY, user_id INTEGER, approved_by TEXT, titre TEXT,
    description TEXT, priorite_saisie TEXT, priorite_finale TEXT,
    classification_finale TEXT, assigne_a TEXT, filiale TEXT, equipement TEXT,
    categorie_predite TEXT, categorie_finale TEXT, confiance REAL, statut TEXT,
    solution_rag TEXT, knowledge_rag TEXT, rag_score REAL,
    commentaire_client TEXT, commentaire_admin TEXT, feedback_vote TEXT,
    feedback_comment TEXT, created_at TEXT, resolved_at TEXT,
    model_version TEXT, heuristic_applied BOOLEAN, heuristic_rule TEXT
);
CREATE TABLE ticket_history (
    id INTEGER PRIMARY KEY, ticket_id INTEGER, changed_by INTEGER,
    champ_modifie TEXT, ancienne_valeur TEXT, nouvelle_valeur TEXT, timestamp TEXT
);
"""


def titre(texte: str) -> None:
    print(f"\n{'=' * 78}\n  {texte}\n{'=' * 78}")


def executer(commande: list[str], titre_etape: str) -> tuple[int, str]:
    print(f"\n$ {' '.join(commande)}")
    # La demonstration ne doit rien laisser dans le registre MLflow : ses modeles
    # sont entraines sur des tickets synthetiques et n'ont rien a y faire.
    environnement = dict(os.environ, HELPDESK_SKIP_MLFLOW_REGISTRY="1")
    resultat = subprocess.run(commande, capture_output=True, text=True, env=environnement)
    sortie = (resultat.stdout or "") + (resultat.stderr or "")
    for ligne in sortie.splitlines():
        if ligne.strip() and not ligne.startswith(("  ", "warnings.warn")):
            print(f"    {ligne}")
    if resultat.returncode != 0:
        print(f"    [ECHEC] {titre_etape} — code {resultat.returncode}")
    return resultat.returncode, sortie


def construire_base(chemin: str) -> dict[str, int]:
    """Base SQLite au schema de production, peuplee de tickets realistes."""
    conn = sqlite3.connect(chemin)
    conn.executescript(SCHEMA)
    base_date = datetime.now(timezone.utc) - timedelta(days=40)

    conn.execute(
        "INSERT INTO users (id, email, nom, prenom, role, filiale, is_active) "
        "VALUES (7, 'admin@otbs.local', 'Admin', 'Demo', 'admin', 'OTBS', 1)"
    )
    conn.execute(
        "INSERT INTO users (id, email, nom, prenom, role, filiale, is_active) "
        "VALUES (3, 'client@otbs.local', 'Client', 'Demo', 'client', 'OTBS', 1)"
    )

    repartition = {"corrected": 0, "confirmed": 0, "weak": 0}
    ticket_id = 0
    histo_id = 0

    # Chaque scenario est instancie plusieurs fois, avec des formulations variees,
    # pour atteindre un volume ou l'entrainement a du sens.
    for repetition in range(6):
        for titre_t, description, predite, finale, solution, force in SCENARIOS:
            ticket_id += 1
            cree = base_date + timedelta(days=repetition * 5, hours=ticket_id % 12)
            resolu = cree + timedelta(hours=6)
            suffixe = "" if repetition == 0 else f" (signalement {repetition + 1})"

            conn.execute(
                "INSERT INTO tickets (id, user_id, approved_by, titre, description, "
                "priorite_saisie, priorite_finale, classification_finale, filiale, "
                "categorie_predite, categorie_finale, confiance, statut, solution_rag, "
                "knowledge_rag, rag_score, commentaire_admin, created_at, resolved_at, "
                "model_version, heuristic_applied, heuristic_rule) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (ticket_id, 3, "7", titre_t + suffixe, description,
                 "Modere", "Modere", "Incident", "OTBS",
                 predite, finale, 0.62, "Résolu", "suggestion RAG d'origine", "",
                 0.41, solution, cree.isoformat(), resolu.isoformat(),
                 "v1", 0, None),
            )

            # Journal de creation : changed_by NULL, comme api/routers/tickets.py:79
            histo_id += 1
            conn.execute(
                "INSERT INTO ticket_history (id, ticket_id, changed_by, champ_modifie, "
                "ancienne_valeur, nouvelle_valeur, timestamp) VALUES (?,?,?,?,?,?,?)",
                (histo_id, ticket_id, None, "categorie_finale", None, predite,
                 cree.isoformat()),
            )
            if force != "weak":
                histo_id += 1
                conn.execute(
                    "INSERT INTO ticket_history (id, ticket_id, changed_by, "
                    "champ_modifie, ancienne_valeur, nouvelle_valeur, timestamp) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (histo_id, ticket_id, 7, "statut", "Prise en Charge", "Résolu",
                     resolu.isoformat()),
                )
            if force == "corrected":
                histo_id += 1
                conn.execute(
                    "INSERT INTO ticket_history (id, ticket_id, changed_by, "
                    "champ_modifie, ancienne_valeur, nouvelle_valeur, timestamp) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (histo_id, ticket_id, 7, "categorie_finale", predite, finale,
                     resolu.isoformat()),
                )
            repartition[force] += 1

    conn.commit()
    conn.close()
    return repartition


# Artefacts que la demonstration ecrase et doit rendre a l'identique. Les artefacts
# du candidat en font partie : sans eux, models/candidate_metadata.json resterait
# celui du modele entraine sur les tickets simules, alors qu'il est versionne.
ETAT_SAUVEGARDE = (
    TRAIN_CURRENT,
    TRAIN_CURRENT.replace(".csv", ".manifest.json"),
    SERVED,
    "models/model_metadata.json",
    "models/candidate_pipeline.pkl",
    "models/candidate_metadata.json",
    "metrics/ml_eval.json",
    "metrics/ml_eval_candidate.json",
    "metrics/confusion_matrix_candidate.json",
    "metrics/promotion_decision.json",
)


def sauvegarder_etat(dossier: str) -> None:
    os.makedirs(dossier, exist_ok=True)
    # Trace des artefacts absents avant la demonstration : ils devront le redevenir.
    absents = [c for c in ETAT_SAUVEGARDE if not os.path.exists(c)]
    with open(os.path.join(dossier, "absents.json"), "w", encoding="utf-8") as f:
        json.dump(absents, f)
    for chemin in ETAT_SAUVEGARDE:
        if os.path.exists(chemin):
            shutil.copy2(chemin, os.path.join(dossier, os.path.basename(chemin)))
    if os.path.exists("models/registry"):
        shutil.copytree("models/registry", os.path.join(dossier, "registry"),
                        dirs_exist_ok=True)
    if os.path.exists(CURATED_DIR):
        shutil.copytree(CURATED_DIR, os.path.join(dossier, "curated"),
                        dirs_exist_ok=True)


def restaurer_etat(dossier: str) -> None:
    for cible in ETAT_SAUVEGARDE:
        source = os.path.join(dossier, os.path.basename(cible))
        if os.path.exists(source):
            shutil.copy2(source, cible)

    # Un artefact qui n'existait pas avant la demonstration ne doit pas subsister :
    # il decrirait un modele entraine sur des tickets simules.
    try:
        with open(os.path.join(dossier, "absents.json"), encoding="utf-8") as f:
            for chemin in json.load(f):
                if os.path.exists(chemin):
                    os.remove(chemin)
    except (OSError, json.JSONDecodeError):
        pass
    if os.path.exists(os.path.join(dossier, "registry")):
        shutil.rmtree("models/registry", ignore_errors=True)
        shutil.copytree(os.path.join(dossier, "registry"), "models/registry")
    if os.path.exists(os.path.join(dossier, "curated")):
        shutil.rmtree(CURATED_DIR, ignore_errors=True)
        shutil.copytree(os.path.join(dossier, "curated"), CURATED_DIR)


def run(args: argparse.Namespace) -> int:
    temporaire = tempfile.mkdtemp(prefix="helpdesk_mlops_demo_")
    base = os.path.join(temporaire, "production_demo.db")
    sauvegarde = os.path.join(temporaire, "etat_initial")
    echecs: list[str] = []

    titre("ETAPE 0 — Sauvegarde de l'etat du depot")
    sauvegarder_etat(sauvegarde)
    print(f"    Etat sauvegarde dans {sauvegarde}")

    titre("ETAPE 1 — Simulation d'une base de production")
    repartition = construire_base(base)
    total = sum(repartition.values())
    print(f"    {total} tickets resolus inseres dans {base}")
    for force, n in repartition.items():
        print(f"      {force:10s} : {n}")

    titre("ETAPE 2 — Collecte des tickets valides (axe 1)")
    code, sortie = executer(
        [sys.executable, "src/pipeline/collect.py", "--db-url", f"sqlite:///{base}"],
        "collect",
    )
    if code != 0:
        echecs.append("collect")
    if "corrected" not in sortie:
        echecs.append("collect: repartition des etiquettes absente")

    titre("ETAPE 3 — Construction de la version du dataset")
    code, sortie = executer([sys.executable, "src/pipeline/build_dataset.py"], "build_dataset")
    if code != 0:
        echecs.append("build_dataset")
    if "Anti-fuite OK" not in sortie:
        echecs.append("build_dataset: garde-fou anti-fuite non confirme")

    manifeste = {}
    chemin_manifeste = TRAIN_CURRENT.replace(".csv", ".manifest.json")
    if os.path.exists(chemin_manifeste):
        with open(chemin_manifeste, encoding="utf-8") as f:
            manifeste = json.load(f)
        print(f"\n    version du dataset : {manifeste.get('dataset_version')}")
        print(f"    lignes             : {manifeste.get('n_rows')} "
              f"(dont {manifeste.get('n_production_retenues')} de production)")
        print(f"    rejets anti-fuite  : {manifeste.get('rejets_anti_fuite')}")

    titre("ETAPE 4 — Entrainement d'un candidat")
    code, sortie = executer([sys.executable, "src/pipeline/train.py"], "train")
    if code != 0:
        echecs.append("train")
    if "non promu" not in sortie:
        echecs.append("train: le candidat ne devrait jamais etre promu par l'entrainement")

    titre("ETAPE 5 — Porte de promotion")
    code, sortie = executer([sys.executable, "src/pipeline/promote.py"], "promote")
    if code != 0:
        echecs.append("promote")

    decision = {}
    if os.path.exists("metrics/promotion_decision.json"):
        with open("metrics/promotion_decision.json", encoding="utf-8") as f:
            decision = json.load(f)

    titre("ETAPE 6 — Registre des modeles")
    executer([sys.executable, "src/pipeline/promote.py", "--list"], "registry")

    titre("RESULTAT DU CYCLE")
    print(f"    Tickets de production collectes : {manifeste.get('n_production_retenues', 0)}")
    print(f"    Version du dataset produite     : {manifeste.get('dataset_version', 'n/a')}")
    if decision:
        comparaison = decision.get("comparaison") or {}
        print(f"    Decision                        : {decision.get('resultat', 'n/a').upper()}")
        print(f"    Motif                           : {decision.get('motif', 'n/a')}")
        if comparaison:
            print(f"    Metrique                        : {comparaison.get('metrique_decision')}")
            print(f"      production v{decision.get('version_production_precedente')} "
                  f"= {comparaison.get('valeur_production')}")
            print(f"      candidat   v{decision.get('version_candidate')} "
                  f"= {comparaison.get('valeur_candidat')} "
                  f"(delta {comparaison.get('delta'):+.4f})")
            for porte in comparaison.get("portes", []):
                print(f"      [{'OK ' if porte['passe'] else 'NON'}] {porte['porte']}")

    print("\n    Le cycle est demontre quelle que soit la decision. Un rejet prouve")
    print("    que la porte protege la production ; une promotion prouve qu'une")
    print("    amelioration mesuree est bien mise en service.")

    if not args.keep:
        titre("ETAPE 7 — Restauration de l'etat initial")
        restaurer_etat(sauvegarde)
        print("    Depot restaure — dataset, modele servi, registre et lots collectes.")
    else:
        print(f"\n    --keep : etat non restaure. Sauvegarde disponible dans {sauvegarde}")

    if echecs:
        print(f"\n[DEMO] ECHECS : {echecs}")
        return 1
    print("\n[DEMO] Cycle complet execute sans erreur.")
    if not args.keep:
        shutil.rmtree(temporaire, ignore_errors=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--keep", action="store_true",
                   help="conserve l'etat produit par la demonstration")
    sys.exit(run(p.parse_args()))
