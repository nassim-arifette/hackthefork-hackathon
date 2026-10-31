"""Checks of real SIM processing: preserve calendar and spatial quantities."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from fetch_sim_features import agriculture_weights, overlap_days, phase_values, read_year, spatial_average


def calendar_frame(year=2020, x=100):
    return pd.DataFrame([dict(LAMBX=x, LAMBY=24000, DATE=year * 100 + month,
        DECADE=decade, PRETOTD=10., EVAP=5., ETP=20., SWI=.3)
        for month in range(1, 13) for decade in (1, 2, 3)])


def test_leap_decade_and_partial_window():
    assert overlap_days(2020, 2, 3, ("02-21", "02-29")) == (9, 9)
    assert overlap_days(2019, 2, 3, ("02-21", "02-28")) == (8, 8)
    assert overlap_days(2020, 5, 2, ("05-15", "06-30")) == (6, 10)
    values = phase_values(calendar_frame(), 2020, ("02-01", "02-29"))
    assert values["low_swi_days"] == 29
    assert values["deficit_mm"] == 30
    assert values["rain_mm"] == 30
    assert values["evap_etp"] == .25
    assert values["swi_mean"] == pytest.approx(.3)


def test_spatial_weights_preserve_mass_and_detect_missing_grid():
    a, b = calendar_frame(x=100), calendar_frame(x=180)
    b["PRETOTD"], b["SWI"] = 30., .9
    weights = pd.DataFrame([dict(dep="77", LAMBX=100, LAMBY=24000, weight=.25),
                            dict(dep="77", LAMBX=180, LAMBY=24000, weight=.75)])
    result = spatial_average(pd.concat([a, b]), weights)
    assert len(result) == 36
    assert np.allclose(result.PRETOTD, 25.)
    assert np.allclose(result.SWI, .75)
    with pytest.raises(ValueError, match="coverage"):
        spatial_average(a, weights)


def test_reader_rejects_missing_and_duplicate_preserves_condensation(tmp_path):
    path = tmp_path / "input.csv.gz"
    data = calendar_frame()
    data.loc[0, "EVAP"] = -1.2
    data.to_csv(path, index=False, sep=";")
    assert read_year(path, 2020).EVAP.iloc[0] == -1.2
    data.iloc[:-1].to_csv(path, index=False, sep=";")
    with pytest.raises(ValueError, match="36 decades"):
        read_year(path, 2020)
    pd.concat([data, data.iloc[:1]]).to_csv(path, index=False, sep=";")
    with pytest.raises(ValueError, match="Duplicate"):
        read_year(path, 2020)


def test_agricultural_fraction_changes_spatial_support_without_imputation():
    geometry = pd.DataFrame([dict(dep="77", LAMBX=100, LAMBY=24000, weight=.5),
                             dict(dep="77", LAMBX=180, LAMBY=24000, weight=.5)])
    fractions = pd.DataFrame([dict(LAMBX=100, LAMBY=24000, agri_fraction=.2),
                              dict(LAMBX=180, LAMBY=24000, agri_fraction=.8)])
    result = agriculture_weights(geometry, fractions)
    assert result.weight.to_list() == pytest.approx([.2, .8])
    with pytest.raises(ValueError, match="Missing agricultural"):
        agriculture_weights(geometry, fractions.iloc[:1])
    explicit_subset = agriculture_weights(geometry, fractions.iloc[:1], allow_unmapped=True)
    assert explicit_subset.weight.to_list() == [1.]
    assert explicit_subset.LAMBX.to_list() == [100]
    fractions.agri_fraction = 0
    with pytest.raises(ValueError, match="without positive"):
        agriculture_weights(geometry, fractions)
