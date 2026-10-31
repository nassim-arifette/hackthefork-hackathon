"""Régressions sur les données réellement apprises, pas sur un filtre reconstruit."""
import numpy as np
import pandas as pd
import pytest

import model
from model import Calibrated, WEATHER, break_even_prices, prepare_as_of


@pytest.fixture
def raw_panel():
    rng = np.random.default_rng(83)
    rows = []
    for dep in ("01", "02", "03", "04", "05"):
        for year in range(2010, 2023):
            weather = rng.normal(size=len(WEATHER))
            rows.append({"dep": dep, "culture": "lentille", "annee": year,
                         "surface_ha": 80 + int(dep), "prix_ble": 180 + year - 2010,
                         "rendement_qha": 10 + int(dep) + 2 * weather[0],
                         "tendance": (year - 2010) / 10,
                         **dict(zip(WEATHER, weather))})
    return pd.DataFrame(rows)


def test_predictor_is_the_object_fitted_before_calibration(monkeypatch, raw_panel):
    fitted = []

    class Spy:
        def fit(self, X, y):
            fitted.append((self, X.copy(), y.copy()))
            return self

        def predict(self, X):
            return np.tile([0.8, 1.0, 1.2], (len(X), 1))

    monkeypatch.setitem(model.MODELS, "M0", Spy)
    fitted_model = Calibrated("M0").fit(prepare_as_of(raw_panel, 2019))
    assert len(fitted) == 1  # A post-calibration fit would fail this test.
    predictor, actual_training_rows, actual_targets = fitted[0]
    assert fitted_model.model is predictor
    assert set(actual_training_rows.annee) == {2010, 2011, 2012, 2013}
    assert np.allclose(actual_targets, actual_training_rows.rendement_qha /
                       actual_training_rows.dep.map(fitted_model.levels))
    assert fitted_model.audit["selection_years"] == [2014, 2015]
    assert fitted_model.audit["calibration_years"] == [2016, 2017, 2018]


def test_calibration_cannot_change_selection_levels_or_weather(raw_panel):
    train = prepare_as_of(raw_panel, 2019)
    first = Calibrated("auto").fit(train)
    altered = train.copy()
    cal = altered.annee.isin(first.audit["calibration_years"])
    altered.loc[cal, "rendement_qha"] *= 8
    altered.loc[cal, "surface_ha"] *= 100
    altered.loc[cal, WEATHER] += 100
    second = Calibrated("auto").fit(altered)
    assert first.kind == second.kind
    assert first.selection == second.selection
    pd.testing.assert_series_equal(first.levels, second.levels)
    pd.testing.assert_frame_equal(first.transformer.centres, second.transformer.centres)
    np.testing.assert_array_equal(first.transformer.scale, second.transformer.scale)
    assert first.groups == second.groups
    np.testing.assert_array_equal(first.predict_quantiles(train), second.predict_quantiles(train))
    assert second.qhat != first.qhat


def test_future_perturbation_preserves_actual_model_and_price(raw_panel):
    future_changed = raw_panel.copy()
    future = future_changed.annee >= 2019
    future_changed.loc[future, "rendement_qha"] = 10000
    future_changed.loc[future, "surface_ha"] = 1e9
    future_changed.loc[future, WEATHER] = -1e6
    future_changed.loc[future, "prix_ble"] = 50000
    fits, prices = [], []
    h = {"charges_ble": 700, "charges_lentille": 800, "bonus": 0}
    for panel in (raw_panel, future_changed):
        past = prepare_as_of(panel, 2019)
        fitted = Calibrated("M1").fit(past)
        pool = past[past.dep == "01"].copy()
        pool["tendance"] = 0.9
        prices.append(break_even_prices(pool, fitted, fitted, fitted.levels["01"],
                                         70, h, n=2000, seed=19)[0])
        fits.append(fitted)
    assert fits[0].audit == fits[1].audit
    np.testing.assert_array_equal(prices[0], prices[1])


def test_grouping_and_representative_use_proper_years_only(raw_panel):
    panel = prepare_as_of(raw_panel, 2019)
    for year in range(2010, 2014):
        value = panel.loc[(panel.dep == "01") & (panel.annee == year), "rendement_qha"].iloc[0]
        panel.loc[(panel.dep == "02") & (panel.annee == year), "rendement_qha"] = value
    first = Calibrated("M0").fit(panel)
    assert first.groups["01"] == "02"  # Larger proper-training surface.
    panel.loc[(panel.dep == "01") & (panel.annee >= 2014), "surface_ha"] = 1e8
    panel.loc[panel.annee >= 2014, "rendement_qha"] = 99
    second = Calibrated("M0").fit(panel)
    assert first.groups == second.groups
    assert "01" in second.levels.index  # Levels available for matching crop territories.


def test_relative_target_supplied_by_caller_is_ignored(raw_panel):
    raw = prepare_as_of(raw_panel, 2019)
    first = Calibrated("M0").fit(raw)
    second = Calibrated("M0").fit(raw.assign(rel=1e6))
    np.testing.assert_array_equal(first.predict(raw), second.predict(raw))


def test_cqr_uses_exact_finite_sample_order_statistic(raw_panel):
    raw = prepare_as_of(raw_panel, 2019)
    fitted = Calibrated("M0").fit(raw)
    cal = raw[raw.annee.isin(fitted.audit["calibration_years"]) &
              raw.dep.isin(fitted.retained_deps)]
    q = fitted.predict_quantiles(cal)
    y = cal.rendement_qha / cal.dep.map(fitted.levels)
    scores = np.maximum(q[:, 0] - y, y - q[:, 2])
    rank = int(np.ceil((len(scores) + 1) * 0.8))
    assert fitted.qhat == pytest.approx(max(0, np.sort(scores)[rank - 1]))


def test_interval_correction_never_changes_simulated_distribution(raw_panel):
    raw = prepare_as_of(raw_panel, 2019)
    fitted = Calibrated("M0").fit(raw)
    pool = raw[raw.dep == "01"]
    h = {"charges_ble": 700, "charges_lentille": 800, "bonus": 0}
    first = break_even_prices(pool, fitted, fitted, 15, 70, h, n=1000, seed=1)
    intervals = fitted.predict(pool)
    fitted.qhat += 10
    second = break_even_prices(pool, fitted, fitted, 15, 70, h, n=1000, seed=1)
    np.testing.assert_array_equal(first[0], second[0])
    assert np.all(fitted.predict(pool)[:, 2] > intervals[:, 2])


def test_tail_sensitivity_changes_only_declared_extrapolation():
    q = np.tile([0.6, 1.0, 1.4], (5, 1))
    u = np.array([0.01, 0.1, 0.5, 0.9, 0.99])
    linear = model.sample_quantile(q, u)
    stress = model.sample_quantile(q, u, tail="stress")
    bounded = model.sample_quantile(q, u, tail="bounded")
    assert stress[0] < linear[0] < bounded[0]
    np.testing.assert_allclose(stress[1:], linear[1:])
    assert bounded[-1] < linear[-1]


def test_ensemble_is_ordered_fixed_weight_average(raw_panel):
    raw = prepare_as_of(raw_panel, 2019)
    fitted = Calibrated("M3").fit(raw)
    transformed = fitted.transformer.transform(raw)
    expected = np.mean([m.predict(transformed) for m in fitted.model.models], axis=0)
    np.testing.assert_allclose(fitted.predict_quantiles(raw), np.clip(expected, 0.02, None))
    assert np.all(np.diff(fitted.predict_quantiles(raw), axis=1) >= 0)


def test_insufficient_history_fails_explicitly(raw_panel):
    with pytest.raises(ValueError, match="huit années"):
        Calibrated("M0").fit(prepare_as_of(raw_panel, 2017))


def test_selection_scores_the_deployed_quantiles(raw_panel):
    raw = prepare_as_of(raw_panel, 2019)
    fitted = Calibrated("auto").fit(raw)
    selection = raw[raw.annee.isin(fitted.audit["selection_years"]) &
                    raw.dep.isin(fitted.retained_deps)]
    losses = [model.pinball(fitted.predict_quantiles(rows),
                           (rows.rendement_qha / rows.dep.map(fitted.levels)).to_numpy())
              for _, rows in selection.groupby("annee")]
    assert fitted.selection[fitted.kind] == pytest.approx(np.mean(losses))


def test_weather_covers_every_usable_lentil_territory():
    panel = pd.read_csv(model.DATA / "panel_rendements.csv", dtype={"dep": str})
    _, weather = model.load()
    lentil_deps = set(panel.loc[panel.utilisable & (panel.culture == "lentille"), "dep"])
    assert lentil_deps <= set(weather.dep)


def test_load_ignores_full_history_duplicate_flags(tmp_path, monkeypatch):
    import shutil

    for name in ("panel_rendements.csv", "meteo_dept.csv", "prix_ble.csv"):
        shutil.copyfile(model.DATA / name, tmp_path / name)
    monkeypatch.setattr(model, "DATA", tmp_path)
    original, weather = model.load()
    panel_path = tmp_path / "panel_rendements.csv"
    panel = pd.read_csv(panel_path, dtype={"dep": str})
    panel["doublon"] = True
    panel["serie_groupe"] = "99"
    panel.to_csv(panel_path, index=False)
    altered, altered_weather = model.load()
    columns = [c for c in original if c not in ("doublon", "serie_groupe")]
    pd.testing.assert_frame_equal(original[columns], altered[columns])
    pd.testing.assert_frame_equal(weather, altered_weather)
