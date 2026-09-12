"""Author synthesis of guideline-aware risk discussion; detailed caveats in legend."""
import sys
from pathlib import Path
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from eval.figure_style import WIDTH,save_figure

fig,ax=plt.subplots(figsize=(WIDTH,4.6))
ax.set_xlim(0,10);ax.set_ylim(0,10);ax.axis('off')
steps=[
 ('1  Establish the clinical context', 'Prior ASCVD, organ damage and prevention needs', '#994a11'),
 ('2  Decide whether risk estimation adds value', 'Follow the applicable T1D guideline pathway', '#2166ac'),
 ('3  If scoring is appropriate, assess model suitability', 'Endpoint, horizon, eligibility and population calibration', '#33486e'),
 ('4  Discuss and implement prevention', 'Combine guideline recommendations with patient preferences', '#286b49'),
]
for i,(lead,body,color) in enumerate(steps):
 y=8.7-i*2.45
 ax.add_patch(FancyBboxPatch((.18,y-.85),9.64,1.70,boxstyle='round,pad=.08',fill=False,edgecolor=color,linewidth=1.4))
 ax.text(5,y+.28,lead,ha='center',va='center',color='#151515',fontsize=12,fontweight='bold')
 ax.text(5,y-.30,body,ha='center',va='center',color='#252525',fontsize=11)
 if i<3:
  ax.add_patch(FancyArrowPatch((5,y-.98),(5,y-1.47),arrowstyle='-|>',mutation_scale=13,lw=1,color='#555555'))
fig.subplots_adjust(left=.025,right=.975,bottom=.015,top=.985)
save_figure(fig,'fig_decision_flowchart.png')
