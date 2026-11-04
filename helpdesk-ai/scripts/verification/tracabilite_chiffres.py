# -*- coding: utf-8 -*-
"""
T6 / 6.1 et 6.4 — tracabilite des chiffres publies.

Releve chaque valeur de la forme 0,XXXX dans les sources LaTeX du memoire, puis
la cherche dans les artefacts de mesure du depot. Une valeur introuvable est
soit un chiffre orphelin, soit une valeur derivee qu'il faut justifier.

Sortie : scratchpad/t6_tracabilite.json + rapport sur la sortie standard.
"""
from __future__ import annotations

import io
import json
import os
import re
import glob

RAPPORT = r"C:\projetpfe\report"
PROJET = r"C:\projetpfe\helpdesk-ai"
SORTIE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rapport_tracabilite.json")


# ── 1. toutes les valeurs numeriques des artefacts ──────────────────────────
def aplatir(obj, chemin, sortie):
    if isinstance(obj, dict):
        for k, v in obj.items():
            aplatir(v, chemin + [str(k)], sortie)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            aplatir(v, chemin + [str(i)], sortie)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        sortie.append((float(obj), "/".join(chemin)))


artefacts = {}
fichiers = sorted(glob.glob(os.path.join(PROJET, "metrics", "*.json")))
fichiers += sorted(glob.glob(os.path.join(PROJET, "models", "*.json")))
fichiers += sorted(glob.glob(os.path.join(PROJET, "models", "registry", "*", "*.json")))
for f in fichiers:
    try:
        with io.open(f, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        continue
    plat = []
    aplatir(d, [], plat)
    artefacts[os.path.relpath(f, PROJET).replace("\\", "/")] = plat

total_valeurs = sum(len(v) for v in artefacts.values())
print("[t6] %d artefacts, %d valeurs numeriques" % (len(artefacts), total_valeurs))


def chercher(valeur, tolerance=5e-5):
    """Retourne la liste des (fichier, chemin) dont la valeur correspond."""
    trouves = []
    for fichier, plat in artefacts.items():
        for v, chemin in plat:
            if abs(v - valeur) <= tolerance:
                trouves.append("%s :: %s" % (fichier, chemin))
    return trouves


# ── 2. valeurs publiees dans le memoire ─────────────────────────────────────
MOTIF = re.compile(r"(?<![\d,])0,(\d{4})(?![\d])")
publiees = {}
for tex in sorted(glob.glob(os.path.join(RAPPORT, "*.tex"))):
    nom = os.path.basename(tex)
    with io.open(tex, encoding="utf-8", errors="replace") as fh:
        for no, ligne in enumerate(fh, 1):
            if ligne.lstrip().startswith("%"):
                continue
            for m in MOTIF.finditer(ligne):
                val = float("0." + m.group(1))
                publiees.setdefault(val, []).append("%s:%d" % (nom, no))

print("[t6] %d valeurs distinctes publiees dans le memoire" % len(publiees))

# ── 3. confrontation ────────────────────────────────────────────────────────
tracees, orphelines = {}, {}
for val in sorted(publiees):
    sources = chercher(val)
    enregistrement = {
        "valeur": val,
        "occurrences_memoire": publiees[val],
        "sources": sources,
    }
    (tracees if sources else orphelines)[("%.4f" % val)] = enregistrement

print()
print("=" * 70)
print("TRACEES : %d valeurs" % len(tracees))
print("ORPHELINES : %d valeurs" % len(orphelines))
print("=" * 70)
print()
for cle in sorted(orphelines, key=lambda c: -len(orphelines[c]["occurrences_memoire"])):
    e = orphelines[cle]
    print("  %s  <- %s" % (cle, ", ".join(e["occurrences_memoire"][:6])))

print()
print("--- valeurs tracees presentes dans PLUSIEURS artefacts (risque de confusion) ---")
for cle in sorted(tracees):
    e = tracees[cle]
    fichiers_distincts = sorted({s.split(" :: ")[0] for s in e["sources"]})
    if len(fichiers_distincts) > 1:
        print("  %s  dans %s" % (cle, ", ".join(fichiers_distincts)))

with io.open(SORTIE, "w", encoding="utf-8") as f:
    json.dump({"tracees": tracees, "orphelines": orphelines}, f,
              indent=2, ensure_ascii=False)
print()
print("[t6] ecrit %s" % SORTIE)
