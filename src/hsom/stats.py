"""Small, dependency-free statistics helpers for benchmark reporting.

The primary interval is Clopper-Pearson (exact binomial).  Wilson is offered
for comparison because it is shorter and better behaved near 0/1, but the
benchmark report uses Clopper-Pearson so a "0 failures" claim is stated as an
upper bound rather than as zero error.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist


@dataclass(frozen=True)
class Interval:
    low: float
    high: float
    method: str
    confidence: float

    def contains(self, value: float) -> bool:
        return self.low <= value <= self.high


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (Lentz's method)."""
    tiny = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-14:
            break
    return h


def _reg_incomplete_beta(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_bt = (
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log1p(-x)
    )
    bt = math.exp(ln_bt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def _beta_ppf(q: float, a: float, b: float) -> float:
    """Inverse regularized incomplete beta by bisection."""
    if q <= 0.0:
        return 0.0
    if q >= 1.0:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if _reg_incomplete_beta(a, b, mid) < q:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-14:
            break
    return (lo + hi) / 2.0


def clopper_pearson(k: int, n: int, *, alpha: float = 0.05,
                    one_sided: bool = False) -> Interval:
    """Exact binomial confidence interval for k successes out of n trials.

    With ``one_sided=True`` the upper bound uses ``alpha`` (0.95 upper bound
    for alpha=0.05); the lower bound is 0 unless ``k == n``.
    """
    if n <= 0:
        raise ValueError("n must be > 0")
    if not 0 <= k <= n:
        raise ValueError("k must be in [0, n]")
    confidence = 1.0 - alpha
    if one_sided:
        low = 0.0 if k == 0 else _beta_ppf(alpha, k, n - k + 1)
        high = 1.0 if k == n else _beta_ppf(1.0 - alpha, k + 1, n - k)
    else:
        low = 0.0 if k == 0 else _beta_ppf(alpha / 2.0, k, n - k + 1)
        high = 1.0 if k == n else _beta_ppf(1.0 - alpha / 2.0, k + 1, n - k)
    return Interval(low, high, "clopper-pearson", confidence)


def wilson(k: int, n: int, *, alpha: float = 0.05) -> Interval:
    """Wilson score interval for a binomial proportion."""
    if n <= 0:
        raise ValueError("n must be > 0")
    if not 0 <= k <= n:
        raise ValueError("k must be in [0, n]")
    z = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return Interval(max(0.0, center - half), min(1.0, center + half),
                    "wilson", 1.0 - alpha)


def percentile(values: list[float], q: float) -> float | None:
    """Linear-interpolated percentile; ``q`` in [0, 1]. None for empty input."""
    if not values:
        return None
    if not 0.0 <= q <= 1.0:
        raise ValueError("q must be in [0, 1]")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return ordered[lo]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)
