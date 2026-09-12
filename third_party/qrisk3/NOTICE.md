# QRISK3-2017 attribution and source

Copyright 2017 ClinRisk Ltd. Licensed under GNU LGPL version 3 or, at your option, any later version. The LGPL incorporates provisions of GPL version 3; both texts are included in `LICENSES/`. No warranty is provided.

The original C source is preserved without changes in `qrisk3-2017.c`. Retrieved from [sisuhealthgroup/qrisk3](https://github.com/sisuhealthgroup/qrisk3/blob/019ded12978a570b4be21957e838fa954d6389b2/src/lib/original/qrisk3.c), commit `019ded12978a570b4be21957e838fa954d6389b2`. Both function bodies match, after removal of comments and whitespace, the ClinRisk source preserved in [CRAN QRISK3](https://github.com/cran/QRISK3/blob/f895997c302c6d9f417e82eb7060094f7e47d9f0/inst/extdata/QRISK3_2017_src.txt), commit `f895997c302c6d9f417e82eb7060094f7e47d9f0`. This repository does not include the GPL-licensed R wrapper.

SHA-256 of the bundled C file: `98bb0cd7071d49fca2d4620f1d447313838f55253616110d3888b3df0cc02aa4`.

`eval/models/qrisk3.py` and `metatool/qrisk3.js` are modified Python and JavaScript ports (2026) distributed under LGPL-3.0-or-later. Modifications include language translation, missing-input defaults, age eligibility and continuous-age evaluation. The browser port exposes the restricted inputs of this comparison tool and assumes unlisted comorbidities and medications are absent. Both modules are supplied as editable source and can be replaced or modified; no obfuscation or signing prevents relinking. `python -m eval.test_qrisk3_source` compiles the bundled original source temporarily and compares both ports offline.

All QRISK3 numerical outputs in the browser and CSV datasets are accompanied by this notice. The upstream additional terms require that the following disclaimer remain with scores and be displayed or prominently accessible beside displayed scores. Redistributors must retain this requirement.

## Upstream disclaimer (verbatim)

The initial version of this file, to be found at http://svn.clinrisk.co.uk/opensource/qrisk2, faithfully implements QRISK3-2017.
ClinRisk Ltd. have released this code under the GNU Lesser General Public License to enable others to implement the algorithm faithfully.
However, the nature of the GNU Lesser General Public License is such that we cannot prevent, for example, someone accidentally
altering the coefficients, getting the inputs wrong, or just poor programming.
ClinRisk Ltd. stress, therefore, that it is the responsibility of the end user to check that the source that they receive produces the same
results as the original code found at https://qrisk.org.
Inaccurate implementations of risk scores can lead to wrong patients being given the wrong treatment.
