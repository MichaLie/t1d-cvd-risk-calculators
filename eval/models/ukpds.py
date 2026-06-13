"""
UKPDS Risk Engine (T2D): CHD (UKPDS 56, Stevens 2001) + Stroke (UKPDS 60,
Kothari 2002). Weibull-type: R(t)=1-exp(-q * d^T * (1-d^t)/(1-d)).
Requires diabetes duration T. Stroke worked example reproduced (6.9%).
Endpoints are CHD-only and stroke-only; a combined 'CVD' is approximated as
1-(1-CHD)(1-stroke) (events not independent -> caveat).
"""
from __future__ import annotations
from math import exp, log


def _chd_q(age, female, afrocarib, smoker, hba1c_pct, sbp, tc_hdl):
    return (0.0112 * 1.059 ** (age - 55) * 0.525 ** female * 0.390 ** afrocarib
            * 1.350 ** smoker * 1.183 ** (hba1c_pct - 6.72) * 1.088 ** ((sbp - 135.7) / 10)
            * 3.845 ** (log(tc_hdl) - 1.59))


def _stroke_q(age, female, smoker, af, sbp, tc_hdl):
    return (0.00186 * 1.092 ** (age - 55) * 0.700 ** female * 1.547 ** smoker
            * 8.554 ** af * 1.122 ** ((sbp - 135.5) / 10) * 1.138 ** (log(tc_hdl) - 1.59))


def _weibull(q, d, T, t):
    return 1 - exp(-q * d ** T * (1 - d ** t) / (1 - d))


def ukpds_chd(*, age, female, smoker, hba1c_pct, sbp, tc_hdl, duration, afrocarib=False, t=10):
    return 100.0 * _weibull(_chd_q(age, int(female), int(afrocarib), int(smoker), hba1c_pct, sbp, tc_hdl), 1.078, duration, t)


def ukpds_stroke(*, age, female, smoker, af, sbp, tc_hdl, duration, t=10):
    return 100.0 * _weibull(_stroke_q(age, int(female), int(smoker), int(af), sbp, tc_hdl), 1.145, duration, t)


def ukpds_cvd(*, age, female, smoker, hba1c_pct, sbp, tc_hdl, duration, af=False, afrocarib=False, t=10):
    """Approximate combined CHD+stroke CVD risk (%)."""
    pchd = ukpds_chd(age=age, female=female, smoker=smoker, hba1c_pct=hba1c_pct, sbp=sbp,
                     tc_hdl=tc_hdl, duration=duration, afrocarib=afrocarib, t=t) / 100
    pstr = ukpds_stroke(age=age, female=female, smoker=smoker, af=af, sbp=sbp, tc_hdl=tc_hdl,
                        duration=duration, t=t) / 100
    return 100.0 * (1 - (1 - pchd) * (1 - pstr))


if __name__ == "__main__":
    s = ukpds_stroke(age=55, female=False, smoker=False, af=False, sbp=147, tc_hdl=5.65 / 1.11, duration=12, t=5)
    print(f"UKPDS stroke worked example -> {s:.2f}%  (expected 6.9%)")
