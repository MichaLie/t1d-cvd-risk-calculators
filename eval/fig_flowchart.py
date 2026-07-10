"""Figure 6 — concise clinical workflow for CV risk estimation in T1D."""
import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Patch

DEFAULT_OUT = Path(__file__).resolve().parent / "out"
OUT = Path(os.environ.get("FIG_OUT_DIR", str(DEFAULT_OUT)))

def save_figure(fig, filename):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / filename
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(filename)

T1D = "#2166ac"; CAUTION = "#b2182b"; ACT = "#1a7f37"; NEUT = "#33486e"; GREY = "#555555"
fig, ax = plt.subplots(figsize=(8.2, 7.4))
ax.set_xlim(0, 10); ax.set_ylim(0, 12); ax.axis("off")

def box(x, y, w, h, text, fc, tc="white", fs=10, style="round,pad=0.1"):
    ax.add_patch(FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle=style,
                                linewidth=1.2, edgecolor="white", facecolor=fc, zorder=2))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=tc, zorder=3, wrap=True)

def arrow(x1, y1, x2, y2, color=GREY):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=16,
                                 lw=1.6, color=color, zorder=1))

box(5, 10.8, 8.6, 1.35, "1  Identify risk-defining disease\nEstablished ASCVD or severe target-organ damage may make formal scoring unnecessary", CAUTION, fs=10)
arrow(5, 10.1, 5, 9.35)
box(5, 8.6, 8.6, 1.35, "2  Prefer a T1D-specific estimate when scoring may help\nScottish–Swedish or Steno; consider LIFE-T1D for lifetime-risk framing", T1D, fs=10)
arrow(5, 7.9, 5, 7.15)
box(5, 6.4, 8.6, 1.45, "3  Interpret the estimate in context\nCheck endpoint, horizon, age eligibility, organ damage, and population calibration\nQRISK3 may serve as a cross-reference where appropriate", NEUT, fs=9.6)
arrow(5, 5.65, 5, 4.9)
box(5, 4.15, 8.6, 1.4, "4  Translate risk into guideline-led prevention\nUse shared decision-making; the estimate informs treatment but does not dictate it", ACT, fs=10)

ax.text(5, 2.85, "Generic scores that do not distinguish T1D should not be the primary estimate.",
        ha="center", fontsize=9.5, style="italic", color=GREY)
ax.legend(handles=[Patch(color=CAUTION, label="Risk-defining disease"), Patch(color=T1D, label="T1D-specific estimate"),
                   Patch(color=NEUT, label="Interpretation"), Patch(color=ACT, label="Action")],
          loc="lower center", ncol=2, fontsize=8.6, frameon=False, bbox_to_anchor=(0.5, 0.08),
          columnspacing=1.8, handlelength=1.3)
ax.set_title("Pragmatic cardiovascular risk estimation in type 1 diabetes", fontsize=12, pad=4)
fig.subplots_adjust(left=0.03, right=0.97, top=0.95, bottom=0.04)
save_figure(fig, "fig_decision_flowchart.png")
