"""
AHA PREVENT (2024), Khan SS et al. Circulation 2024;149:430. Sex-specific
LOGISTIC model for 10-yr TOTAL CVD (ASCVD + heart failure). Coefficients from
the open-source preventr package; worked example reproduced (F -> 14.7%).
Valid age 30-79. Diabetes is a generic binary (no T1D/T2D distinction).
"""
from __future__ import annotations
from math import exp

MGDL = 0.02586  # mg/dL -> mmol/L for cholesterol (PREVENT uses mmol/L)
B = {
    "female": dict(c=-3.307728, age=0.7939329, nonhdl=0.0305239, hdl=-0.1606857,
        sbp_lo=-0.2394003, sbp_hi=0.3600781, dm=0.8667604, smk=0.5360739,
        egfr_lo=0.6045917, egfr_hi=0.0433769, bptx=0.3151672, statin=-0.1477655,
        bptx_sbphi=-0.0663612, statin_nonhdl=0.1197879, age_nonhdl=-0.0819715,
        age_hdl=0.0306769, age_sbphi=-0.0946348, age_dm=-0.27057, age_smk=-0.078715,
        age_egfrlo=-0.1637806),
    "male": dict(c=-3.031168, age=0.7688528, nonhdl=0.0736174, hdl=-0.0954431,
        sbp_lo=-0.4347345, sbp_hi=0.3362658, dm=0.7692857, smk=0.4386871,
        egfr_lo=0.5378979, egfr_hi=0.0164827, bptx=0.288879, statin=-0.1337349,
        bptx_sbphi=-0.0475924, statin_nonhdl=0.150273, age_nonhdl=-0.0517874,
        age_hdl=0.0191169, age_sbphi=-0.1049477, age_dm=-0.2251948, age_smk=-0.0895067,
        age_egfrlo=-0.1543702),
}


def prevent_risk(*, female: bool, age: float, total_chol: float, hdl: float, sbp: float,
                 egfr: float, diabetes: bool, smoker: bool, treated_bp: bool = False,
                 statin: bool = False) -> float:
    """10-yr total-CVD risk (%). total_chol/hdl in mmol/L. NaN outside 30-79."""
    if not (30 <= age <= 79):
        return float("nan")
    b = B["female" if female else "male"]
    nonhdl = (total_chol - hdl) - 3.5
    hdl_t = (hdl - 1.3) / 0.3
    age_t = (age - 55) / 10
    sbp_lo = (min(sbp, 110) - 110) / 20
    sbp_hi = (max(sbp, 110) - 130) / 20
    egfr_lo = (min(egfr, 60) - 60) / -15
    egfr_hi = (max(egfr, 60) - 90) / -15
    dm = 1.0 if diabetes else 0.0
    smk = 1.0 if smoker else 0.0
    bptx = 1.0 if treated_bp else 0.0
    stat = 1.0 if statin else 0.0
    lp = (b["c"] + b["age"] * age_t + b["nonhdl"] * nonhdl + b["hdl"] * hdl_t
          + b["sbp_lo"] * sbp_lo + b["sbp_hi"] * sbp_hi + b["dm"] * dm + b["smk"] * smk
          + b["egfr_lo"] * egfr_lo + b["egfr_hi"] * egfr_hi + b["bptx"] * bptx + b["statin"] * stat
          + b["bptx_sbphi"] * bptx * sbp_hi + b["statin_nonhdl"] * stat * nonhdl
          + b["age_nonhdl"] * age_t * nonhdl + b["age_hdl"] * age_t * hdl_t
          + b["age_sbphi"] * age_t * sbp_hi + b["age_dm"] * age_t * dm
          + b["age_smk"] * age_t * smk + b["age_egfrlo"] * age_t * egfr_lo)
    return 100.0 * exp(lp) / (1 + exp(lp))


if __name__ == "__main__":
    g = prevent_risk(female=True, age=50, total_chol=200 * MGDL, hdl=45 * MGDL, sbp=160,
                     egfr=90, diabetes=True, smoker=False, treated_bp=True, statin=False)
    print(f"PREVENT F worked example -> {g:.2f}%  (expected 14.7%)")
