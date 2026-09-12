"""Exploratory sensitivity checks. No outcome-based validity inference.

Fixed in advance of this run: seed offsets 0..4; all-tools common support;
remove the clipped one-year duration boundary; remove LDL floor/high-TG profiles;
exclude the ADVANCE horizon extrapolation. No scenario is selected by its result.
"""
from itertools import combinations
from pathlib import Path
import numpy as np
import pandas as pd
from eval.harness.profiles import make_synthetic_cohort, make_factorial
from eval.harness.models import REGISTRY
from eval.harness.categories import band
from eval.harness.discordance import cohen_kappa
from eval.models.ukpds import ukpds_chd

OUT=Path(__file__).resolve().parent/'out'

def pair_table(risks,scenario,mask):
    rows=[]
    for a,b in combinations(risks,2):
        use=mask & np.isfinite(risks[a]) & np.isfinite(risks[b])
        ra,rb=risks[a][use],risks[b][use]
        ca=np.array([band(x) for x in ra]);cb=np.array([band(x) for x in rb])
        rows.append(dict(scenario=scenario,model_a=a,model_b=b,n=int(use.sum()),
            kappa=cohen_kappa(ca,cb,'linear',3) if len(ca)>=30 else np.nan,
            exact_agreement_percent=float(np.mean(ca==cb))*100 if len(ca) else np.nan,
            mean_difference_pp=float(np.mean(ra-rb)) if len(ra) else np.nan))
    return rows

def oxford_stroke(p):
    # Sensitivity ONLY: Oxford DTU 05-Sep-2024 sheet calls this Log Lipid Ratio.
    # The original Kothari 2002 p1778 equation uses raw ratio minus 5.11.
    # Keep age at diagnosis and use full-precision stroke parameters from the sheet.
    q=.001854749*1.091797834**(p.onset_age-55)*.700038749**p.female*1.546546697**p.smoker
    q*=1.122089348**((p.sbp-135.549791)/10)*1.138088189**(np.log(p.tc_hdl_ratio)-1.593026)*8.553988106**p.af
    d=1.145004121
    return -np.expm1(-q*d**p.duration*(1-d**10)/(1-d))

def main():
    OUT.mkdir(exist_ok=True)
    rows=[];summary=[]
    for offset in range(5):
        cohort=make_synthetic_cohort(10000,seed=20260613+offset)
        risks={m:np.array([f(p) for p in cohort]) for m,(_,_,f) in REGISTRY.items()}
        masks={f'Seed {20260613+offset}':np.ones(len(cohort),bool)}
        if offset==0:
            masks.update({
                'All-tools common age support':np.logical_and.reduce([np.isfinite(v) for v in risks.values()]),
                'Exclude duration clipped to one year':np.array([not np.isclose(p.duration,1) for p in cohort]),
                'Exclude floored LDL or TG >=4.5':np.array([p.total_chol-p.hdl-p.triglycerides/2.2>=.3 and p.triglycerides<4.5 for p in cohort]),
            })
            uk=risks['UKPDS-CVD']
            alt=[]
            for p in cohort:
                chd=ukpds_chd(age_at_diagnosis=p.onset_age,female=p.female,smoker=p.smoker,hba1c_pct=p.hba1c_pct,sbp=p.sbp,tc_hdl=p.tc_hdl_ratio,duration=p.duration)/100
                alt.append(100*(1-(1-chd)*(1-oxford_stroke(p))))
            alt=np.array(alt)
            pd.DataFrame({'synthetic_id':np.arange(1,len(cohort)+1),'ukpds_paper_cvd_percent':uk,'ukpds_oxford_stroke_variant_cvd_percent':alt,'difference_pp':alt-uk}).to_csv(OUT/'ukpds_source_conflict_sensitivity.csv',index=False)
        for scenario,mask in masks.items():
            pairs=pair_table(risks,scenario,mask);rows.extend(pairs)
            finite=[r['kappa'] for r in pairs if np.isfinite(r['kappa'])]
            summary.append(dict(scenario=scenario,n_profiles=int(mask.sum()),mean_pairwise_kappa=np.mean(finite),n_pairs=len(finite)))
        if offset==0:
            for scenario,keep in [('Exclude ADVANCE extrapolation',[m for m in risks if m != 'ADVANCE*']),('Narrower atherosclerotic endpoints',['Steno-IHDstroke','SCORE2-Diabetes','SCORE2','PCE','QRISK3'])]:
                pairs=pair_table({m:risks[m] for m in keep},scenario,np.ones(len(cohort),bool));rows.extend(pairs)
                vals=[r['kappa'] for r in pairs if np.isfinite(r['kappa'])]
                summary.append(dict(scenario=scenario,n_profiles=len(cohort),mean_pairwise_kappa=np.mean(vals),n_pairs=len(vals)))
    grid=make_factorial()
    gr={m:np.array([f(p) for p in grid]) for m,(_,_,f) in REGISTRY.items()}
    pairs=pair_table(gr,'Structured factorial grid',np.ones(len(grid),bool));rows.extend(pairs)
    vals=[r['kappa'] for r in pairs if np.isfinite(r['kappa'])]
    summary.append(dict(scenario='Structured factorial grid',n_profiles=len(grid),mean_pairwise_kappa=np.mean(vals),n_pairs=len(vals)))
    pd.DataFrame(rows).to_csv(OUT/'robustness_pairwise.csv',index=False)
    df=pd.DataFrame(summary);df.to_csv(OUT/'robustness_summary.csv',index=False)
    print(df.to_string(index=False))

if __name__=='__main__':main()
