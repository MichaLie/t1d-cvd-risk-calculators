"""Fresh Python/JS parity across all 11 endpoints, varied inputs and age boundaries.

Uses no stored reference risks. This detects port drift, not shared formula errors.
"""
import json
import math
import subprocess
from pathlib import Path
import numpy as np
from eval.harness.patient import Patient
from eval.harness.models import REGISTRY, _score2
from eval.models.cederholm import cederholm_risk5

ROOT=Path(__file__).resolve().parents[1]
NAMES={'Steno-CVD':'Steno-CVD','Steno-IHDstroke':'Steno-IHD/stroke','SCORE2-Diabetes':'SCORE2-Diabetes','SCORE2':'SCORE2','PCE':'PCE (ACC/AHA)','QRISK3':'QRISK3','PREVENT':'AHA PREVENT','UKPDS-CVD':'UKPDS','Framingham':'Framingham','ADVANCE*':'ADVANCE*'}

def main():
    rng=np.random.default_rng(20260912)
    ages=[18,24.999,25,29.999,30,39.999,40,69,69.999,70,74,74.999,75,79,79.999,80,84,84.999,85,90]
    records=[]
    for i in range(2400):
        age=ages[i%len(ages)] if i<160 else float(rng.uniform(18,90))
        onset=float(rng.uniform(1,age));tc=float(rng.uniform(3,8));hdl=float(rng.uniform(.6,2.4))
        p=Patient(age=age,female=bool(i%2),duration=age-onset,age_at_diagnosis=onset,
            ethnicity=['white','south_asian','black','other'][i%4],hba1c_pct=float(rng.uniform(5.5,13)),
            sbp=float(rng.uniform(95,200)),dbp=65,total_chol=tc,hdl=hdl,triglycerides=.6,
            egfr=float(rng.uniform(15,150)),bmi=float(rng.uniform(17,40)),albuminuria=['normal','micro','macro'][i%3],
            risk_region=['low','moderate','high','very_high'][(i//4)%4],
            **{k:bool(rng.integers(2)) for k in ['smoker','on_bp_treatment','on_statin','af','retinopathy','prior_cvd','family_history_cvd','regular_exercise']})
        js=dict(vars(p),onset_age=p.onset_age,ldl=p.ldl,tc_hdl_ratio=p.tc_hdl_ratio,diabetes=True,ethrisk={'white':1,'south_asian':2,'black':7,'other':9}[p.ethnicity])
        risks={NAMES[n]:f(p) for n,(_,_,f) in REGISTRY.items()}
        risks['Cederholm (5y)']=cederholm_risk5(age=p.age,duration=p.duration,hba1c_pct=p.hba1c_pct,sbp=p.sbp,total_chol=p.total_chol,hdl=p.hdl,smoker=p.smoker,macroalbuminuria=p.albuminuria=='macro',prior_cvd=p.prior_cvd)
        risks['SCORE2 diabetes']=_score2(p,diabetes_term=True)
        records.append({'patient':js,'expected':{k:v if math.isfinite(v) else None for k,v in risks.items()}})
    script=r'''
const M=require('./metatool/models.js');let input='';process.stdin.on('data',s=>input+=s);process.stdin.on('end',()=>{
 let max=0,n=0;
 for(const {patient:p,expected} of JSON.parse(input))for(const [name,ref] of Object.entries(expected)){
  const got=name==='SCORE2 diabetes'?M.score2(p,{diabetesTerm:true}):M.MODELS[name].fn(p);
  if(ref===null){if(!Number.isNaN(got))throw Error(name+': expected NaN');}
  else {if(!Number.isFinite(got)||Math.abs(got-ref)>1e-9)throw Error(name+': '+got+' != '+ref);max=Math.max(max,Math.abs(got-ref));n++;}
 }
 console.log(JSON.stringify({profiles:2400,endpoints:11,additional_variants:1,finite_comparisons:n,max_abs_difference_pp:max,tolerance_pp:1e-9,status:'PASS'}));
});'''
    result=subprocess.run(['node','-e',script],input=json.dumps(records),text=True,capture_output=True,cwd=ROOT,check=True)
    print(result.stdout.strip())

if __name__=='__main__':main()
