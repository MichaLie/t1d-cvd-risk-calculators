# Reproducible analysis outputs

The compact final tables in this folder describe the 10,000-profile synthetic cohort (primary seed 20260613):

| File | Contents |
|---|---|
| `kappa_matrix.csv` | Ten endpoints, 45 distinct pairs; linearly weighted Cohen’s κ on pairwise-complete profiles. |
| `sensitivity_summary.csv` | Defined subgroups, pair coverage, mean κ and selected contrasts. |
| `sensitivity_model_summary.csv` | Per-model eligibility, risk summaries and category counts in each subgroup. |
| `sensitivity_model_variants.csv` | Primary and alternative SCORE2 diabetes-term specifications. |
| `synthetic_cohort_assumptions.csv` | Generator distributions, fixed defaults and model-input substitutions. |
| `robustness_summary.csv` | Five seeds, common support, exclusions, model subsets and factorial grid. |

`python -m eval.verify` regenerates these tables plus `synthetic_cohort.csv` (input profiles), `cohort_risks.csv` (per-profile outputs), `robustness_pairwise.csv`, `ukpds_source_conflict_sensitivity.csv`, `figure_4_pairwise_values.csv` and `figure_5_boxplot_values.csv`. These larger or derived supporting tables are not versioned. Their join key is `synthetic_id` where present; the factorial grid is a separate dataset, not the primary cohort.

Risk values are percentages; differences are percentage points. Empty numeric cells denote unavailable or mathematically undefined values, never zero. The labels `ADVANCE*` and `UKPDS-CVD` identify adapted implementations described in [METHODS.md](../../METHODS.md). The Scottish–Swedish model is excluded from all numerical tables. Bands and agreement statistics do not establish clinical prediction accuracy.

All QRISK3 scores, their summaries and comparisons are accompanied by the [ClinRisk source notice and required disclaimer](../../third_party/qrisk3/NOTICE.md). Retain that notice when exporting or redistributing the data; displayed QRISK3 scores must prominently link to or display the disclaimer.
