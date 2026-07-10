"""
Steno Type 1 Risk Engine (Vistisen et al., Circulation 2016).

Re-implementation from the published coefficients in the paper's Supplemental
Material (Supplemental Tables 3 and 4).

Model form (per the appendix):
    LP = alpha + sum_i beta_i * x_i
    r  = exp(LP)                      # annual incidence rate
    P(t) = 1 - exp(-r * t)            # risk over t years

Two endpoints are published:
  - 'cvd'    : composite fatal/non-fatal CVD (IHD, ischaemic stroke, HF, PAD)
  - 'ihd_stroke' : fatal/non-fatal IHD or stroke only

The eGFR term uses log2(eGFR) with an age-dependent coefficient
(<40 vs >=40 years). HbA1c enters in mmol/mol.

This module is intentionally dependency-light (pure math) so selected output
can be checked against the live web tool and the implementation reused in the
evaluation grid.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import exp, log2

# ---------------------------------------------------------------------------
# Published coefficients (Vistisen 2016, Supplemental Tables 3 & 4)
# ---------------------------------------------------------------------------
COEF = {
    "cvd": {  # composite CVD (Suppl. Table 3)
        "alpha": -6.046429053,
        "age": 0.040672727,
        "female": -0.234111177,
        "duration": 0.013062752,
        "sbp": 0.005814221,
        "ldl": 0.082287009,
        "hba1c_mmol": 0.012209026,
        "micro": 0.437359313,
        "macro": 0.738916137,
        "log2egfr_lt40": -0.404318528,
        "log2egfr_ge40": -0.345596046,
        "smoking": 0.204224209,
        "no_exercise": 0.229279688,
    },
    "ihd_stroke": {  # IHD or stroke (Suppl. Table 4)
        "alpha": -5.716956267,
        "age": 0.044302014,
        "female": -0.208960873,
        "duration": 0.007769067,
        "sbp": 0.006514040,
        "ldl": 0.117920173,
        "hba1c_mmol": 0.008561294,
        "micro": 0.295662570,
        "macro": 0.532588474,
        "log2egfr_lt40": -0.504447543,
        "log2egfr_ge40": -0.443012444,
        "smoking": 0.308949210,
        "no_exercise": 0.183553384,
    },
}


def hba1c_pct_to_mmol(pct: float) -> float:
    """IFCC <- DCCT conversion: mmol/mol = 10.929 * (% - 2.15)."""
    return 10.929 * (pct - 2.15)


@dataclass
class StenoPatient:
    age: float                 # years
    female: bool
    duration: float            # diabetes duration, years
    sbp: float                 # systolic BP, mmHg
    ldl: float                 # LDL cholesterol, mmol/L
    hba1c_pct: float           # HbA1c in % (DCCT) -> converted before use
    egfr: float                # mL/min/1.73 m^2
    albuminuria: str = "normal"  # 'normal' | 'micro' | 'macro'
    smoker: bool = False
    regular_exercise: bool = True  # model uses "no regular exercise" indicator


def steno_risk(p: StenoPatient, years: int = 10, outcome: str = "cvd") -> float:
    """Return absolute risk (probability, 0-1) over `years` for the given endpoint."""
    if outcome not in COEF:
        raise ValueError(f"outcome must be one of {list(COEF)}")
    c = COEF[outcome]
    hba1c_mmol = hba1c_pct_to_mmol(p.hba1c_pct)
    micro = 1.0 if p.albuminuria == "micro" else 0.0
    macro = 1.0 if p.albuminuria == "macro" else 0.0
    egfr_coef = c["log2egfr_lt40"] if p.age < 40 else c["log2egfr_ge40"]

    lp = (
        c["alpha"]
        + c["age"] * p.age
        + c["female"] * (1.0 if p.female else 0.0)
        + c["duration"] * p.duration
        + c["sbp"] * p.sbp
        + c["ldl"] * p.ldl
        + c["hba1c_mmol"] * hba1c_mmol
        + c["micro"] * micro
        + c["macro"] * macro
        + egfr_coef * log2(p.egfr)
        + c["smoking"] * (1.0 if p.smoker else 0.0)
        + c["no_exercise"] * (0.0 if p.regular_exercise else 1.0)
    )
    r = exp(lp)            # annual incidence rate
    return 1.0 - exp(-r * years)


if __name__ == "__main__":
    # Reference profiles for implementation checks against the live web tool.
    cases = {
        "A: 50M, dur20, SBP140, LDL3.0, A1c8.0%, eGFR90, smoker, exercises, normo": StenoPatient(
            age=50, female=False, duration=20, sbp=140, ldl=3.0, hba1c_pct=8.0,
            egfr=90, albuminuria="normal", smoker=True, regular_exercise=True),
        "B: 35F, dur15, SBP120, LDL2.5, A1c7.0%, eGFR100, non-smoker, exercises, normo": StenoPatient(
            age=35, female=True, duration=15, sbp=120, ldl=2.5, hba1c_pct=7.0,
            egfr=100, albuminuria="normal", smoker=False, regular_exercise=True),
        "C: 60M, dur30, SBP150, LDL3.5, A1c9.0%, eGFR60, smoker, no-exercise, macro": StenoPatient(
            age=60, female=False, duration=30, sbp=150, ldl=3.5, hba1c_pct=9.0,
            egfr=60, albuminuria="macro", smoker=True, regular_exercise=False),
    }
    for name, pt in cases.items():
        print(f"\n{name}")
        for yr in (5, 10):
            print(f"   {yr}-yr  CVD={steno_risk(pt, yr, 'cvd')*100:6.2f}%   "
                  f"IHD/stroke={steno_risk(pt, yr, 'ihd_stroke')*100:6.2f}%")
