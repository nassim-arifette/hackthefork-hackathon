"""Statistical invariants for advanced preprocessing and yield distributions."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from advanced_models import (AdvancedFeatures, AdvancedYieldModel, DENSE_QUANTILES,
                             prepare_advanced_training)
from multicrop_models import WEATHER, YieldModel, prepare_training


def panel():
    rows = []
    for dep, level, soil in (("01", 12, 80), ("02", 21, 160), ("03", 30, 240)):
        for year in range(2010, 2020):
            row = {"culture": "lentille", "dep": dep, "annee": year,
                   "region": "R1" if dep != "03" else "R2", "surface_ha": 100,
                   "rendement_qha": level + .5 * (year - 2010) + (year % 3) * int(dep),
                   "soil": soil}
            row.update({name: 10 * int(dep) + (i + 1) * (year - 2010)
                        for i, name in enumerate(WEATHER)})
            rows.append(row)
    return pd.DataFrame(rows)


def test_default_preprocessing_exactly_matches_previous_training():
    history = panel()
    old = prepare_training(history)
    new = prepare_advanced_training(history)
    pd.testing.assert_series_equal(old.levels, new.levels)
    np.testing.assert_array_equal(old.X, new.X)
    np.testing.assert_array_equal(old.y, new.y)
    assert old.representatives == new.representatives


def test_static_soil_is_not_erased_by_department_centering():
    history = panel()
    features = AdvancedFeatures(WEATHER, static_columns=("soil",)).fit(history)
    X = features.transform(history)
    soil_index = features.feature_names_.index("static:soil")
    assert np.unique(X[:, soil_index]).size == 3
    assert np.ptp(X[:, soil_index]) > 1
    for _, group in history.groupby("dep"):
        assert np.std(features.transform(group)[:, soil_index]) < 1e-12


def test_absolute_and_anomaly_blocks_preserve_different_information():
    history = panel()
    features = AdvancedFeatures(WEATHER, mode="absolute_anomaly").fit(history)
    X = features.transform(history)
    anomaly = X[:, features.feature_names_.index("anomaly:" + WEATHER[0])]
    absolute = X[:, features.feature_names_.index("absolute:" + WEATHER[0])]
    assert not np.array_equal(anomaly, absolute)
    assert np.allclose(pd.Series(anomaly).groupby(history.dep).mean(), 0)


def test_imputation_and_prediction_cannot_change_training_statistics():
    history = panel()
    history.loc[0, WEATHER[0]] = np.nan
    features = AdvancedFeatures(WEATHER, ("soil",), imputation="median").fit(history)
    snapshot = (features.medians.copy(), features.global_mean.copy(), features.scale.copy(),
                features.centres.copy())
    future = history.iloc[:2].copy()
    future.loc[:, list(WEATHER)] = 1e9
    future.loc[0, WEATHER[0]] = np.nan
    transformed = features.transform(future)
    assert transformed[0, features.feature_names_.index("missing:" + WEATHER[0])] == 1
    for before, after in zip(snapshot, (features.medians, features.global_mean,
                                        features.scale, features.centres)):
        if isinstance(before, pd.DataFrame):
            pd.testing.assert_frame_equal(before, after)
        else:
            pd.testing.assert_series_equal(before, after)


def test_strict_missing_and_all_missing_imputation_fail_explicitly():
    history = panel()
    history[WEATHER[0]] = np.nan
    with pytest.raises(ValueError, match="missing"):
        AdvancedFeatures().fit(history)
    with pytest.raises(ValueError, match="no observed training value"):
        AdvancedFeatures(imputation="median").fit(history)


def test_shrinkage_keeps_cohort_and_relative_target_restores_measurements():
    history = panel()
    prepared = prepare_advanced_training(history, static_columns=("soil",),
        spec={"target_normalization": "shrinkage", "shrinkage_strength": 5})
    old = prepare_training(history)
    assert set(prepared.levels.index) == set(old.levels.index)
    assert prepared.levels["01"] > old.levels["01"]
    assert prepared.levels["02"] < old.levels["02"]
    assert prepared.levels["03"] == pytest.approx(old.levels["03"])
    np.testing.assert_allclose(prepared.y * prepared.levels.reindex(history.dep).to_numpy(),
                               history.rendement_qha)


def test_shrinkage_statistics_ignore_future_when_passed_history_is_unchanged():
    data = panel()
    history = data[data.annee < 2016]
    spec = {"target_normalization": "shrinkage"}
    first = AdvancedYieldModel({"family": "trend", **spec}).fit(history, static_columns=("soil",))
    data.loc[data.annee >= 2016, ["rendement_qha", "soil", *WEATHER]] = 1e8
    second = AdvancedYieldModel({"family": "trend", **spec}).fit(
        data[data.annee < 2016], static_columns=("soil",))
    np.testing.assert_array_equal(first.predict_distribution(history),
                                  second.predict_distribution(history))


def test_trend_three_quantiles_reproduce_existing_model():
    history = panel()
    old = YieldModel("trend").fit(history)
    new = AdvancedYieldModel({"family": "trend"}).fit(history)
    np.testing.assert_allclose(old.predict_quantiles(history), new.predict_quantiles(history))
    assert new.predict_distribution(history).shape == (len(history), len(DENSE_QUANTILES))


@pytest.mark.parametrize("family,params", [
    ("qrf", {"n_estimators": 12, "max_depth": 3}),
    ("catboost", {"iterations": 8, "depth": 2}),
    ("lightgbm", {"n_estimators": 8, "min_child_samples": 3}),
    ("linear", {}),
])
def test_families_predict_finite_ordered_dense_quantiles(family, params):
    modules = {"qrf": "quantile_forest", "catboost": "catboost", "lightgbm": "lightgbm"}
    if family in modules:
        pytest.importorskip(modules[family])
    if family == "catboost" and not Path("/proc/self/statm").is_file():
        pytest.skip("CatBoost requires /proc/self/statm, unavailable in this sandbox")
    history = panel()
    model = AdvancedYieldModel({"family": family, "params": params}).fit(
        history, static_columns=("soil",))
    q = model.predict_distribution(history.iloc[:4])
    assert q.shape == (4, len(DENSE_QUANTILES))
    assert np.isfinite(q).all()
    assert np.all(np.diff(q, axis=1) >= 0)
    np.testing.assert_allclose(model.predict_quantiles(history.iloc[:4]),
                               q[:, [2, 6, 10]])


def test_sparse_fitted_grid_is_explicit_and_interpolated_not_refitted():
    history = panel()
    model = AdvancedYieldModel({"family": "linear", "quantiles": (.1, .5, .9)}).fit(history)
    sparse = model.predict_quantiles(history.iloc[:2])
    dense = model.predict_distribution(history.iloc[:2], (.05, .1, .3, .5, .9, .95))
    np.testing.assert_allclose(dense[:, 2], (sparse[:, 0] + sparse[:, 1]) / 2)
    np.testing.assert_array_equal(dense[:, 0], sparse[:, 0])
    np.testing.assert_array_equal(dense[:, -1], sparse[:, -1])
