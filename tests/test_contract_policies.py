import numpy as np
import pandas as pd
import pytest

from benchmark_contract_policies import (
    CONFIGS, calibration, check_cohorts, choose_protection_policy, make_configs, weighted_quantile,
)


def test_weighted_quantile_is_minimal_and_equality_counts():
    values = np.array([100., 200., 200., 500.])
    weights = np.array([.2, .3, .3, .2])
    q = weighted_quantile(values, weights)
    assert q == 200.
    assert weights[values <= q].sum() >= .8
    assert weights[values < q].sum() < .8


def test_calibration_ignores_decision_and_future_outcomes_and_weights_years():
    history = pd.DataFrame([
        *[{"year": 2017, "price": 100., "realised_break_even": 110., "region": "a"}] * 20,
        {"year": 2018, "price": 100., "realised_break_even": 200., "region": "a"},
        {"year": 2019, "price": 100., "realised_break_even": 1e10, "region": "a"},
        {"year": 2020, "price": 100., "realised_break_even": 1e10, "region": "a"},
    ])
    config = CONFIGS["log_expanding_signed"]
    score, audit = calibration(history, 2019, config)
    assert np.isclose(score, np.log(2.))
    assert audit["calibration_years"] == [2017, 2018]
    history.loc[history.year >= 2019, "realised_break_even"] = 1e-10
    assert calibration(history, 2019, config)[0] == score


def selection_rows():
    rows = []
    for year in [2016, 2017, 2018]:
        for i in range(5):
            for name, price, held in [("trend__raw", 500., i < 3),
                                      ("qrf__raw", 700., i < 4),
                                      ("qrf__more", 900., True)]:
                rows.append(dict(year=year, dep=str(i), model=name, price=price, held=held, region="a"))
    return pd.DataFrame(rows)


def test_selector_minimizes_price_under_80_constraint_without_future():
    rows = selection_rows()
    candidates = ["trend__raw", "qrf__raw", "qrf__more"]
    chosen, audit = choose_protection_policy(rows, 2019, candidates, "a")
    assert chosen == "qrf__raw"  # cheap but only 60% M0 is ineligible
    assert audit["feasible"] and audit["scope"] == "region"
    future = rows.assign(year=2019, held=False, price=1e10)
    assert choose_protection_policy(pd.concat([rows, future]), 2019, candidates, "a")[0] == chosen


def test_regional_selector_falls_back_to_global_for_small_groups():
    rows = selection_rows()
    rows.loc[rows.dep == "0", "region"] = "tiny"
    chosen, audit = choose_protection_policy(rows, 2019, list(rows.model.unique()), "tiny")
    assert chosen == "qrf__raw" and audit["scope"] == "global"
    assert audit["n_validation_per_candidate"] == 15


def test_selector_maximizes_protection_when_no_candidate_feasible():
    rows = selection_rows()
    rows.loc[rows.model == "qrf__more", "held"] = False
    rows.loc[(rows.model == "qrf__raw") & (rows.dep == "3"), "held"] = False
    rows.loc[(rows.model == "trend__raw") & (rows.dep == "2"), "held"] = False
    chosen, audit = choose_protection_policy(rows, 2019, list(rows.model.unique()))
    assert chosen == "qrf__raw" and not audit["feasible"]


def test_comparison_rejects_missing_candidate_case():
    rows = selection_rows()
    bad = rows.drop(rows[(rows.model == "qrf__raw") & (rows.year == 2016)].index[0])
    with pytest.raises(ValueError, match="inconsistent comparison cohorts"):
        check_cohorts(bad, list(rows.model.unique()))


def test_internal_calibration_level_changes_correction_not_product_constraint():
    rows = pd.DataFrame([dict(year=2018, price=100., realised_break_even=100. + i, region="a")
                         for i in range(1, 21)])
    configs = make_configs([.8, .9, .95])
    q80, _ = calibration(rows, 2019, configs["log_expanding_signed"])
    q90, audit = calibration(rows, 2019, configs["log_expanding_q90_signed"])
    assert np.isclose(np.exp(q80), 1.16)
    assert np.isclose(np.exp(q90), 1.18)
    assert audit["internal_calibration_quantile"] == .9
    # The same selector still accepts the 80%-held, cheapest feasible candidate.
    records = selection_rows()
    assert choose_protection_policy(records, 2019, list(records.model.unique()))[0] == "qrf__raw"
