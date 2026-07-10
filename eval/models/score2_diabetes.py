"""
SCORE2-Diabetes (ESC, Eur Heart J 2023;44:2544; DOI 10.1093/eurheartj/ehad260).

Sex-specific competing-risk model extending SCORE2 with three diabetes terms
(age at diagnosis, HbA1c, eGFR), recalibrated to four European risk regions.
Coefficients, baseline values and scales are transcribed from the ESC-aligned open
implementation and reproduce the paper's worked examples at reported precision.

3 steps:
  LP   = sum(beta * centered_term)            (sex-specific)
  unc  = 1 - S0 ** exp(LP)                      (S0: men 0.9605, women 0.9776)
  risk = 1 - exp(-exp(s1 + s2*ln(-ln(1-unc)))) (region+sex recalibration)

Endpoint: 10-yr first fatal/non-fatal CVD (CV death + non-fatal MI + stroke).
Intended age range: 40-79 years; returns NaN outside this range rather than
extrapolating.
NOTE: derived & validated in TYPE 2 diabetes only. Applying it to T1D is exactly
the 'borrowing' scenario the review interrogates.
"""
from __future__ import annotations
from math import exp, log

S0 = {"male": 0.9605, "female": 0.9776}

# scale1, scale2 by region and sex (shared with SCORE2/SCORE2-OP)
SCALES = {
    "male":   {"low": (-0.5699, 0.7476), "moderate": (-0.1565, 0.8009),
               "high": (0.3207, 0.9360), "very_high": (0.5836, 0.8294)},
    "female": {"low": (-0.7380, 0.7019), "moderate": (-0.3143, 0.7701),
               "high": (0.5710, 0.9369), "very_high": (0.9412, 0.8329)},
}

B = {
    "male": {
        "age": 0.5368, "smk": 0.4774, "sbp": 0.1322, "dm": 0.6457, "tc": 0.1102,
        "hdl": -0.1087, "age_smk": -0.0672, "age_sbp": -0.0268, "age_dm": -0.0983,
        "age_tc": -0.0181, "age_hdl": 0.0095, "dm_age_dx": -0.0998, "hba1c": 0.0955,
        "legfr": -0.0591, "legfr2": 0.0058, "hba1c_age": -0.0134, "legfr_age": 0.0115,
    },
    "female": {
        "age": 0.6624, "smk": 0.6139, "sbp": 0.1421, "dm": 0.8096, "tc": 0.1127,
        "hdl": -0.1568, "age_smk": -0.1122, "age_sbp": -0.0167, "age_dm": -0.1272,
        "age_tc": -0.0200, "age_hdl": 0.0186, "dm_age_dx": -0.1180, "hba1c": 0.1173,
        "legfr": -0.0640, "legfr2": 0.0062, "hba1c_age": -0.0196, "legfr_age": 0.0169,
    },
}


def score2_diabetes_risk(*, female: bool, age: float, smoker: bool, sbp: float,
                         total_chol: float, hdl: float, age_at_diagnosis: float,
                         hba1c_mmol: float, egfr: float, region: str = "high",
                         diabetes: bool = True) -> float:
    """Return 10-yr CVD risk (%), or NaN outside ages 40-79.

    Inputs in mmol/L, mmol/mol (HbA1c), and mL/min/1.73m2.
    """
    if not (40 <= age < 80):
        return float("nan")
    sex = "female" if female else "male"
    b = B[sex]
    dm = 1.0 if diabetes else 0.0
    cage = (age - 60) / 5
    csbp = (sbp - 120) / 20
    ctc = (total_chol - 6)
    chdl = (hdl - 1.3) / 0.5
    cdx = (age_at_diagnosis - 50) / 5
    ca1c = (hba1c_mmol - 31) / 9.34
    legfr = (log(egfr) - 4.5) / 0.15

    lp = (b["age"] * cage + b["smk"] * smoker + b["sbp"] * csbp + b["dm"] * dm
          + b["tc"] * ctc + b["hdl"] * chdl
          + b["age_smk"] * cage * smoker + b["age_sbp"] * cage * csbp
          + b["age_dm"] * cage * dm + b["age_tc"] * cage * ctc
          + b["age_hdl"] * cage * chdl
          + b["dm_age_dx"] * dm * cdx
          + b["hba1c"] * ca1c + b["legfr"] * legfr + b["legfr2"] * legfr ** 2
          + b["hba1c_age"] * ca1c * cage + b["legfr_age"] * legfr * cage)

    unc = 1 - S0[sex] ** exp(lp)
    s1, s2 = SCALES[sex][region]
    risk = 1 - exp(-exp(s1 + s2 * log(-log(1 - unc))))
    return risk * 100.0


if __name__ == "__main__":
    # 16 worked examples from EHJ 2023 graphical abstract (60yo, non-smoker, SBP140, TC5.5, HDL1.3)
    # A favourable: dx age 60, HbA1c 50, eGFR 90 | B unfavourable: dx 50, HbA1c 70, eGFR 60
    A = dict(age=60, smoker=False, sbp=140, total_chol=5.5, hdl=1.3,
             age_at_diagnosis=60, hba1c_mmol=50, egfr=90)
    Bp = dict(age=60, smoker=False, sbp=140, total_chol=5.5, hdl=1.3,
              age_at_diagnosis=50, hba1c_mmol=70, egfr=60)
    expected = {  # (region, sex): (A, B)
        ("moderate", "male"): (11.0, 17.2), ("moderate", "female"): (7.6, 12.7),
        ("low", "male"): (8.4, 12.9), ("low", "female"): (6.1, 9.8),
        ("high", "male"): (12.5, 20.4), ("high", "female"): (11.1, 20.6),
        ("very_high", "male"): (20.3, 31.2), ("very_high", "female"): (20.6, 34.0),
    }
    print(f"{'region':10} {'sex':7} {'A exp':>6} {'A got':>6} {'B exp':>6} {'B got':>6}")
    maxerr = 0.0
    for (region, sex), (ea, eb) in expected.items():
        fem = sex == "female"
        ga = score2_diabetes_risk(female=fem, region=region, **A)
        gb = score2_diabetes_risk(female=fem, region=region, **Bp)
        maxerr = max(maxerr, abs(ga - ea), abs(gb - eb))
        print(f"{region:10} {sex:7} {ea:6.1f} {ga:6.1f} {eb:6.1f} {gb:6.1f}")
    print(f"\nmax abs error vs published: {maxerr:.2f} pp")
