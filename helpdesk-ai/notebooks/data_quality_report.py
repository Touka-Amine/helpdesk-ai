"""
data_quality_report.py
----------------------
Génère le diagnostic de qualité des données HelpDesk :
- calcule les indicateurs clés (complétude, classes, redondance, longueurs, base RAG) ;
- produit des figures PNG dans notebooks/figures/ ;
- compile l'ensemble dans un PDF : notebooks/figures/diagnostic_qualite_donnees.pdf ;
- écrit un résumé JSON : notebooks/figures/diagnostic_qualite_donnees.json

Exécution :
    python notebooks/data_quality_report.py
(depuis la racine helpdesk-ai/, avec l'environnement du projet activé)
"""
from __future__ import annotations
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIG_DIR = os.path.join(HERE, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# Chemins candidats pour les données brutes
DATA_CANDIDATES = [
    os.path.join(ROOT, "data", "raw", "HelpDesk1.csv"),
    os.path.join(ROOT, "HelpDesk1.csv"),
]


def load_data() -> pd.DataFrame:
    path = next((p for p in DATA_CANDIDATES if os.path.exists(p)), None)
    if path is None:
        raise FileNotFoundError("HelpDesk1.csv introuvable (data/raw/ ou racine).")
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            df = pd.read_csv(path, encoding=enc)
            if df.shape[1] > 5:
                print(f"[OK] Données chargées : {path} (encodage={enc}, shape={df.shape})")
                return df
        except Exception:
            continue
    raise RuntimeError("Échec du chargement du CSV.")


def find_col(df: pd.DataFrame, sub: str) -> str | None:
    for c in df.columns:
        if sub.lower() in c.lower():
            return c
    return None


def compute_metrics(df: pd.DataFrame) -> dict:
    cat = find_col(df, "gorie")
    desc = find_col(df, "Description")
    titre = find_col(df, "Titre")
    res = find_col(df, "solution")
    statut = find_col(df, "STATUT")

    n = len(df)
    wl = df[desc].fillna("").str.split().apply(len)
    vc = df[cat].value_counts()
    combo = (df[titre].fillna("") + " || " + df[desc].fillna(""))

    metrics = {
        "n_lignes": int(n),
        "n_colonnes": int(df.shape[1]),
        "n_classes": int(vc.size),
        "classes": {str(k): int(v) for k, v in vc.items()},
        "ratio_desequilibre": round(float(vc.max() / vc.min()), 2),
        "doublons_lignes_completes": int(df.duplicated().sum()),
        "descriptions_uniques": int(df[desc].nunique()),
        "titres_uniques": int(df[titre].nunique()),
        "doublons_description": int(df[desc].duplicated().sum()),
        "doublons_titre_desc": int(combo.duplicated().sum()),
        "tickets_vides": int((wl == 0).sum()),
        "mots_desc_min": int(wl.min()),
        "mots_desc_median": int(wl.median()),
        "mots_desc_max": int(wl.max()),
        "mots_desc_moyenne": round(float(wl.mean()), 1),
        "statut": {str(k): int(v) for k, v in df[statut].value_counts().items()},
        "base_rag_resolus": int(df[statut].astype(str).str.contains("solu", case=False, na=False).sum()),
        "completude_pct": {c: round(float(df[c].notna().mean() * 100), 2) for c in df.columns},
        "manquants_pct": {c: round(float(df[c].isna().mean() * 100), 2)
                           for c in df.columns if df[c].isna().any()},
    }
    metrics["_cols"] = {"cat": cat, "desc": desc, "titre": titre, "res": res, "statut": statut}
    return metrics


def make_figures(df: pd.DataFrame, m: dict) -> list[str]:
    cols = m["_cols"]
    plt.style.use("seaborn-v0_8-muted")
    paths = []

    # 1. Distribution des classes
    fig, ax = plt.subplots(figsize=(10, 5))
    s = pd.Series(m["classes"]).sort_values(ascending=False)
    s.plot(kind="bar", ax=ax, color="steelblue", edgecolor="white")
    ax.set_title(f"Distribution des catégories (déséquilibre {m['ratio_desequilibre']}x)",
                 fontweight="bold")
    ax.set_ylabel("Nombre de tickets")
    for p in ax.patches:
        ax.annotate(f"{int(p.get_height())}", (p.get_x() + p.get_width() / 2, p.get_height()),
                    ha="center", va="bottom", fontsize=9)
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    p1 = os.path.join(FIG_DIR, "dq_01_distribution_classes.png")
    fig.savefig(p1, dpi=150, bbox_inches="tight"); paths.append(p1); plt.close(fig)

    # 2. Complétude des colonnes
    fig, ax = plt.subplots(figsize=(10, 6))
    comp = pd.Series(m["completude_pct"]).sort_values()
    comp.plot(kind="barh", ax=ax, color="seagreen", edgecolor="white")
    ax.set_title("Complétude des colonnes (%)", fontweight="bold")
    ax.set_xlabel("% de valeurs renseignées"); ax.set_xlim(0, 100)
    plt.tight_layout()
    p2 = os.path.join(FIG_DIR, "dq_02_completude.png")
    fig.savefig(p2, dpi=150, bbox_inches="tight"); paths.append(p2); plt.close(fig)

    # 3. Longueur des descriptions (mots)
    fig, ax = plt.subplots(figsize=(10, 5))
    wl = df[cols["desc"]].fillna("").str.split().apply(len)
    wl.hist(bins=30, ax=ax, color="steelblue", edgecolor="white")
    ax.axvline(wl.median(), color="red", linestyle="--", label=f"Médiane : {int(wl.median())}")
    ax.set_title("Longueur des descriptions (nombre de mots)", fontweight="bold")
    ax.set_xlabel("Mots"); ax.set_ylabel("Tickets"); ax.legend()
    plt.tight_layout()
    p3 = os.path.join(FIG_DIR, "dq_03_longueurs.png")
    fig.savefig(p3, dpi=150, bbox_inches="tight"); paths.append(p3); plt.close(fig)

    # 4. Redondance / diversité
    fig, ax = plt.subplots(figsize=(10, 5))
    red = pd.Series({
        "Lignes": m["n_lignes"],
        "Descriptions uniques": m["descriptions_uniques"],
        "Titres uniques": m["titres_uniques"],
    })
    red.plot(kind="bar", ax=ax, color=["#444", "steelblue", "#c0792b"], edgecolor="white")
    ax.set_title("Diversité du corpus : lignes vs descriptions vs titres uniques",
                 fontweight="bold")
    ax.set_ylabel("Nombre")
    for p in ax.patches:
        ax.annotate(f"{int(p.get_height())}", (p.get_x() + p.get_width() / 2, p.get_height()),
                    ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.tick_params(axis="x", rotation=0)
    plt.tight_layout()
    p4 = os.path.join(FIG_DIR, "dq_04_redondance.png")
    fig.savefig(p4, dpi=150, bbox_inches="tight"); paths.append(p4); plt.close(fig)

    # 5. Statut + base RAG
    fig, ax = plt.subplots(figsize=(10, 5))
    pd.Series(m["statut"]).sort_values(ascending=False).plot(
        kind="bar", ax=ax, color="slateblue", edgecolor="white")
    ax.set_title(f"Répartition des statuts (base de résolution RAG : "
                 f"{m['base_rag_resolus']} tickets résolus)", fontweight="bold")
    ax.set_ylabel("Nombre de tickets"); ax.tick_params(axis="x", rotation=20)
    plt.tight_layout()
    p5 = os.path.join(FIG_DIR, "dq_05_statuts.png")
    fig.savefig(p5, dpi=150, bbox_inches="tight"); paths.append(p5); plt.close(fig)

    return paths


def build_pdf(png_paths: list[str], m: dict) -> str:
    pdf_path = os.path.join(FIG_DIR, "diagnostic_qualite_donnees.pdf")
    with PdfPages(pdf_path) as pdf:
        # Page de garde
        fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
        fig.text(0.5, 0.80, "Diagnostic de qualité des données", ha="center",
                 fontsize=20, fontweight="bold")
        fig.text(0.5, 0.74, "HelpDesk AI", ha="center", fontsize=14)
        lignes = [
            f"Lignes : {m['n_lignes']}    Colonnes : {m['n_colonnes']}    Classes : {m['n_classes']}",
            f"Déséquilibre des classes : {m['ratio_desequilibre']}x",
            f"Descriptions uniques : {m['descriptions_uniques']} / {m['n_lignes']}",
            f"Titres uniques (types de tickets) : {m['titres_uniques']}",
            f"Tickets vides : {m['tickets_vides']}    Doublons de ligne : {m['doublons_lignes_completes']}",
            f"Longueur médiane (desc.) : {m['mots_desc_median']} mots",
            f"Base de résolution (RAG) : {m['base_rag_resolus']} tickets résolus",
        ]
        for i, l in enumerate(lignes):
            fig.text(0.12, 0.62 - i * 0.035, "• " + l, fontsize=11)
        fig.text(0.5, 0.06, "Document généré automatiquement", ha="center",
                 fontsize=8, style="italic", color="gray")
        pdf.savefig(fig); plt.close(fig)
        # Figures
        for p in png_paths:
            img = plt.imread(p)
            fig = plt.figure(figsize=(11, 6))
            ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.imshow(img)
            pdf.savefig(fig); plt.close(fig)
    return pdf_path


def main():
    df = load_data()
    m = compute_metrics(df)
    pngs = make_figures(df, m)
    pdf = build_pdf(pngs, m)
    m.pop("_cols", None)
    with open(os.path.join(FIG_DIR, "diagnostic_qualite_donnees.json"), "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)
    print(f"[OK] {len(pngs)} figures PNG générées dans {FIG_DIR}")
    print(f"[OK] PDF : {pdf}")
    print(f"[OK] Résumé JSON : diagnostic_qualite_donnees.json")


if __name__ == "__main__":
    main()
