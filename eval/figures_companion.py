"""Source-checked literature figures and data-backed simulation distributions.
Titles, explanations and source locators are in submission_figures/FIGURE_LEGENDS.md
and figure_data.json. See submission_figures/FIGURE_LEGENDS.md for interpretation.
"""
import sys
from pathlib import Path
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.colors import ListedColormap
from eval.figure_style import WIDTH, DEFAULT_OUT, CTYPE, T1D_C, T2D_C, GEN_C, save_figure

DATA = json.loads((Path(__file__).with_name('figure_data.json')).read_text())

def predictor_grid():
    preds = DATA['predictor_domains']
    rows = DATA['predictors']
    M = np.array([r['values'] for r in rows])
    fig, ax = plt.subplots(figsize=(WIDTH, 5.1))
    ax.imshow(M, cmap=ListedColormap(['#f4f4f4', T1D_C]), vmin=0, vmax=1, aspect='auto')
    ax.set_xticks(range(len(preds)), labels=preds, rotation=58, ha='right', rotation_mode='anchor')
    ax.set_yticks(range(len(rows)), labels=[r['model'] for r in rows])
    ax.tick_params(length=0, pad=4)
    for i in range(len(rows)+1): ax.axhline(i-.5, color='white', lw=.7)
    for j in range(len(preds)+1): ax.axvline(j-.5, color='white', lw=.7)
    ax.axhline(4.5, color='#555555', lw=1)
    ax.axhline(8.5, color='#555555', lw=1)
    for tick, row in zip(ax.get_yticklabels(), rows): tick.set_color(CTYPE[row['type']])
    ax.legend(handles=[Patch(facecolor=T1D_C, label='Included'), Patch(facecolor='#f4f4f4', edgecolor='#999999', label='Not included')],
              loc='lower center', bbox_to_anchor=(.5,1.015), ncol=2, frameon=False, fontsize=8)
    for sp in ax.spines.values(): sp.set_visible(False)
    fig.legend(handles=[Line2D([],[],color=CTYPE[t],lw=2,label=l) for t,l in [('T1D','T1D-specific'),('T2D','T2D'),('general','General / mixed')]], loc='upper center', bbox_to_anchor=(.65,.995), ncol=3, frameon=False, fontsize=7.5)
    fig.subplots_adjust(left=.315, right=.985, bottom=.255, top=.855)
    save_figure(fig, 'fig_predictor_grid.png')


def bubble_size(n):
    return 25 + 18 * np.log10(n)


def timeline():
    fig, ax = plt.subplots(figsize=(WIDTH, 4.45))
    # Vertical staggering has no quantitative meaning; year is the x coordinate.
    layouts = {
        'Pittsburgh EDC': (2.12, -3, 11, 'right'),
        'Cederholm NDR': (1.92, 0, -22, 'center'),
        'EURODIAB': (2.15, 0, 11, 'center'),
        'Steno T1': (1.92, 0, -22, 'center'),
        'Scottish–Swedish': (2.15, -2, 11, 'right'),
        'LIFE-T1D': (1.92, 1, -22, 'center'),
        'UKPDS CHD': (.93, 0, -22, 'center'),
        'ADVANCE': (1.1, 0, 11, 'center'),
        'DIAL': (.93, 0, -22, 'center'),
        'SCORE2-Diabetes': (1.12, 7, 11, 'center'),
        'Framingham': (.12, 0, 11, 'center'),
        'PCE': (-.08, 0, -22, 'center'),
        'QRISK3': (.12, 0, 11, 'center'),
        'SCORE2': (-.08, -3, -22, 'center'),
        'PREVENT': (.12, 2, 11, 'center'),
    }
    for r in DATA['timeline']:
        y, dx, dy, ha = layouts[r['model']]
        ax.scatter(r['year'], y, s=bubble_size(r['n']), color=CTYPE[r['type']], edgecolor='white', lw=.6, zorder=3)
        ax.annotate(r['model'], (r['year'], y), xytext=(dx,dy), textcoords='offset points', ha=ha,
                    va='bottom' if dy>0 else 'top', fontsize=7.5)
    ax.set_yticks([0,1,2], labels=['General / mixed', 'Type 2 diabetes', 'Type 1 diabetes'])
    ax.tick_params(axis='y', length=0)
    ax.set_xlim(1999,2027); ax.set_ylim(-.72,2.72)
    ax.set_xticks([2000,2005,2010,2015,2020,2025]); ax.set_xlabel('Publication year')
    ax.grid(axis='x', alpha=.22, lw=.5)
    for y in [.5,1.5]: ax.axhline(y, color='#dddddd', lw=.5)
    for sp in ['top','right','left']: ax.spines[sp].set_visible(False)
    handles=[Line2D([],[],marker='o',ls='',markerfacecolor='#cccccc',markeredgecolor='#777777',
                    markersize=np.sqrt(bubble_size(n)),label=lab) for n,lab in [(1000,'1,000'),(100000,'100,000'),(10000000,'10,000,000')]]
    ax.legend(handles=handles, title='Derivation cohort size (log-scaled symbols)', loc='upper center', bbox_to_anchor=(.5,1.10),
              ncol=3, fontsize=7.5, title_fontsize=8, frameon=False, columnspacing=1.3)
    fig.subplots_adjust(left=.205,right=.985,bottom=.125,top=.87)
    save_figure(fig,'fig_model_timeline.png')


def cstat_forest():
    # Separate published estimates: no invented midpoint, no range presented as CI.
    rows=DATA['discrimination']
    fig, ax=plt.subplots(figsize=(WIDTH,6.45))
    y=len(rows)-1
    ticks=[]; labels=[]
    marker={'development':'s','external':'o','pooled':'D'}
    for r in rows:
        ticks.append(y); labels.append(r['label'])
        c=CTYPE[r['type']]
        ax.scatter(r['value'],y,marker=marker[r['stage']],s=27,color=c,edgecolor='white',lw=.35,zorder=3)
        ax.text(.913,y,format(r['value'], '.3f' if r['source']=='05' else '.2f'),ha='right',va='center',fontsize=7.5)
        y-=1
        if r.get('separator_after'): ax.axhline(y+.5,color='#cccccc',lw=.6)
    ax.set_yticks(ticks,labels=labels); ax.tick_params(axis='y',length=0,pad=4)
    ax.set_xlim(.65,.92);ax.set_ylim(-.7,len(rows)-.3)
    ax.set_xticks([.65,.70,.75,.80,.85,.90]); ax.set_xlabel('Reported C-statistic')
    ax.grid(axis='x',color='#e8e8e8',lw=.5)
    fig.legend(handles=[Line2D([],[],marker=m,ls='',color='#444444',label=l,markersize=5) for m,l in
                       [('s','Development / internal'),('o','External'),('D','Pooled')]],
              loc='upper center',bbox_to_anchor=(.5,.995),ncol=3,fontsize=7.5,frameon=False)
    for sp in ['top','right','left']:ax.spines[sp].set_visible(False)
    fig.subplots_adjust(left=.455,right=.975,bottom=.085,top=.925)
    save_figure(fig,'fig_cstat_forest.png')


def risk_distributions():
    # Use the exact frozen evaluation CSV also underlying Figure 4.
    risks=pd.read_csv(DEFAULT_OUT/'cohort_risks.csv')
    types=DATA['analysis_types']
    models=list(types)
    data={m:risks[m].dropna().to_numpy() for m in models}
    order=sorted(models,key=lambda m:np.median(data[m]))
    fig,ax=plt.subplots(figsize=(WIDTH,4.25))
    bp=ax.boxplot([data[m] for m in order],vert=False,patch_artist=True,showfliers=False,widths=.56)
    for patch,m in zip(bp['boxes'],order):patch.set_facecolor(CTYPE[types[m]]);patch.set_alpha(.8)
    for med in bp['medians']:med.set_color('black');med.set_linewidth(1)
    ax.set_yticks(range(1,len(order)+1),labels=[f"{DATA['analysis_labels'][m]} (n={len(data[m]):,})" for m in order])
    for x,ls in [(10,'--'),(20,'-.')]:ax.axvline(x,color='#555555',ls=ls,lw=.7)
    ax.set_xlim(0,100);ax.set_xticks(range(0,101,20));ax.set_xlabel('Predicted 10-year risk (%)')
    ax.set_ylim(.4,len(order)+.7)
    ax.legend(handles=[Patch(facecolor=c,label=l) for c,l in [(T1D_C,'T1D-specific'),(T2D_C,'T2D'),(GEN_C,'General / mixed')]],
              loc='lower center',bbox_to_anchor=(.35,1.025),ncol=3,frameon=False,fontsize=7.5)
    for sp in ['top','right']:ax.spines[sp].set_visible(False)
    fig.subplots_adjust(left=.365,right=.975,bottom=.13,top=.90)
    save_figure(fig,'fig_risk_distributions.png')

if __name__=='__main__':
    timeline();predictor_grid();cstat_forest();risk_distributions()
