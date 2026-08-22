"""
Stage DVC optionnel — Augmentation de données par paraphrase LLM locale.

Objectif : créer de la DIVERSITÉ LEXICALE, pas seulement rééquilibrer les comptes.
Le corpus contient 58 types de tickets dont le corps de description est quasi
identique d'une instance à l'autre (seule la formule d'appel varie). Un modèle
entraîné dessus voit ~31 quasi-doublons par scénario.

Principe :
  - lit UNIQUEMENT data/splits/train.csv (jamais test.csv ni rag.csv) ;
  - demande à Ollama de reformuler la description comme un autre demandeur
    l'aurait écrite, en conservant à l'identique les termes techniques ;
  - garde le Titre et la Catégorie d'origine (la propriété anti-fuite du
    découpage par groupe reste donc vraie) ;
  - marque chaque ligne générée par is_augmented=True ;
  - rejette les paraphrases qui ont perdu le vocabulaire discriminant.

RÈGLES À NE PAS ENFREINDRE
  1. Augmenter APRÈS le découpage, sur le train seul. Augmenter avant
     réintroduirait exactement la fuite que split.py élimine.
  2. Ne jamais injecter les lignes augmentées dans la base RAG : elles
     contiendraient des résolutions synthétiques.
  3. Comparer avant/après sur le MÊME jeu de test, non augmenté.

Usage :
    python src/pipeline/augment.py
    python src/pipeline/augment.py --dry-run          # 5 exemples, sans écriture
    python src/pipeline/augment.py --categories Sécurité Backup
"""

from __future__ import annotations

import argparse
import os
import random
import re
import sys
import time
import unicodedata

import pandas as pd
import requests
import yaml

IN_TRAIN = "data/splits/train.csv"
OUT_AUG = "data/splits/train_augmented.csv"
PARAMS_PATH = "params.yaml"

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")

# Termes dont la disparition invalide la paraphrase : ce sont eux qui portent
# le signal de catégorie. Aligné sur la liste _KEEP de src/data/preprocess.py.
TERMES_PROTEGES = {
    "reseau", "systeme", "application", "serveur", "poste", "acces",
    "connexion", "microsoft", "outlook", "teams", "vpn", "dns", "wifi",
    "sage", "erp", "backup", "sauvegarde", "securite", "virus", "antivirus",
    "firewall", "internet", "email", "mail", "bureau", "windows", "excel",
    "imprimante", "spooler", "ransomware", "phishing", "quarantaine",
    "office", "sharepoint", "licence", "mot de passe", "verrouillage",
}

GABARIT = """Tu reformules une demande d'assistance informatique en français.

Réécris le message ci-dessous comme l'aurait écrit un AUTRE collaborateur : \
autre tournure, autre ordre des idées, autre niveau de détail, registre plus \
familier ou plus formel selon le cas.

Contraintes impératives :
- conserve EXACTEMENT les termes techniques, noms de logiciels, codes d'erreur \
et chiffres présents dans l'original ;
- n'introduis AUCUN terme technique qui ne figure pas dans l'original : pas de \
« sauvegarde », « réseau », « serveur », « VPN » ou autre s'il n'y est pas déjà ;
- le problème décrit doit rester strictement le même ;
- n'invente aucun détail, aucune cause, aucune solution absente de l'original ;
- réponds UNIQUEMENT par le message reformulé, sans commentaire ni préambule.

Message original :
{texte}"""


# ─────────────────────────────────────────────────────────── utilitaires

def normalise(texte: str) -> str:
    """Minuscules sans accents, pour comparer le vocabulaire."""
    t = unicodedata.normalize("NFKD", str(texte).lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def termes_presents(texte: str) -> set[str]:
    n = normalise(texte)
    return {t for t in TERMES_PROTEGES if t in n}


def mots(texte: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{3,}", normalise(texte)))


def paraphrase_valide(source: str, candidat: str) -> tuple[bool, str]:
    """
    Garde-fous. Une paraphrase est rejetée si elle :
      - est vide ou trop courte / trop longue par rapport à la source ;
      - a PERDU un terme technique présent dans la source ;
      - a AJOUTÉ un terme technique absent de la source ;
      - est identique à la source (le LLM a recopié) ;
      - partage moins de 25 % de vocabulaire avec la source (dérive de sujet).

    Le contrôle des termes ajoutés n'est pas cosmétique. Observé en test sur un
    ticket « Sécurité / antivirus signalant un ransomware », llama3.2:3b a
    spontanément introduit « fichier de sauvegarde » — mot-clé de la catégorie
    Backup — dans une description qui n'en contenait pas. Une paraphrase qui
    injecte le vocabulaire d'une autre catégorie que celle de son étiquette
    dégrade le jeu au lieu de l'enrichir.
    """
    if not candidat or len(candidat.split()) < 8:
        return False, "trop court"

    ratio_long = len(candidat.split()) / max(len(source.split()), 1)
    if not 0.5 <= ratio_long <= 2.2:
        return False, f"longueur x{ratio_long:.1f}"

    ts, tc = termes_presents(source), termes_presents(candidat)
    if ts - tc:
        return False, f"termes perdus : {sorted(ts - tc)}"
    if tc - ts:
        return False, f"termes ajoutes : {sorted(tc - ts)}"

    if normalise(candidat).strip() == normalise(source).strip():
        return False, "identique a la source"

    ms, mc = mots(source), mots(candidat)
    if ms and len(ms & mc) / len(ms) < 0.25:
        return False, "derive de sujet"

    return True, "ok"


def appelle_ollama(texte: str, temperature: float, timeout: int = 120) -> str | None:
    try:
        r = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": GABARIT.format(texte=texte),
                "stream": False,
                "options": {"temperature": temperature, "top_p": 0.95},
            },
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except Exception as exc:                      # noqa: BLE001
        print(f"    [ollama] {type(exc).__name__}: {exc}")
        return None


# ─────────────────────────────────────────────────────────── plan d'augmentation

def plan_augmentation(df: pd.DataFrame, cible: int, max_par_source: int) -> dict[str, int]:
    """
    Combien de paraphrases générer par catégorie.

    On vise `cible` tickets par catégorie, sans dépasser `max_par_source`
    paraphrases par ticket d'origine — au-delà, on ne fait que multiplier
    les variantes d'un même scénario sans apport d'information.
    """
    plan = {}
    for cat, n in df["Catégorie"].value_counts().items():
        deficit = max(cible - n, 0)
        plafond = n * max_par_source
        plan[cat] = min(deficit, plafond)
    return plan


def run(args: argparse.Namespace) -> None:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        params = yaml.safe_load(f)
    aug = params.get("augment", {})
    cible = args.cible or aug.get("cible_par_categorie", 0)
    max_par_source = args.max_par_source or aug.get("max_par_source", 5)
    temperature = aug.get("temperature", 0.9)
    seed = params["data"]["random_state"]

    random.seed(seed)

    df = pd.read_csv(IN_TRAIN, encoding="utf-8")
    print(f"[augment] train  : {len(df)} lignes | {df['Titre'].nunique()} types")
    print(f"[augment] modele : {OLLAMA_MODEL} sur {OLLAMA_HOST}")

    if not cible:
        cible = int(df["Catégorie"].value_counts().max())
    plan = plan_augmentation(df, cible, max_par_source)

    if args.categories:
        plan = {c: n for c, n in plan.items() if c in args.categories}

    total = sum(plan.values())
    print(f"[augment] cible {cible}/categorie, plafond {max_par_source}/source "
          f"-> {total} paraphrases a generer")
    for c, n in sorted(plan.items(), key=lambda kv: -kv[1]):
        print(f"    {c:16s} {int((df['Catégorie'] == c).sum()):4d} -> +{n}")

    if args.dry_run:
        total, plan = 5, {list(plan)[0]: 5}
        print("[augment] DRY-RUN : 5 exemples, aucune ecriture")

    lignes, rejets, t0 = [], 0, time.time()
    for cat, besoin in plan.items():
        if besoin <= 0:
            continue
        pool = df[df["Catégorie"] == cat]
        # On tourne sur les sources pour repartir les paraphrases entre scenarios.
        sources = pool.sample(frac=1, random_state=seed).to_dict("records")
        i, produits, tentatives = 0, 0, 0

        while produits < besoin and tentatives < besoin * 3:
            src = sources[i % len(sources)]
            i, tentatives = i + 1, tentatives + 1

            cand = appelle_ollama(str(src["Description"]), temperature)
            if cand is None:
                continue
            ok, motif = paraphrase_valide(str(src["Description"]), cand)
            if not ok:
                rejets += 1
                if args.verbose:
                    print(f"    rejet ({motif})")
                continue

            nouvelle = dict(src)
            nouvelle["Description"] = cand
            nouvelle["is_augmented"] = True
            # Les champs de resolution ne sont PAS repris : ces lignes ne doivent
            # jamais alimenter la base de connaissances du moteur RAG.
            for champ in ("Résolution/Motif", "Analyse", "knowledge Base"):
                nouvelle[champ] = ""
            lignes.append(nouvelle)
            produits += 1

            if produits % 20 == 0:
                dt = time.time() - t0
                print(f"    {cat:16s} {produits}/{besoin}  ({dt/max(len(lignes),1):.1f} s/paraphrase)")

        print(f"[augment] {cat:16s} +{produits} (rejets cumules : {rejets})")

    if args.dry_run:
        for l in lignes:
            print("\n---", l["Titre"])
            print(l["Description"][:400])
        return

    df["is_augmented"] = False
    out = pd.concat([df, pd.DataFrame(lignes)], ignore_index=True)
    out.to_csv(OUT_AUG, index=False, encoding="utf-8")

    print(f"\n[augment] ecrit {OUT_AUG}")
    print(f"[augment] {len(df)} -> {len(out)} lignes (+{len(lignes)}), {rejets} rejets")
    print(f"[augment] duree : {(time.time()-t0)/60:.1f} min")

    # Verification anti-fuite : aucun nouveau titre n'a ete introduit.
    inconnus = set(out["Titre"]) - set(df["Titre"])
    assert not inconnus, f"Titres inattendus apres augmentation : {inconnus}"
    print("[augment] anti-fuite OK — aucun titre nouveau, le decoupage reste valide.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true", help="5 exemples, sans ecriture")
    p.add_argument("--cible", type=int, help="tickets vises par categorie")
    p.add_argument("--max-par-source", type=int, dest="max_par_source")
    p.add_argument("--categories", nargs="+", help="limiter a certaines categories")
    p.add_argument("--verbose", action="store_true", help="afficher le motif des rejets")
    sys.exit(run(p.parse_args()))
