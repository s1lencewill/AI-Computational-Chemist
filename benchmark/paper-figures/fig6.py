# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Figure 6 — head-to-head benchmark comparison, drawn ONLY from
benchmark/evaluations/evaluation-v2-a312cf8b-gpt5.5xhigh/SUMMARY.md and
benchmark/evaluations/evaluation-v2-a312cf8b-fable5/SUMMARY.md (five cases; the AI-KIMI
arm and the Kimi evaluator run are excluded from the manuscript).

Panels:
  a  distribution of per-case weighted totals (0-100) per arm, one box +
     five case points per arm, under each of the two evaluators; the mean is
     direct-labelled (this is also the contrast relief for the aqua series)
  b  per-dimension mean scores (0-10) under the GPT-5.5 evaluator
     (Claude-evaluator values are quoted in the text)
  c  red-flag incidence under the GPT-5.5 evaluator
  d  follow-up delta per case under the GPT-5.5 evaluator
     ("†/identical file" = report-f.docx byte-identical to report.docx)

Categorical palette: dataviz reference palette slots 1/2/4 in fixed order,
validated 2026-07-05 (worst adjacent CVD dE 35.9 on white; the sub-3:1 aqua
is relieved by direct mean labels here and Supplementary Table 3 as the
table view).
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- palette
ARMS = ["HUMAN", "AI-GPT5.5", "AI-GPT5.5-FU"]
COL = {
    "HUMAN": "#2a78d6",        # slot 1 blue
    "AI-GPT5.5": "#1baf7a",    # slot 2 aqua
    "AI-GPT5.5-FU": "#008300", # slot 4 green
}
INK, INK2, MUT = "#0b0b0b", "#52514e", "#898781"
GRID, BASE = "#e1e0d9", "#c3c2b7"
DIV_POS, DIV_NEG = "#2a78d6", "#e34948"  # diverging pair (blue <-> red)

# --------------------------------------------- data from the two SUMMARY §1
# per-case weighted totals, cases 1-5 (AI-KIMI arm omitted from the paper)
TOTALS = {
    # evaluation-v2-a312cf8b-gpt5.5xhigh/SUMMARY.md, Score Matrix
    "GPT-5.5 evaluator": {
        "HUMAN":        [65.5, 45.8, 66.5, 50.5, 45.0],
        "AI-GPT5.5":    [65.8, 66.5, 53.5, 74.8, 66.8],
        "AI-GPT5.5-FU": [77.0, 74.3, 60.8, 74.8, 74.0],
    },
    # evaluation-v2-a312cf8b-fable5/SUMMARY.md §1
    "Claude evaluator": {
        "HUMAN":        [82.0, 70.0, 82.0, 65.0, 63.8],
        "AI-GPT5.5":    [54.8, 79.5, 58.5, 67.3, 64.0],
        "AI-GPT5.5-FU": [65.8, 81.5, 68.5, 67.3, 65.8],
    },
}
EVALS = list(TOTALS)  # GPT-5.5 evaluator first (mainly discussed)

# ------------------------- data from gpt5.5xhigh SUMMARY, per-dimension table
DIMS = [
    "D1 Responsiveness",
    "D2 Coverage",
    "D3 Methods",
    "D4 Execution",
    "D5 Correctness",
    "D6 Transparency",
]
DIM_MEANS = {
    "HUMAN":        [6.7, 6.0, 5.1, 4.3, 5.5, 3.8],
    "AI-GPT5.5":    [5.9, 5.2, 6.3, 7.5, 6.9, 8.4],
    "AI-GPT5.5-FU": [7.2, 6.7, 6.7, 7.7, 7.1, 8.3],
}

# ---------------------------- data from gpt5.5xhigh SUMMARY, red-flag table
FLAGS = [
    "1 Wrong question",
    "2 Selective reporting",
    "3 Undocumented results",
    "4 Misreading sources",
    "5 Overinterpretation",
    "6 Anomalous magnitudes",
    "7 Insufficient statistics",
]
FLAG_COUNTS = {
    "HUMAN":        [1, 1, 5, 0, 5, 1, 5],
    "AI-GPT5.5":    [3, 0, 0, 1, 1, 1, 3],
    "AI-GPT5.5-FU": [1, 0, 0, 1, 0, 2, 3],
}
N_ARM = {a: 5 for a in ARMS}

# ------------------------------- data from gpt5.5xhigh SUMMARY, Delta table
# deltas: case1 65.8->77.0, case2 66.5->74.3, case3 53.5->60.8,
# case5 66.8->74.0; case4 byte-identical files (null delta by construction)
FU_CASES = [1, 2, 3, 4, 5]
FU_DELTA = {1: 11.2, 2: 7.8, 3: 7.3, 4: 0.0, 5: 7.2}
BYTE_IDENTICAL_FU = {4}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.size": 10.5,
    "text.color": INK,
    "axes.edgecolor": BASE,
    "axes.labelcolor": INK2,
    "axes.linewidth": 0.9,
    "xtick.color": MUT,
    "ytick.color": MUT,
    "xtick.labelcolor": INK2,
    "ytick.labelcolor": INK2,
    "svg.fonttype": "none",
})


def style(ax, grid_axis="y"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)


def panel_letter(ax, letter, dx=-0.06, dy=1.06):
    ax.text(dx, dy, letter, transform=ax.transAxes, fontsize=17,
            fontweight="bold", va="top", ha="left", color=INK)


fig = plt.figure(figsize=(12.8, 7.8))
gs = fig.add_gridspec(2, 3, height_ratios=[1.06, 1.0],
                      left=0.105, right=0.985, top=0.90, bottom=0.075,
                      hspace=0.56, wspace=0.42)

# ================================================================ panel a
ax = fig.add_subplot(gs[0, :])
panel_letter(ax, "a", dx=-0.045)
JIT = [-0.16, -0.08, 0.0, 0.08, 0.16]  # deterministic per-case jitter
pos0 = {EVALS[0]: 0.0, EVALS[1]: 4.0}
for ev in EVALS:
    for i, arm in enumerate(ARMS):
        x = pos0[ev] + i
        vals = TOTALS[ev][arm]
        bp = ax.boxplot([vals], positions=[x], widths=0.62,
                        patch_artist=True, showfliers=False,
                        medianprops=dict(color=COL[arm], lw=1.6),
                        whiskerprops=dict(color=BASE, lw=1.0),
                        capprops=dict(color=BASE, lw=1.0))
        bp["boxes"][0].set(facecolor=COL[arm], alpha=0.14,
                           edgecolor=COL[arm], lw=1.2)
        for j, v in enumerate(vals):
            ax.plot(x + JIT[j], v, "o", ms=7.5, color=COL[arm],
                    markeredgecolor="white", markeredgewidth=1.3, zorder=4)
        m = float(np.mean(vals))
        ax.plot(x, m, marker="_", ms=24, mew=2.4, color=INK, zorder=5)
        ax.text(x + 0.40, m, f"{m:.1f}", va="center", ha="left",
                fontsize=9.5, color=INK2)
ax.set_xlim(-0.8, 6.9)
ax.set_ylim(35, 92)
ax.set_yticks(range(40, 91, 10))
ax.set_ylabel("Weighted total (0–100)")
ax.set_xticks([0, 1, 2, 4, 5, 6],
              ["HUMAN", "GPT5.5", "FU"] * 2, fontsize=9.5)
for ev in EVALS:
    ax.text(pos0[ev] + 1.0, -0.15, ev, transform=ax.get_xaxis_transform(),
            ha="center", va="top", fontsize=10.5, color=INK)
ax.axvline(3.0, color=GRID, lw=0.9)
ax.set_title("Per-arm score distributions over the five cases "
             "(box = quartiles, dash = mean, dots = cases)",
             loc="left", fontsize=11.5, color=INK2, pad=10)
style(ax)
handles = [plt.Rectangle((0, 0), 1, 1, color=COL[a]) for a in ARMS]
labels = [f"{a} (n=5)" for a in ARMS]
ax.legend(handles, labels, ncols=3, frameon=False, loc="lower left",
          bbox_to_anchor=(0.0, 1.10), fontsize=9.5, handlelength=1.2,
          handleheight=1.0, columnspacing=1.4)

# ================================================================ panel b
ax = fig.add_subplot(gs[1, 0])
panel_letter(ax, "b", dx=-0.34)
ypos = np.arange(len(DIMS))[::-1]
dodge = {a: d for a, d in zip(ARMS, (0.16, 0.0, -0.16))}
for yi, di in zip(ypos, range(len(DIMS))):
    ax.plot([0, 10], [yi, yi], color=GRID, lw=0.8, zorder=1)
    for arm in ARMS:
        ax.plot(DIM_MEANS[arm][di], yi + dodge[arm], "o", ms=7,
                color=COL[arm], markeredgecolor="white",
                markeredgewidth=1.2, zorder=3)
ax.set_yticks(ypos, DIMS, fontsize=9)
ax.set_xlim(0, 10)
ax.set_ylim(-0.55, len(DIMS) - 0.45)
ax.set_xticks(range(0, 11, 2))
ax.set_xlabel("Mean dimension score (0–10)")
ax.set_title("Per-dimension means\n(GPT-5.5 evaluator)", loc="left",
             fontsize=11.5, color=INK2, pad=8)
style(ax, grid_axis="x")

# ================================================================ panel c
ax = fig.add_subplot(gs[1, 1])
panel_letter(ax, "c", dx=-0.42)
frac = np.array([[FLAG_COUNTS[a][f] / N_ARM[a] for a in ARMS]
                 for f in range(len(FLAGS))])
cmap = LinearSegmentedColormap.from_list(
    "blues", ["#ffffff", "#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6",
              "#1c5cab", "#0d366b"])
im = ax.imshow(frac, cmap=cmap, vmin=0, vmax=1, aspect="auto")
for f in range(len(FLAGS)):
    for a_i, arm in enumerate(ARMS):
        cnt = FLAG_COUNTS[arm][f]
        ax.text(a_i, f, str(cnt), ha="center", va="center", fontsize=9,
                color="white" if frac[f, a_i] > 0.55 else INK)
ax.set_xticks(range(len(ARMS)),
              ["HUMAN\n(n=5)", "GPT5.5\n(n=5)", "FU\n(n=5)"],
              fontsize=8.5)
ax.set_yticks(range(len(FLAGS)), [f[2:] for f in FLAGS], fontsize=9)
ax.tick_params(length=0)
for side in ("top", "right", "left", "bottom"):
    ax.spines[side].set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
cb.ax.tick_params(labelsize=8, color=MUT, labelcolor=INK2)
cb.outline.set_visible(False)
cb.set_label("Fraction of evaluated cases", fontsize=8.5, color=INK2)
ax.set_title("Red-flag incidence\n(GPT-5.5 evaluator)", loc="left",
             fontsize=11.5, color=INK2, pad=8)

# ================================================================ panel d
ax = fig.add_subplot(gs[1, 2])
panel_letter(ax, "d", dx=-0.30)
ypos = np.arange(len(FU_CASES))[::-1]
for yi, c in zip(ypos, FU_CASES):
    d = FU_DELTA[c]
    if c in BYTE_IDENTICAL_FU:
        ax.text(0.35, yi, "0  (identical file)", va="center", fontsize=9,
                color=MUT)
    else:
        ax.barh(yi, d, height=0.5, color=DIV_POS if d > 0 else DIV_NEG)
        ax.text(d + (0.35 if d > 0 else -0.35), yi, f"{d:+.1f}",
                va="center", ha="left" if d > 0 else "right", fontsize=9.5,
                color=INK2)
ax.axvline(0, color=BASE, lw=0.9)
ax.set_yticks(ypos, [f"Case {c}" for c in FU_CASES], fontsize=9.5)
ax.set_xlim(-2.5, 13.5)
ax.set_xlabel("Δ weighted total (follow-up − autonomous)")
ax.set_title("What human follow-up bought\n(GPT-5.5 evaluator)", loc="left",
             fontsize=11.5, color=INK2, pad=8)
style(ax, grid_axis="x")

out = HERE / "fig6.png"
fig.savefig(out, dpi=300, facecolor="white")
print(f"wrote {out}")
