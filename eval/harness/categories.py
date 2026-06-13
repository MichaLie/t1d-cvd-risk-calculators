"""
Risk-category banding for cross-model agreement.

Different guidelines use different thresholds. For the headline cross-model
agreement we band the harmonised 10-year CVD risk with the widely used,
treatment-decision-relevant NICE/Steno bands (the Steno engine itself reports
these): low <10%, moderate 10-20%, high >=20%. ESC SCORE2 age-dependent bands
are provided as a sensitivity alternative.

Banding returns an ordinal integer 0..K-1 so Cohen's kappa (incl. ordinal
weighting) can be computed directly.
"""
from __future__ import annotations

# primary common banding (10-year CVD)
NICE_STENO_BANDS = [(10.0, "low"), (20.0, "moderate"), (float("inf"), "high")]
NICE_STENO_LABELS = ["low", "moderate", "high"]


def band(risk_pct: float, bands=NICE_STENO_BANDS) -> int:
    """Return ordinal index of the band containing risk_pct (in %)."""
    for i, (upper, _label) in enumerate(bands):
        if risk_pct < upper:
            return i
    return len(bands) - 1


def band_label(risk_pct: float, bands=NICE_STENO_BANDS) -> str:
    return bands[band(risk_pct, bands)][1]


def score2_band(risk_pct: float, age: float) -> int:
    """ESC SCORE2 age-dependent thresholds (low-to-moderate / high / very-high)."""
    if age < 50:
        cuts = (2.5, 7.5)
    elif age < 70:
        cuts = (5.0, 10.0)
    else:
        cuts = (7.5, 15.0)
    return 0 if risk_pct < cuts[0] else (1 if risk_pct < cuts[1] else 2)
