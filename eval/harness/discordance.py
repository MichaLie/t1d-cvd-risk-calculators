"""
Discordance / agreement metrics for the in-silico head-to-head.

These quantify how much calculators DISAGREE on the same patients. They make
NO claim about which model is correct (no outcomes here) — this is by design an
agreement study. The headline metric is pairwise Cohen's kappa after outputs are
mapped to common analytic bands and is supported by exact-agreement rate,
Bland-Altman on predicted risk, and the
distribution of pairwise predicted-risk ratios.
"""
from __future__ import annotations
from typing import Dict, Sequence
import numpy as np
import pandas as pd


def cohen_kappa(a: Sequence[int], b: Sequence[int], weights: str | None = None,
                k: int | None = None) -> float:
    """Cohen's kappa for two label vectors. weights: None | 'linear' | 'quadratic'."""
    if weights not in (None, "linear", "quadratic"):
        raise ValueError("weights must be None, 'linear', or 'quadratic'")
    a = np.asarray(a); b = np.asarray(b)
    if a.ndim != 1 or b.ndim != 1 or a.shape != b.shape:
        raise ValueError("labels must be one-dimensional vectors of equal length")
    if not (np.isfinite(a).all() and np.isfinite(b).all()):
        raise ValueError("filter missing labels before calculating kappa")
    if np.any(a < 0) or np.any(b < 0) or np.any(a != np.floor(a)) or np.any(b != np.floor(b)):
        raise ValueError("labels must be non-negative integers")
    a = a.astype(int); b = b.astype(int)
    if len(a) == 0:
        return float("nan")
    if k is None:
        k = int(max(a.max(), b.max())) + 1
    if not isinstance(k, (int, np.integer)) or k < 1 or np.any(a >= k) or np.any(b >= k):
        raise ValueError("k must exceed the largest label")
    O = np.zeros((k, k), float)
    for i, j in zip(a, b):
        O[i, j] += 1
    n = O.sum()
    if n == 0:
        return float("nan")
    O /= n
    row = O.sum(1); col = O.sum(0)
    E = np.outer(row, col)
    if weights is None:
        w = 1.0 - np.eye(k)            # disagreement weight 1 off-diagonal
    else:
        idx = np.arange(k)
        d = np.abs(idx[:, None] - idx[None, :]).astype(float)
        w = d if weights == "linear" else d ** 2
    denom = (w * E).sum()
    if denom == 0:
        return float("nan")  # Identical single-category marginals: undefined, not perfect kappa.
    return 1.0 - (w * O).sum() / denom


def agreement_rate(a: Sequence[int], b: Sequence[int]) -> float:
    a = np.asarray(a, int); b = np.asarray(b, int)
    return float((a == b).mean())


def pairwise_kappa_matrix(cats: Dict[str, Sequence[int]], weights: str | None = "linear",
                          k: int | None = None) -> pd.DataFrame:
    """Full pairwise kappa matrix across models (diagonal = 1)."""
    names = list(cats)
    if k is None:
        k = int(max(np.max(v) for v in cats.values())) + 1
    M = pd.DataFrame(np.eye(len(names)), index=names, columns=names)
    for i, x in enumerate(names):
        for j in range(i + 1, len(names)):
            y = names[j]
            kv = cohen_kappa(cats[x], cats[y], weights=weights, k=k)
            M.loc[x, y] = kv; M.loc[y, x] = kv
    return M


def bland_altman(x: Sequence[float], y: Sequence[float]) -> dict:
    """Bland-Altman on predicted risk (%). Returns bias and 95% limits of agreement."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    diff = x - y
    bias = float(diff.mean()); sd = float(diff.std(ddof=1))
    return {"bias": bias, "sd": sd,
            "loa_lower": bias - 1.96 * sd, "loa_upper": bias + 1.96 * sd}


def risk_ratio_summary(x: Sequence[float], y: Sequence[float], eps: float = 1e-6) -> dict:
    """Distribution of the pairwise predicted-risk ratio x/y."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    r = (x + eps) / (y + eps)
    return {"median": float(np.median(r)),
            "q1": float(np.percentile(r, 25)), "q3": float(np.percentile(r, 75)),
            "p05": float(np.percentile(r, 5)), "p95": float(np.percentile(r, 95))}
