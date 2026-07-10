"""Common analytic banding for cross-model agreement.

The compared calculators use different endpoints, horizons, eligibility rules,
and native decision thresholds. For the exploratory agreement analysis, their
10-year outputs are mapped to common bands (<10%, 10 to <20%, and >=20%) only
to summarise ordinal concordance. These are not universal treatment thresholds.

Banding returns an ordinal integer 0..K-1 so Cohen's kappa (including ordinal
weighting) can be computed directly.
"""
from __future__ import annotations

from math import isfinite

# Primary common analytic banding for the 10-year agreement matrix.
COMMON_ANALYTIC_BANDS = [
    (10.0, "<10%"),
    (20.0, "10 to <20%"),
    (float("inf"), ">=20%"),
]
COMMON_ANALYTIC_LABELS = ["<10%", "10 to <20%", ">=20%"]


def band(risk_pct: float, bands=COMMON_ANALYTIC_BANDS) -> int:
    """Return the ordinal band index, or -1 for a non-finite risk."""
    if not isfinite(risk_pct):
        return -1
    for i, (upper, _label) in enumerate(bands):
        if risk_pct < upper:
            return i
    return len(bands) - 1


def band_label(risk_pct: float, bands=COMMON_ANALYTIC_BANDS) -> str:
    index = band(risk_pct, bands)
    return "not available" if index < 0 else bands[index][1]


def score2_band(risk_pct: float, age: float) -> int:
    """ESC SCORE2 age-dependent thresholds (low-to-moderate / high / very-high)."""
    if age < 50:
        cuts = (2.5, 7.5)
    elif age < 70:
        cuts = (5.0, 10.0)
    else:
        cuts = (7.5, 15.0)
    return 0 if risk_pct < cuts[0] else (1 if risk_pct < cuts[1] else 2)
