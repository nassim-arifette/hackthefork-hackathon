"""Tests of cohort, temporal and economic invariants of the common benchmark."""
import argparse
import importlib

import numpy as np
import pandas as pd
import pytest

import benchmark_multilegumes as benchmark
from contract_economics import contract_basis, evaluate
from multicrop_models import (Features, WEATHER, YieldModel, prepare_training,
    read_data, representatives, scenario_draws, simulated_yields)


def example_panel():
    rows = []
    for culture in ("ble", "lentille"):
        for dep, area, base in (("01", 100, 12), ("02", 200, 18), ("03", 300, 23)):
            for year in range(2010, 2021):
                item = {"dep": dep, "culture": culture, "annee": year,
                    "surface_ha": area, "region": "Example region", "doublon": False,
                    "rendement_qha": base + (year - 2010) * .2 + int(dep) * (year % 3),
                    "prix_ble": 160 + 8 * (year - 2010)}
                if culture == "ble":
                    item["rendement_qha"] += 45
                for i, name in enumerate(WEATHER):
                    item[name] = 10 + 2 * int(dep) + i + (year - 2010) * (i + 1)
                rows.append(item)
    return pd.DataFrame(rows)


def test_representatives_rebuild_the_group_from_past_only():
    rows = []
    for dep, area in (("01", 50), ("02", 100)):
        for year in range(2010, 2026):
            rows.append({"culture": "lentille", "dep": dep, "annee": year,
                "surface_ha": area, "rendement_qha": 10 + year % 4 +
                (int(dep) if year < 2018 else 0)})
    panel = pd.DataFrame(rows)
    assert representatives(panel[panel.annee < 2018]) == {"01", "02"}
    assert representatives(panel) == {"02"}
    panel.loc[panel.annee >= 2018, "surface_ha"] = 100000
    assert representatives(panel[panel.annee < 2018]) == {"01", "02"}


def test_vectorized_grouping_matches_existing_agreste_rule_on_supplied_history():
    raw, _ = read_data()
    history = raw[(raw.culture == "pois") & (raw.annee < 2020)]
    flagged = importlib.import_module("01_agreste").flag_duplicates(history.copy())
    expected = set(flagged.loc[flagged.dep == flagged.serie_groupe, "dep"])
    assert representatives(history) == expected


def test_levels_and_weather_centres_use_only_fitting_history():
    panel = example_panel()
    history = panel[(panel.culture == "lentille") & (panel.annee < 2016)]
    prepared = prepare_training(history)
    expected = history.groupby("dep").rendement_qha.mean()
    pd.testing.assert_series_equal(prepared.levels, expected)
    pd.testing.assert_frame_equal(prepared.features.centres,
                                  history.groupby("dep")[list(WEATHER)].mean())
    assert max(prepared.years) == 2015
    assert np.isfinite(prepared.X).all()


def test_feature_transform_does_not_learn_from_prediction_weather():
    panel = example_panel()
    history = panel[(panel.culture == "lentille") & (panel.annee < 2016)]
    features = Features().fit(history)
    centres = features.centres.copy(deep=True)
    scale = features.scale.copy(deep=True)
    future = history.iloc[:2].copy()
    future.loc[:, list(WEATHER)] = 1e10
    features.transform(future)
    pd.testing.assert_frame_equal(features.centres, centres)
    pd.testing.assert_series_equal(features.scale, scale)


def test_common_random_numbers_are_stable_across_model_and_contract_order():
    expected = scenario_draws(9, 2019, "77", 1000)
    scenario_draws(9, 2020, "28", 1000)
    actual = scenario_draws(9, 2019, "77", 1000)
    for left, right in zip(expected, actual):
        np.testing.assert_array_equal(left, right)
    assert not np.array_equal(expected[1], expected[2])


@pytest.mark.parametrize("shape", ["fixed", "indexed", "tiers"])
def test_each_raw_contract_is_exactly_minimal_at_eighty_percent(shape):
    net = np.arange(1, 11, dtype=float) / 5
    wheat_price = np.linspace(160, 320, 10)
    need = np.array([-200, 0, 50, 300, 400, 600, 900, 1300, 2000, 4000])
    result = benchmark.evaluate_contract(shape, need, net, wheat_price, 1.2,
                                         actual_need=-20, actual_net=1., actual_wheat_price=200)
    basis = contract_basis(shape, net, wheat_price, 1.2)
    assert result["simulated_protection"] >= .8
    lower = np.nextafter(result["coefficient"], -np.inf)
    assert np.mean(evaluate(lower, basis, need, net)["held"]) < .8
    assert result["required_coefficient"] < 0
    assert result["held"]
    assert result["expected_unit_cost"] == pytest.approx(
        np.mean(result["coefficient"] * basis) / np.mean(net))


def test_current_data_cohorts_are_explicit_and_shared_by_models():
    raw, _ = read_data()
    wheat = raw[raw.culture == "ble"]
    expected = {"lentille": (133, 192), "pois_chiche": (100, 129),
                "haricot": (71, 78), "pois": (493, 494), "feverole": (446, 491)}
    wheat_levels = {year: prepare_training(wheat[wheat.annee < year]).levels
                    for year in range(2019, 2026)}
    for culture, (old_count, modern_count) in expected.items():
        assert len(benchmark.legacy_keys(raw, culture, range(2019, 2026))) == old_count
        crop = raw[raw.culture == culture]
        count = 0
        for year in range(2019, 2026):
            levels = prepare_training(crop[crop.annee < year]).levels
            common = set(levels.index) & set(wheat_levels[year].index)
            common &= set(wheat[wheat.annee == year].dep)
            count += len(crop[(crop.annee == year) & crop.dep.isin(common)])
        assert count == modern_count


def test_candidate_comparison_rejects_a_missing_case():
    rows = pd.DataFrame([{"culture": "pois", "year": 2020, "dep": dep,
                          "model": model, "contract": contract}
        for dep in ("01", "02") for model in ("trend", "qrf")
        for contract in benchmark.CONTRACTS])
    benchmark.assert_common_cohort(rows, ["trend", "qrf"])
    with pytest.raises(ValueError, match="different cases"):
        benchmark.assert_common_cohort(rows.iloc[1:], ["trend", "qrf"])


def test_summary_unit_cost_weights_tonnes_before_averaging_years():
    rows = pd.DataFrame({"culture": ["pois"] * 2, "model": ["trend"] * 2,
        "contract": ["fixed"] * 2, "year": [2019] * 2, "held": [True, True],
        "expected_unit_cost": [100., 300.], "coefficient": [100., 300.],
        "simulation_basis_mean": [1., 3.], "simulation_accepted_mean": [1., 3.],
        "paid_actual_eur_ha": [100., 900.], "accepted_yield_actual": [1., 3.],
        "shortfall_eur_ha": [0., 0.], "contract_loss_eur_ha": [0., 0.],
        "old_cohort": [True, True]})
    row = benchmark.summarize(rows)[0]
    assert row["expected_unit_cost_year_mean"] == 250
    assert row["realized_unit_cost_year_mean"] == 250


def test_end_to_end_prices_ignore_current_and_future_outcomes_and_weather(tmp_path, monkeypatch):
    panel = example_panel()
    weather = panel[panel.culture == "ble"][["dep", "annee", "prix_ble", *WEATHER]].copy()
    monkeypatch.setattr(benchmark, "read_data", lambda **_: (panel.copy(), weather.copy()))
    args = argparse.Namespace(output=tmp_path / "first", cultures=["lentille"],
        models=["trend", "linear"], years=[2019], samples=1000, seed=42,
        threads=1, seasonal_file=None, seasonal_columns=None)
    before = benchmark.run(args)
    mask = panel.annee >= 2019
    panel.loc[mask, "rendement_qha"] *= 2
    panel.loc[mask, "surface_ha"] *= 100
    panel.loc[mask, list(WEATHER)] += 1000
    panel.loc[mask, "prix_ble"] *= 2
    weather.loc[weather.annee >= 2019, list(WEATHER)] += 1000
    weather.loc[weather.annee >= 2019, "prix_ble"] *= 2
    args.output = tmp_path / "perturbed"
    after = benchmark.run(args)
    columns = ["dep", "model", "contract", "coefficient", "expected_unit_cost",
               "simulation_basis_mean", "simulation_accepted_mean", "past_mean_accepted"]
    pd.testing.assert_frame_equal(before[columns], after[columns])
    assert not np.array_equal(before.actual_need_eur_ha, after.actual_need_eur_ha)
    # The same signature resumes individual model/year files, without refitting.
    monkeypatch.setattr(YieldModel, "fit", lambda *args, **kwargs: pytest.fail("unexpected refit"))
    resumed = benchmark.run(args)
    pd.testing.assert_frame_equal(after, resumed)
