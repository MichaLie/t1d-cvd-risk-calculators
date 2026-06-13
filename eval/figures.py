"""Publication-style figures from the discordance run."""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

K = pd.read_csv("eval/out/kappa_matrix.csv", index_col=0)
labels = list(K.columns)
M = K.values

fig, ax = plt.subplots(figsize=(7.2, 6.2))
cmap = LinearSegmentedColormap.from_list("agree", ["#b2182b", "#f7f7c8", "#2166ac"])
im = ax.imshow(M, cmap=cmap, vmin=0, vmax=1)

ax.set_xticks(range(len(labels))); ax.set_yticks(range(len(labels)))
ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=9)
ax.set_yticklabels(labels, fontsize=9)
for i in range(len(labels)):
    for j in range(len(labels)):
        v = M[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=9,
                color="white" if (v < 0.25 or v > 0.85) else "black",
                fontweight="bold" if i != j else "normal")
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label("Cohen's κ (linear-weighted)\nrisk-category agreement", fontsize=9)
ax.set_title("Cross-calculator agreement on 10-yr CVD risk category\n"
             "synthetic T1D cohort (n=10,000), pairwise-complete",
             fontsize=11, pad=12)
off = M[~np.eye(len(labels), dtype=bool)]
ax.text(0.5, -0.32, f"mean off-diagonal κ = {off.mean():.2f}  "
        f"(range {off.min():.2f}–{off.max():.2f})  |  κ<0.4 = poor, 0.4–0.6 moderate, 0.6–0.8 substantial",
        transform=ax.transAxes, ha="center", fontsize=8, style="italic")
plt.tight_layout()
plt.savefig("eval/out/kappa_heatmap.png", dpi=170, bbox_inches="tight")
print("saved eval/out/kappa_heatmap.png")
