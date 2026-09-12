"""Build the six publication figures and verify their numerical source data.
Run from repository root: python -m eval.build_submission_figures
Uses the generated cohort CSVs; does not rerun or change calculator models.
"""
import json
import os
import subprocess
import sys
import numpy as np
import pandas as pd
from eval.figure_style import ROOT, DEFAULT_OUT

OUT=ROOT/'submission_figures'
OUT.mkdir(exist_ok=True)
data=json.loads((ROOT/'eval/figure_data.json').read_text())
risks=pd.read_csv(DEFAULT_OUT/'cohort_risks.csv')
K=pd.read_csv(DEFAULT_OUT/'kappa_matrix.csv',index_col=0)
models=list(data['analysis_types'])
assert len(risks)==10000 and risks['synthetic_id'].is_unique
assert list(K.columns)==list(K.index)==models
assert np.isfinite(K.values).all() and np.allclose(K.values,K.values.T)
pairs=[]
for i,a in enumerate(models):
    for b in models[i+1:]:
        mask=np.isfinite(risks[a]) & np.isfinite(risks[b])
        ac=np.digitize(risks.loc[mask,a],[10,20]);bc=np.digitize(risks.loc[mask,b],[10,20])
        table=np.bincount(ac*3+bc,minlength=9).reshape(3,3).astype(float)
        n=table.sum(); expected=np.outer(table.sum(axis=1),table.sum(axis=0))/n
        distance=np.abs(np.arange(3)[:,None]-np.arange(3)[None,:])
        kappa=1-(table*distance).sum()/(expected*distance).sum()
        assert abs(kappa-K.loc[a,b])<1e-12,(a,b,kappa,K.loc[a,b])
        pairs.append(dict(model_a=a,model_b=b,n=int(n),kappa=kappa))
summary=[]
for m in models:
    r=risks[m].dropna().to_numpy();assert np.isfinite(r).all() and ((r>=0)&(r<=100)).all()
    q1,median,q3=np.percentile(r,[25,50,75]);iqr=q3-q1
    lo=r[r>=q1-1.5*iqr].min();hi=r[r<=q3+1.5*iqr].max()
    summary.append(dict(model=m,n=len(r),q1=q1,median=median,q3=q3,whisker_low=lo,whisker_high=hi,
                        min=r.min(),max=r.max(),outliers_not_drawn=int(((r<lo)|(r>hi)).sum())))
pd.DataFrame(pairs).to_csv(DEFAULT_OUT/'figure_4_pairwise_values.csv',index=False)
pd.DataFrame(summary).to_csv(DEFAULT_OUT/'figure_5_boxplot_values.csv',index=False)
assert len(data['timeline'])==15 and len(data['predictors'])==14 and len(data['discrimination'])==17
assert all(len(r['values'])==11 and set(r['values'])<={0,1} for r in data['predictors'])
env={**os.environ,'FIG_SUBMISSION':'1','FIG_OUT_DIR':str(OUT)}
for module in ['eval.figures_companion','eval.figures','eval.fig_flowchart']:
    subprocess.run([sys.executable,'-m',module],cwd=ROOT,env=env,check=True)
legends=(OUT/'FIGURE_LEGENDS.md').read_text()
legend_lengths={}
for block in legends.split('## Figure ')[1:]:
    heading,body=block.split('\n',1);title=heading.split('. ',1)[1]
    legend_lengths[heading]={'title_words':len(title.split()),'legend_words':len(body.split())}
assert len(legend_lengths)==6
stats=pd.DataFrame(pairs)['kappa']
checks={'cohort_n':len(risks),'distinct_pairs_checked':len(pairs),'kappa_max_abs_error_limit':1e-12,
        'mean_pairwise_kappa':stats.mean(),'min_pairwise_kappa':stats.min(),'max_pairwise_kappa':stats.max(),
        'legend_lengths':legend_lengths}
print(json.dumps(checks,indent=2))
print(f'PASS: {len(pairs)} pairwise kappa values; {len(models)} boxplot summaries; 6 separate legends; 12 figure files.')
