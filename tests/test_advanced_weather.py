"""Check order-sensitive information, calendar boundaries and complete inputs."""
import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from advanced_weather import (FEATURE_SPECS, ROOT, advanced_columns,
                              aggregate_year, longest_spell)
from crop_weather import read_daily


@pytest.fixture
def quiet_year():
    return pd.DataFrame({"T2M_MAX": 20.0, "T2M_MIN": 10.0, "PRECTOTCORR": 0.0},
                        index=pd.date_range("2024-01-01", "2024-12-31"))


def test_rain_order_changes_sequences_despite_same_total(quiet_year):
    dispersed, concentrated = quiet_year.copy(), quiet_year.copy()
    dispersed.loc[pd.date_range("2024-05-01", "2024-06-30", freq="5D"), "PRECTOTCORR"] = 10
    concentrated.loc[pd.date_range("2024-05-01", periods=13), "PRECTOTCORR"] = 10
    assert dispersed.PRECTOTCORR.sum() == concentrated.PRECTOTCORR.sum()
    a, b = aggregate_year(dispersed, 2024), aggregate_year(concentrated, 2024)
    assert a["lentille_dry_spell_reproductive_days"] == 4
    assert b["lentille_dry_spell_reproductive_days"] == 48
    assert a["lentille_rain_max5_reproductive_mm"] == 10
    assert b["lentille_rain_max5_reproductive_mm"] == 50


def test_thresholds_and_phase_boundaries(quiet_year):
    quiet_year.loc["2024-04-30":"2024-05-02", "T2M_MAX"] = 31
    quiet_year.loc["2024-05-03", ["T2M_MAX", "PRECTOTCORR"]] = [30, 1]
    quiet_year.loc["2024-05-04", ["T2M_MAX", "PRECTOTCORR"]] = [31, 10]
    quiet_year.loc["2024-07-01":"2024-07-03", "PRECTOTCORR"] = [1, 0.99, 2]
    result = aggregate_year(quiet_year, 2024)
    assert result["lentille_hot_spell_reproductive_days"] == 2
    assert result["lentille_hot_dry_reproductive_days"] == 2
    assert result["lentille_heavy_rain_reproductive_days"] == 1
    assert result["lentille_wet_spell_harvest_days"] == 1
    assert result["lentille_rain_top5_share_reproductive"] == 1


def test_shifted_windows_and_antecedent_do_not_alias_main_phase(quiet_year):
    quiet_year.loc[["2024-02-29", "2024-04-17", "2024-07-14", "2024-07-15"], "PRECTOTCORR"] = [2, 3, 5, 11]
    result = aggregate_year(quiet_year, 2024)
    assert result["lentille_rain_reproductive_early14_mm"] == 3
    assert result["lentille_rain_reproductive_late14_mm"] == 5
    assert result["lentille_rain_antecedent_mm"] == 2
    # Pea vegetative period starts February 1, so February 29 belongs to the
    # vegetative phase and cannot enter its January-only antecedent rainfall.
    assert result["pois_rain_antecedent_mm"] == 0
    assert result["pois_gdd5_vegetative_cdays"] == 90 * 10
    assert result["lentille_gdd5_vegetative_cdays"] == 61 * 10


def test_zero_rain_has_defined_concentration_and_full_dry_spell(quiet_year):
    result = aggregate_year(quiet_year, 2024)
    assert result["lentille_rain_top5_share_reproductive"] == 0
    assert result["lentille_dry_spell_reproductive_days"] == 61
    assert result["lentille_rain_max5_reproductive_mm"] == 0


def test_missing_day_sentinel_and_invalid_measurements_fail(quiet_year):
    with pytest.raises(ValueError, match="Incomplete"):
        aggregate_year(quiet_year.drop(pd.Timestamp("2024-02-29")), 2024)
    for column, value, message in [("PRECTOTCORR", np.nan, "Incomplete"),
                                   ("PRECTOTCORR", -1, "negative"),
                                   ("T2M_MIN", 21, "temperatures")]:
        broken = quiet_year.copy()
        broken.loc["2024-06-01", column] = value
        with pytest.raises(ValueError, match=message):
            aggregate_year(broken, 2024)
    with pytest.raises(ValueError, match="unique"):
        aggregate_year(pd.concat([quiet_year, quiet_year.iloc[[0]]]), 2024)


def test_other_years_do_not_enter_features(quiet_year):
    original = aggregate_year(quiet_year, 2024)
    future = quiet_year.copy()
    future.index += pd.DateOffset(years=4)
    future.PRECTOTCORR = 1000
    future.T2M_MAX = 100
    assert aggregate_year(pd.concat([quiet_year, future]), 2024) == original


def test_spell_boundary_runs_empty_input_and_shape():
    assert longest_spell([]) == 0
    assert longest_spell([False, False]) == 0
    assert longest_spell([True, True, False, True, True, True]) == 3
    assert longest_spell([True, True, True]) == 3
    with pytest.raises(ValueError, match="one-dimensional"):
        longest_spell([[True]])


def test_generated_features_and_manifest_reproduce_raw_cache():
    path = ROOT / "data/meteo_advanced_cultures.csv"
    data = pd.read_csv(path, dtype={"dep": str})
    base = pd.read_csv(ROOT / "data/meteo_dept_cultures.csv", dtype={"dep": str})
    columns = [column for crop in FEATURE_SPECS for column in advanced_columns(crop)]
    assert list(data.columns) == ["dep", "annee"] + columns
    assert len(data) == 1392
    assert not data.duplicated(["dep", "annee"]).any()
    assert set(map(tuple, data[["dep", "annee"]].to_numpy())) == set(map(tuple, base[["dep", "annee"]].to_numpy()))
    assert np.isfinite(data[columns].to_numpy()).all()
    assert (data[columns] >= 0).all().all()
    shares = [column for column in columns if "share" in column]
    assert (data[shares] <= 1).all().all()
    original = aggregate_year(read_daily(ROOT / "data_raw/nasa_power/77.json"), 2025)
    row = data[(data.dep == "77") & (data.annee == 2025)].iloc[0]
    assert np.allclose(row[columns].to_numpy(dtype=float), [original[c] for c in columns])
    manifest = json.loads((ROOT / "data/meteo_advanced_manifest.json").read_text())
    assert manifest["output_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert manifest["rows"] == len(data)
    assert len(manifest["spec"]["sources_sha256"]) == 90
    with pytest.raises(ValueError, match="Unknown"):
        advanced_columns("unobserved_crop")
