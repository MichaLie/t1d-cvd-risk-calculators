"""
Scottish-Swedish type-1-diabetes CVD risk model (McGurnaghan, Diabetologia
2021;64:2001). Poisson rate model accumulated over attained-age intervals.

The authors' repo (github.com/diabepi/t1cvdrisk) is training code only (the
fitted object is built from private Scottish data); the model FORM is confirmed
there: per-interval rate = exp(LP), survival = exp(-rate), and
10-yr risk = 1 - exp(-sum_t rate_t) with age (and age^2, age^3, age*weight)
updated each year. Two coefficient variants:
  - 'main' : Table 4, includes SIMD deprivation quintile + Sex*HbA1c
  - 'alt'  : ESM Table 9, deprivation-free (recommended for non-Scottish/non-SIMD
             populations, e.g. a Czech T1D cohort) + Age*mean-HbA1c

The 'main' implementation was checked against selected outputs from the authors'
live Shiny calculator (diabepi.shinyapps.io/cvdrisk). This is an implementation
check, not external clinical validation.
"""
from __future__ import annotations
from math import exp, log

# Final model (published coefficient table, Table 4; IRRs -> beta=ln(IRR)).
# Includes BOTH age-at-entry (the deployed-model term omitted from Table 4) and the Age*mean-HbA1c
# interaction. NB: the cubic-age and interaction IRRs are published only to 3 d.p.,
# so those betas (age2/age3/age_weight/age_mean_hba1c) cannot be recovered to full
# precision from the paper -> residual mismatch vs the deployed app is expected.
A_MAIN = dict(intercept=-4.03403744, age_entry=-0.03356271, age=0.32483759,
    age2=-0.00389356, age3=1.993e-05,
    female=-0.91153788, duration=0.0201993, hba1c=0.01071311, mean_hba1c=0.02712284,
    log_bmi=-1.9247447, height=-2.84393889, weight=0.00802065, sbp=0.0041725,
    log_tchdl=0.49545924, log_egfr=-0.34828245, alb_micro=0.34128044, alb_macro=0.91835596,
    retino_nonref=0.09832872, retino_ref=0.40705123, smoke_ever=0.34002647,
    treated_htn=0.30504081, treated_dyslip=0.14012891, af=0.61882651,
    female_log_tchdl=0.39282042, age_weight=0.00023665, female_hba1c=0.00335224,
    age_mean_hba1c=-0.00028851)
DEP = {1: 0.0, 2: -0.11366821, 3: -0.28641292, 4: -0.38497544, 5: -0.55777639}

# ESM Table 9 (alt, deprivation-free)
A_ALT = dict(intercept=-3.64810112, age=0.3271865, age2=-0.00403131, age3=2.08e-05,
    female=-0.77934644, duration=0.01943773, hba1c=0.01143295, mean_hba1c=0.02781042,
    log_bmi=-2.01243842, height=-3.18108541, weight=0.00741941, sbp=0.00381897,
    log_tchdl=0.49215468, log_egfr=-0.32126549, alb_micro=0.36310623, alb_macro=0.94826311,
    retino_nonref=0.10606169, retino_ref=0.41224979, smoke_ever=0.38809494,
    treated_htn=0.31887555, treated_dyslip=0.14728126, af=0.70356665,
    female_log_tchdl=0.48736885, age_weight=0.0002678, age_mean_hba1c=-0.00028851)

HEIGHT = {"male": 1.75, "female": 1.62}


def scottish_swedish_risk(*, female: bool, age: float, duration: float, hba1c_mmol: float,
                          sbp: float, tc_hdl_ratio: float, egfr: float, bmi: float = 25.0,
                          height_m: float | None = None, weight_kg: float | None = None,
                          mean_hba1c_mmol: float | None = None, albuminuria: str = "normal",
                          retinopathy: str = "none", smoker: bool = False,
                          treated_htn: bool = False, treated_dyslip: bool = False, af: bool = False,
                          variant: str = "alt", deprivation_quintile: int = 3, years: int = 10,
                          cal: float = 1.0) -> float:
    sex = "female" if female else "male"
    A = A_MAIN if variant == "main" else A_ALT
    h = height_m if height_m is not None else HEIGHT[sex]
    weight = weight_kg if weight_kg is not None else bmi * h * h
    if bmi is None or weight_kg is not None and height_m is not None:
        bmi = weight / (h * h)
    mean_a1c = mean_hba1c_mmol if mean_hba1c_mmol is not None else hba1c_mmol

    fixed = (A["intercept"] + A["female"] * female + A["duration"] * duration
             + A["hba1c"] * hba1c_mmol + A["mean_hba1c"] * mean_a1c
             + A["log_bmi"] * log(bmi) + A["height"] * h + A["weight"] * weight
             + A["sbp"] * sbp + A["log_tchdl"] * log(tc_hdl_ratio) + A["log_egfr"] * log(egfr)
             + A["alb_micro"] * (albuminuria == "micro") + A["alb_macro"] * (albuminuria == "macro")
             + A["retino_nonref"] * (retinopathy == "nonref") + A["retino_ref"] * (retinopathy == "ref")
             + A["smoke_ever"] * smoker + A["treated_htn"] * treated_htn
             + A["treated_dyslip"] * treated_dyslip + A["af"] * af
             + A["female_log_tchdl"] * female * log(tc_hdl_ratio))
    fixed += A.get("age_entry", 0.0) * age           # age-at-entry (fixed across intervals)
    if variant == "main":
        fixed += DEP[deprivation_quintile] + A["female_hba1c"] * female * hba1c_mmol

    cum = 0.0
    for t in range(years):
        ca = age + t
        lp = (fixed + A["age"] * ca + A["age2"] * ca * ca + A["age3"] * ca ** 3
              + A["age_weight"] * ca * weight
              + A.get("age_mean_hba1c", 0.0) * ca * mean_a1c)
        cum += exp(lp)
    return (1 - exp(-cum * cal)) * 100.0


if __name__ == "__main__":
    # Check the MAIN variant against the authors' live Shiny app default profile -> 5%.
    g = scottish_swedish_risk(female=True, age=42, duration=5, hba1c_mmol=74, mean_hba1c_mmol=74,
                              sbp=128, tc_hdl_ratio=3.3, egfr=97, bmi=26, height_m=1.71, weight_kg=77,
                              albuminuria="normal", retinopathy="none", smoker=False,
                              variant="main", deprivation_quintile=4)
    print(f"MAIN model, Shiny default profile -> {g:.2f}%   (app shows 5%)")
    galt = scottish_swedish_risk(female=True, age=42, duration=5, hba1c_mmol=74, mean_hba1c_mmol=74,
                                 sbp=128, tc_hdl_ratio=3.3, egfr=97, bmi=26, height_m=1.71, weight_kg=77,
                                 variant="alt")
    print(f"ALT (deprivation-free) same profile -> {galt:.2f}%")
