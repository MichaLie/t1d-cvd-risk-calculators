"""End-to-end pipeline smoke test: cohort -> model -> analytic bands -> discordance."""
import numpy as np
from eval.harness.profiles import make_synthetic_cohort, make_factorial
from eval.harness.models import REGISTRY
from eval.harness.categories import band, band_label
from eval.harness.discordance import (cohen_kappa, agreement_rate,
                                       bland_altman, risk_ratio_summary)

cohort = make_synthetic_cohort(5000)
cvd = np.array([REGISTRY["Steno-CVD"][2](p) for p in cohort])
ihd = np.array([REGISTRY["Steno-IHDstroke"][2](p) for p in cohort])
cat_cvd = [band(x) for x in cvd]
cat_ihd = [band(x) for x in ihd]

print("=== pipeline smoke test (Steno composite-CVD vs IHD/stroke, n=5000) ===")
print(f"mean 10-yr risk   CVD={cvd.mean():.1f}%   IHD/stroke={ihd.mean():.1f}%")
print(f"analytic-band counts CVD (<10/10-<20/>=20) = "
      f"{sum(c==0 for c in cat_cvd)}/{sum(c==1 for c in cat_cvd)}/{sum(c==2 for c in cat_cvd)}")
print(f"kappa (unweighted): {cohen_kappa(cat_cvd, cat_ihd, None, k=3):.3f}")
print(f"kappa (linear)    : {cohen_kappa(cat_cvd, cat_ihd, 'linear', k=3):.3f}")
print(f"exact agreement   : {agreement_rate(cat_cvd, cat_ihd)*100:.1f}%")
print(f"Bland-Altman (pp) : {bland_altman(cvd, ihd)}")
print(f"risk ratio CVD/IHD: {risk_ratio_summary(cvd, ihd)}")

grid = make_factorial()
g = np.array([REGISTRY["Steno-CVD"][2](p) for p in grid])
print(f"\nfactorial grid n={len(grid)}  Steno-CVD 10-yr range: "
      f"{g.min():.1f}%–{g.max():.1f}%  (median {np.median(g):.1f}%)")
print("PIPELINE OK")
