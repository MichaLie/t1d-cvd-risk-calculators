"""
UKPDS Risk Engine (T2D): CHD (UKPDS 56, Stevens 2001, Clin Sci 101:671) + Stroke
(UKPDS 60, Kothari 2002, Stroke 33:1776). Weibull-type:
    R_T(t) = 1 - exp(-q * d^T * (1 - d^t) / (1 - d))
where T = years since diagnosis and t = horizon.

IMPORTANT: in both papers `age` is AGE AT DIAGNOSIS of diabetes (Stevens Table 2:
"AGE Age in years at diagnosis of diabetes"; Kothari Table 3: "Age at diagnosis of
diabetes, per year 1.092"). Duration enters only through d^T. The CHD lipid term is
3.845^(ln(TC/HDL) - 1.59); the STROKE lipid term is LINEAR, 1.138^(TC/HDL - 5.11)
(Kothari 2002 model equation and worked example: 6.9%).
Endpoints are CHD-only and stroke-only; a combined 'CVD' is approximated as
1-(1-CHD)(1-stroke) (independence assumption, not from the papers -> caveat).
"""
from __future__ import annotations
from math import exp, log


def _chd_q(age_dx, female, afrocarib, smoker, hba1c_pct, sbp, tc_hdl):
    return (0.0112 * 1.059 ** (age_dx - 55) * 0.525 ** female * 0.390 ** afrocarib
            * 1.350 ** smoker * 1.183 ** (hba1c_pct - 6.72) * 1.088 ** ((sbp - 135.7) / 10)
            * 3.845 ** (log(tc_hdl) - 1.59))


def _stroke_q(age_dx, female, smoker, af, sbp, tc_hdl):
    # Kothari 2002: lipid ratio enters linearly, centred at 5.11 (not log-centred as in UKPDS 56)
    return (0.00186 * 1.092 ** (age_dx - 55) * 0.700 ** female * 1.547 ** smoker
            * 8.554 ** af * 1.122 ** ((sbp - 135.5) / 10) * 1.138 ** (tc_hdl - 5.11))


def _weibull(q, d, T, t):
    return 1 - exp(-q * d ** T * (1 - d ** t) / (1 - d))


def ukpds_chd(*, age_at_diagnosis, female, smoker, hba1c_pct, sbp, tc_hdl, duration, afrocarib=False, t=10):
    """UKPDS 56 CHD risk (%) over t years for a patient diagnosed at `age_at_diagnosis` with `duration` years since."""
    return 100.0 * _weibull(_chd_q(age_at_diagnosis, int(female), int(afrocarib), int(smoker), hba1c_pct, sbp, tc_hdl), 1.078, duration, t)


def ukpds_stroke(*, age_at_diagnosis, female, smoker, af, sbp, tc_hdl, duration, t=10):
    """UKPDS 60 stroke risk (%) over t years."""
    return 100.0 * _weibull(_stroke_q(age_at_diagnosis, int(female), int(smoker), int(af), sbp, tc_hdl), 1.145, duration, t)


def ukpds_cvd(*, age_at_diagnosis, female, smoker, hba1c_pct, sbp, tc_hdl, duration, af=False, afrocarib=False, t=10):
    """Approximate combined CHD+stroke CVD risk (%), independence assumption."""
    pchd = ukpds_chd(age_at_diagnosis=age_at_diagnosis, female=female, smoker=smoker, hba1c_pct=hba1c_pct,
                     sbp=sbp, tc_hdl=tc_hdl, duration=duration, afrocarib=afrocarib, t=t) / 100
    pstr = ukpds_stroke(age_at_diagnosis=age_at_diagnosis, female=female, smoker=smoker, af=af, sbp=sbp,
                        tc_hdl=tc_hdl, duration=duration, t=t) / 100
    return 100.0 * (1 - (1 - pchd) * (1 - pstr))


if __name__ == "__main__":
    # Kothari 2002 (p. 1778): man diagnosed at 55, 12 y of diabetes, SBP 147, TC 5.65 / HDL 1.11, non-smoker, no AF
    s = ukpds_stroke(age_at_diagnosis=55, female=False, smoker=False, af=False, sbp=147, tc_hdl=5.65 / 1.11, duration=12, t=5)
    print(f"UKPDS stroke worked example -> {s:.2f}%  (paper: q=0.00212, 6.9%)")
