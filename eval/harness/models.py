"""
Model registry: maps a calculator name -> callable(Patient, years) -> risk in %.

Each adapter translates the unified Patient into the inputs that model needs and
returns absolute risk as a PERCENT (0-100). The registry inclusion flag means an
endpoint is included in the in-silico agreement analysis; endpoint-specific
implementation checks and clinical-validity caveats are documented separately.
"""
from __future__ import annotations
from ..models.steno_t1 import StenoPatient, steno_risk
from ..models.score2_diabetes import score2_diabetes_risk
from ..models.score2 import score2_risk
from ..models.pce import pce_risk, MMOL_TO_MGDL
from ..models.qrisk3 import qrisk3_risk
from ..models.scottish_swedish import scottish_swedish_risk
from ..models.prevent import prevent_risk
from ..models.ukpds import ukpds_cvd
from ..models.framingham import framingham_risk, MGDL as FRS_MGDL
from ..models.advance import advance_risk
from ..models.cederholm import cederholm_risk5


def _steno(p, years: int, outcome: str) -> float:
    sp = StenoPatient(
        age=p.age, female=p.female, duration=p.duration, sbp=p.sbp,
        ldl=p.ldl, hba1c_pct=p.hba1c_pct, egfr=p.egfr,
        albuminuria=p.albuminuria, smoker=p.smoker,
        regular_exercise=p.regular_exercise,
    )
    return steno_risk(sp, years, outcome) * 100.0


def _score2d(p) -> float:
    # T1D patient pushed through the T2D tool: age_at_diagnosis = onset age
    return score2_diabetes_risk(
        female=p.female, age=p.age, smoker=p.smoker, sbp=p.sbp,
        total_chol=p.total_chol, hdl=p.hdl, age_at_diagnosis=p.onset_age,
        hba1c_mmol=p.hba1c_mmol, egfr=p.egfr, region=p.risk_region, diabetes=True,
    )


def _score2(p) -> float:
    # Published SCORE2 has no diabetes term; run it as the general-population tool it is.
    return score2_risk(female=p.female, age=p.age, smoker=p.smoker, sbp=p.sbp,
                       total_chol=p.total_chol, hdl=p.hdl, diabetes=False, region=p.risk_region)


_ETHRISK = {"white": 1, "south_asian": 2, "black": 7, "other": 9}


def _pce(p) -> float:
    return pce_risk(female=p.female, age=p.age,
                    total_chol_mgdl=p.total_chol * MMOL_TO_MGDL, hdl_mgdl=p.hdl * MMOL_TO_MGDL,
                    sbp=p.sbp, treated_bp=p.on_bp_treatment, smoker=p.smoker,
                    diabetes=True, black=(p.ethnicity == "black"))


def _qrisk3(p) -> float:
    return qrisk3_risk(female=p.female, age=p.age, ethrisk=_ETHRISK.get(p.ethnicity, 1),
                       smoke_cat=2 if p.smoker else 0, bmi=p.bmi, rati=p.tc_hdl_ratio,
                       sbp=p.sbp, sbps5=None, town=0.0, b_type1=True, b_type2=False,
                       b_renal=(p.egfr < 60), b_treatedhyp=p.on_bp_treatment,
                       b_AF=p.af, fh_cvd=p.family_history_cvd)


def _scotswed(p) -> float:
    # Final-model coefficients from the published coefficient table (Table 4),
    # with the omitted age-at-entry term restored; deprivation is set to a
    # representative middle quintile (3) for a non-SIMD cohort; cal=1.32 absorbs the
    # publication-rounding level offset, fit to the deployed Shiny calculator.
    retinopathy = "nonref" if p.retinopathy else "none"
    return scottish_swedish_risk(
        female=p.female, age=p.age, duration=p.duration, hba1c_mmol=p.hba1c_mmol,
        sbp=p.sbp, tc_hdl_ratio=p.tc_hdl_ratio, egfr=p.egfr, bmi=p.bmi,
        albuminuria=p.albuminuria, retinopathy=retinopathy, smoker=p.smoker,
        treated_htn=p.on_bp_treatment,
        treated_dyslip=p.on_statin, af=p.af,
        variant="main", deprivation_quintile=3, cal=1.32)


def _prevent(p) -> float:
    return prevent_risk(female=p.female, age=p.age, total_chol=p.total_chol, hdl=p.hdl,
                        sbp=p.sbp, egfr=p.egfr, diabetes=True, smoker=p.smoker,
                        treated_bp=p.on_bp_treatment, statin=p.on_statin)


def _ukpds(p) -> float:
    return ukpds_cvd(age=p.age, female=p.female, smoker=p.smoker, hba1c_pct=p.hba1c_pct,
                     sbp=p.sbp, tc_hdl=p.tc_hdl_ratio, duration=p.duration, af=p.af, t=10)


def _framingham(p) -> float:
    return framingham_risk(female=p.female, age=p.age, total_chol_mgdl=p.total_chol * FRS_MGDL,
                           hdl_mgdl=p.hdl * FRS_MGDL, sbp=p.sbp, treated_bp=p.on_bp_treatment,
                           smoker=p.smoker, diabetes=True)


def _advance(p) -> float:
    return advance_risk(female=p.female, age_at_diagnosis=p.onset_age, duration=p.duration,
                        sbp=p.sbp, dbp=p.dbp, hba1c_pct=p.hba1c_pct, albuminuria=p.albuminuria,
                        total_chol=p.total_chol, hdl=p.hdl, retinopathy=p.retinopathy, af=p.af,
                        treated_htn=p.on_bp_treatment, horizon=10)


# name -> (category, include_in_analysis, fn). Inclusion means the endpoint is
# used in the agreement analysis; it is not a claim of external/live-tool
# validation for every endpoint.
REGISTRY = {
    "Steno-CVD":        ("T1D", True,  lambda p, years=10: _steno(p, years, "cvd")),
    "Steno-IHDstroke":  ("T1D", True,  lambda p, years=10: _steno(p, years, "ihd_stroke")),
    "SCORE2-Diabetes":  ("T2D", True,  lambda p, years=10: _score2d(p)),
    "SCORE2":           ("general", True, lambda p, years=10: _score2(p)),
    "PCE":              ("general", True, lambda p, years=10: _pce(p)),
    "QRISK3":           ("general", True, lambda p, years=10: _qrisk3(p)),
    "PREVENT":          ("general", True, lambda p, years=10: _prevent(p)),
    "UKPDS-CVD":        ("T2D", True,  lambda p, years=10: _ukpds(p)),
    "Framingham":       ("general", True, lambda p, years=10: _framingham(p)),
    "ADVANCE*":         ("T2D", True,  lambda p, years=10: _advance(p)),  # *4-yr native, 10-yr extrapolated
    # calibrated to the deployed Shiny tool: age-at-entry term restored, gradient matches; ~level offset
    # absorbed by cal=1.32 (publication rounds cubic/interaction coeffs to 3 d.p.)
    "Scottish-Swedish": ("T1D", True, lambda p, years=10: _scotswed(p)),
}


def analysis_models() -> list[str]:
    return [n for n, (_c, include, _f) in REGISTRY.items() if include]


def all_models() -> list[str]:
    return list(REGISTRY)
