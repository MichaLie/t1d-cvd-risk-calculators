"""Manuscript figures (publication-style) for the T1D CV-calculator review."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from eval.harness.profiles import make_synthetic_cohort
from eval.harness.models import REGISTRY, validated_models

OUT = "eval/out/"
T1D_C = "#2166ac"; T2D_C = "#b2182b"; GEN_C = "#7f7f7f"
CTYPE = {"T1D": T1D_C, "T2D": T2D_C, "general": GEN_C}

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
    M = np.array([[1 if x.strip() == "1" else 0 for x in v.split(",")] for v in models.values()])
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.imshow(M, cmap=matplotlib.colors.ListedColormap(["#f3f3f3", "#2166ac"]), aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(preds))); ax.set_xticklabels(preds, rotation=55, ha="right", fontsize=8)
    ax.set_yticks(range(len(names))); ax.set_yticklabels(names, fontsize=8.5)
    for i in range(len(names) + 1): ax.axhline(i - 0.5, color="white", lw=1)
    for j in range(len(preds) + 1): ax.axvline(j - 0.5, color="white", lw=1)
    ax.axhline(4.5, color="black", lw=2)  # T1D | candidate separator
    ax.text(-3.4, 2, "T1D-specific", rotation=90, va="center", fontsize=9, fontweight="bold", color=T1D_C)
    ax.text(-3.4, 9.5, "candidate T2D / general", rotation=90, va="center", fontsize=9, fontweight="bold", color=T2D_C)
    ax.set_title("Predictors used by each cardiovascular risk calculator", fontsize=12, pad=10)
    fig.text(0.5, 0.005, "Filled = predictor used. T1D-specific tools capture renal (eGFR, albuminuria), retinopathy and duration/onset; "
             "generic tools rely on conventional factors only.", ha="center", fontsize=7.5, style="italic")
    plt.tight_layout(rect=[0.04, 0.03, 1, 1]); plt.savefig(OUT + "fig_predictor_grid.png", dpi=170, bbox_inches="tight"); plt.close()
    print("fig_predictor_grid.png")

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
    for name, yr, n, typ, hz in M:
        y = lanes[typ] + (hash(name) % 5 - 2) * 0.06
        ax.scatter(yr, y, s=60 + 38 * np.log10(n), color=CTYPE[typ], alpha=0.75, edgecolor="white", zorder=3)
        ax.annotate(f"{name}\n({hz})", (yr, y), fontsize=7, ha="center",
                    va="bottom" if (hash(name) % 2) else "top",
                    xytext=(0, 10 if (hash(name) % 2) else -16), textcoords="offset points")
    ax.set_yticks([0, 1, 2]); ax.set_yticklabels(["General population", "Type 2 diabetes", "Type 1 diabetes"], fontsize=10)
    ax.set_xlim(2000, 2027); ax.set_ylim(-0.6, 2.6); ax.set_xlabel("Year of publication", fontsize=10)
    ax.set_title("Landscape of cardiovascular risk models relevant to type 1 diabetes\n(bubble area ∝ log derivation cohort size)", fontsize=12)
    for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout(); plt.savefig(OUT + "fig_model_timeline.png", dpi=170, bbox_inches="tight"); plt.close()
    print("fig_model_timeline.png")

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
    fig, ax = plt.subplots(figsize=(8.5, 6))
    ys = range(len(rows))[::-1]
    for y, (name, c, lo, hi, typ) in zip(ys, rows):
        pooled = "Pooled" in name
        ax.plot([lo, hi], [y, y], color=CTYPE[typ], lw=2.2 if pooled else 1.4, alpha=0.9)
        ax.scatter(c, y, marker="D" if pooled else "o", s=90 if pooled else 55, color=CTYPE[typ],
                   edgecolor="black", zorder=3, linewidth=0.6)
        ax.text(0.655, y, name, fontsize=8.5, va="center", ha="left", fontweight="bold" if pooled else "normal")
    ax.axvline(0.81, color=T1D_C, ls="--", lw=0.8, alpha=0.6); ax.axvline(0.75, color=GEN_C, ls="--", lw=0.8, alpha=0.6)
    ax.set_xlim(0.65, 0.90); ax.set_yticks([]); ax.set_xlabel("C-statistic (discrimination) in type 1 diabetes", fontsize=10)
    ax.set_title("Discrimination of CV risk models in type 1 diabetes\n(T1D-specific vs general/T2D; pooled estimates from Erqou 2025)", fontsize=11.5)
    ax.legend(handles=[Patch(color=T1D_C, label="T1D-specific"), Patch(color=T2D_C, label="T2D"),
                       Patch(color=GEN_C, label="General")], loc="lower right", fontsize=8.5, frameon=False)
    for sp in ["top", "right", "left"]: ax.spines[sp].set_visible(False)
    fig.text(0.5, 0.005, "Values compiled from primary derivation/validation papers and the Erqou 2025 meta-analysis; ranges approximate.",
             ha="center", fontsize=7, style="italic")
    plt.tight_layout(rect=[0, 0.02, 1, 1]); plt.savefig(OUT + "fig_cstat_forest.png", dpi=170, bbox_inches="tight"); plt.close()
    print("fig_cstat_forest.png")

# ---------------------------------------------------------------- Figure: per-tool 10-yr risk distribution
def risk_distributions():
    cohort = make_synthetic_cohort(10000)
    models = validated_models()
    data, colors, labels = [], [], []
    for m in models:
        r = np.array([REGISTRY[m][2](p) for p in cohort], float)
        r = r[np.isfinite(r)]
        data.append(r); colors.append(CTYPE[REGISTRY[m][0]]); labels.append(m)
    order = np.argsort([np.median(d) for d in data])
    data = [data[i] for i in order]; colors = [colors[i] for i in order]; labels = [labels[i] for i in order]
    fig, ax = plt.subplots(figsize=(10, 6))
    bp = ax.boxplot(data, vert=False, patch_artist=True, showfliers=False, widths=0.6)
    for patch, c in zip(bp["boxes"], colors): patch.set_facecolor(c); patch.set_alpha(0.7)
    for med in bp["medians"]: med.set_color("black")
    ax.set_yticklabels(labels, fontsize=9)
    ax.axvline(10, color="green", ls="--", lw=0.8, alpha=0.6); ax.axvline(20, color="orange", ls="--", lw=0.8, alpha=0.6)
    ax.set_xlabel("Predicted 10-year CVD risk (%) on the same synthetic T1D cohort", fontsize=10)
    ax.set_title("Same patients, different answers: predicted-risk distributions by calculator\n(dashed lines = 10% and 20% treatment thresholds)", fontsize=11.5)
    ax.legend(handles=[Patch(color=T1D_C, label="T1D-specific"), Patch(color=T2D_C, label="T2D"),
                       Patch(color=GEN_C, label="General")], loc="lower right", fontsize=8.5, frameon=False)
    for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    ax.set_xlim(0, 70)
    plt.tight_layout(); plt.savefig(OUT + "fig_risk_distributions.png", dpi=170, bbox_inches="tight"); plt.close()
    print("fig_risk_distributions.png")


if __name__ == "__main__":
    predictor_grid(); timeline(); cstat_forest(); risk_distributions()
    print("all manuscript figures written to", OUT)
