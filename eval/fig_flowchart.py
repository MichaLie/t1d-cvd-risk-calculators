"""Figure 6 — clinical decision flowchart for CV risk estimation in T1D (Section 9)."""
import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(os.environ.get("FIG_OUT_DIR", "eval/out"))

def save_figure(fig, filename):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / filename
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(filename)

T1D = "#2166ac"; CAUTION = "#b2182b"; ACT = "#1a7f37"; NEUT = "#33486e"; GREY = "#555555"
fig, ax = plt.subplots(figsize=(9.4, 9.4))
ax.set_xlim(0, 12); ax.set_ylim(4.65, 23); ax.axis("off")

def box(x, y, w, h, text, fc, tc="white", fs=10, style="round,pad=0.1"):
    ax.add_patch(FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle=style,
                                linewidth=1.2, edgecolor="white", facecolor=fc, zorder=2))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=tc, zorder=3, wrap=True)

def arrow(x1, y1, x2, y2, label=None, color=GREY):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=16,
                                 lw=1.6, color=color, zorder=1))
    if label:
        ax.text((x1 + x2)/2 + 0.35, (y1 + y2)/2, label, fontsize=8.5, color=color, style="italic", ha="left")

box(5, 22.2, 6.4, 1.0, "Adult with type 1 diabetes\n(cardiovascular risk assessment)", NEUT, fs=11)
arrow(5, 21.7, 5, 21.0)

box(5, 20.2, 8.2, 1.5, "STEP 1 — Confirm T1D and screen for risk-defining features\nTarget-organ damage (albuminuria, ↓eGFR, retinopathy) and established ASCVD", T1D, fs=9.5)
arrow(5, 19.45, 5, 18.8)

# decision diamond
ax.add_patch(plt.Polygon([(5, 18.7), (8.1, 17.5), (5, 16.3), (1.9, 17.5)], closed=True,
                         facecolor=CAUTION, edgecolor="white", lw=1.2, zorder=2))
ax.text(5, 17.5, "Established ASCVD,\nsevere target-organ damage,\nor early-onset T1D >20 yr?", ha="center", va="center", fontsize=9, color="white", zorder=3)
arrow(8.05, 17.5, 9.45, 16.45)
ax.text(8.95, 17.08, "YES", fontsize=9, color=CAUTION, fontweight="bold", va="center")
box(10.6, 15.95, 2.2, 1.15, "Very-high risk:\ntreat intensively", CAUTION, fs=8.7)
arrow(5, 16.3, 5, 15.6, "NO", color=GREY)

box(5, 14.7, 8.6, 1.7, "STEP 2 — Estimate absolute risk with a T1D-SPECIFIC tool\nSteno Type 1 Risk Engine or Scottish–Swedish model (κ 0.83; C ≈ 0.82–0.85)\nLIFE-T1D where lifetime risk / treatment-benefit framing aids shared decisions", T1D, fs=9.5)
arrow(5, 13.85, 5, 13.2)

box(5, 12.3, 8.6, 1.7, "STEP 3 — Interpret, do not transcribe\nAwareness of over-/under-estimation (e.g. Steno over-estimates outside N Europe);\nrecalibrate to local event rates; cross-check ESC/EASD category + ADA targets", NEUT, fs=9.5)
arrow(5, 11.45, 5, 10.8)

box(5, 9.9, 8.6, 1.6, "STEP 4 — Do NOT anchor on generic scores\nGeneric SCORE2/PCE/PREVENT often under-call risk;\nSCORE2/PCE age windows miss many young adults;\nQRISK3 (dedicated T1D term) is a reasonable cross-reference where available", CAUTION, fs=9.0)
arrow(5, 9.15, 5, 8.5)

box(5, 7.5, 8.6, 1.7, "STEP 5 — Translate risk into action\nLipid target LDL <1.8 mmol/L (higher-risk primary) / <1.4 (secondary); BP <130/80;\nstatin discussion (esp. younger patients); adjunct therapy only where T1D guidance supports it", ACT, fs=9.5)

ax.text(5, 6.1, "The estimate informs the conversation; it does not replace it.", ha="center", fontsize=9.5, style="italic", color=GREY)

# legend
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=T1D, label="T1D-specific step"), Patch(color=CAUTION, label="High-risk / caution"),
                   Patch(color=ACT, label="Action"), Patch(color=NEUT, label="Interpretation")],
          loc="lower center", ncol=4, fontsize=8.8, frameon=False, bbox_to_anchor=(0.5, 0.01),
          columnspacing=1.2, handlelength=1.1)
ax.set_title("CV risk estimation workflow in type 1 diabetes", fontsize=12, pad=4)
fig.subplots_adjust(left=0.02, right=0.98, top=0.96, bottom=0.02)
save_figure(fig, "fig_decision_flowchart.png")
