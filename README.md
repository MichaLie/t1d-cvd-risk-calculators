# Cardiovascular risk prediction in type 1 diabetes: critical appraisal of current tools and an in-silico head-to-head comparison

Companion research software, version **2.0.0**, for the manuscript with the title above. The browser tool compares published risk equations; the Python pipeline measures their agreement in a reproducible synthetic type 1 diabetes cohort. No patient records or observed cardiovascular outcomes are included. Agreement does not establish predictive accuracy, calibration, clinical benefit or suitability for treatment decisions.

[Open the browser calculator](https://michalie.github.io/t1d-cvd-risk-calculators/metatool/) · [Methods and model scope](METHODS.md) · [Figure legends](submission_figures/FIGURE_LEGENDS.md)

The hosted calculator follows the published GitHub Pages version. To run this checkout, open `metatool/index.html` in a browser, or serve the repository with `python -m http.server 8000` and visit `http://localhost:8000/metatool/`. Inputs remain in the browser; the calculator requires no server, account or external scripts.

## Scope

The numerical comparison contains ten 10-year endpoints from nine model families: Steno composite CVD and IHD/stroke, SCORE2-Diabetes, SCORE2, PCE, QRISK3, PREVENT, UKPDS-CVD, Framingham and ADVANCE. Cederholm’s native five-year endpoint is available separately in the browser. General-population and T2D equations are applied to T1D as an exploratory comparison, outside their intended populations where applicable.

The Scottish–Swedish model remains in the literature figures but is excluded from the calculator and numerical analysis because the sources available to this project do not establish a complete reproducible final-model specification. See the [original publication](https://doi.org/10.1007/s00125-021-05478-4) and [authors’ illustrative tool](https://diabepi.shinyapps.io/cvdrisk/). Other material adaptations, including ADVANCE’s centring/horizon and the UKPDS combined endpoint, are described in [METHODS.md](METHODS.md).

## Reproduce and verify

Use Python 3.12, Node.js 22 and a C compiler (`cc`, for the offline QRISK3 reference test). Install the hash-pinned dependencies in a virtual environment (`requirements-tested.in` records the direct versions used to generate the lock):

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-lock.txt
python -m eval.verify
```

This command runs the numerical, input-handling and Python/JavaScript checks; compares QRISK3 against the bundled original C source; regenerates the seeded analysis and sensitivity tables; and builds all six figures. It writes generated tables to `eval/out/` and final PDF/600-dpi PNG artwork to `submission_figures/`. The continuous-integration workflow runs the same command. Tests establish specified implementation properties, not clinical validation.

For analysis or figure generation separately:

```sh
python -m eval.run_eval
python -m eval.supplement
python -m eval.robustness
python -m eval.build_submission_figures
```

The primary cohort contains 10,000 profiles, seed 20260613. Only compact final summary tables are versioned; per-profile and pair-level tables are reproducible generated outputs. [Results documentation](eval/out/README.md) describes their interpretation. Literature values and publication locators are stored in `eval/figure_data.json`. Figure titles and explanatory notes are supplied as separate legends, without embedded captions in the artwork.

## Citation and licensing

Use [CITATION.cff](CITATION.cff) and cite the archived software version actually used. The associated manuscript title is given above; it does not imply that the manuscript has been published. A DOI for this software version must identify the corresponding archived release.

Original project code is MIT licensed. The QRISK3 Python/JavaScript ports and bundled ClinRisk C source are **LGPL-3.0-or-later**, with the upstream disclaimer and full licence texts included. Dataset and figure reuse is covered by CC BY 4.0; QRISK3 outputs must retain the [QRISK3 notice and disclaimer](third_party/qrisk3/NOTICE.md). See [LICENSE](LICENSE) for the scope of each licence.
