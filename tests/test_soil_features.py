import importlib.util
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location("fetch_soil_features", Path(__file__).parents[1] / "pipeline/fetch_soil_features.py")
soil = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(soil)


def test_soil_statistics_preserve_real_zero_and_reject_invalid():
    result = soil.summarize_values([0, 100, 200, np.nan, -999])
    assert result["soil_ru_mean_mm"] == 100
    assert result["soil_ru_q10_mm"] == 20
    assert result["soil_ru_q90_mm"] == 180
    assert result["soil_ru_sd_spatial_mm"] == pytest.approx(np.std([0, 100, 200]))


def test_no_invented_soil_values_for_empty_geometry():
    with pytest.raises(ValueError, match="No finite"):
        soil.summarize_values([np.nan, -999])


def test_weighted_statistics_are_area_weighted_and_scale_invariant():
    result = soil.weighted_soil_statistics([0, 100, 200], [1, 8, 1])
    assert result == soil.weighted_soil_statistics([0, 100, 200], [10, 80, 10])
    assert result["soil_ru_mean_mm"] == 100
    assert result["soil_ru_q10_mm"] == 0
    assert result["soil_ru_q90_mm"] == 100
    assert result["soil_ru_sd_spatial_mm"] == pytest.approx(np.sqrt(2000))


def test_negative_or_missing_area_is_not_silently_accepted():
    for weights in ([-1, 1], [np.nan, 1]):
        with pytest.raises(ValueError, match="Invalid soil weights"):
            soil.weighted_soil_statistics([50, 100], weights)


def test_static_soil_aggregation_does_not_invent_missing_grid_values():
    import pandas as pd
    cells = pd.DataFrame({"LAMBX": [1, 2], "LAMBY": [1, 1],
        "rupro": [100., 200.], "pro": [50., 100.], "hcc": [30., 40.], "hpf": [10., 20.],
        "agri_fraction": [.1, .9]})
    weights = pd.DataFrame({"dep": ["01"] * 3, "LAMBX": [1, 2, 3], "LAMBY": [1, 1, 1],
                            "weight": [.25, .25, .5]})
    result, coverage = soil.aggregate_soil_cells(cells, weights)
    assert result.iloc[0].soil_ru_mean_mm == 190
    assert result.iloc[0].soil_depth_mean_cm == 95
    assert coverage[0]["known_soil_land_weight"] == .5
    assert coverage[0]["positive_agricultural_cells"] == 2
