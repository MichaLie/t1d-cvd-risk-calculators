"""
Pooled Cohort Equations (ACC/AHA 2013, Goff et al., Circulation 2014;129:S49).
Sex- and race-specific 10-yr hard-ASCVD (MI/CHD death + stroke). Ages 40-79.
Cholesterol inputs in mg/dL (convert mmol/L * 38.67). Diabetes is a binary;
PCE makes no T1D/T2D distinction (a key 'borrowing' limitation for this review).

risk = 1 - S0 ** exp(IndX - MeanIndX)
"""
from __future__ import annotations
from math import exp, log

MMOL_TO_MGDL = 38.67

# group -> betas (missing term = 0), plus S0 and centering mean
G = {
    "white_female": dict(ln_age=-29.799, ln_age2=4.884, ln_tc=13.540, ln_age_tc=-3.114,
        ln_hdl=-13.578, ln_age_hdl=3.149, ln_sbp_t=2.019, ln_sbp_u=1.957,
        smk=7.574, ln_age_smk=-1.665, dm=0.661, S0=0.9665, mean=-29.18),
    "black_female": dict(ln_age=17.114, ln_tc=0.940, ln_hdl=-18.920, ln_age_hdl=4.475,
        ln_sbp_t=29.291, ln_age_sbp_t=-6.432, ln_sbp_u=27.820, ln_age_sbp_u=-6.087,
        smk=0.691, dm=0.874, S0=0.9533, mean=86.61),
    "white_male": dict(ln_age=12.344, ln_tc=11.853, ln_age_tc=-2.664, ln_hdl=-7.990,
        ln_age_hdl=1.769, ln_sbp_t=1.797, ln_sbp_u=1.764, smk=7.837, ln_age_smk=-1.795,
        dm=0.658, S0=0.9144, mean=61.18),
    "black_male": dict(ln_age=2.469, ln_tc=0.302, ln_hdl=-0.307, ln_sbp_t=1.916,
        ln_sbp_u=1.809, smk=0.549, dm=0.645, S0=0.8954, mean=19.54),
}


def _group(female: bool, black: bool) -> str:
    return f"{'black' if black else 'white'}_{'female' if female else 'male'}"


def pce_risk(*, female: bool, age: float, total_chol_mgdl: float, hdl_mgdl: float,
             sbp: float, treated_bp: bool, smoker: bool, diabetes: bool,
             black: bool = False) -> float:
    """10-yr ASCVD risk (%). Returns NaN outside 40-79."""
    if not (40 <= age < 80):
        return float("nan")
    b = G[_group(female, black)]
    la, ltc, lhdl, lsbp = log(age), log(total_chol_mgdl), log(hdl_mgdl), log(sbp)
    ind = (b.get("ln_age", 0) * la + b.get("ln_age2", 0) * la * la
           + b.get("ln_tc", 0) * ltc + b.get("ln_age_tc", 0) * la * ltc
           + b.get("ln_hdl", 0) * lhdl + b.get("ln_age_hdl", 0) * la * lhdl
           + b.get("smk", 0) * smoker + b.get("ln_age_smk", 0) * la * smoker
           + b.get("dm", 0) * (1.0 if diabetes else 0.0))
    if treated_bp:
        ind += b.get("ln_sbp_t", 0) * lsbp + b.get("ln_age_sbp_t", 0) * la * lsbp
    else:
        ind += b.get("ln_sbp_u", 0) * lsbp + b.get("ln_age_sbp_u", 0) * la * lsbp
    return (1 - b["S0"] ** exp(ind - b["mean"])) * 100.0


if __name__ == "__main__":
    # Guideline worked example: age55, TC213, HDL50, untreated SBP120, nonsmoker, nondiabetic
    kw = dict(age=55, total_chol_mgdl=213, hdl_mgdl=50, sbp=120,
              treated_bp=False, smoker=False, diabetes=False)
    expd = {("white", "female"): 2.1, ("white", "male"): 5.3,
            ("black", "female"): 3.0, ("black", "male"): 6.1}
    print(f"{'race':6} {'sex':7} {'exp%':>5} {'got%':>5}")
    for (race, sex), e in expd.items():
        g = pce_risk(female=(sex == "female"), black=(race == "black"), **kw)
        print(f"{race:6} {sex:7} {e:5.1f} {g:5.2f}")
