"""Focused regression assertions for model implementation checks."""
from __future__ import annotations

from math import isfinite, isnan

from eval.harness.categories import band, band_label
from eval.harness.models import REGISTRY
from eval.harness.patient import Patient
from eval.models.qrisk3 import qrisk3_risk
from eval.models.score2_diabetes import score2_diabetes_risk
from eval.models.steno_t1 import StenoPatient, steno_risk


def assert_close(name: str, got: float, expected: float, tol: float) -> None:
    if not isfinite(got) or not isfinite(expected) or abs(got - expected) > tol:
        raise AssertionError(f"{name}: got {got:.12g}, expected {expected:.12g} +/- {tol}")


def test_qrisk3_missing_sbps5() -> None:
    params = dict(
        female=False, age=45, ethrisk=1, smoke_cat=0, bmi=25,
        rati=4.8 / 1.4, sbp=130, town=0, b_type1=True, b_type2=False,
        b_AF=False, b_treatedhyp=False, b_renal=False, fh_cvd=False,
    )
    missing = qrisk3_risk(sbps5=None, **params)
    raw_zero = qrisk3_risk(sbps5=0, **params)

    assert_close("QRISK3 missing SBP SD uses raw zero", missing, raw_zero, 1e-12)
    assert_close("QRISK3 canonical T1D man with missing SBP SD", missing, 7.217081960246674, 1e-9)


def test_score2_diabetes_age_guard() -> None:
    params = dict(
        female=False, smoker=False, sbp=140, total_chol=5.5, hdl=1.3,
        age_at_diagnosis=50, hba1c_mmol=50, egfr=90, region="high",
    )

    assert isnan(score2_diabetes_risk(age=39, **params))
    assert isfinite(score2_diabetes_risk(age=40, **params))
    assert isfinite(score2_diabetes_risk(age=79, **params))
    assert isnan(score2_diabetes_risk(age=80, **params))


def test_steno_ihd_stroke_table4_regression() -> None:
    patient = StenoPatient(
        age=50, female=True, duration=30, hba1c_pct=70 / 10.929 + 2.15,
        sbp=130, ldl=2.0, egfr=100, albuminuria="normal", smoker=False,
        regular_exercise=True,
    )
    risk_percent = 100 * steno_risk(patient, 10, "ihd_stroke")
    assert_close("Steno IHD/stroke Supplemental Table 4 regression", risk_percent,
                 8.37492513748504, 1e-12)


def test_common_analytic_band_boundaries() -> None:
    assert band(9.999) == 0
    assert band(10.0) == 1
    assert band(19.999) == 1
    assert band(20.0) == 2
    assert band(float("nan")) == -1
    assert band_label(float("nan")) == "not available"


def main() -> None:
    tests = [
        test_qrisk3_missing_sbps5,
        test_score2_diabetes_age_guard,
        test_steno_ihd_stroke_table4_regression,
        test_common_analytic_band_boundaries,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print("MODEL ASSERTIONS OK")


if __name__ == "__main__":
    main()
