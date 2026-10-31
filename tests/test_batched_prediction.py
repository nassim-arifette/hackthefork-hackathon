"""Batching must be a bit-for-bit execution optimization, not a new model."""
from types import SimpleNamespace

import numpy as np
import pandas as pd

import benchmark_advanced as benchmark
from advanced_models import AdvancedYieldModel, DENSE_QUANTILES
from batched_prediction import install_batched_predictions
from test_advanced_benchmark import example_panel, inject_data, args, small_registry


def small_data():
    return pd.DataFrame([{"culture": "lentille", "dep": dep, "region": "R1", "annee": year,
        "surface_ha": 100, "rendement_qha": 10 + int(dep) * (year % 3) + .3 * (year - 2010),
        "x": int(dep) * 10 + year % 4, "soil": int(dep) * 40}
        for dep in ("01", "02", "03") for year in range(2010, 2021)])


def make_model(history):
    return AdvancedYieldModel({"family": "qrf", "params": {"n_estimators": 15, "min_samples_leaf": 2}}, seed=42).fit(
        history, columns=("x",), static_columns=("soil",))


def test_dense_sparse_and_repeated_returns_are_bitwise_identical():
    data = small_data()
    history = data[data.annee < 2018]
    pool = data[(data.dep == "01") & (data.annee < 2018)].copy()
    pool["annee"] = 2018
    ordinary = make_model(history)
    dense = ordinary.predict_distribution(pool)
    sparse = ordinary.predict_quantiles(pool)
    module = SimpleNamespace(AdvancedYieldModel=AdvancedYieldModel, load_data=lambda *_: (data, data.copy(), []))
    with install_batched_predictions(module) as batching:
        module.load_data(None)
        model = make_model(history)
        actual = model.predict_distribution(pool)
        np.testing.assert_array_equal(actual, dense)
        np.testing.assert_array_equal(model.predict_quantiles(pool), sparse)
        actual[:] = -100
        np.testing.assert_array_equal(model.predict_distribution(pool), dense)
        assert batching.stats["batches"] == 1
        assert batching.stats["cache_calls"] == 3
        assert batching.stats["batched_rows"] == 27  # 2010--2018, never 2019/2020.


def test_unmatched_values_and_grids_fall_back_and_refit_invalidates_cache():
    data = small_data()
    history = data[data.annee < 2018]
    rows = data[data.annee == 2018].copy()
    module = SimpleNamespace(AdvancedYieldModel=AdvancedYieldModel, load_data=lambda *_: (data, data.copy(), []))
    with install_batched_predictions(module) as batching:
        module.load_data(None)
        model = make_model(history)
        first = model.predict_distribution(rows)
        altered = rows.copy()
        altered["x"] += .123456789
        np.testing.assert_array_equal(model.predict_distribution(altered), batching.original_predict(model, altered))
        np.testing.assert_array_equal(model.predict_distribution(rows, (.123, .567)),
                                      batching.original_predict(model, rows, (.123, .567)))
        changed = history.copy()
        changed.loc[changed.annee >= 2016, "rendement_qha"] *= 2
        model.fit(changed, columns=("x",), static_columns=("soil",))
        after = model.predict_distribution(rows)
        np.testing.assert_array_equal(after, batching.original_predict(model, rows))
        assert not np.array_equal(first, after)
        assert batching.stats["batches"] == 2
        assert batching.stats["fallback_calls"] == 2


def test_future_weather_never_changes_earlier_input_lookup():
    data = small_data()
    history = data[data.annee < 2018].copy()
    rows = data[(data.dep == "01") & (data.annee < 2018)].copy()
    rows["annee"] = 2018
    module = SimpleNamespace(AdvancedYieldModel=AdvancedYieldModel, load_data=lambda *_: (data, data.copy(), []))
    with install_batched_predictions(module) as batching:
        module.load_data(None)
        model = make_model(history)
        before = model.predict_distribution(rows)
        data.loc[data.annee >= 2018, "x"] = 1e12
        module.load_data(None)  # New captured data generation invalidates the old lookup.
        after = model.predict_distribution(rows)
        np.testing.assert_array_equal(before, after)
        assert batching.stats["batches"] == 2


def test_eight_arm_contract_prices_and_future_perturbation_are_exact(tmp_path, monkeypatch):
    data = example_panel()
    weather = inject_data(monkeypatch, data)
    registry = small_registry()
    monkeypatch.setattr(benchmark, "candidate_registry", lambda: registry)
    names = ["trend", "qrf_seasonal", "qrf_soil_sparse", "qrf_soil_dense",
             "qrf_joint_gaussian", "qrf_joint_empirical", "qrf_lgb_mixture", "qrf_wheat_dense"]
    ordinary = benchmark.run(args(tmp_path / "ordinary", names, years=(2018, 2019)))
    original_method = AdvancedYieldModel.predict_distribution
    with install_batched_predictions(benchmark) as batching:
        batched = benchmark.run(args(tmp_path / "batched", names, years=(2018, 2019)))
        pd.testing.assert_frame_equal(ordinary, batched, check_exact=True)
        assert batching.stats["batches"] > 0 and batching.stats["cache_calls"] > batching.stats["batches"]
        data.loc[data.annee >= 2019, "rendement_qha"] *= 2
        data.loc[data.annee >= 2019, "prix_ble"] *= 2
        weather.loc[weather.annee >= 2019, "prix_ble"] *= 2
        from multicrop_models import WEATHER
        data.loc[data.annee >= 2019, list(WEATHER)] += 1000
        weather.loc[weather.annee >= 2019, list(WEATHER)] += 1000
        perturbed = benchmark.run(args(tmp_path / "perturbed", names, years=(2018, 2019)))
        columns = ["dep", "year", "model", "contract", "coefficient", "expected_unit_cost",
                   "simulation_basis_mean", "simulation_accepted_mean", "past_mean_accepted", "rho"]
        pd.testing.assert_frame_equal(batched[columns], perturbed[columns], check_exact=True)
        assert not np.array_equal(batched.actual_need_eur_ha, perturbed.actual_need_eur_ha)
    assert AdvancedYieldModel.predict_distribution is original_method
