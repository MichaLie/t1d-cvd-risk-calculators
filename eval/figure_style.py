"""Shared publication figure styling and lossless export, without embedded captions."""
import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "eval" / "out"
OUT = Path(os.environ.get("FIG_OUT_DIR", str(DEFAULT_OUT)))
NAMES = {
    "fig_model_timeline": "Figure_1_model_timeline",
    "fig_predictor_grid": "Figure_2_predictor_grid",
    "fig_cstat_forest": "Figure_3_discrimination",
    "kappa_heatmap": "Figure_4_agreement",
    "fig_risk_distributions": "Figure_5_risk_distributions",
    "fig_decision_flowchart": "Figure_6_clinical_workflow",
}
WIDTH = 170 / 25.4
T1D_C = "#2166ac"
T2D_C = "#b35806"
GEN_C = "#606060"
CTYPE = {"T1D": T1D_C, "T2D": T2D_C, "general": GEN_C}
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8,
    "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "axes.linewidth": 0.6, "lines.linewidth": 0.8,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
    "savefig.facecolor": "white", "svg.hashsalt": "t1d-cvd-figures",
})

def save_figure(fig, filename):
    """170-mm-wide canvas; submission mode also writes vector PDF."""
    if any(ax.get_title() for ax in fig.axes) or fig._suptitle is not None:
        raise ValueError("Figure titles belong in FIGURE_LEGENDS.md")
    OUT.mkdir(parents=True, exist_ok=True)
    stem = Path(filename).stem
    submission = os.environ.get("FIG_SUBMISSION") == "1"
    name = NAMES[stem] if submission else stem
    formats = ("pdf", "png") if submission else ("png",)
    for fmt in formats:
        metadata = {"CreationDate": None, "ModDate": None} if fmt == "pdf" else ({"Date": None} if fmt == "svg" else None)
        fig.savefig(OUT / f"{name}.{fmt}", dpi=600, metadata=metadata)
    plt.close(fig)
    print(name)
