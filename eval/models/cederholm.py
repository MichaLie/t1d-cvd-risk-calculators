"""
Cederholm 2011 Swedish NDR 5-year CVD model for T1D (Diabet Med 28:1213).
T1D-SPECIFIC but native horizon = 5 years (no 10-yr baseline published), so it
serves as a separate 5-yr T1D comparator, NOT in the 10-yr matrix.
Worked example reproduced (48yo T1D patient -> 7.1%). HbA1c in % (DCCT).
"""
from __future__ import annotations
from math import exp, log

S0_5 = 0.97136
B = dict(duration=0.08426, onset=0.04742, ln_tchdl=0.80050, ln_hba1c=1.27275,
         ln_sbp=1.20050, smoker=0.56688, macro=0.41995, prior_cvd=1.25506)
C = dict(duration=28.014, onset=16.601, ln_tchdl=1.1470, ln_hba1c=2.0605,
         ln_sbp=4.8598, smoker=0.1483, macro=0.1237, prior_cvd=0.0612)


def cederholm_risk5(*, age: float, duration: float, total_chol: float, hdl: float,
                    hba1c_pct: float, sbp: float, smoker: bool = False,
                    macroalbuminuria: bool = False, prior_cvd: bool = False) -> float:
    onset = age - duration
    lp = (B["duration"] * (duration - C["duration"]) + B["onset"] * (onset - C["onset"])
          + B["ln_tchdl"] * (log(total_chol / hdl) - C["ln_tchdl"])
          + B["ln_hba1c"] * (log(hba1c_pct) - C["ln_hba1c"])
          + B["ln_sbp"] * (log(sbp) - C["ln_sbp"])
          + B["smoker"] * ((1 if smoker else 0) - C["smoker"])
          + B["macro"] * ((1 if macroalbuminuria else 0) - C["macro"])
          + B["prior_cvd"] * ((1 if prior_cvd else 0) - C["prior_cvd"]))
    return 100.0 * (1 - S0_5 ** exp(lp))


if __name__ == "__main__":
    g = cederholm_risk5(age=48, duration=30, total_chol=5.0, hdl=1.1, hba1c_pct=8.0, sbp=150,
                        smoker=False, macroalbuminuria=True, prior_cvd=False)
    print(f"Cederholm 5-yr worked example -> {g:.2f}%  (expected 7.1%)")
