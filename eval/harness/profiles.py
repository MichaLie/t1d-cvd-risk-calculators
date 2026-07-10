"""
Synthetic T1D patient generators for the discordance eval.

Two products, serving two purposes:

  make_factorial()        -> a structured factorial grid over the key axes,
                             for the divergence heat-grid and one-at-a-time
                             sensitivity (shows WHERE models diverge).

  make_synthetic_cohort() -> n illustrative profiles sampled from specified
                             marginal distributions with imposed dependencies,
                             for the headline agreement statistics (Cohen's
                             kappa, Bland-Altman) in a transparent case-mix.

This is an assumption-based generator, not a sampled or fitted registry
population. Every assumption is explicit here so it can be inspected,
reproduced, and challenged. All randomness is seeded; results are deterministic
at the reported precision in a compatible Python/NumPy environment.
"""
from __future__ import annotations
from typing import Iterator, List
import numpy as np
from .patient import Patient

# --- factorial grid axes (clinically interpretable levels) ------------------
FACTORS = {
    "age": [30, 40, 50, 60, 70],
    "female": [False, True],
    "duration": [10, 20, 30],
    "hba1c_pct": [7.0, 8.0, 9.0, 10.0],
    "sbp": [120, 140, 160],
    "total_chol": [4.0, 5.0, 6.0],     # HDL/TG held fixed in the grid
    "egfr": [60, 90, 120],
    "albuminuria": ["normal", "micro", "macro"],
    "smoker": [False, True],
}


def _plausible(p: Patient) -> bool:
    """Drop clinically incoherent factorial cells."""
    if p.onset_age < 0.5:                      # duration cannot exceed age
        return False
    if p.albuminuria == "macro" and p.egfr >= 120:  # macroalbuminuria w/ hyperfiltration: rare
        return False
    if p.albuminuria == "normal" and p.egfr <= 60 and p.duration < 20:
        return False
    return True


def make_factorial(plausible_only: bool = True) -> List[Patient]:
    import itertools
    keys = list(FACTORS)
    out: List[Patient] = []
    for combo in itertools.product(*FACTORS.values()):
        kw = dict(zip(keys, combo))
        p = Patient(hdl=1.4, triglycerides=1.2, **kw)
        if (not plausible_only) or _plausible(p):
            out.append(p)
    return out


def make_synthetic_cohort(n: int = 10000, seed: int = 20260613,
                          risk_region: str = "high") -> List[Patient]:
    rng = np.random.default_rng(seed)

    # age and onset -> duration (keep T1D plausible)
    age = np.clip(rng.normal(45, 14, n), 18, 85)
    onset = np.clip(rng.normal(22, 12, n), 1, age - 1)
    duration = age - onset

    hba1c = np.clip(rng.normal(8.2, 1.3, n), 5.5, 13.0)
    sbp = np.clip(rng.normal(128, 16, n), 95, 200)
    tc = np.clip(rng.normal(4.7, 0.9, n), 2.8, 8.0)
    hdl = np.clip(rng.normal(1.5, 0.4, n), 0.6, 3.0)
    tg = np.clip(rng.lognormal(np.log(1.1), 0.4, n), 0.4, 6.0)

    # eGFR declines with age and duration (light, documented model)
    egfr = np.clip(rng.normal(102, 16, n) - 0.25 * (age - 40) - 0.35 * duration, 15, 140)

    # albuminuria prevalence rises with duration and HbA1c
    p_abn = np.clip(0.04 + 0.006 * duration + 0.04 * (hba1c - 8.0), 0.02, 0.6)
    u = rng.random(n)
    albuminuria = np.where(u < p_abn * 0.65, "micro",
                  np.where(u < p_abn, "macro", "normal"))

    smoker = rng.random(n) < 0.20
    female = rng.random(n) < 0.45
    on_bp = (sbp > 140) & (rng.random(n) < 0.6)

    cohort: List[Patient] = []
    for i in range(n):
        cohort.append(Patient(
            age=float(age[i]), female=bool(female[i]), diabetes_type=1,
            duration=float(duration[i]), age_at_diagnosis=float(onset[i]),
            hba1c_pct=float(hba1c[i]), sbp=float(sbp[i]),
            on_bp_treatment=bool(on_bp[i]),
            total_chol=float(tc[i]), hdl=float(hdl[i]), triglycerides=float(tg[i]),
            egfr=float(egfr[i]), albuminuria=str(albuminuria[i]),
            smoker=bool(smoker[i]), risk_region=risk_region,
        ))
    return cohort


if __name__ == "__main__":
    grid = make_factorial()
    cohort = make_synthetic_cohort(2000)
    import numpy as np
    print(f"Factorial cells (plausible): {len(grid)}  /  full = "
          f"{len(make_factorial(plausible_only=False))}")
    print(f"Synthetic cohort: n={len(cohort)}")
    a = np.array([p.age for p in cohort]); d = np.array([p.duration for p in cohort])
    e = np.array([p.egfr for p in cohort])
    from collections import Counter
    print(f"  age  mean={a.mean():.1f}  duration mean={d.mean():.1f}  eGFR mean={e.mean():.1f}")
    print(f"  albuminuria: {Counter(p.albuminuria for p in cohort)}")
