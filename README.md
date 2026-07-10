# Cardiovascular risk prediction in type 1 diabetes — reproducible analysis and open comparison tool

Open, reproducible companion to *"Cardiovascular risk prediction in type 1 diabetes:
critical appraisal of current tools and an in-silico head-to-head comparison."*

This repository contains everything needed to reproduce the quantitative analysis and to inspect
and run the risk calculators yourself. It has two parts:

**Launch the browser meta-calculator:** https://michalie.github.io/t1d-cvd-risk-calculators/metatool/

1. **`eval/`** — a reproducible pipeline that implements 12 model endpoints from 11 calculator
   families using published equations plus explicitly documented adaptations. The agreement
   analysis runs the 11 ten-year or ten-year-adapted endpoints on a seeded synthetic
   type-1-diabetes cohort; the native five-year Cederholm endpoint is reported separately.
2. **`metatool/`** — a self-contained browser meta-calculator that runs the implemented calculators
   side by side for one patient, flags where they occupy different common analytic bands, and lets
   you recalibrate to local risk. Every coefficient is open in `models.js`.

> **This is an agreement/discordance study, not an accuracy study.** No patient outcomes are used.
> It quantifies how published tools disagree on identical inputs — not which one is "right."
> No individual-patient data are used anywhere; the cohort is synthetic and seeded.

## Calculators included

**T1D-specific:** Steno Type 1 Risk Engine, Scottish–Swedish model (McGurnaghan 2021),
Cederholm NDR (5-year). **Type-2-derived (off-label in T1D):** SCORE2-Diabetes, UKPDS Risk Engine,
ADVANCE. **General-population (off-label in T1D):** SCORE2, QRISK3, Pooled Cohort Equations (ACC/AHA),
AHA PREVENT, Framingham. The browser exposes 12 model endpoints from 11 calculator families. The
10-year agreement matrix contains 11 endpoints from 10 families; the native 5-year Cederholm
endpoint is excluded. The test harness performs selected source-paper, live-tool, and regression
checks. These are implementation checks, not external clinical validation; endpoint-specific
status is reported in the browser tool.

## Quickstart

Requires **Python 3.12** and (for the browser-tool tests) **Node 22**. No internet is needed after
dependencies are installed.

```bash
python -m pip install -r requirements-lock.txt  # tested, fully resolved environment
# or: python -m pip install -r requirements.txt # broader compatible lower bounds

# reproduce the analysis (prints all statistics; writes results to eval/out/)
python -m eval.run_eval          # mean off-diagonal κ = 0.39 ; per-tool risk summary
python -m eval.smoke_test        # sanity check → "PIPELINE OK"
python -m eval.model_assertions  # model-level regression and source checks
python -m eval.supplement        # cohort, assumptions, sensitivity and coverage tables

# regenerate the figures
python -m eval.figures              # κ heatmap
python -m eval.figures_companion    # timeline, predictor grid, C-stat forest, risk distributions
python -m eval.fig_flowchart        # decision flowchart

# the meta-calculator (no install, no server required)
open metatool/index.html            # or: python3 -m http.server -d metatool
node metatool/test_models.js        # implementation checks: 41/41 should pass
```

The synthetic cohort is generated with a fixed seed (`20260613`), so results are deterministic at
the reported precision in a compatible Python/NumPy environment.

The manuscript release was verified with Python 3.12.0, NumPy 2.2.6, pandas 2.3.3,
SciPy 1.16.3, Matplotlib 3.10.8 and Node 22.14.0. `requirements-tested.in` records the tested
top-level Python versions, while `requirements-lock.txt` contains the fully resolved dependency
graph with hashes. `requirements.txt` retains broader lower bounds for ordinary use.

## Browser meta-calculator

The meta-calculator is a static browser app: it has no backend, no build step, no package install,
and no external assets. It can be opened directly from `metatool/index.html` or served from any
static host.

For GitHub Pages, publish the repository from the root of the main branch. The top-level
`index.html` redirects to `metatool/index.html`, so the repository Pages URL will open the
calculator directly.

## Layout

```
eval/
  harness/      patient schema, synthetic-cohort generator, discordance metrics, model registry
  models/       one file per calculator (published coefficients, fully commented)
  run_eval.py   the main discordance run
  figures.py, figures_companion.py, fig_flowchart.py
  smoke_test.py
  supplement.py supplementary cohort, assumption, sensitivity, and coverage tables
  out/          generated outputs (committed for convenience; all regenerable):
                  kappa_matrix.csv, cohort_risks.csv, synthetic_cohort.csv,
                  synthetic_cohort_assumptions.csv, sensitivity_summary.csv,
                  sensitivity_model_summary.csv, and the six figures
metatool/
  index.html    the meta-calculator UI (self-contained)
  models.js     12 model endpoints from 11 calculator families ported to JavaScript
  test_models.js selected worked-example, live-tool, and regression checks
  README.md
```

The CSV outputs are the canonical supplementary-analysis records. `synthetic_id` links rows in
`synthetic_cohort.csv` and `cohort_risks.csv`; both files use the same deterministic row order.
The formatted journal workbook is distributed as a fixed asset with the GitHub release.

### Figures

| Figure | File (`eval/out/`) |
|---|---|
| Figure 1 | fig_model_timeline.png |
| Figure 2 | fig_predictor_grid.png |
| Figure 3 | fig_cstat_forest.png |
| Figure 4 | kappa_heatmap.png |
| Figure 5 | fig_risk_distributions.png |
| Figure 6 | fig_decision_flowchart.png |

## A note on the Scottish–Swedish model

Its coefficients are taken from the published final model (McGurnaghan 2021, *Diabetologia*).
The published coefficient table (Table 4) omits the age-at-entry term appearing in the final
multivariable model; that term is restored here. A fitted ×1.32 constant aligns selected deployed-
tool output because the published cubic and interaction coefficients are rounded to three decimals.
This is a transparent reconstruction, not a coefficient-complete independent reproduction. The
authors' R training code at `github.com/diabepi/t1cvdrisk` is referenced for provenance but **not
redistributed here**.

## License

- **Code** — MIT (see `LICENSE`).
- **Data & figures** (`eval/out/*.csv`, `eval/out/*.png`) — CC-BY-4.0.

## Citing

Please cite the associated paper and this versioned software release:

> Liegertová M. T1D-CVD risk calculators: reproducible agreement analysis and open comparison
> tool. Version 1.0.0. 2026. https://github.com/MichaLie/t1d-cvd-risk-calculators/releases/tag/v1.0.0

Machine-readable citation metadata are provided in [`CITATION.cff`](CITATION.cff). Version 1.0.0
adds the supplementary analysis, manuscript-aligned figures, and public documentation.

## Disclaimer

The meta-calculator is a transparent **decision-support and comparison** tool for research and
education. It is **not a new validated prediction model** and **not a regulated medical device**.
It must not be used for clinical care without local validation and appropriate regulatory approval.
