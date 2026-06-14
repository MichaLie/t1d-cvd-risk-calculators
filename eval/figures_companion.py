"""Companion-paper figures for the T1D CV-calculator review."""
import os
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

if __package__ in (None, ""):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eval.harness.profiles import make_synthetic_cohort
from eval.harness.models import REGISTRY, analysis_models

OUT = Path(os.environ.get("FIG_OUT_DIR", "eval/out"))
T1D_C = "#2166ac"; T2D_C = "#b2182b"; GEN_C = "#7f7f7f"
CTYPE = {"T1D": T1D_C, "T2D": T2D_C, "general": GEN_C}

def save_figure(fig, filename):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / filename
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(filename)

def bubble_size(n):
    return 60 + 38 * np.log10(n)

# ---------------------------------------------------------------- Figure: predictor heat-grid
def predictor_grid():
    preds = ["Age", "Sex", "Diabetes duration", "Age at onset/dx", "HbA1c",
             "Mean/long-term HbA1c", "Systolic BP", "Lipids (TC/HDL/LDL)", "eGFR",
             "Albuminuria", "Retinopathy", "Smoking", "BMI/anthropometry",
             "Treated hypertension", "Lipid-lowering Rx", "Atrial fibrillation",
             "Prior CVD", "Deprivation", "Ethnicity", "Exercise"]
    # 1 = predictor used by the model
    models = {
        # T1D-specific
        "Cederholm 2011 (T1D)":      "Age?,_,1,1,1,_,1,1,_,1,_,1,_,_,_,_,1,_,_,_",
        "Steno 2016 (T1D)":          "1,1,1,_,1,_,1,1,1,1,_,1,_,_,_,_,_,_,_,1",
        "EURODIAB 2014 (T1D)":       "1,_,_,_,1,_,_,1,_,1,_,_,1,_,_,_,_,_,_,_",
        "Scottish–Swedish 2021 (T1D)":"1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,_,1,_,_",
        "LIFE-T1D 2024 (T1D)":       "_,1,_,1,_,_,1,1,1,1,1,1,1,_,_,_,_,_,_,_",
        # candidate T2D / general
        "SCORE2-Diabetes 2023 (T2D)":"1,1,_,1,1,_,1,1,1,_,_,1,_,_,_,_,_,_,_,_",
        "DIAL 2019 (T2D)":           "1,1,1,_,1,_,1,1,1,1,_,1,1,_,_,_,1,_,_,_",
        "ADVANCE 2011 (T2D)":        "_,1,1,1,1,_,1,1,_,1,1,_,_,1,_,1,_,_,_,_",
        "UKPDS (T2D)":               "1,1,1,_,1,_,1,1,_,_,_,1,_,_,_,1,_,_,1,_",
        "SCORE2 2021 (gen.)":        "1,1,_,_,_,_,1,1,_,_,_,1,_,_,_,_,_,_,_,_",
        "PCE 2013 (gen.)":           "1,1,_,_,_,_,1,1,_,_,_,1,_,1,_,_,_,_,1,_",
        "PREVENT 2024 (gen.)":       "1,1,_,_,_,_,1,1,1,_,_,1,1,1,1,_,_,_,_,_",
        "QRISK3 2017 (gen.)":        "1,1,_,_,_,_,1,1,1,_,_,1,1,1,_,1,_,1,1,_",
        "Framingham 2008 (gen.)":    "1,1,_,_,_,_,1,1,_,_,_,1,_,_,_,_,_,_,_,_",
    }
    names = list(models)
    tokens = [[x.strip() for x in v.split(",")] for v in models.values()]
    M = np.array([[0.5 if "?" in x else 1 if x == "1" else 0 for x in row] for row in tokens])
    fig, ax = plt.subplots(figsize=(11.8, 7.2))
    cmap = matplotlib.colors.ListedColormap(["#f3f3f3", "#9ecae1", "#2166ac"])
    norm = matplotlib.colors.BoundaryNorm([-0.1, 0.25, 0.75, 1.1], cmap.N)
    ax.imshow(M, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(range(len(preds))); ax.set_xticklabels(preds, rotation=55, ha="right", fontsize=8)
    ax.set_yticks(range(len(names))); ax.set_yticklabels(names, fontsize=8.5)
    for i in range(len(names) + 1): ax.axhline(i - 0.5, color="white", lw=1)
    for j in range(len(preds) + 1): ax.axvline(j - 0.5, color="white", lw=1)
    ax.axhline(4.5, color="black", lw=2)  # T1D | candidate separator
    ax.set_xlim(-2.25, len(preds) - 0.5)
    ax.axvline(-0.5, color="#d9d9d9", lw=1.2)

    def group_bracket(y0, y1, label, color):
        x = -1.25
        ax.plot([x, x], [y0 - 0.38, y1 + 0.38], color=color, lw=1.5, clip_on=False)
        ax.plot([x, -0.65], [y0 - 0.38, y0 - 0.38], color=color, lw=1.5, clip_on=False)
        ax.plot([x, -0.65], [y1 + 0.38, y1 + 0.38], color=color, lw=1.5, clip_on=False)
        ax.text(-1.73, (y0 + y1) / 2, label, rotation=90, va="center", ha="center",
                fontsize=9, fontweight="bold", color=color)

    group_bracket(0, 4, "T1D-specific", T1D_C)
    group_bracket(5, len(names) - 1, "candidate T2D / general", T2D_C)
    for i, j in np.argwhere(M == 0.5):
        ax.text(j, i, "?", ha="center", va="center", fontsize=9, fontweight="bold", color="#1f1f1f")
    ax.set_title("Predictors used by each cardiovascular risk calculator", fontsize=12, pad=10)
    fig.text(0.5, 0.005, "Filled = predictor used; ? = uncertain/ambiguous encoding in the source description. T1D-specific tools capture renal (eGFR, albuminuria), retinopathy and duration/onset; "
             "generic tools rely on conventional factors only.", ha="center", fontsize=7.5, style="italic")
    fig.tight_layout(rect=[0.03, 0.03, 1, 1])
    save_figure(fig, "fig_predictor_grid.png")

# ---------------------------------------------------------------- Figure: model timeline
def timeline():
    # (name, year, cohort_n, type, horizon)
    M = [("Pittsburgh EDC", 2006, 600, "T1D", "10y"), ("Cederholm NDR", 2011, 3661, "T1D", "5y"),
         ("EURODIAB", 2014, 2329, "T1D", "7y"), ("Steno T1", 2016, 4306, "T1D", "5/10y"),
         ("Scottish–Swedish", 2021, 27527, "T1D", "10y"), ("LIFE-T1D", 2024, 30000, "T1D", "10y/life"),
         ("UKPDS", 2001, 4540, "T2D", "—"), ("ADVANCE", 2011, 7168, "T2D", "4y"),
         ("DIAL", 2019, 389366, "T2D", "10y/life"), ("SCORE2-Diabetes", 2023, 229460, "T2D", "10y"),
         ("Framingham gen.", 2008, 8491, "general", "10y"), ("PCE", 2013, 24626, "general", "10y"),
         ("QRISK3", 2017, 7800000, "general", "10y"), ("SCORE2", 2021, 677684, "general", "10y"),
         ("PREVENT", 2024, 6612004, "general", "10/30y")]
    fig, ax = plt.subplots(figsize=(12, 5.5))
    lanes = {"T1D": 2, "T2D": 1, "general": 0}
    label_layout = {
        "Pittsburgh EDC": (0.04, 0, 10),
        "Cederholm NDR": (0.10, 0, -18),
        "EURODIAB": (-0.09, 0, 10),
        "Steno T1": (0.07, 0, -18),
        "Scottish–Swedish": (-0.06, -8, 11),
        "LIFE-T1D": (0.10, 12, -18),
        "UKPDS": (-0.07, 0, -18),
        "ADVANCE": (0.07, 0, 10),
        "DIAL": (-0.08, 0, -18),
        "SCORE2-Diabetes": (0.08, 0, 10),
        "Framingham gen.": (0.05, 0, 10),
        "PCE": (-0.08, 0, -18),
        "QRISK3": (0.07, 0, 10),
        "SCORE2": (-0.08, -4, -18),
        "PREVENT": (0.09, 10, 10),
    }
    for name, yr, n, typ, hz in M:
        y_jitter, x_offset, y_offset = label_layout[name]
        y = lanes[typ] + y_jitter
        ax.scatter(yr, y, s=bubble_size(n), color=CTYPE[typ], alpha=0.75, edgecolor="white", zorder=3)
        ax.annotate(f"{name}\n({hz})", (yr, y), fontsize=7, ha="center",
                    va="bottom" if y_offset > 0 else "top",
                    xytext=(x_offset, y_offset), textcoords="offset points")
    ax.set_yticks([0, 1, 2]); ax.set_yticklabels(["General population", "Type 2 diabetes", "Type 1 diabetes"], fontsize=10)
    ax.set_xlim(2000, 2027); ax.set_ylim(-0.6, 2.6); ax.set_xlabel("Year of publication", fontsize=10)
    ax.set_title("Landscape of cardiovascular risk models relevant to type 1 diabetes", fontsize=12)
    size_handles = [
        Line2D([0], [0], marker="o", linestyle="", markerfacecolor="#d9d9d9", markeredgecolor="#666666",
               markersize=np.sqrt(bubble_size(n)), label=label)
        for n, label in [(1_000, "1k"), (100_000, "100k"), (10_000_000, "10M")]
    ]
    ax.legend(handles=size_handles, title="Derivation cohort n", loc="lower left",
              bbox_to_anchor=(0.01, 0.02), fontsize=7.5, title_fontsize=8, frameon=False,
              handletextpad=1.2, borderpad=0.2)
    for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    save_figure(fig, "fig_model_timeline.png")

# ---------------------------------------------------------------- Figure: C-statistic forest plot
def cstat_forest():
    # (model, C_point, lo, hi, type) — compiled from primary papers + Erqou 2025 meta-analysis (approximate)
    rows = [("Cederholm 2011", 0.815, 0.80, 0.83, "T1D"), ("Steno 2016", 0.815, 0.80, 0.83, "T1D"),
            ("Pittsburgh EDC", 0.785, 0.77, 0.80, "T1D"), ("EURODIAB 2014", 0.775, 0.77, 0.78, "T1D"),
            ("Scottish–Swedish 2021", 0.835, 0.82, 0.85, "T1D"), ("LIFE-T1D 2024", 0.77, 0.73, 0.85, "T1D"),
            ("Pooled T1D-specific (Erqou)", 0.81, 0.78, 0.84, "T1D"),
            ("SCORE2 in T1D", 0.74, 0.67, 0.81, "general"), ("PCE in T1D", 0.755, 0.73, 0.78, "general"),
            ("QRISK3 in T1D", 0.755, 0.73, 0.78, "general"), ("UKPDS in T1D", 0.72, 0.68, 0.76, "T2D"),
            ("Pooled general/T2D (Erqou)", 0.75, 0.72, 0.78, "general")]
    fig, ax = plt.subplots(figsize=(8.8, 6))
    ys = list(range(len(rows))[::-1])
    for y, (name, c, lo, hi, typ) in zip(ys, rows):
        pooled = "Pooled" in name
        ax.plot([lo, hi], [y, y], color=CTYPE[typ], lw=2.2 if pooled else 1.4, alpha=0.9)
        ax.scatter(c, y, marker="D" if pooled else "o", s=90 if pooled else 55, color=CTYPE[typ],
                   edgecolor="black", zorder=3, linewidth=0.6)
    ax.axvline(0.81, color=T1D_C, ls="--", lw=0.8, alpha=0.6); ax.axvline(0.75, color=GEN_C, ls="--", lw=0.8, alpha=0.6)
    ax.set_xlim(0.65, 0.90)
    ax.set_ylim(-0.75, len(rows) - 0.25)
    ax.set_yticks(ys); ax.set_yticklabels([r[0] for r in rows], fontsize=8.5)
    for tick, row in zip(ax.get_yticklabels(), rows):
        if "Pooled" in row[0]:
            tick.set_fontweight("bold")
    ax.tick_params(axis="y", length=0, pad=6)
    ax.set_xlabel("C-statistic (discrimination) in type 1 diabetes", fontsize=10)
    ax.set_title("Discrimination of CV risk models in type 1 diabetes\n(T1D-specific vs general/T2D; pooled estimates from Erqou 2025)", fontsize=11.5)
    ax.legend(handles=[Patch(color=T1D_C, label="T1D-specific"), Patch(color=T2D_C, label="T2D"),
                       Patch(color=GEN_C, label="General")], loc="lower right", fontsize=8.5, frameon=False)
    for sp in ["top", "right", "left"]: ax.spines[sp].set_visible(False)
    fig.text(0.5, 0.005, "Values compiled from primary derivation/validation papers and the Erqou 2025 meta-analysis; ranges approximate.",
             ha="center", fontsize=7, style="italic")
    fig.tight_layout(rect=[0, 0.02, 1, 1])
    save_figure(fig, "fig_cstat_forest.png")

# ---------------------------------------------------------------- Figure: per-tool 10-yr risk distribution
def risk_distributions():
    cohort = make_synthetic_cohort(10000)
    models = analysis_models()
    data, colors, labels = [], [], []
    ukpds_stats = None
    for m in models:
        r = np.array([REGISTRY[m][2](p) for p in cohort], float)
        r = r[np.isfinite(r)]
        if m == "UKPDS-CVD":
            ukpds_stats = (float(np.median(r)), float(np.mean(r)))
            continue
        data.append(r); colors.append(CTYPE[REGISTRY[m][0]]); labels.append(m)
    order = np.argsort([np.median(d) for d in data])
    data = [data[i] for i in order]; colors = [colors[i] for i in order]; labels = [labels[i] for i in order]
    fig, ax = plt.subplots(figsize=(10, 6))
    bp = ax.boxplot(data, vert=False, patch_artist=True, showfliers=False, widths=0.6)
    for patch, c in zip(bp["boxes"], colors): patch.set_facecolor(c); patch.set_alpha(0.7)
    for med in bp["medians"]: med.set_color("black")
    ax.set_yticklabels(labels, fontsize=9)
    threshold_specs = [(10, "10% threshold", "green", "--"), (20, "20% threshold", "orange", "-.")]
    for x, label, color, ls in threshold_specs:
        ax.axvline(x, color=color, ls=ls, lw=1.0, alpha=0.75)
        ax.text(x + 1.0, len(data) + 0.45, label, color=color, fontsize=8, va="center", ha="left")
    ax.set_xlabel("Predicted 10-year CVD risk (%) on the same synthetic T1D cohort", fontsize=10)
    ax.set_title("Same patients, different answers: predicted-risk distributions by calculator\n(main axis excludes the structurally implausible UKPDS outlier)", fontsize=11.5)
    if ukpds_stats:
        ax.text(0.995, 0.08,
                f"UKPDS-CVD treated as outlier: median {ukpds_stats[0]:.0f}%, mean {ukpds_stats[1]:.0f}%\n"
                "from extrapolating a newly diagnosed T2D duration term",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=8,
                color="#7a1f2c",
                bbox=dict(boxstyle="round,pad=0.35", facecolor="#fff4f1", edgecolor="#d6a0a7", linewidth=0.8))
    # Figure 5 is read primarily by row labels; omitting a legend keeps the
    # UKPDS outlier note from competing with the main distribution panel.
    for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    ax.set_xlim(0, 40)
    ax.set_ylim(0.5, len(data) + 0.7)
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    save_figure(fig, "fig_risk_distributions.png")


if __name__ == "__main__":
    predictor_grid(); timeline(); cstat_forest(); risk_distributions()
    print("all companion figures written to", OUT)
