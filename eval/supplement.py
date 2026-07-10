"""Generate transparent supplementary tables for the synthetic-cohort analysis.

The descriptive sensitivity analyses are post hoc slices of the single seeded
cohort; they do not generate new populations or imply external validation.
"""
from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from eval.harness.categories import band
from eval.harness.discordance import cohen_kappa
from eval.harness.models import REGISTRY, analysis_models
from eval.harness.profiles import make_synthetic_cohort


N = 10_000
SEED = 20_260_613
OUT = Path(__file__).resolve().parent / "out"


def patient_record(index, patient):
    return {
        "synthetic_id": index,
        "age_years": patient.age,
        "female": int(patient.female),
        "age_at_diagnosis_years": patient.onset_age,
        "diabetes_duration_years": patient.duration,
        "hba1c_percent": patient.hba1c_pct,
        "hba1c_mmol_mol": patient.hba1c_mmol,
        "sbp_mmhg": patient.sbp,
        "dbp_mmhg": patient.dbp,
        "bp_treatment": int(patient.on_bp_treatment),
        "total_cholesterol_mmol_l": patient.total_chol,
        "hdl_cholesterol_mmol_l": patient.hdl,
        "triglycerides_mmol_l": patient.triglycerides,
        "ldl_cholesterol_mmol_l": patient.ldl,
        "egfr_ml_min_1_73m2": patient.egfr,
        "albuminuria": patient.albuminuria,
        "current_smoker": int(patient.smoker),
        "bmi_kg_m2": patient.bmi,
        "regular_exercise": int(patient.regular_exercise),
        "retinopathy": int(patient.retinopathy),
        "atrial_fibrillation": int(patient.af),
        "prior_cvd": int(patient.prior_cvd),
        "statin_treatment": int(patient.on_statin),
        "family_history_cvd": int(patient.family_history_cvd),
        "ethnicity": patient.ethnicity,
        "score2_risk_region": patient.risk_region,
    }


def scenario_masks(cohort):
    age = np.array([p.age for p in cohort])
    onset = np.array([p.onset_age for p in cohort])
    hba1c = np.array([p.hba1c_pct for p in cohort])
    sbp = np.array([p.sbp for p in cohort])
    ldl = np.array([p.ldl for p in cohort])
    smoker = np.array([p.smoker for p in cohort], dtype=bool)
    egfr = np.array([p.egfr for p in cohort])
    albuminuria = np.array([p.albuminuria for p in cohort])
    return {
        "Full seeded cohort": np.ones(len(cohort), dtype=bool),
        "Young with early-onset T1D": (age < 40) & (onset < 18),
        "Renal-risk subgroup": (albuminuria != "normal") | (egfr < 60),
        "Favourable risk-factor subgroup": (
            (hba1c < 7.5)
            & (sbp < 130)
            & (ldl < 2.6)
            & (~smoker)
            & (albuminuria == "normal")
        ),
        "Age 70 years or older": age >= 70,
    }


SCENARIO_DEFINITIONS = {
    "Full seeded cohort": "All 10,000 profiles generated with seed 20260613.",
    "Young with early-onset T1D": "Age <40 years and age at diagnosis <18 years.",
    "Renal-risk subgroup": "Albuminuria above normal or eGFR <60 mL/min/1.73 m2.",
    "Favourable risk-factor subgroup": (
        "HbA1c <7.5%, SBP <130 mmHg, LDL cholesterol <2.6 mmol/L, "
        "not currently smoking, and normal albuminuria."
    ),
    "Age 70 years or older": (
        "Age >=70 years; coded age limits remain enforced, although some models "
        "still extrapolate beyond their derivation age range."
    ),
}


def pair_kappa(cat_a, cat_b, risk_a, risk_b, mask):
    eligible = mask & np.isfinite(risk_a) & np.isfinite(risk_b)
    n = int(eligible.sum())
    if n < 30:
        return np.nan, n, np.nan
    a = cat_a[eligible]
    b = cat_b[eligible]
    exact = float(np.mean(a == b))
    # Kappa is mathematically undefined when both marginals occupy the same
    # single category; exact agreement is retained to expose saturation.
    if len(np.unique(a)) == 1 and len(np.unique(b)) == 1 and a[0] == b[0]:
        return np.nan, n, exact
    return cohen_kappa(a, b, "linear", k=3), n, exact


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cohort = make_synthetic_cohort(N, seed=SEED)
    cohort_df = pd.DataFrame(patient_record(i + 1, p) for i, p in enumerate(cohort))
    cohort_df.to_csv(OUT / "synthetic_cohort.csv", index=False)

    models = analysis_models()
    risks = {m: np.array([REGISTRY[m][2](p) for p in cohort], dtype=float) for m in models}
    cats = {m: np.array([band(r) if np.isfinite(r) else -1 for r in risks[m]]) for m in models}
    masks = scenario_masks(cohort)

    summary_rows = []
    model_rows = []
    for scenario, mask in masks.items():
        pair_values = []
        pair_sample_sizes = []
        for a, b in combinations(models, 2):
            value, pair_n, _ = pair_kappa(cats[a], cats[b], risks[a], risks[b], mask)
            if np.isfinite(value):
                pair_values.append(value)
                pair_sample_sizes.append(pair_n)

        steno_scottish, n_steno_scottish, exact_steno_scottish = pair_kappa(
            cats["Steno-CVD"], cats["Scottish-Swedish"],
            risks["Steno-CVD"], risks["Scottish-Swedish"], mask,
        )
        steno_score2d, n_steno_score2d, exact_steno_score2d = pair_kappa(
            cats["Steno-IHDstroke"], cats["SCORE2-Diabetes"],
            risks["Steno-IHDstroke"], risks["SCORE2-Diabetes"], mask,
        )
        summary_rows.append({
            "scenario": scenario,
            "definition": SCENARIO_DEFINITIONS[scenario],
            "n_profiles": int(mask.sum()),
            "mean_pairwise_linear_weighted_kappa": float(np.mean(pair_values)) if pair_values else np.nan,
            "n_model_pairs_estimable": len(pair_values),
            "minimum_pairwise_n": min(pair_sample_sizes) if pair_sample_sizes else 0,
            "steno_cvd_vs_scottish_swedish_kappa": steno_scottish,
            "steno_cvd_vs_scottish_swedish_n": n_steno_scottish,
            "steno_cvd_vs_scottish_swedish_exact_agreement_percent": 100 * exact_steno_scottish,
            "steno_ihdstroke_vs_score2_diabetes_kappa": steno_score2d,
            "steno_ihdstroke_vs_score2_diabetes_n": n_steno_score2d,
            "steno_ihdstroke_vs_score2_diabetes_exact_agreement_percent": 100 * exact_steno_score2d,
        })

        for model in models:
            eligible = mask & np.isfinite(risks[model])
            values = risks[model][eligible]
            categories = cats[model][eligible]
            model_rows.append({
                "scenario": scenario,
                "model": model,
                "model_class": REGISTRY[model][0],
                "n_profiles": int(mask.sum()),
                "n_scored": int(eligible.sum()),
                "coverage_percent": 100 * eligible.sum() / max(1, mask.sum()),
                "mean_risk_percent": float(np.mean(values)) if len(values) else np.nan,
                "median_risk_percent": float(np.median(values)) if len(values) else np.nan,
                "band_lt10_n": int((categories == 0).sum()),
                "band_10_to_lt20_n": int((categories == 1).sum()),
                "band_ge20_n": int((categories == 2).sum()),
            })

    pd.DataFrame(summary_rows).to_csv(OUT / "sensitivity_summary.csv", index=False)
    pd.DataFrame(model_rows).to_csv(OUT / "sensitivity_model_summary.csv", index=False)

    duration_one_n = int(np.sum(np.isclose(cohort_df["diabetes_duration_years"], 1.0)))
    assumptions = [
        ("Cohort purpose", "Illustrative, assumption-based case mix; not sampled or fitted from patient-level registry data and not population-representative", "Design statement"),
        ("Age", "Normal(mean 45, SD 14), clipped to 18-85 years", "Simulated"),
        ("Age at diagnosis", "Normal(mean 22, SD 12), clipped to 1 to age-1 years", "Simulated"),
        ("Diabetes duration", "Age minus age at diagnosis", "Derived"),
        ("Duration boundary", f"Age at diagnosis is clipped to age-1; {duration_one_n:,} profiles therefore have duration exactly 1 year", "Generator consequence"),
        ("HbA1c", "Normal(mean 8.2%, SD 1.3), clipped to 5.5-13.0%", "Simulated; one current value only"),
        ("Long-term/mean HbA1c", "Set equal to current HbA1c where required", "Fixed substitution"),
        ("SBP", "Normal(mean 128, SD 16), clipped to 95-200 mmHg", "Simulated"),
        ("DBP", "78 mmHg", "Fixed default"),
        ("Blood-pressure treatment", "If SBP >140 mmHg, probability 0.60; otherwise no", "Derived stochastic flag"),
        ("Total cholesterol", "Normal(mean 4.7, SD 0.9), clipped to 2.8-8.0 mmol/L", "Simulated"),
        ("HDL cholesterol", "Normal(mean 1.5, SD 0.4), clipped to 0.6-3.0 mmol/L", "Simulated"),
        ("Triglycerides", "Log-normal(log mean 1.1, sigma 0.4), clipped to 0.4-6.0 mmol/L", "Simulated"),
        ("LDL cholesterol", "Friedewald: total cholesterol - HDL - triglycerides/2.2; minimum 0.3", "Derived"),
        ("eGFR", "Normal(mean 102, SD 16) - 0.25*(age-40) - 0.35*duration; clipped to 15-140", "Simulated with imposed dependence"),
        ("Albuminuria", "Prevalence increases with duration and HbA1c; 65% of abnormal cases microalbuminuria", "Simulated with imposed dependence"),
        ("Current smoking", "Bernoulli probability 0.20", "Simulated"),
        ("Female sex", "Bernoulli probability 0.45", "Simulated"),
        ("BMI", "25 kg/m2", "Fixed default"),
        ("Regular exercise", "Yes", "Fixed default"),
        ("Retinopathy", "No", "Fixed default"),
        ("Atrial fibrillation", "No", "Fixed default"),
        ("Prior CVD", "No", "Fixed default; primary-prevention cohort"),
        ("Statin treatment", "No", "Fixed default"),
        ("Family history of CVD", "No", "Fixed default"),
        ("Ethnicity", "White", "Fixed default"),
        ("SCORE2 region", "High-risk region", "Fixed to Central European/Czech setting"),
        ("Scottish deprivation", "Quintile 3", "Fixed in model adapter"),
        ("Common analytic bands", "<10%, 10 to <20%, and >=20%; not native treatment thresholds", "Analysis choice"),
        ("Mean kappa", "Unweighted mean of finite pairwise-complete linear-weighted kappas; pairs with n<30 or identical single-category marginals are excluded", "Analysis choice"),
        ("Randomisation and robustness", "Single seed 20260613 and one prespecified generator parameter set; no repeated-seed or distribution-perturbation analysis", "Analysis limitation"),
        ("Verified runtime", "Python 3.12.0; NumPy 2.2.6; pandas 2.3.3; SciPy 1.16.3; Matplotlib 3.10.8; Node 22.14.0", "Environment snapshot"),
        ("QRISK3 adapter", "Townsend score 0; current smoking mapped to category 2; SBP variability raw input 0; other comorbidities off", "Documented adaptation"),
        ("Scottish-Swedish adapter", "Current smoking proxies ever-smoking; sex-default height and BMI-derived weight; current HbA1c proxies mean HbA1c; SIMD quintile 3; fitted x1.32 calibration", "Documented adaptation"),
        ("ADVANCE adapter", "Albuminuria mapped to ACR 10/100/500 mg/g; native 4-year risk extrapolated to 10 years under constant hazard", "Documented adaptation"),
        ("UKPDS adapter", "CHD and stroke combined using an independence approximation", "Documented adaptation"),
        ("Cederholm endpoint", "Native 5-year endpoint is available in the browser but excluded from the 10-year agreement matrix", "Horizon rule"),
    ]
    pd.DataFrame(assumptions, columns=["variable", "implementation", "status"]).to_csv(
        OUT / "synthetic_cohort_assumptions.csv", index=False
    )

    print(f"Supplementary files written to {OUT}")


if __name__ == "__main__":
    main()
