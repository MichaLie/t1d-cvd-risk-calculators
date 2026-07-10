# T1D-CVD Meta-Calculator

A transparent, open, self-contained web tool that runs implemented published
cardiovascular-risk calculators side by side for an adult with type 1 diabetes, shows
where they agree and diverge, and lets you recalibrate to local risk.

It is not a new prediction model. A clinically validated equation would require
individual-patient outcome data. This tool instead reproduces existing equations,
shows discordance explicitly, documents recalibration, and keeps coefficients open.
It is provided for research and education, not as a clinical decision rule or regulated
medical device.

## Run It

No build, no server, no dependencies are required for ordinary browser use. Either open
`index.html` in a browser, or serve the folder locally:

```bash
python3 -m http.server 8000
```

Nothing leaves the browser; all computation is client-side.

## Files

| File | What it is |
|------|------------|
| `index.html` | The UI: input form, grouped bar chart, discordance flag, recalibration, and transparency panel. |
| `models.js` | The engine: 12 calculator endpoints ported to JavaScript, with coefficients open and commented. Exports `T1DCVD` in the browser and `module.exports` in Node. |
| `test_models.js` | Implementation-check harness for selected source-paper examples, live-tool comparisons where available, and regression guards. |

## Included Tools

T1D-specific: Steno Type 1 Risk Engine (CVD; IHD/stroke), Scottish-Swedish
(McGurnaghan 2021), and Cederholm NDR (5-year).

T2D-derived, off-label in T1D: SCORE2-Diabetes, UKPDS Risk Engine, and ADVANCE.

General-population, off-label in T1D: SCORE2, QRISK3, PCE (ACC/AHA), AHA PREVENT,
and Framingham.

Each is grouped and colour-coded by class so an off-label borrowed model is not
mistaken for a T1D-native estimate.

## Implementation checks

```bash
node test_models.js     # 41/41 pass
```

The 41 checks cover selected source-paper examples and tables, live-tool comparisons where available,
and regression guards. They assess implementation consistency, not external clinical
validity. The Steno-IHD/stroke coefficients were checked against Vistisen 2016 Supplemental
Table 4, and selected Steno-CVD live-tool output was reproduced to the reported precision.

The native five-year Cederholm endpoint is displayed separately from the 10-year outputs,
without common analytic boundaries, and is excluded from the 10-year agreement matrix.

## Recalibration

- The SCORE2 family is recalibrated by risk region, using the published mechanism.
- T1D-specific tools take an optional observed/expected ratio that applies transparent
  cumulative-hazard scaling. Set it from a local registry O/E value when available.
  Default 1.0 means no additional user-supplied O/E scaling; it does not certify
  published calibration, and the Scottish–Swedish implementation still includes the
  fitted reconstruction constant described below.

## Reproducibility Note

The Scottish-Swedish implementation uses the published final-model coefficients. The
published coefficient table (Table 4) omits the age-at-entry term appearing in the final
multivariable model; that term is restored here. A fitted calibration constant (`x1.32`)
aligns selected output from the deployed calculator because the published cubic and
interaction coefficients are rounded to three decimals. Deprivation is fixed at quintile
3. This is a transparent reconstruction, not a coefficient-complete independent
reproduction.

## Status

Equations are human-traceable to published sources. Version 1.0.0 accompanies
*Cardiovascular risk prediction in type 1 diabetes: critical appraisal of current tools
and an in-silico head-to-head comparison*. Not for clinical use without local validation
and regulatory approval.
