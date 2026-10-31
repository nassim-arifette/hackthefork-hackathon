"""Regression checks for the temporal boundary, not just dataframe filtering."""
import numpy as np
import pandas as pd
import pytest

from benchmark_models import FrozenSplit, RollingCalibrated, conformal_adjustment, read_data, representatives, quantile_loss


@pytest.fixture(scope="module")
def lentils():
    raw, _ = read_data()
    return raw[(raw.culture == "lentille") & (raw.annee < 2022)].copy()


def test_calibration_cannot_change_fitted_predictor_or_preprocessing(lentils):
    base = FrozenSplit("linear").fit(lentils)
    changed = lentils.copy()
    cal = changed.annee.isin(base.calibration_years)
    changed.loc[cal, "rendement_qha"] *= 5
    changed.loc[cal, "surface_ha"] *= 100
    changed.loc[cal, "pluie_mj"] += 1000
    other = FrozenSplit("linear").fit(changed)
    pd.testing.assert_series_equal(base.levels, other.levels)
    pd.testing.assert_frame_equal(base.features.centres, other.features.centres)
    pd.testing.assert_series_equal(base.features.scale, other.features.scale)
    assert base.reps == other.reps
    X = base.features.transform(lentils.iloc[:5])
    np.testing.assert_allclose(base.model.predict(X), other.model.predict(X))
    assert base.qhat != other.qhat
    assert max(base.proper_years) < min(base.calibration_years)


def test_full_period_duplicate_flags_are_ignored(lentils):
    altered = lentils.assign(doublon=True, serie_groupe="FAKE")
    base = FrozenSplit("trend").fit(lentils)
    other = FrozenSplit("trend").fit(altered)
    assert base.reps == other.reps
    np.testing.assert_allclose(base.predict(lentils.iloc[:3]), other.predict(lentils.iloc[:3]))


def test_duplicate_representative_uses_only_supplied_past():
    rows = [{"dep": dep, "culture": "lentille", "annee": year,
             "rendement_qha": 10 + year - 2010, "surface_ha": area}
            for dep, area in [("01", 100), ("02", 200)] for year in range(2010, 2018)]
    frame = pd.DataFrame(rows)
    assert representatives(frame) == {"02"}
    # A future difference cannot break the already fitted group.
    future = pd.DataFrame([{"dep": "01", "culture": "lentille", "annee": 2018,
                            "rendement_qha": 200, "surface_ha": 10000}])
    full = pd.concat([frame, future])
    assert representatives(full[full.annee < 2018]) == {"02"}


def test_exact_conformal_order_statistic():
    assert conformal_adjustment(np.arange(9), alpha=.2) == 7
    assert conformal_adjustment(-np.arange(9), alpha=.2) == 0
    with pytest.raises(ValueError):
        conformal_adjustment([1, 2], alpha=.2)


def test_predictions_stay_positive_ordered(lentils):
    model = FrozenSplit("linear").fit(lentils)
    q = model.predict(lentils.iloc[:20])
    assert np.isfinite(q).all() and (q > 0).all()
    assert (np.diff(q, axis=1) >= 0).all()


def test_contract_score_penalizes_underpricing_four_times_more():
    assert quantile_loss(1000, 900, .8) == pytest.approx(80)
    assert quantile_loss(1000, 1100, .8) == pytest.approx(20)


def test_raw_simulation_is_independent_of_interval_correction(lentils):
    from benchmark_models import simulate
    model = RollingCalibrated("trend").fit(lentils)
    dep = model.levels.index[0]
    pool = lentils[lentils.dep == dep]
    h = {"charges_ble": 440, "charges_lentille": 280, "bonus": 122, "tau": .8}
    before = simulate(pool, model, model, dep, h, n=500, simulation_quantiles="raw")
    interval = model.predict(pool).copy()
    model.qhat += 10
    after = simulate(pool, model, model, dep, h, n=500, simulation_quantiles="raw")
    assert before == after
    assert (model.predict(pool)[:, 2] > interval[:, 2]).all()


def test_rolling_calibration_forecasts_precede_their_targets(lentils):
    model = RollingCalibrated("linear").fit(lentils)
    assert all(r["train_max"] < r["year"] for r in model.calibration_audit)
    assert max(model.proper_years) == lentils.annee.max()
    assert model.n_cal > 0


def test_contract_features_cannot_see_target_year_weather_prices_or_yields():
    from benchmark_contract import FEATURES, make_examples
    from common import hypotheses
    from model import hyp_values
    raw, weather = read_data()
    before = make_examples(raw, weather, hyp_values(hypotheses()), final_year=2020)
    changed, changed_weather = raw.copy(), weather.copy()
    changed.loc[changed.annee >= 2020, "rendement_qha"] *= 10
    changed.loc[changed.annee >= 2020, "prix_ble"] *= 5
    changed_weather.loc[changed_weather.annee >= 2020, "prix_ble"] *= 5
    changed.loc[changed.annee >= 2020, "pluie_mj"] += 9999
    after = make_examples(changed, changed_weather, hyp_values(hypotheses()), final_year=2020)
    cols = ["dep", "year", "baseline", *FEATURES]
    pd.testing.assert_frame_equal(before.loc[before.year == 2020, cols], after.loc[after.year == 2020, cols])
    assert not np.allclose(before.loc[before.year == 2020, "target"], after.loc[after.year == 2020, "target"], equal_nan=True)


def test_minimum_price_includes_equal_margins():
    from forecast_research import minimum_price
    required = np.arange(100., 110.)
    price = minimum_price(required, .8)
    assert price == 107
    assert np.mean(required <= price) == .8
    assert np.mean(required <= np.nextafter(price, -np.inf)) == .7


def test_price_calibration_does_not_use_current_year_outcomes():
    from calibrate_contract_prices import calibrate
    rows = [{"model": "lightgbm", "year": year, "dep": "01", "price": 100.,
             "realised_break_even": 110., "actual_lentil": 1.}
            for year in range(2016, 2021)]
    before, _ = calibrate(pd.DataFrame(rows))
    rows[-1]["realised_break_even"] = 10000.
    after, audit = calibrate(pd.DataFrame(rows))
    np.testing.assert_allclose(before.price, after.price)
    assert all(max(a["calibration_years"]) < a["year"] for a in audit)
