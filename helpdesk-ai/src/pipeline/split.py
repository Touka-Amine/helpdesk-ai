"""
Stage DVC 2/4 — Split anti-fuite, avec jeu de test GELE.

STRATEGIE DE DECOUPAGE (params.yaml → split.strategy)
    "group"            GroupShuffleSplit par Titre. Comportement historique,
                       conserve tel quel : c'est lui qui a produit la reference
                       f1_macro = 0.685 publiee dans le memoire.
    "stratified_group" Groupes par Titre egalement, mais repartis pour que les
                       8 categories soient representees au test. Corrige le
                       f1_Applicatifs = 0.0 (classe a support nul), au prix d'un
                       changement de la reference d'evaluation.

POURQUOI LE JEU DE TEST EST GELE
    Avant cette version, `dvc repro` regenerait test.csv a chaque execution. Des
    lors que des tickets de production enrichissent le corpus, le jeu de test
    change a chaque iteration et comparer la F1-macro du modele v2 a celle du v1
    ne mesure plus rien : la porte de promotion (src/pipeline/promote.py) devient
    arbitraire.

    Au premier passage, split.py ecrit data/reference/test_reference.csv et son
    manifeste. Aux passages suivants, il RELIT cette reference et construit le
    train avec tout le reste. Le jeu de test ne bouge plus jamais tout seul.

    Creer une reference v2 est une decision explicite : supprimer le fichier de
    reference, ou basculer split.strategy, puis relancer. Le manifeste conserve
    la trace de ce qui a ete gele et quand.

Sorties :
  - data/splits/train.csv  — tickets d'entrainement (ML)
  - data/splits/test.csv   — copie de travail du jeu de test gele
  - data/splits/rag.csv    — tickets documentes pour la base RAG (issus du train seul) :
                             tout ticket dont "Resolution/Motif" porte un texte, quel que
                             soit son statut. Ce n'est PAS un filtre sur "Resolu".

Usage :
    python src/pipeline/split.py
"""

import hashlib
import json
import os
from datetime import datetime, timezone

import pandas as pd
import yaml
from sklearn.model_selection import GroupShuffleSplit

PROC_PATH   = "data/processed/HelpDesk1.csv"
PARAMS_PATH = "params.yaml"
OUT_TRAIN   = "data/splits/train.csv"
OUT_TEST    = "data/splits/test.csv"
OUT_RAG     = "data/splits/rag.csv"


# ── strategies de decoupage ──────────────────────────────────────────────────

def split_group(df: pd.DataFrame, test_size: float, random_state: int) -> list[str]:
    """GroupShuffleSplit par Titre. Retourne les Titres affectes au test."""
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    _, test_idx = next(gss.split(df, groups=df["Titre"]))
    return sorted(df.iloc[test_idx]["Titre"].unique().tolist())


def split_stratified_group(df: pd.DataFrame, test_size: float, random_state: int) -> list[str]:
    """
    Groupes par Titre, repartis categorie par categorie.

    Chaque Titre appartient a une seule categorie dans ce corpus (verifie a
    l'execution). On traite donc chaque categorie independamment : ses Titres sont
    melanges de façon deterministe, puis on en verse au test jusqu'a approcher
    test_size du volume de la categorie, avec au moins un Titre. La propriete
    anti-fuite est preservee puisque l'unite de decoupage reste le Titre.
    """
    rng = __import__("random").Random(random_state)
    titres_test: list[str] = []

    for cat, bloc in df.groupby("Catégorie"):
        titres = sorted(bloc["Titre"].unique().tolist())
        if len(titres) == 1:
            # Un seul scenario : le verser au test viderait la categorie du train.
            # On le garde au train et on le signale plutot que de casser l'un des deux.
            print(f"[split]   {cat}: 1 seul Titre, conserve au train (test impossible)")
            continue
        rng.shuffle(titres)
        cible = len(bloc) * test_size
        cumul, retenus = 0, []
        for t in titres:
            if cumul >= cible and retenus:
                break
            retenus.append(t)
            cumul += int((bloc["Titre"] == t).sum())
        titres_test.extend(retenus)
        print(f"[split]   {cat}: {len(retenus)}/{len(titres)} Titres au test ({cumul}/{len(bloc)} tickets)")

    return sorted(set(titres_test))


STRATEGIES = {
    "group": split_group,
    "stratified_group": split_stratified_group,
}


# ── reference gelee ──────────────────────────────────────────────────────────

def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloc in iter(lambda: f.read(65536), b""):
            h.update(bloc)
    return h.hexdigest()


def ecrire_reference(test_df: pd.DataFrame, ref_path: str, manifest_path: str,
                     strategy: str, test_size: float, random_state: int) -> None:
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    test_df.to_csv(ref_path, index=False, encoding="utf-8")

    support = test_df["Catégorie"].value_counts().to_dict()
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "strategy": strategy,
        "test_size": test_size,
        "random_state": random_state,
        "n_rows": int(len(test_df)),
        "n_titres": int(test_df["Titre"].nunique()),
        "titres": sorted(test_df["Titre"].unique().tolist()),
        "class_support": {str(k): int(v) for k, v in support.items()},
        "sha256": _sha256(ref_path),
        "note": (
            "Jeu de test gele. Toute evaluation et toute comparaison de modeles "
            "s'appuient sur ce fichier. Le regenerer invalide les comparaisons "
            "anterieures et doit etre une decision explicite."
        ),
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"[split] Reference gelee ecrite : {ref_path}")
    print(f"[split]   {manifest['n_rows']} lignes | {manifest['n_titres']} Titres "
          f"| {len(support)} categories | sha256 {manifest['sha256'][:12]}")


def charger_reference(ref_path: str, manifest_path: str) -> tuple[pd.DataFrame, dict]:
    ref_df = pd.read_csv(ref_path, encoding="utf-8")
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    empreinte = _sha256(ref_path)
    if empreinte != manifest.get("sha256"):
        raise RuntimeError(
            f"Le jeu de test gele a ete modifie depuis sa creation.\n"
            f"  attendu : {manifest.get('sha256')}\n"
            f"  obtenu  : {empreinte}\n"
            f"Restaurez le fichier (git/dvc checkout) ou creez une reference v2 "
            f"deliberement en supprimant {manifest_path}."
        )
    return ref_df, manifest


# ── pipeline ─────────────────────────────────────────────────────────────────

def run() -> None:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        params = yaml.safe_load(f)
    test_size    = params["data"]["test_size"]
    random_state = params["data"]["random_state"]
    split_p      = params.get("split", {})
    strategy     = split_p.get("strategy", "group")
    freeze       = split_p.get("freeze_test", True)
    ref_path     = split_p.get("reference_test_path", "data/reference/test_reference.csv")
    manifest_path= split_p.get("reference_manifest", "data/reference/test_reference_manifest.json")

    if strategy not in STRATEGIES:
        raise ValueError(f"split.strategy inconnue : {strategy} (attendu : {list(STRATEGIES)})")

    print(f"[split] Lecture : {PROC_PATH}")
    df = pd.read_csv(PROC_PATH, encoding="utf-8")
    print(f"[split] {len(df)} lignes | strategie={strategy} | test_size={test_size} "
          f"| random_state={random_state} | freeze={freeze}")

    reference_existante = freeze and os.path.exists(ref_path) and os.path.exists(manifest_path)

    if reference_existante:
        test_df, manifest = charger_reference(ref_path, manifest_path)
        titres_test = set(manifest["titres"])
        train_df = df[~df["Titre"].isin(titres_test)].reset_index(drop=True)
        print(f"[split] Jeu de test GELE relu ({manifest['created_at'][:10]}, "
              f"strategie {manifest['strategy']}) — {len(test_df)} lignes, non regenere")
        nouveaux = len(df) - len(train_df) - len(df[df["Titre"].isin(titres_test)])
        if nouveaux:
            print(f"[split]   {nouveaux} lignes hors reference et hors train — a verifier")
    else:
        titres_test = set(STRATEGIES[strategy](df, test_size, random_state))
        masque_test = df["Titre"].isin(titres_test)
        test_df  = df[masque_test].reset_index(drop=True)
        train_df = df[~masque_test].reset_index(drop=True)
        if freeze:
            ecrire_reference(test_df, ref_path, manifest_path, strategy, test_size, random_state)

    # Base RAG : tickets documentes du train uniquement, c'est-a-dire ceux dont le champ
    # "Resolution/Motif" porte un texte. Le statut n'entre pas dans le filtre : un ticket
    # rejete, en cours ou en attente documente lui aussi une reponse.
    # Anti-fuite : les resolutions de test ne doivent pas etre recherchables.
    rag_mask = (
        train_df["Résolution/Motif"].notna()
        & (train_df["Résolution/Motif"].astype(str).str.strip() != "")
        & (train_df["Résolution/Motif"].astype(str).str.lower() != "nan")
    )
    rag_df = train_df[rag_mask].reset_index(drop=True)

    os.makedirs(os.path.dirname(OUT_TRAIN), exist_ok=True)
    train_df.to_csv(OUT_TRAIN, index=False, encoding="utf-8")
    test_df.to_csv(OUT_TEST,  index=False, encoding="utf-8")
    rag_df.to_csv(OUT_RAG,   index=False, encoding="utf-8")

    print(f"[split] train={len(train_df)} | test={len(test_df)} | rag={len(rag_df)}")
    print(f"[split] Titres uniques — train: {train_df['Titre'].nunique()} "
          f"| test: {test_df['Titre'].nunique()}")

    couverture = test_df["Catégorie"].nunique()
    total_cat  = df["Catégorie"].nunique()
    print(f"[split] Categories couvertes au test : {couverture}/{total_cat}")
    if couverture < total_cat:
        manquantes = sorted(set(df["Catégorie"]) - set(test_df["Catégorie"]))
        print(f"[split]   AVERTISSEMENT — sans support au test : {manquantes}")
        print(f"[split]   Leur F1 vaudra 0.0 par construction et tirera la F1-macro "
              f"vers le bas. promote.py les exclut des comparaisons.")

    overlap = set(train_df["Titre"]) & set(test_df["Titre"])
    assert not overlap, f"Fuite detectee — {len(overlap)} Titres communs train/test !"
    print("[split] Anti-fuite OK — aucun Titre commun train/test.")


if __name__ == "__main__":
    run()
