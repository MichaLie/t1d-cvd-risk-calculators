"""Agreement heatmap, linked to the evaluated cohort and separate figure legend."""
import sys
from pathlib import Path
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from eval.figure_style import WIDTH,DEFAULT_OUT,save_figure

K=pd.read_csv(DEFAULT_OUT/'kappa_matrix.csv',index_col=0)
DATA=json.loads(Path(__file__).with_name('figure_data.json').read_text())
assert list(K.index)==list(K.columns), 'Kappa row/column order differs'
M=K.to_numpy()
assert np.allclose(M,M.T,equal_nan=True), 'Kappa matrix must be symmetric'
labels=[DATA['analysis_labels'][n] for n in K.columns]
fig,ax=plt.subplots(figsize=(WIDTH,5.8))
cmap=LinearSegmentedColormap.from_list('agree',['#f7fbff','#6baed6','#08306b'])
im=ax.imshow(M,cmap=cmap,vmin=0,vmax=1)
ax.set_xticks(range(len(labels)),labels=labels,rotation=55,ha='right',rotation_mode='anchor')
ax.set_yticks(range(len(labels)),labels=labels)
ax.tick_params(length=0,pad=3)
for i in range(len(labels)):
    for j in range(len(labels)):
        v=M[i,j]
        ax.text(j,i,f'{v:.2f}',ha='center',va='center',fontsize=7.2,color='white' if v>.62 else '#151515')
cb=fig.colorbar(im,ax=ax,fraction=.045,pad=.03)
cb.set_label("Linearly weighted Cohen’s κ",fontsize=8)
for s in ax.spines.values():s.set_visible(False)
fig.subplots_adjust(left=.245,right=.91,bottom=.23,top=.99)
save_figure(fig,'kappa_heatmap.png')
