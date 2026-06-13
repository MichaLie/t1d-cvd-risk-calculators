"""
Unified patient representation for the in-silico CV-risk-calculator eval.

A single `Patient` carries the SUPERSET of inputs any calculator needs.
Each model adapter reads only the fields it uses. Lipids are stored as a
coherent panel (total / HDL / triglycerides in mmol/L); LDL and non-HDL are
derived so that every model receives mutually consistent lipid inputs.

Canonical units (converters provided for the common alternatives):
  cholesterol   mmol/L      (x 38.67 -> mg/dL)
  HbA1c         %  (DCCT)   (-> mmol/mol via IFCC)
  SBP/DBP       mmHg
  eGFR          mL/min/1.73 m^2
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

# --- unit converters --------------------------------------------------------
def hba1c_pct_to_mmol(pct: float) -> float:
    """IFCC: mmol/mol = 10.929 * (DCCT% - 2.15)."""
    return 10.929 * (pct - 2.15)

def hba1c_mmol_to_pct(mmol: float) -> float:
    return mmol / 10.929 + 2.15

def chol_mgdl_to_mmol(mgdl: float) -> float:
    return mgdl / 38.67

def chol_mmol_to_mgdl(mmol: float) -> float:
    return mmol * 38.67


@dataclass
class Patient:
    # --- demographics ---
    age: float                          # years
    female: bool
    ethnicity: str = "white"            # white | south_asian | black | other  (PCE/QRISK3)

    # --- diabetes ---
    diabetes_type: int = 1              # 1 or 2
    duration: float = 15.0              # years since diagnosis
    age_at_diagnosis: Optional[float] = None  # if None, derived as age - duration

    # --- glycaemia ---
    hba1c_pct: float = 8.0

    # --- blood pressure ---
    sbp: float = 130.0
    dbp: float = 78.0
    on_bp_treatment: bool = False

    # --- lipids (coherent panel, mmol/L) ---
    total_chol: float = 4.8
    hdl: float = 1.4
    triglycerides: float = 1.2
    ldl_override: Optional[float] = None   # set to bypass Friedewald

    # --- renal ---
    egfr: float = 95.0
    albuminuria: str = "normal"         # normal | micro | macro
    acr_mg_g: Optional[float] = None    # albumin:creatinine ratio if needed

    # --- lifestyle / other ---
    smoker: bool = False
    bmi: float = 25.0
    regular_exercise: bool = True       # Steno: ">=3.5 h/week"
    retinopathy: bool = False
    af: bool = False                    # atrial fibrillation (QRISK3)
    prior_cvd: bool = False
    on_statin: bool = False
    family_history_cvd: bool = False

    # --- SCORE2 calibration region (Czech Republic = 'high') ---
    risk_region: str = "high"           # low | moderate | high | very_high

    # extra comorbidity flags (QRISK3) default off; documented as held at baseline
    extras: dict = field(default_factory=dict)

    # --- derived lipid quantities ---
    @property
    def ldl(self) -> float:
        if self.ldl_override is not None:
            return self.ldl_override
        # Friedewald (mmol/L): LDL = TC - HDL - TG/2.2
        return max(0.3, self.total_chol - self.hdl - self.triglycerides / 2.2)

    @property
    def non_hdl(self) -> float:
        return self.total_chol - self.hdl

    @property
    def tc_hdl_ratio(self) -> float:
        return self.total_chol / self.hdl

    @property
    def hba1c_mmol(self) -> float:
        return hba1c_pct_to_mmol(self.hba1c_pct)

    @property
    def onset_age(self) -> float:
        return self.age_at_diagnosis if self.age_at_diagnosis is not None else self.age - self.duration

    def copy_with(self, **changes) -> "Patient":
        from dataclasses import replace
        return replace(self, **changes)
