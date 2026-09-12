"""
Framingham General CVD 10-yr risk (D'Agostino 2008, Circulation 117:743),
lab-based Cox model. Broad 'hard+soft' CVD composite (incl. HF, angina, TIA,
PAD). Cholesterol in mg/dL. Worked examples reproduced (woman 8.4%, man 15.6%).
"""
from __future__ import annotations
from math import exp, log

MGDL = 38.67  # mmol/L -> mg/dL
B = {
    "female": dict(S0=0.95012, mean=26.1931, ln_age=2.32888, ln_tc=1.20904, ln_hdl=-0.70833,
                   ln_sbp_u=2.76157, ln_sbp_t=2.82263, smk=0.52873, dm=0.69154),
    "male": dict(S0=0.88936, mean=23.9802, ln_age=3.06117, ln_tc=1.12370, ln_hdl=-0.93263,
                 ln_sbp_u=1.93303, ln_sbp_t=1.99881, smk=0.65451, dm=0.57367),
}


def framingham_risk(*, female: bool, age: float, total_chol_mgdl: float, hdl_mgdl: float,
                    sbp: float, treated_bp: bool, smoker: bool, diabetes: bool) -> float:
    """10-yr general-CVD risk (%). Reasonable range age 30-74 -> NaN outside."""
    if not (30 <= age < 75):
        return float("nan")
    b = B["female" if female else "male"]
    lp = (b["ln_age"] * log(age) + b["ln_tc"] * log(total_chol_mgdl) + b["ln_hdl"] * log(hdl_mgdl)
          + (b["ln_sbp_t"] if treated_bp else b["ln_sbp_u"]) * log(sbp)
          + b["smk"] * (1 if smoker else 0) + b["dm"] * (1 if diabetes else 0))
    return 100.0 * (1 - b["S0"] ** exp(lp - b["mean"]))


if __name__ == "__main__":
    w = framingham_risk(female=True, age=61, total_chol_mgdl=230, hdl_mgdl=47, sbp=124,
                        treated_bp=False, smoker=False, diabetes=False)
    m = framingham_risk(female=False, age=53, total_chol_mgdl=161, hdl_mgdl=55, sbp=125,
                        treated_bp=True, smoker=False, diabetes=True)
    print(f"Framingham woman -> {w:.2f}% (expected 8.4%);  man -> {m:.2f}% (expected 15.6%)")
