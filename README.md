# Cardiovascular risk calculators in type 1 diabetes — code, data & open meta-calculator

Open, reproducible companion to the study *"Cardiovascular risk calculators in type 1 diabetes:
a critical appraisal of dedicated and borrowed tools, their guideline standing, an in-silico
head-to-head of their discordance, and an open meta-calculator."*

This repository contains everything needed to reproduce the quantitative analysis and to inspect
and run the risk calculators yourself. It has two parts:

1. **`eval/`** — a reproducible pipeline that re-implements 12 published cardiovascular-risk
   calculators from their source-paper coefficients, runs them on a seeded synthetic type-1-diabetes
   cohort, and quantifies how much they disagree (linear-weighted Cohen's κ, Bland–Altman, risk-ratio).
2. **`metatool/`** — a self-contained browser meta-calculator that runs the implemented calculators
   side by side for one patient, flags where they disagree on risk category, and lets you recalibrate
   to local risk. Every coefficient is open in `models.js`.

> **This is an agreement/discordance study, not an accuracy study.** No patient outcomes are used.
> It quantifies how published tools disagree on identical inputs — not which one is "right."
> No individual-patient data are used anywhere; the cohort is synthetic and seeded.

## Calculators included

**T1D-specific:** Steno Type 1 Risk Engine, Scottish–Swedish model (McGurnaghan 2021),
Cederholm NDR (5-year). **Type-2-derived (off-label in T1D):** SCORE2-Diabetes, UKPDS Risk Engine,
ADVANCE. **General-population (off-label in T1D):** SCORE2, QRISK3, Pooled Cohort Equations (ACC/AHA),
AHA PREVENT, Framingham. The test harness checks source-paper worked examples, live-tool
comparisons where available, and regression guards; endpoint-specific status is reported in the
browser tool.

## Quickstart

Requires **Python 3.12** and (for the meta-tool tests only) **Node 18+**. No internet needed.

```bash
pip install -r requirements.txt

# reproduce the analysis (prints all statistics; writes results to eval/out/)
python -m eval.run_eval          # mean off-diagonal κ = 0.39 ; per-tool risk summary
python -m eval.smoke_test        # sanity check → "PIPELINE OK"

# regenerate the figures
python -m eval.figures              # κ heatmap
python -m eval.figures_companion    # timeline, predictor grid, C-stat forest, risk distributions
python -m eval.fig_flowchart        # decision flowchart

# the meta-calculator (no install, no server required)
open metatool/index.html            # or: python3 -m http.server -d metatool
node metatool/test_models.js        # validation: 36/36 should pass
```

The synthetic cohort is generated with a fixed seed (`20260613`), so every reported number is
exactly reproducible.

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
  out/          generated outputs (committed for convenience; all regenerable):
                  kappa_matrix.csv, cohort_risks.csv, and the six figures
metatool/
  index.html    the meta-calculator UI (self-contained)
  models.js     all 12 calculators ported to JavaScript (open coefficients)
  test_models.js validation against each source's worked example
  README.md
```

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

Its coefficients are taken from the published final model (McGurnaghan 2021, *Diabetologia*),
restoring the age-at-entry term omitted from the supplementary table, with a single calibration
constant fit to the authors' deployed tool (the cubic/interaction coefficients are published only
to three decimals). The authors' own R training code at `github.com/diabepi/t1cvdrisk` is
referenced for provenance but **not redistributed here**.

## License

- **Code** — MIT (see `LICENSE`).
- **Data & figures** (`eval/out/*.csv`, `eval/out/*.png`) — CC-BY-4.0.

## Citing

Please cite the associated paper and the archived repository release once available.

## Disclaimer

The meta-calculator is a transparent **decision-support and comparison** tool for research and
education. It is **not a new validated prediction model** and **not a regulated medical device**.
It must not be used for clinical care without local validation and appropriate regulatory approval.
