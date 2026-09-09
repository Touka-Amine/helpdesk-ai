# -*- coding: utf-8 -*-
"""Langage visuel commun aux figures du chapitre 6."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import (FancyBboxPatch, Rectangle, Ellipse,
                                FancyArrowPatch, Circle, Arc)
from matplotlib.path import Path

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["savefig.dpi"] = 200

# Couleurs semantiques : une famille = un role, pas un arc-en-ciel.
PAL = {
    "external": ("#FAEFD0", "#A67C1A"),
    "input":    ("#DCE9F8", "#2F6DA8"),
    "process":  ("#E2E3F5", "#4B51A0"),
    "storage":  ("#D6EFE7", "#1E7A64"),
    "neutral":  ("#EDEFF2", "#6B7280"),
    "risk":     ("#F8DEDE", "#A83F3F"),
}
FG, MUTED, LINE = "#1B2430", "#5A6472", "#57606E"
TT, LB, SM, XS = 12.5, 10.0, 8.4, 7.4
Z_EDGE, Z_NODE, Z_TEXT = 2, 3, 4


def canvas(w, h, xlim, ylim):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_aspect("equal"); ax.axis("off")
    return fig, ax


def box(ax, cx, cy, w, h, kind="neutral", r=0.09, lw=1.1, ls="-", z=Z_NODE):
    fill, edge = PAL[kind]
    p = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                       boxstyle="round,pad=0,rounding_size=%.2f" % r,
                       facecolor=fill, edgecolor=edge, linewidth=lw,
                       linestyle=ls, zorder=z)
    ax.add_patch(p)
    return p


def txt(ax, x, y, s, size=SM, weight="normal", color=FG, ha="center",
        va="center", style="normal", z=Z_TEXT, rot=0):
    return ax.text(x, y, s, fontsize=size, fontweight=weight, color=color,
                   ha=ha, va=va, style=style, zorder=z, rotation=rot,
                   rotation_mode="anchor" if rot else None)


def titled(ax, cx, cy, w, h, kind, title, subs=(), r=0.09, tsize=LB, ssize=SM,
           lw=1.1, ls="-"):
    """Boite a titre gras et lignes secondaires, centree verticalement."""
    box(ax, cx, cy, w, h, kind, r=r, lw=lw, ls=ls)
    n = 1 + len(subs)
    step = 0.30
    top = cy + (n - 1) * step / 2
    txt(ax, cx, top, title, size=tsize, weight="bold")
    for i, s in enumerate(subs):
        txt(ax, cx, top - (i + 1) * step, s, size=ssize, color=MUTED)


def arrow(ax, pts, dashed=False, color=LINE, lw=1.15, head=11,
          style="-|>", rad=None, z=Z_EDGE):
    if rad is not None:
        a = FancyArrowPatch(pts[0], pts[-1], arrowstyle=style,
                            connectionstyle="arc3,rad=%.3f" % rad,
                            mutation_scale=head, linewidth=lw, color=color,
                            linestyle="--" if dashed else "-",
                            shrinkA=0, shrinkB=0, zorder=z)
    else:
        path = Path(pts, [Path.MOVETO] + [Path.LINETO] * (len(pts) - 1))
        a = FancyArrowPatch(path=path, arrowstyle=style, mutation_scale=head,
                            linewidth=lw, color=color,
                            linestyle="--" if dashed else "-", zorder=z)
    ax.add_patch(a)
    return a


def link(ax, pts, color=LINE, lw=1.15, dashed=False, z=Z_EDGE):
    """Trait sans fleche (association UML)."""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    ax.plot(xs, ys, color=color, lw=lw, zorder=z,
            linestyle="--" if dashed else "-", solid_capstyle="round")


def elabel(ax, x, y, s, color=MUTED, size=XS, ha="center", va="center",
           bg=True):
    t = txt(ax, x, y, s, size=size, color=color, ha=ha, va=va)
    if bg:
        t.set_bbox(dict(facecolor="white", edgecolor="none", pad=1.2,
                        alpha=0.92))
    return t


def note(ax, cx, cy, w, h, lines, anchor=None):
    """Note UML : coin superieur droit replie."""
    x0, y0 = cx - w / 2, cy - h / 2
    c = 0.28
    pts = [(x0, y0), (x0, y0 + h), (x0 + w - c, y0 + h), (x0 + w, y0 + h - c),
           (x0 + w, y0), (x0, y0)]
    ax.add_patch(plt.Polygon(pts, closed=True, facecolor="#FFFDF3",
                             edgecolor="#B9A46A", lw=0.9, zorder=Z_NODE))
    ax.plot([x0 + w - c, x0 + w - c, x0 + w], [y0 + h, y0 + h - c, y0 + h - c],
            color="#B9A46A", lw=0.9, zorder=Z_NODE + 1)
    step = 0.30
    top = cy + (len(lines) - 1) * step / 2
    for i, s in enumerate(lines):
        txt(ax, cx, top - i * step, s, size=XS, color="#6B5B2E")
    if anchor:
        ax.plot([cx, anchor[0]], [cy, anchor[1]], color="#B9A46A", lw=0.8,
                linestyle=(0, (3, 3)), zorder=Z_EDGE)


def actor(ax, x, y, name, sub=None, s=1.0, color=None):
    """Bonhomme UML."""
    c = color or PAL["external"][1]
    ax.add_patch(Circle((x, y + 0.55 * s), 0.20 * s, facecolor=PAL["external"][0],
                        edgecolor=c, lw=1.2, zorder=Z_NODE))
    ax.plot([x, x], [y + 0.35 * s, y - 0.20 * s], color=c, lw=1.2, zorder=Z_NODE)
    ax.plot([x - 0.32 * s, x + 0.32 * s], [y + 0.18 * s, y + 0.18 * s],
            color=c, lw=1.2, zorder=Z_NODE)
    ax.plot([x, x - 0.28 * s], [y - 0.20 * s, y - 0.70 * s], color=c, lw=1.2,
            zorder=Z_NODE)
    ax.plot([x, x + 0.28 * s], [y - 0.20 * s, y - 0.70 * s], color=c, lw=1.2,
            zorder=Z_NODE)
    txt(ax, x, y - 1.00 * s, name, size=SM, weight="bold")
    if sub:
        txt(ax, x, y - 1.30 * s, sub, size=XS, color=MUTED)


def legend(ax, x, y, items, dx=2.6, sw=0.30):
    for i, (kind, lab) in enumerate(items):
        fill, edge = PAL[kind]
        ax.add_patch(FancyBboxPatch((x + i * dx, y), sw, sw,
                                    boxstyle="round,pad=0,rounding_size=0.05",
                                    facecolor=fill, edgecolor=edge, lw=1.0,
                                    zorder=Z_NODE))
        txt(ax, x + i * dx + sw + 0.16, y + sw / 2, lab, size=XS, color=MUTED,
            ha="left")


def save(fig, name):
    import os
    out = os.path.join(r"C:\projetpfe\report\img\_matplotlib", name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, bbox_inches="tight", pad_inches=0.12, facecolor="white")
    plt.close(fig)
    print("  ecrit %s" % name)
