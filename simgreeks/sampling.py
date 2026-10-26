"""Sampling distributions of the option inputs for a training set. Not part of
the paper.

Volatility. The network is meant to be accurate for sigma in [5 %, 50 %]. A
network is least accurate at the edges of its training data, so sigma is
drawn from a plateau on [5 %, 50 %] with tails that fall to 0 at 1 % and 60 %:
the network sees labels on both sides of 5 % and 50 %. The density is
flat on the plateau and g((x - lo) / (a - lo)) times the plateau level in the
lower tail (and the mirror image in the upper tail), with g(0) = 0, g(1) = 1:

    "concave"  g(t) = sqrt(1 - (1 - t)^2)   quarter ellipse (default): stays near the plateau
                                            level, drops vertically to 0 at lo and hi
    "cosine"   g(t) = (1 - cos(pi t)) / 2   fades to 0 smoothly at lo and hi
    "linear"   g(t) = t                     trapezoid
    "convex"   g(t) = t^2                   fewest labels just past the edges

"concave" and "cosine" both join the plateau without a kink (g'(1) = 0). What
protects the edges is the density beyond 5 % and 50 %: concave keeps it high
furthest out (0.87 of the plateau level at 3 % and 55 %, cosine 0.50), at the
cost of more labels outside [5 %, 50 %]. Share of the labels in the tails with
the default bounds (lower 1-5 %, upper 50-60 %): concave 19.6 % (5.6 % below
5 %, 14.0 % above 50 %), cosine and linear 13.5 %, convex 9.4 %.

Draws go through the inverse CDF, so uniform (e.g. Sobol) points keep their
low discrepancy.
"""
from __future__ import annotations

import numpy as np

SIGMA_BOUNDS = (0.01, 0.05, 0.50, 0.60)   # (lo, a, b, hi): tails on [lo, a] and [b, hi]
TAILS = {
    "cosine": lambda t: 0.5 * (1.0 - np.cos(np.pi * t)),
    "concave": lambda t: np.sqrt(np.clip(1.0 - (1.0 - t) ** 2, 0.0, None)),
    "linear": lambda t: t,
    "convex": lambda t: t ** 2,
}
_GRID = 20_001                            # points per tail of the numerical CDF


def _check(bounds, tail):
    lo, a, b, hi = bounds
    if not lo <= a < b <= hi:
        raise ValueError(f"bounds must satisfy lo <= a < b <= hi, got {bounds}")
    if tail not in TAILS:
        raise ValueError(f"unknown tail {tail!r}; one of {sorted(TAILS)}")
    return lo, a, b, hi


def plateau_pdf(x, bounds=SIGMA_BOUNDS, tail: str = "concave") -> np.ndarray:
    """Density of the plateau-with-tails distribution at x."""
    lo, a, b, hi = _check(bounds, tail)
    x = np.asarray(x, dtype=float)
    g = TAILS[tail]
    f = np.zeros_like(x)
    f[(x >= a) & (x <= b)] = 1.0
    if a > lo:
        m = (x >= lo) & (x < a)
        f[m] = g((x[m] - lo) / (a - lo))
    if hi > b:
        m = (x > b) & (x <= hi)
        f[m] = g((hi - x[m]) / (hi - b))
    return f / _mass(bounds, tail)


def _tail_mass(tail: str) -> float:
    """Integral of g over [0, 1] (trapezoid on the CDF grid)."""
    t = np.linspace(0.0, 1.0, _GRID)
    return float(np.trapezoid(TAILS[tail](t), t))


def _mass(bounds, tail) -> float:
    lo, a, b, hi = bounds
    return (b - a) + ((a - lo) + (hi - b)) * _tail_mass(tail)


def plateau_ppf(u, bounds=SIGMA_BOUNDS, tail: str = "concave") -> np.ndarray:
    """Inverse CDF: maps u in [0, 1] to the plateau-with-tails distribution.
    The tails are inverted numerically (linear interpolation of the CDF on a
    fine grid), the plateau exactly."""
    lo, a, b, hi = _check(bounds, tail)
    g = TAILS[tail]
    t = np.linspace(0.0, 1.0, _GRID)
    gt = g(t)
    G = np.concatenate([[0.0], np.cumsum(0.5 * (gt[1:] + gt[:-1]) * np.diff(t))])  # int_0^t g
    total = _mass(bounds, tail)
    m_lo, m_hi = (a - lo) * G[-1] / total, (hi - b) * G[-1] / total
    u = np.asarray(u, dtype=float)
    x = np.empty_like(u)
    low, high = u < m_lo, u > 1.0 - m_hi
    mid = ~(low | high)
    # lower tail: CDF(x) = (a - lo) int_0^t g / total, t = (x - lo) / (a - lo)
    x[low] = lo + (a - lo) * np.interp(u[low] * total / (a - lo), G, t)
    x[mid] = a + (u[mid] - m_lo) * total
    # upper tail, by symmetry: 1 - CDF(x) = (hi - b) int_0^s g / total, s = (hi - x) / (hi - b)
    x[high] = hi - (hi - b) * np.interp((1.0 - u[high]) * total / (hi - b), G, t)
    return x


def tail_share(bounds=SIGMA_BOUNDS, tail: str = "concave") -> float:
    """Probability of a draw outside [a, b]."""
    lo, a, b, hi = _check(bounds, tail)
    return 1.0 - (b - a) / _mass(bounds, tail)
