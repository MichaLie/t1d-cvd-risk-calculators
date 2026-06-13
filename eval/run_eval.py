"""
Cross-model discordance run (NaN-aware: each tool scores only within its valid
age range, comparisons are pairwise-complete).

Headline uses the 5 web/example-validated calculators. Scottish-Swedish is
reported separately as PROVISIONAL (absolute-risk calibration unresolved).

NOT an accuracy study (no outcomes): this quantifies disagreement on identical
synthetic T1D patients.
"""
import numpy as np, pandas as pd
from eval.harness.profiles import make_synthetic_cohort
from eval.harness.models import REGISTRY, validated_models
from eval.harness.categories import band
from eval.harness.discordance import cohen_kappa, agreement_rate, bland_altman, risk_ratio_summary

N = 10000
cohort = make_synthetic_cohort(N)
ages = np.array([p.age for p in cohort])
models = validated_models()
risk = {m: np.array([REGISTRY[m][2](p) for p in cohort], float) for m in models}
cat = {m: np.array([band(r) if np.isfinite(r) else -1 for r in risk[m]]) for m in models}


def both_finite(a, b, extra=None):
    m = np.isfinite(risk[a]) & np.isfinite(risk[b])
    if extra is not None:
        m &= extra
    return m


print(f"=== In-silico discordance: synthetic T1D cohort n={N} (Czech/high region) ===")
print(f"(validated models: {', '.join(models)})\n")
hdr = f"{'model':16} {'category':9} {'coverage':>8} {'mean%':>7} {'median%':>8} {'low/mod/high':>16}"
print(hdr); print("-" * len(hdr))
for m in models:
    fin = np.isfinite(risk[m]); r = risk[m][fin]; c = cat[m][fin]
    print(f"{m:16} {REGISTRY[m][0]:9} {fin.mean()*100:7.0f}% {r.mean():7.1f} {np.median(r):8.1f} "
          f"{(c==0).sum():5d}/{(c==1).sum():4d}/{(c==2).sum():4d}")

print("\n--- pairwise category agreement (Cohen's kappa, linear-weighted; pairwise-complete) ---")
K = pd.DataFrame(np.eye(len(models)), index=models, columns=models)
for i, a in enumerate(models):
    for b in models[i+1:]:
        m = both_finite(a, b)
        kv = cohen_kappa(cat[a][m], cat[b][m], "linear", k=3)
        K.loc[a, b] = K.loc[b, a] = kv
print(K.round(2).to_string())
print(f"\nmean off-diagonal kappa = {K.values[~np.eye(len(models),dtype=bool)].mean():.2f}")

def pair_report(a, b, extra=None, label=""):
    m = both_finite(a, b, extra)
    if m.sum() < 30:
        print(f"\n[{label}] n={m.sum()} (too few) — skipped"); return
    ra, rb, ca, cb = risk[a][m], risk[b][m], cat[a][m], cat[b][m]
    ba = bland_altman(ra, rb); rr = risk_ratio_summary(ra, rb)
    print(f"\n[{label or a+' vs '+b}] n={m.sum()}")
    print(f"  kappa(lin)={cohen_kappa(ca, cb, 'linear', k=3):.3f}  exact agreement={agreement_rate(ca, cb)*100:.1f}%")
    print(f"  Bland-Altman bias={ba['bias']:+.1f}pp  95% LoA [{ba['loa_lower']:.1f},{ba['loa_upper']:.1f}]")
    print(f"  risk-ratio {a}/{b}: median={rr['median']:.2f} (IQR {rr['q1']:.2f}-{rr['q3']:.2f}, 5-95% {rr['p05']:.2f}-{rr['p95']:.2f})")

print("\n=== Key contrasts ===")
pair_report("Steno-IHDstroke", "SCORE2-Diabetes", label="T1D-specific vs borrowed-T2D (endpoint-aligned)")
pair_report("Steno-IHDstroke", "QRISK3", label="T1D-specific vs QRISK3 (has dedicated T1D term)")
pair_report("Steno-IHDstroke", "PCE", label="T1D-specific vs PCE (generic diabetes binary)")
pair_report("SCORE2", "SCORE2-Diabetes", label="general SCORE2 vs its diabetes extension")

print("\n=== Disagreement by age band (Steno IHD/stroke vs SCORE2-Diabetes) ===")
for lo, hi, name in [(40, 50, "40-49"), (50, 60, "50-59"), (60, 70, "60-69")]:
    pair_report("Steno-IHDstroke", "SCORE2-Diabetes", extra=(ages >= lo) & (ages < hi), label=f"age {name}")

# provisional Scottish-Swedish (reported, not in headline)
ss = np.array([REGISTRY["Scottish-Swedish"][2](p) for p in cohort], float)
print(f"\n[PROVISIONAL] Scottish-Swedish mean={np.nanmean(ss):.1f}% median={np.nanmedian(ss):.1f}% "
      f"(calibration vs ESM Table 8 unresolved — excluded from headline)")

out = pd.DataFrame({m: risk[m] for m in models}); out["age"] = ages
out.to_csv("eval/out/cohort_risks.csv", index=False); K.to_csv("eval/out/kappa_matrix.csv")
print("\nsaved -> eval/out/cohort_risks.csv, eval/out/kappa_matrix.csv")
