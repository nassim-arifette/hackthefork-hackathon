"""Economic, temporal and distribution invariants for the expanded benchmark."""
import argparse
from copy import deepcopy

import numpy as np
import pandas as pd
import pytest
from scipy.special import ndtri

import benchmark_advanced as advanced
import benchmark_multilegumes as previous
from advanced_weather import advanced_columns
from analyze_multilegumes import validate_raw
from crop_weather import seasonal_columns
from fetch_sim_features import sim_columns
from multicrop_models import WEATHER, sample_quantile


def example_panel():
    records = []
    for culture in ("ble", "lentille"):
        for dep, area, base in (("01", 100, 12), ("02", 200, 18), ("03", 300, 23)):
            for year in range(2010, 2021):
                row = {"dep": dep, "culture": culture, "annee": year, "surface_ha": area,
                    "region": "R1", "doublon": False, "prix_ble": 160 + 8 * (year - 2010),
                    "rendement_qha": base + (year - 2010) * .2 + int(dep) * (year % 3)
                        + (45 if culture == "ble" else 0)}
                columns = (*WEATHER, *seasonal_columns("lentille"), *advanced_columns("lentille"),
                           *sim_columns("lentille"), *sim_columns("ble"),
                           *sim_columns("lentille", tag="sim_agri"))
                for i, name in enumerate(columns):
                    row[name] = 10 + 2 * int(dep) + i + (year - 2010) * (i + 1)
                for i, name in enumerate(advanced.SOIL_COLUMNS):
                    row[name] = 40 * int(dep) + i * 10
                records.append(row)
    return pd.DataFrame(records)


def inject_data(monkeypatch, panel):
    weather = panel[panel.culture == "ble"].drop(columns=["culture", "rendement_qha", "region",
        "doublon", "surface_ha"]).copy()
    monkeypatch.setattr(advanced, "load_data", lambda *_: (panel.copy(), weather.copy(), []))
    return weather


def args(tmp_path, models, years=(2019,)):
    return argparse.Namespace(output=tmp_path, data_dir=advanced.ROOT / "data", cultures=["lentille"],
        models=models, years=list(years), samples=1000, seed=42, threads=1)


def small_registry():
    registry = deepcopy(advanced.candidate_registry())
    for spec in registry.values():
        if spec.get("model_spec", {}).get("family") == "qrf":
            spec["model_spec"].setdefault("params", {})["n_estimators"] = 12
    return registry


def test_three_point_sampler_is_exact_legacy_and_dense_tails_are_explicit():
    u = np.array([0., .05, .1, .3, .5, .8, .9, 1.])
    q = np.tile([.3, 1., 2.], (len(u), 1))
    np.testing.assert_array_equal(advanced.inverse_quantiles(q, u, (.1, .5, .9)), sample_quantile(q, u))
    grid = np.array([.05, .2, .5, .8, .95])
    linear = np.repeat((2 * grid + .1)[None, :], len(u), axis=0)
    np.testing.assert_allclose(advanced.inverse_quantiles(linear, u, grid), 2 * u + .1)
    with pytest.raises(ValueError, match="ordered"):
        advanced.inverse_quantiles(linear[:, ::-1], u, grid)


def test_gaussian_copula_preserves_marginals_and_has_requested_normal_correlation():
    rng = np.random.default_rng(12)
    uc, uw = rng.random(100000), rng.random(100000)
    a, b = advanced.coupled_uniforms(uc, uw, np.zeros((30, 2)),
        {"rho": .6, "dependence_fallback": False}, "gaussian", 2019, "77", 42)
    assert a.mean() == pytest.approx(.5, abs=.004)
    assert b.mean() == pytest.approx(.5, abs=.004)
    assert np.var(b) == pytest.approx(1 / 12, abs=.001)
    assert np.corrcoef(ndtri(a), ndtri(b))[0, 1] == pytest.approx(.6, abs=.01)


def test_empirical_copula_preserves_uniform_marginals_and_paired_order():
    rng = np.random.default_rng(13)
    uc, uw = rng.random(100000), rng.random(100000)
    pairs = np.column_stack([np.arange(50), np.arange(50)])
    a, b = advanced.coupled_uniforms(uc, uw, pairs,
        {"rho": 0., "dependence_fallback": False}, "empirical_checkerboard", 2019, "77", 42)
    assert a.mean() == pytest.approx(.5, abs=.004)
    assert b.mean() == pytest.approx(.5, abs=.004)
    assert np.var(a) == pytest.approx(1 / 12, abs=.001)
    assert np.corrcoef(a, b)[0, 1] > .99
    again = advanced.coupled_uniforms(uc, uw, pairs,
        {"rho": 0., "dependence_fallback": False}, "empirical_checkerboard", 2019, "77", 42)
    np.testing.assert_array_equal(a, again[0])


def test_dependence_uses_only_past_out_of_time_pairs_and_shrinks():
    diagnostics = [{"culture": "lentille", "model": "x", "year": 2018, "dep": str(i),
                    "crop_residual_standardized": i, "wheat_residual_standardized": i} for i in range(40)]
    pairs, metadata = advanced.dependence_history(diagnostics, "lentille", "x", 2019)
    assert metadata["rho"] == pytest.approx(40 / 70)
    assert metadata["dependence_max_year"] == 2018
    future = [{**r, "year": 2019, "wheat_residual_standardized": -r["wheat_residual_standardized"]}
              for r in diagnostics]
    pairs2, metadata2 = advanced.dependence_history(diagnostics + future, "lentille", "x", 2019)
    assert metadata == metadata2
    np.testing.assert_array_equal(pairs, pairs2)
    _, sparse = advanced.dependence_history(diagnostics[:19], "lentille", "x", 2019)
    assert sparse["dependence_fallback"] and sparse["rho"] == 0


def test_missing_data_is_reported_and_explicit_request_rejected():
    panel = example_panel()
    weather = panel[panel.culture == "ble"].drop(columns=list(advanced.SOIL_COLUMNS))
    chosen, missing = advanced.available_candidates(advanced.candidate_registry(), panel, weather, ["lentille"])
    assert "trend" in chosen and "qrf_sim_dense" in chosen
    assert "qrf_soil_dense" not in chosen and "qrf_soil_dense" in missing
    with pytest.raises(ValueError, match="Requested data unavailable"):
        advanced.available_candidates(advanced.candidate_registry(), panel, weather,
                                      ["lentille"], ["qrf_soil_dense"])


def test_reference_prices_reproduce_published_benchmark_exactly(tmp_path, monkeypatch):
    panel = example_panel()
    weather = inject_data(monkeypatch, panel)
    monkeypatch.setattr(previous, "read_data", lambda **_: (panel.copy(), weather.copy()))
    old_args = argparse.Namespace(output=tmp_path / "old", cultures=["lentille"],
        models=["trend", "qrf_seasonal"], years=[2019], samples=1000, seed=42, threads=1,
        seasonal_file=advanced.ROOT / "data/meteo_saisonnier_cultures.csv", seasonal_columns=None)
    old = previous.run(old_args)
    new = advanced.run(args(tmp_path / "new", ["trend", "qrf_seasonal"]))
    columns = ["culture", "dep", "year", "model", "contract", "coefficient", "actual_basis",
               "simulation_basis_mean", "simulation_accepted_mean", "held", "expected_unit_cost"]
    pd.testing.assert_frame_equal(old[columns], new[columns])


def test_future_perturbation_cannot_change_prices_and_shrinkage_preserves_contract_basis(tmp_path, monkeypatch):
    panel = example_panel()
    weather = inject_data(monkeypatch, panel)
    registry = small_registry()
    monkeypatch.setattr(advanced, "candidate_registry", lambda: registry)
    names = ["trend", "qrf_soil_shrinkage", "qrf_joint_gaussian", "qrf_joint_empirical"]
    before = advanced.run(args(tmp_path / "before", names, years=(2016, 2017, 2018, 2019)))
    validate_raw(before)
    mask = panel.annee >= 2019
    panel.loc[mask, "rendement_qha"] *= 2
    panel.loc[mask, "prix_ble"] *= 2
    panel.loc[mask, list(WEATHER)] += 1000
    weather.loc[weather.annee >= 2019, "prix_ble"] *= 2
    weather.loc[weather.annee >= 2019, list(WEATHER)] += 1000
    after = advanced.run(args(tmp_path / "after", names, years=(2016, 2017, 2018, 2019)))
    columns = ["dep", "year", "model", "contract", "coefficient", "expected_unit_cost",
               "simulation_basis_mean", "simulation_accepted_mean", "past_mean_accepted", "rho"]
    pd.testing.assert_frame_equal(before[columns], after[columns])
    assert not np.array_equal(before.actual_need_eur_ha, after.actual_need_eur_ha)
    monkeypatch.setattr(advanced.AdvancedYieldModel, "fit", lambda *a, **k: pytest.fail("unexpected fit"))
    resumed = advanced.run(args(tmp_path / "after", names, years=(2016, 2017, 2018, 2019)))
    pd.testing.assert_frame_equal(after, resumed)
