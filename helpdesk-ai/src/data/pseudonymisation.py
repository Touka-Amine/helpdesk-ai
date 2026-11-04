# -*- coding: utf-8 -*-
"""Pseudonymisation des personnes nommees dans le corpus et dans la base.

Ce que l'exigence demande
-------------------------
ENF-04 volet (b) : « traitement des donnees personnelles conforme a la
reglementation ». Le memoire la declarait non tenue : le corpus, la base et les
sauvegardes portaient les noms en clair, et aucune duree de conservation n'avait
ete arretee.

Ce que ce module traite, et ce qu'il ne traite pas
---------------------------------------------------
Un releve prealable (scripts/verification/audit_donnees_personnelles.py) etablit
que les donnees personnelles du corpus tiennent dans DEUX colonnes :

    Demandeur    202 personnes
    Assigne a     11 consultants

Le texte libre, lui, n'en contient aucune : aucun nom de la liste n'y figure en
mot entier, aucune adresse de courriel, aucune adresse IP. La seule suite de
chiffres qui ressemble a un numero est « 80080300 », repetee 48 fois : c'est le
numero du support, une donnee de l'entreprise et non d'une personne.

La pseudonymisation porte donc sur les deux colonnes, et le releve est rejoue
apres coup pour verifier qu'il ne reste rien.

Pourquoi un pseudonyme calcule et non un simple numero d'ordre
---------------------------------------------------------------
Le service doit pouvoir, en cas de besoin legitime, retrouver qui se cache
derriere un pseudonyme — pour repondre a une demande d'acces, par exemple. Un
numero d'ordre tire au hasard l'obligerait a conserver une table de
correspondance aussi sensible que les noms eux-memes.

Le pseudonyme est donc un HMAC-SHA256 tronque, calcule avec une cle secrete :

  - sans la cle, le pseudonyme ne se remonte pas, meme en essayant tous les noms
    de l'annuaire, car la cle manque ;
  - avec la cle, le service recalcule le pseudonyme d'un nom donne et retrouve
    ses tickets, sans jamais stocker de table ;
  - la meme personne porte toujours le meme pseudonyme, ce qui preserve les
    statistiques par demandeur et par consultant.

La cle vit dans la variable d'environnement PSEUDO_KEY. Elle n'est pas dans le
depot, et sa perte rend la reidentification impossible — ce qui est une
propriete, non un defaut.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import unicodedata

VARIABLE_CLE = "PSEUDO_KEY"
LONGUEUR = 10
COLONNES_IDENTIFIANTES = ("Demandeur", "Assigné à")


class CleManquante(RuntimeError):
    """Levee quand la cle de pseudonymisation n'est pas fournie."""


def cle(obligatoire: bool = True) -> bytes:
    """La cle secrete, lue dans l'environnement.

    En developpement, une cle de demonstration est acceptee si la variable
    n'est pas posee ET que l'appelant l'autorise explicitement. Jamais en
    production : `charger_cle_ou_echouer` est le point d'entree du pipeline.
    """
    valeur = os.environ.get(VARIABLE_CLE, "")
    if valeur:
        return valeur.encode("utf-8")
    if obligatoire:
        raise CleManquante(
            "La variable %s n'est pas posee. Sans elle, la pseudonymisation "
            "produirait des pseudonymes que personne ne peut recalculer. "
            "Poser une cle longue et la conserver hors du depot." % VARIABLE_CLE)
    return b""


def _normaliser(nom: str) -> str:
    """« Ismail SBAA », « ismail sbaa » et « Ismail  SBAA » donnent le meme pseudonyme.

    Sans cette etape, une saisie differente de la meme personne produirait deux
    pseudonymes, et les statistiques par demandeur seraient fausses.
    """
    t = unicodedata.normalize("NFKD", str(nom).strip().lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(t.split())


def pseudonyme(nom: str, prefixe: str = "P", secret: bytes | None = None) -> str:
    """Le pseudonyme stable d'une personne, par exemple « P-3f9a1c2b4d »."""
    if nom is None or str(nom).strip() == "" or str(nom).lower() == "nan":
        return ""
    k = secret if secret is not None else cle()
    empreinte = hmac.new(k, _normaliser(nom).encode("utf-8"), hashlib.sha256).hexdigest()
    return "%s-%s" % (prefixe, empreinte[:LONGUEUR])


def pseudonymiser_tableau(df, colonnes=COLONNES_IDENTIFIANTES, secret: bytes | None = None):
    """Remplace sur place les colonnes identifiantes presentes dans le tableau.

    Retourne (tableau, rapport) ou le rapport dit, par colonne, combien de
    personnes distinctes ont ete remplacees. Une colonne absente est ignoree
    sans erreur : tous les exports ne portent pas les memes champs.
    """
    k = secret if secret is not None else cle()
    rapport = {}
    prefixes = {"Demandeur": "DEM", "Assigné à": "AGT"}
    for col in colonnes:
        if col not in df.columns:
            continue
        avant = df[col].dropna().nunique()
        df[col] = df[col].map(lambda v: pseudonyme(v, prefixes.get(col, "P"), k))
        rapport[col] = {"personnes_distinctes": int(avant),
                        "pseudonymes_distincts": int(df[col].replace("", None).dropna().nunique())}
    return df, rapport


def retrouver(nom: str, colonne: str = "Demandeur", secret: bytes | None = None) -> str:
    """Le pseudonyme d'un nom connu, pour repondre a une demande d'acces.

    Le service qui detient la cle recalcule le pseudonyme et filtre ses tickets
    dessus. Aucune table de correspondance n'est conservee nulle part.
    """
    prefixes = {"Demandeur": "DEM", "Assigné à": "AGT"}
    return pseudonyme(nom, prefixes.get(colonne, "P"), secret)
