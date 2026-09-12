"""
SCORE2 (ages 40-69), ESC, Eur Heart J 2021;42:2439; coefficients as tabulated to
4 d.p. in Hageman et al., Eur Heart J 2022;43:241 (Table 1; a Discussion Forum
reply that adds precision, not a corrigendum). General-population 10-yr
fatal+non-fatal CVD, recalibrated to 4 European risk regions.

The fitted SCORE2 model DOES contain a diabetes term (0.6457 men / 0.8096 women)
and an age x diabetes interaction (-0.0983 / -0.1272), but SCORE2 "is not
intended for use in individuals with diabetes" and in its target population the
term is always 0 (Hageman 2022, footnote a). By default this function reproduces
SCORE2 as deployed for people without diabetes (term = 0), which is what a
clinician borrowing SCORE2 for a T1D patient obtains from the charts/app.
`diabetes_term=True` applies the published diabetes coefficients instead
(sensitivity analysis; equally off-label in T1D).

Shares the region recalibration scale factors with SCORE2-Diabetes.
Valid age 40-69 -> returns NaN outside (SCORE2-OP covers >=70; its scales were
flagged approximate in extraction, so we do not extrapolate here).
"""
from __future__ import annotations
from math import exp, log, expm1
from .score2_diabetes import SCALES

S0 = {"male": 0.9605, "female": 0.9776}
B = {
    "male":   {"age": 0.3742, "smk": 0.6012, "sbp": 0.2777,
               "tc": 0.1458, "hdl": -0.2698, "age_smk": -0.0755, "age_sbp": -0.0255,
               "age_tc": -0.0281, "age_hdl": 0.0426, "dm": 0.6457, "age_dm": -0.0983},
    "female": {"age": 0.4648, "smk": 0.7744, "sbp": 0.3131,
               "tc": 0.1002, "hdl": -0.2606, "age_smk": -0.1088, "age_sbp": -0.0277,
               "age_tc": -0.0226, "age_hdl": 0.0613, "dm": 0.8096, "age_dm": -0.1272},
}


def score2_risk(*, female: bool, age: float, smoker: bool, sbp: float,
                total_chol: float, hdl: float, diabetes: bool = False,
                region: str = "high", diabetes_term: bool = False) -> float:
    """10-yr CVD risk (%). Returns NaN outside the validated 40-69 age range.

    Default (`diabetes_term=False`): SCORE2 as deployed, diabetes term at 0
    regardless of `diabetes`. With `diabetes_term=True` and `diabetes=True`, the
    published diabetes and age x diabetes coefficients are applied (sensitivity).
    """
    if not (40 <= age < 70):
        return float("nan")
    sex = "female" if female else "male"
    b = B[sex]
    dm = 1.0 if (diabetes_term and diabetes) else 0.0
    cage = (age - 60) / 5
    csbp = (sbp - 120) / 20
    ctc = total_chol - 6
    chdl = (hdl - 1.3) / 0.5
    lp = (b["age"] * cage + b["smk"] * smoker + b["sbp"] * csbp
          + b["tc"] * ctc + b["hdl"] * chdl
          + b["age_smk"] * cage * smoker + b["age_sbp"] * cage * csbp
          + b["age_tc"] * cage * ctc + b["age_hdl"] * cage * chdl
          + b["dm"] * dm + b["age_dm"] * cage * dm)
    s1, s2 = SCALES[sex][region]
    return -expm1(-exp(s1 + s2 * (log(-log(S0[sex])) + lp))) * 100.0


if __name__ == "__main__":
    # EHJ 2021: 50yo current smoker, SBP140, TC5.5, HDL1.3, no diabetes
    kw = dict(age=50, smoker=True, sbp=140, total_chol=5.5, hdl=1.3, diabetes=False)
    exp_vals = {("male", "low"): 5.9, ("male", "very_high"): 14.0,
                ("female", "low"): 4.2, ("female", "very_high"): 13.7}
    print(f"{'sex':7} {'region':10} {'exp%':>5} {'got%':>5}")
    for (sex, region), e in exp_vals.items():
        g = score2_risk(female=(sex == "female"), region=region, **kw)
        print(f"{sex:7} {region:10} {e:5.1f} {g:5.1f}")
