import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from fetch_rpg_sim_features import crop_features, start_from_fallback, validate_rpg_weights
from fetch_sim_features import SPECS, sim_columns


def test_rpg_weights_normalize_roundoff_and_reject_invalid_support():
    data = pd.DataFrame([dict(dep="77", culture="lentille", LAMBX=1, LAMBY=2, weight=.3333333333),
                         dict(dep="77", culture="lentille", LAMBX=2, LAMBY=2, weight=.6666666666)])
    normalized = validate_rpg_weights(data, ["77"])
    assert normalized.weight.sum() == pytest.approx(1, abs=1e-15)
    with pytest.raises(ValueError, match="unknown target department"):
        validate_rpg_weights(data, ["78"])
    data.loc[0, "weight"] = .1
    with pytest.raises(ValueError, match="sum to one"):
        validate_rpg_weights(data, ["77"])


def test_fallback_preserves_each_crop_exactly():
    row = {"dep": "77", "annee": 2020}
    for i, crop in enumerate(SPECS):
        row.update({column: i + .12345678 for column in sim_columns(crop, "sim_agri")})
    result = start_from_fallback(pd.DataFrame([row]))
    assert result.loc[("77", 2020), "ble_sim_rpg_swi_vegetative"] == row["ble_sim_agri_swi_vegetative"]
    assert result.loc[("77", 2020), "haricot_sim_rpg_rain_harvest_mm"] == row["haricot_sim_agri_rain_harvest_mm"]


def test_crop_features_use_crop_calendar_and_decadal_fluxes():
    data = pd.DataFrame([dict(dep="77", DATE=202000 + month, DECADE=decade,
        PRETOTD=10., EVAP=5., ETP=20., SWI=.3)
        for month in range(1, 13) for decade in (1, 2, 3)])
    row = crop_features(data, 2020, "lentille").iloc[0]
    assert row.lentille_sim_rpg_low_swi_reproductive_days_proxy == 61
    assert row.lentille_sim_rpg_climatic_deficit_reproductive_mm == 60
    assert row.lentille_sim_rpg_evap_etp_reproductive_ratio == .25
