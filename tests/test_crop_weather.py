"""Meaningful checks for crop windows, missing-data handling and replay dates."""
import numpy as np
import pandas as pd
import pytest

from crop_weather import (FEATURE_SPECS, LEGACY_WEATHER, PARAMETERS, ROOT,
                          aggregate_year, read_daily, seasonal_columns)


@pytest.fixture
def quiet_year():
    return pd.DataFrame({"T2M_MAX": 20.0, "T2M_MIN": 10.0, "PRECTOTCORR": 0.0},
                        index=pd.date_range("2024-01-01", "2024-12-31"))


def test_seasonal_features_follow_crop_calendar_not_one_shared_window(quiet_year):
    # A late July storm/heatwave is a reproductive event for bean/chickpea and
    # harvest weather for lentil/pea; faba bean has its own lower heat threshold.
    quiet_year.loc["2024-07-20", ["T2M_MAX", "PRECTOTCORR"]] = [40, 11]
    result = aggregate_year(quiet_year, 2024)
    assert result["haricot_rain_reproductive_mm"] == 11
    assert result["pois_chiche_rain_reproductive_mm"] == 11
    assert result["lentille_rain_reproductive_mm"] == 0
    assert result["lentille_rain_harvest_mm"] == 11
    assert result["pois_rain_harvest_mm"] == 11
    assert result["haricot_heat_excess_cdays"] == 10
    assert result["pois_chiche_heat_excess_cdays"] == 5
    assert result["lentille_heat_excess_cdays"] == 0
    assert result["feverole_heat_excess_cdays"] == 0


def test_crop_heat_thresholds_and_cold_mean_approximation(quiet_year):
    quiet_year.loc["2024-06-10", "T2M_MAX"] = 28
    quiet_year.loc["2024-06-11", ["T2M_MAX", "T2M_MIN"]] = [18, 10]
    result = aggregate_year(quiet_year, 2024)
    assert result["feverole_heat_excess_cdays"] == 3
    assert result["lentille_heat_excess_cdays"] == 0
    assert result["pois_chiche_cold_days"] == 1  # (18 + 10) / 2 < 15
    assert result["haricot_cold_days"] == 0


def test_inclusive_boundaries_and_leap_day(quiet_year):
    quiet_year.loc[["2024-02-29", "2024-05-15", "2024-06-30", "2024-07-01"], "PRECTOTCORR"] = 1
    result = aggregate_year(quiet_year, 2024)
    assert result["pois_rain_vegetative_mm"] == 1
    assert result["lentille_rain_vegetative_mm"] == 0
    assert result["haricot_rain_vegetative_mm"] == 2
    assert result["haricot_rain_reproductive_mm"] == 1
    assert result["lentille_rain_reproductive_mm"] == 2


def test_missing_day_or_sentinel_cannot_silently_become_zero_rain(quiet_year):
    with pytest.raises(ValueError, match="Incomplete"):
        aggregate_year(quiet_year.drop(pd.Timestamp("2024-06-15")), 2024)
    quiet_year.loc["2024-06-15", "PRECTOTCORR"] = np.nan
    with pytest.raises(ValueError, match="Incomplete"):
        aggregate_year(quiet_year, 2024)


def test_other_year_weather_does_not_enter_an_annual_feature(quiet_year):
    expected = aggregate_year(quiet_year, 2024)
    future = quiet_year.copy()
    future.index = future.index + pd.DateOffset(years=4)
    future.PRECTOTCORR = 1000
    future.T2M_MAX = 100
    assert aggregate_year(pd.concat([quiet_year, future]), 2024) == expected


def test_checked_in_file_matches_universe_and_raw_observations():
    base = pd.read_csv(ROOT / "data/meteo_dept_cultures.csv", dtype={"dep": str})
    seasonal = pd.read_csv(ROOT / "data/meteo_saisonnier_cultures.csv", dtype={"dep": str})
    assert len(seasonal) == 87 * 16
    assert not seasonal.duplicated(["dep", "annee"]).any()
    assert set(map(tuple, seasonal[["dep", "annee"]].to_numpy())) == set(
        map(tuple, base[["dep", "annee"]].to_numpy()))
    columns = [name for crop in FEATURE_SPECS for name in seasonal_columns(crop)]
    assert list(seasonal.columns) == ["dep", "annee"] + columns
    assert np.isfinite(seasonal[columns].to_numpy()).all()
    assert (seasonal[columns] >= 0).all().all()
    # Independently cross-check a real NASA rain sum and temperature sum.
    raw = read_daily(ROOT / "data_raw/nasa_power/77.json")
    row = seasonal[(seasonal.dep == "77") & (seasonal.annee == 2025)].iloc[0]
    assert row.haricot_rain_harvest_mm == pytest.approx(raw.loc["2025-08-16":"2025-09-30", "PRECTOTCORR"].sum())
    assert row.feverole_heat_excess_cdays == pytest.approx(
        sum(max(float(t) - 25, 0) for t in raw.loc["2025-05-01":"2025-07-15", "T2M_MAX"]))
    assert seasonal_columns("ble") == LEGACY_WEATHER
    with pytest.raises(ValueError, match="Unknown culture"):
        seasonal_columns("unknown")
