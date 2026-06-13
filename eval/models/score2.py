"""
SCORE2 (ages 40-69), ESC, Eur Heart J 2021;42:2439 with the Hageman 2022
correction (EHJ 2022;43:241). General-population 10-yr fatal+non-fatal CVD,
recalibrated to 4 European risk regions. SCORE2 has NO diabetes covariate by
design (that is the raison d'etre of the separate SCORE2-Diabetes model).

Shares the region recalibration scale factors with SCORE2-Diabetes.
Valid age 40-69 -> returns NaN outside (SCORE2-OP covers >=70; its scales were
flagged approximate in extraction, so we do not extrapolate here).
"""
from __future__ import annotations
from math import exp, log
from .score2_diabetes import SCALES

S0 = {"male": 0.9605, "female": 0.9776}
B = {
    "male":   {"age": 0.3742, "smk": 0.6012, "sbp": 0.2777,
               "tc": 0.1458, "hdl": -0.2698, "age_smk": -0.0755, "age_sbp": -0.0255,
               "age_tc": -0.0281, "age_hdl": 0.0426},
    "female": {"age": 0.4648, "smk": 0.7744, "sbp": 0.3131,
               "tc": 0.1002, "hdl": -0.2606, "age_smk": -0.1088, "age_sbp": -0.0277,
               "age_tc": -0.0226, "age_hdl": 0.0613},
}


def score2_risk(*, female: bool, age: float, smoker: bool, sbp: float,
                total_chol: float, hdl: float, diabetes: bool = False,
                region: str = "high") -> float:
    """10-yr CVD risk (%). Returns NaN outside the validated 40-69 age range.

    `diabetes` is accepted for call-site compatibility but IGNORED: published
    SCORE2 has no diabetes term. Diabetic patients should use SCORE2-Diabetes.
    """
    if not (40 <= age <= 69):
        return float("nan")
    sex = "female" if female else "male"
    b = B[sex]
    cage = (age - 60) / 5
    csbp = (sbp - 120) / 20
    ctc = total_chol - 6
    chdl = (hdl - 1.3) / 0.5
    lp = (b["age"] * cage + b["smk"] * smoker + b["sbp"] * csbp
          + b["tc"] * ctc + b["hdl"] * chdl
          + b["age_smk"] * cage * smoker + b["age_sbp"] * cage * csbp
          + b["age_tc"] * cage * ctc + b["age_hdl"] * cage * chdl)
    unc = 1 - S0[sex] ** exp(lp)
    s1, s2 = SCALES[sex][region]
    return (1 - exp(-exp(s1 + s2 * log(-log(1 - unc))))) * 100.0


if __name__ == "__main__":
    # EHJ 2021: 50yo current smoker, SBP140, TC5.5, HDL1.3, no diabetes
    kw = dict(age=50, smoker=True, sbp=140, total_chol=5.5, hdl=1.3, diabetes=False)
    exp_vals = {("male", "low"): 5.9, ("male", "very_high"): 14.0,
                ("female", "low"): 4.2, ("female", "very_high"): 13.7}
    print(f"{'sex':7} {'region':10} {'exp%':>5} {'got%':>5}")
    for (sex, region), e in exp_vals.items():
        g = score2_risk(female=(sex == "female"), region=region, **kw)
        print(f"{sex:7} {region:10} {e:5.1f} {g:5.1f}")
