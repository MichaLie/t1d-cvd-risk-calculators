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


def _score2(p, diabetes_term: bool = False) -> float:
    # SCORE2 as deployed for people without diabetes (its published diabetes term at 0, Hageman
    # 2022 footnote a): the number a clinician borrowing SCORE2 for a T1D patient obtains.
    # diabetes_term=True applies the published diabetes coefficients (sensitivity, eval/supplement.py).
    return score2_risk(female=p.female, age=p.age, smoker=p.smoker, sbp=p.sbp,
                       total_chol=p.total_chol, hdl=p.hdl, diabetes=True, region=p.risk_region,
                       diabetes_term=diabetes_term)


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


def _prevent(p) -> float:
    return prevent_risk(female=p.female, age=p.age, total_chol=p.total_chol, hdl=p.hdl,
                        sbp=p.sbp, egfr=p.egfr, diabetes=True, smoker=p.smoker,
                        treated_bp=p.on_bp_treatment, statin=p.on_statin)


def _ukpds(p) -> float:
    # UKPDS defines age as age AT DIAGNOSIS; duration enters separately via d^T.
    return ukpds_cvd(age_at_diagnosis=p.onset_age, female=p.female, smoker=p.smoker,
                     hba1c_pct=p.hba1c_pct, sbp=p.sbp, tc_hdl=p.tc_hdl_ratio, duration=p.duration,
                     af=p.af, afrocarib=(p.ethnicity == "black"), t=10)


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
}


def analysis_models() -> list[str]:
    return [n for n, (_c, include, _f) in REGISTRY.items() if include]


def all_models() -> list[str]:
    return list(REGISTRY)
