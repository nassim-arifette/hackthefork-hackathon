import numpy as np
import pandas as pd
import pytest

from analyze_price_frontier import (assert_same_cohort, equal_year_weights,
                                    minimal_multiplier, weighted_quantile, summarize_honest_policies)


def test_minimum_quantile_includes_ties_and_rejects_lower_value():
    values = np.array([1., 2., 2., 5.])
    weights = np.array([.2, .3, .3, .2])
    q = weighted_quantile(values, weights, .8)
    assert q == 2.
    assert weights[values <= q].sum() >= .8
    assert weights[values < q].sum() < .8


def test_year_equal_weights_prevent_large_year_from_dominating():
    d = pd.DataFrame([{"year": 2019, "price": 100., "realised_break_even": 100.}] * 20 +
                     [{"year": 2020, "price": 100., "realised_break_even": 200.}])
    weights = equal_year_weights(d)
    assert np.isclose(weights[:20].sum(), weights[-1])
    assert minimal_multiplier(d, .8) == 2.
    assert weighted_quantile(d.realised_break_even / d.price, np.ones(len(d)), .8) == 1.


def test_factor_is_minimal_for_equal_price_boundaries():
    d = pd.DataFrame({"year": [2019] * 5, "price": [100.] * 5,
                      "realised_break_even": [100., 120., 150., 200., 300.]})
    factor = minimal_multiplier(d, .8)
    assert factor == 2.
    assert (factor * d.price >= d.realised_break_even).mean() == .8
    assert (np.nextafter(factor, -np.inf) * d.price >= d.realised_break_even).mean() < .8


def test_frontier_refuses_different_model_cohorts():
    rows = pd.DataFrame([{"year": 2019, "dep": dep, "model": model, "realised_break_even": 100.}
                         for model, deps in [("trend", ["10", "28"]), ("qrf", ["10"])] for dep in deps])
    with pytest.raises(ValueError, match="same evaluation cohort"):
        assert_same_cohort(rows, ("trend", "qrf"))


def test_policy_sources_with_same_name_are_kept_distinct_without_rescaling():
    rows = pd.DataFrame({"year": [2019, 2020], "dep": ["10", "10"],
        "model": ["qrf__past_selected"] * 2, "price": [100., 200.],
        "realised_break_even": [90., 220.], "actual_lentil_t_ha": [1., 1.]})
    keys = {(2019, "10"), (2020, "10")}
    truth = rows.set_index(["year", "dep"]).realised_break_even.sort_index()
    raw = summarize_honest_policies(rows, "sensitivity_raw", keys, truth, keys)
    expanded = summarize_honest_policies(rows.assign(price=[300., 400.]),
        "sensitivity_expanded", keys, truth, keys)
    assert raw[0]["model"] == expanded[0]["model"]
    assert raw[0]["policy_source"] != expanded[0]["policy_source"]
    assert raw[0]["factor"] == expanded[0]["factor"] == 1.
    assert raw[0]["mean_price_year_equal"] == 150.
    assert expanded[0]["mean_price_year_equal"] == 350.
