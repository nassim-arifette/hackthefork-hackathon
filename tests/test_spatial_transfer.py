import numpy as np
import pandas as pd

from benchmark_spatial_transfer import climate_analogues, region_training
from model import WEATHER


def weather_rows():
    return pd.DataFrame([dict(dep=dep, annee=year, **{w: value+year-2010 for w in WEATHER})
                         for dep, value in [('01', 0.), ('02', 1.), ('03', 2.), ('04', 3.), ('05', 10.), ('99', 1.5)]
                         for year in range(2010, 2026)])


def test_climate_donors_and_level_cannot_see_future_weather():
    weather = weather_rows()
    levels = pd.Series([10., 20., 30., 40., 50.], index=['01', '02', '03', '04', '05'])
    before = climate_analogues(weather, levels, '99', 2019)
    changed = weather.copy()
    changed.loc[changed.annee >= 2019, WEATHER] = 1e9
    after = climate_analogues(changed, levels, '99', 2019)
    assert before[:3] == after[:3]
    assert before[1] == ['02', '03', '01', '04']
    assert before[0] == 25.


def test_target_lentil_level_never_enters_analogue_estimate():
    weather = weather_rows()
    levels = pd.Series([10., 20., 30., 40., 50., 999.], index=['01', '02', '03', '04', '05', '99'])
    first = climate_analogues(weather, levels, '99', 2019)
    levels.loc['99'] = .001
    second = climate_analogues(weather, levels, '99', 2019)
    assert first[:3] == second[:3]
    assert '99' not in first[1]


def test_region_exclusion_also_removes_duplicate_source_series():
    rows = []
    for dep, region, offset in [('01', 'held', 0.), ('02', 'train', 0.), ('03', 'train', 3.)]:
        for year in range(2010, 2020):
            rows.append(dict(dep=dep, region=region, culture='lentille', annee=year,
                             surface_ha=100., rendement_qha=10.+year-2010+offset))
    data = pd.DataFrame(rows)
    train, excluded = region_training(data, 'held', 2019)
    assert set(train.dep) == {'03'} and excluded == ['02']
    assert train.annee.max() == 2018
    data.loc[data.annee >= 2019, 'rendement_qha'] = 1e9
    changed, excluded_changed = region_training(data, 'held', 2019)
    pd.testing.assert_frame_equal(train, changed)
    assert excluded_changed == excluded
