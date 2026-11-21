"""Draw the paper's two result figures (test-set PR-AUC and BSS; mean probability around RI onset).

Run from the repo root:  python src/make_result_figures.py
Writes results/figures/fig_test_scores.pdf and fig_onset.pdf.

Three colours, chosen with the authors: blue, orange and sage. Scores figure: blue = tabular input, orange =
tabular + images (marker fill repeats this: filled = tabular, open = + images). Onset figure: blue = Claude Sonnet 5.5,
orange = GPT-6 Luna, sage = Claude Haiku 5.5. Fig. 1 uses the same blue for its probability bar. XGBoost is
near-black and reference lines are grey and dashed. The trio passes the dataviz colourblind check (all pairs).
"""
import csv
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parent.parent

OUT = ROOT / "results" / "figures"
ANALYSIS = ROOT / "results" / "analysis" / "test"
OUT.mkdir(parents=True, exist_ok=True)

COLORS = {
    "claude-sonnet-5-5": "#2a78d6",   # blue
    "gpt-6-luna": "#ef7d22",          # orange
    "claude-haiku-5-5": "#4fa48b",    # sage
    "gpt-5.6-luna": "#6250d6",        # violet
    "gpt-5-mini": "#008300",          # green
    "gpt-5.4-mini": "#7a5195",        # plum
    "xgboost": "#222222",             # near-black: the trained reference
}
MODE_COLORS = {"tabular": "#2a78d6", "image": "#ef7d22"}                   # {"tabular": hex, "image": hex}: colour the scores figure by input mode instead of by model
NAMES = {"claude-sonnet-5-5": "Claude Sonnet 5.5", "gpt-6-luna": "GPT-6 Luna", "claude-haiku-5-5": "Claude Haiku 5.5",
         "gpt-5.6-luna": "GPT-5.6 Luna", "gpt-5-mini": "GPT-5 mini", "gpt-5.4-mini": "GPT-5.4 mini",
         "xgboost": "XGBoost (trained)"}
ORDER = ["claude-sonnet-5-5", "gpt-6-luna", "claude-haiku-5-5", "gpt-5.6-luna", "gpt-5-mini", "gpt-5.4-mini"]

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "STIXGeneral"],
                     "mathtext.fontset": "stix", "font.size": 9, "axes.linewidth": 0.6,
                     "axes.edgecolor": "#444444", "xtick.color": "#333333", "ytick.color": "#333333",
                     "pdf.fonttype": 42})


def value_ci(cell):
    """'0.820 [0.771, 0.862]' -> (0.820, 0.771, 0.862)."""
    v, lo, hi = map(float, re.findall(r"-?\d+\.\d+", cell))
    return v, lo, hi


def read_scores(mode):
    with open(ANALYSIS / f"ri_test_{mode}_threshold_free.csv") as f:
        return {r["model"]: {"ROC-AUC": value_ci(r["ROC-AUC"]), "BSS": value_ci(r["BSS vs dev climatology"]),
                             "PR-AUC": value_ci(next(v for k, v in r.items() if k.startswith("PR-AUC")))}
                for r in csv.DictReader(f)}


def fig_test_scores():
    tab, img = read_scores("text_only"), read_scores("text_image")
    # Layout of the original figure: filled markers with a white edge (circle = tabular, square = + images),
    # thick interval lines, a three-item legend, and fixed axis ranges.
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 1.95), sharey=True)
    y = np.arange(len(ORDER))[::-1]
    for ax, metric, ref, title, xlim in [
            (axes[0], "PR-AUC", 0.108, "Test PR-AUC (0.108 = chance)", (0.08, 0.6)),
            (axes[1], "BSS", 0.0, "Test Brier skill score (0 = climatology)", (-0.085, 0.25))]:
        for yi, m in zip(y, ORDER):
            for scores, dy, marker, mode in [(tab, 0.19, "o", "tabular"), (img, -0.19, "s", "image")]:
                c = MODE_COLORS[mode] if MODE_COLORS else COLORS[m]
                v, lo, hi = scores[m][metric]
                ax.plot([lo, hi], [yi + dy] * 2, color=c, lw=1.6, solid_capstyle="butt", zorder=2)
                ax.plot(v, yi + dy, marker=marker, ms=4.6, mfc=c, mec="white", mew=0.7, zorder=3)
        ax.axvline(tab["xgboost"][metric][0], color=COLORS["xgboost"], lw=1.3, zorder=1)
        ax.set_xlim(*xlim)
        if xlim[0] <= ref <= xlim[1]:
            ax.axvline(ref, color="#555555", lw=0.8, ls=(0, (3, 2)), zorder=1)
        ax.set_title(title, fontsize=9.5, pad=3)
        ax.grid(axis="x", color="#e6e6e6", lw=0.5, zorder=0)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0].set_xticks([0.1, 0.2, 0.3, 0.4, 0.5, 0.6], ["0.10", "0.20", "0.30", "0.40", "0.50", "0.60"])
    axes[1].set_xticks([-0.05, 0, 0.05, 0.10, 0.15, 0.20, 0.25],
                       ["−0.05", "0.00", "0.05", "0.10", "0.15", "0.20", "0.25"])
    axes[0].set_yticks(y, [NAMES[m] for m in ORDER])
    ct, ci = (MODE_COLORS["tabular"], MODE_COLORS["image"]) if MODE_COLORS else ("#444444", "#444444")
    handles = [Line2D([], [], color=ct, marker="o", mfc=ct, mec="white", lw=1.6, ms=4.6, label="tabular"),
               Line2D([], [], color=ci, marker="s", mfc=ci, mec="white", lw=1.6, ms=4.6, label="tabular + images"),
               Line2D([], [], color=COLORS["xgboost"], lw=1.3, label="XGBoost, trained (tabular)")]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=8.5, bbox_to_anchor=(0.55, -0.03),
               handlelength=2.2, columnspacing=2.0)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(OUT / "fig_test_scores.pdf", bbox_inches="tight")
    plt.close(fig)


def fig_onset():
    composite = json.loads((ANALYSIS / "onset_composite.json").read_text())
    models = ["gpt-6-luna", "claude-sonnet-5-5", "claude-haiku-5-5", "xgboost"]
    markers = {"gpt-6-luna": "s", "claude-sonnet-5-5": "o", "claude-haiku-5-5": "^", "xgboost": "D"}
    fig, ax = plt.subplots(figsize=(3.4, 2.05))
    hours = list(range(-24, 25, 6))
    ends = {}
    for m in models:
        vals = [composite[m][str(h)] for h in hours]
        ax.plot(hours, vals, color=COLORS[m], lw=1.6, marker=markers[m], ms=4, mec="white", mew=0.6, zorder=3)
        ends[m] = vals[-1]
    # end labels, spread apart so neighbours never overlap (top to bottom, at least GAP apart)
    GAP, placed = 0.02, {}
    for m in sorted(ends, key=ends.get, reverse=True):
        y = ends[m] if not placed else min(ends[m], min(placed.values()) - GAP)
        placed[m] = y
        ax.annotate(NAMES[m], (hours[-1], ends[m]), xytext=(hours[-1] + 2.5, y), textcoords="data",
                    va="center", fontsize=7.5, color="#222222")
    ax.axvline(0, color="#555555", lw=0.9, zorder=2)
    ax.text(-0.8, ax.get_ylim()[1], "RI onset", ha="right", va="top", fontsize=7.5, color="#555555")
    ax.set_xticks(hours, [f"{h:d}".replace("-", "−") for h in hours])
    ax.set_xlabel("Hours relative to the first RI-labeled observation")
    ax.set_ylabel("Mean predicted RI probability")
    ax.set_xlim(-26, 40)
    ax.grid(axis="y", color="#e6e6e6", lw=0.5, zorder=0)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "fig_onset.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_test_scores()
    fig_onset()
    print("wrote", OUT / "fig_test_scores.pdf", "and", OUT / "fig_onset.pdf")
