# T1D-CVD Meta-Calculator

A transparent, open, self-contained web tool that runs every published, externally-validated
cardiovascular-risk calculator **side by side** for an adult with type 1 diabetes, shows where
they agree and where they diverge, and lets you recalibrate to local risk.

**It is not a new prediction model.** A new *validated* equation would require individual-patient
outcome data we do not have. The value here is the opposite of a black box: faithful reproduction
of existing tools, an explicit discordance read-out, transparent recalibration, and fully open
coefficients. Decision support only — not a substitute for clinical judgement or a regulated
medical device.

## Run it

No build, no server, no dependencies. Either:

```bash
open index.html                      # straight from disk
# or, to avoid file:// quirks:
python3 -m http.server 8000          # then visit http://localhost:8000
```

Nothing leaves the browser; all computation is client-side.

## Files

| File | What it is |
|------|-----------|
| `index.html` | The whole UI (input form, grouped bar chart, discordance flag, recalibration, transparency panel). Self-contained. |
| `models.js`  | The engine: 12 calculators ported to JS, every coefficient open and commented. Exports `T1DCVD` (browser) / `module.exports` (Node). |
| `test_models.js` | Validation harness. Each model is checked against its source paper's worked example or its live web tool. |

## The 12 tools

**T1D-specific:** Steno Type 1 Risk Engine (CVD; IHD/stroke), Scottish–Swedish (McGurnaghan 2021),
Cederholm NDR (5-yr). **T2D-derived (off-label in T1D):** SCORE2-Diabetes, UKPDS Risk Engine,
ADVANCE. **General-population (off-label in T1D):** SCORE2, QRISK3, PCE (ACC/AHA), AHA PREVENT,
Framingham.

Each is grouped and colour-coded by class so an off-label borrow is never mistaken for a
T1D-native estimate.

## Validation

```bash
node test_models.js     # 26/26 pass
```

Every model reproduces its source to the decimal (e.g. Steno 6.1/11.8%, SCORE2-Diabetes,
PCE across all four sex/ethnicity groups, QRISK3 19.1%, PREVENT 14.7%, Framingham, UKPDS
stroke 6.9%, Cederholm, Scottish–Swedish against the deployed app).

## Recalibration

- **SCORE2 family** is recalibrated by risk region — a published mechanism (region defaults to
  *High*, which covers Central Europe incl. Czechia).
- **T1D-specific tools** take an optional observed/expected ratio that applies a transparent
  cumulative-hazard scaling. Set it from your local registry's O/E (e.g. ~0.55 reproduces the
  Italian over-estimation of Steno). Default 1.0 = published calibration.

## Reproducibility note

The Scottish–Swedish tool uses the published **final-model** coefficients — including the
age-at-entry term omitted from the supplementary table — with a calibration constant (×1.32) fit
to the authors' deployed app, because the published cubic/interaction coefficients are rounded to
three decimals. Deprivation is fixed at quintile 3. This is documented rather than hidden; it is
one of the transparency gaps the companion review flags in the existing literature.

## Status

AI-assisted development; all equations human-traceable to their published sources. Built as a
companion to a review of CV risk calculators in T1D. **Not for clinical use without local
validation and regulatory approval.**
