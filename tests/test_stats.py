"""Dependency-free interval helpers used by the benchmark report."""

import pytest

from hsom.stats import clopper_pearson, percentile, wilson


def test_clopper_pearson_zero_failures_one_sided_upper():
    ci = clopper_pearson(0, 88, one_sided=True)
    assert ci.low == 0.0
    assert ci.high == pytest.approx(0.03347, abs=1e-4)


def test_clopper_pearson_zero_of_five():
    ci = clopper_pearson(0, 5, one_sided=True)
    assert ci.low == 0.0
    assert ci.high == pytest.approx(0.4507, abs=1e-3)


def test_clopper_pearson_all_failures():
    ci = clopper_pearson(5, 5)
    assert ci.low == pytest.approx(0.4782, abs=1e-3)
    assert ci.high == 1.0


def test_clopper_pearson_midpoint_symmetric():
    ci = clopper_pearson(50, 100)
    assert ci.low == pytest.approx(1 - ci.high, abs=1e-9)
    assert ci.low < 0.5 < ci.high


def test_wilson_zero_failures_is_an_upper_bound():
    exact = clopper_pearson(0, 88)
    score = wilson(0, 88)
    assert exact.high < 0.05 and score.high < 0.05
    assert score.low == 0.0


def test_interval_validation():
    with pytest.raises(ValueError):
        clopper_pearson(1, 0)
    with pytest.raises(ValueError):
        clopper_pearson(-1, 10)
    with pytest.raises(ValueError):
        clopper_pearson(11, 10)


def test_percentile():
    assert percentile([], 0.5) is None
    assert percentile([42], 0.95) == 42
    assert percentile([1, 2, 3, 4], 0.5) == 2.5
    assert percentile([1, 2, 3, 4], 0.95) == pytest.approx(3.85)
