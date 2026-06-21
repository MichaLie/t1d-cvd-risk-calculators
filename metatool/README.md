# T1D-CVD Meta-Calculator

A transparent, open, self-contained web tool that runs implemented published
cardiovascular-risk calculators side by side for an adult with type 1 diabetes, shows
where they agree and diverge, and lets you recalibrate to local risk.

It is not a new prediction model. A new validated equation would require
individual-patient outcome data. This tool instead reproduces existing equations,
shows discordance explicitly, documents recalibration, and keeps coefficients open.
Decision support only; not a substitute for clinical judgement or a regulated medical
device.

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
| `test_models.js` | Validation harness for source-paper worked examples, live-tool checks where available, and regression guards. |

## Included Tools

T1D-specific: Steno Type 1 Risk Engine (CVD; IHD/stroke), Scottish-Swedish
(McGurnaghan 2021), and Cederholm NDR (5-year).

T2D-derived, off-label in T1D: SCORE2-Diabetes, UKPDS Risk Engine, and ADVANCE.

General-population, off-label in T1D: SCORE2, QRISK3, PCE (ACC/AHA), AHA PREVENT,
and Framingham.

Each is grouped and colour-coded by class so an off-label borrowed model is not
mistaken for a T1D-native estimate.

## Validation

```bash
node test_models.js     # 36/36 pass
```

The 36 checks cover source-paper worked examples, live-tool comparisons where available,
and regression guards. Most implemented tools reproduce their reference cases to the
expected tolerance. The Steno-IHD/stroke endpoint is intentionally flagged
`validated: false` in `models.js`: it is a secondary endpoint from the Steno paper and is
not exposed by the public web tool, so it remains pending coefficient re-check against
the source supplement. The primary Steno-CVD endpoint is live-tool validated.

## Recalibration

- The SCORE2 family is recalibrated by risk region, using the published mechanism.
- T1D-specific tools take an optional observed/expected ratio that applies transparent
  cumulative-hazard scaling. Set it from a local registry O/E value when available.
  Default 1.0 means published calibration.

## Reproducibility Note

The Scottish-Swedish tool uses the published final-model coefficients, including the
age-at-entry term omitted from the supplementary table, with a calibration constant
(`x1.32`) fit to the authors' deployed app because the published cubic/interaction
coefficients are rounded to three decimals. Deprivation is fixed at quintile 3. This is
documented rather than hidden; it is one of the transparency gaps the companion review
flags in the existing literature.

## Status

Equations are human-traceable to published sources. Built as a companion to a review of
CV risk calculators in type 1 diabetes. Not for clinical use without local validation and
regulatory approval.
