import numpy as np
import pandas as pd
import pytest

from analyze_model_groups import KNOWN_GROUPS, build_groups, department_analysis, paired_rows, paired_summary


def test_preseason_groups_and_thresholds_ignore_target_and_future_outcomes():
    rng = np.random.default_rng(14)
    rows, weather = [], []
    for dep in ["01", "02", "03", "04", "05", "06"]:
        for year in range(2010, 2023):
            rows.append({"dep": dep, "region": "test", "culture": "lentille", "annee": year,
                "utilisable": True, "serie_groupe": dep, "surface_ha": 100.,
                "rendement_qha": float(10 + int(dep) + rng.normal(0, int(dep) / 3))})
            weather.append({"dep": dep, "annee": year, "pluie_mj": 100 + rng.uniform(0, 100), "j30_jj": rng.integers(0, 20)})
    panel, meteo = pd.DataFrame(rows), pd.DataFrame(weather)
    prices = pd.DataFrame({"annee": range(2010, 2023), "prix_eur_t": np.arange(13) + 150.})
    cohort = pd.DataFrame({"year": [2019] * 3, "dep": ["01", "02", "03"]})
    original, thresholds = build_groups(panel, meteo, prices, cohort, set())
    panel.loc[panel.annee >= 2019, "rendement_qha"] *= 100
    meteo.loc[meteo.annee >= 2019, ["pluie_mj", "j30_jj"]] *= 100
    prices.loc[prices.annee >= 2019, "prix_eur_t"] *= 100
    changed, changed_thresholds = build_groups(panel, meteo, prices, cohort, set())
    fields = ["year", "dep", *KNOWN_GROUPS, "history_n", "past_mean_qha", "past_cv", "past_series_group"]
    pd.testing.assert_frame_equal(original[fields], changed[fields])
    assert thresholds == changed_thresholds
    assert not original.realised_yield_ratio.equals(changed.realised_yield_ratio)


def test_comparison_refuses_different_denominators_or_realised_truth():
    base = pd.DataFrame({"year": [2019, 2020], "dep": ["10", "10"], "model": ["trend"] * 2,
                         "realised_break_even": [900., 1000.]})
    candidate = base.assign(model="qrf")
    with pytest.raises(ValueError, match="Different evaluation cohorts"):
        paired_rows(pd.concat([base, candidate.iloc[:1]]), "trend", "qrf")
    candidate.loc[0, "realised_break_even"] = 901.
    with pytest.raises(ValueError, match="Different realised outcomes"):
        paired_rows(pd.concat([base, candidate]), "trend", "qrf")


def test_bootstrap_and_point_estimate_use_whole_years_not_case_count():
    records = []
    for year, count, delta in [(2019, 10, 20.), (2020, 1, -20.)]:
        for i in range(count):
            records.append({"year": year, "dep": str(i), "past_series_group": str(i), "region": "x",
                "contract_loss_baseline": 100., "contract_loss_candidate": 100. + delta,
                "price_baseline": 1000., "price_candidate": 1100.,
                "held_baseline": True, "held_candidate": True,
                "shortfall_eur_ha_baseline": 0., "shortfall_eur_ha_candidate": 0.})
    summary, annual = paired_summary(pd.DataFrame(records), bootstrap_draws=5000)
    assert summary["delta_contract_loss"] == 0.
    assert summary["delta_contract_loss_ci95_low"] == -20.
    assert summary["delta_contract_loss_ci95_high"] == 20.
    assert len(annual) == 2


def test_department_80_percent_means_six_wins_out_of_seven():
    records = []
    for model, wins in [("trend", 5), ("qrf", 6)]:
        for i, year in enumerate(range(2019, 2026)):
            records.append({"year": year, "dep": "10", "model": model,
                "realised_break_even": 1000., "held": i < wins, "price": 1001. if i < wins else 999.,
                "contract_loss": .2 if i < wins else .8, "shortfall_eur_ha": 0. if i < wins else 1.})
    metadata = pd.DataFrame({"year": range(2019, 2026), "dep": ["10"] * 7, "region": ["test"] * 7})
    details, summaries = department_analysis(pd.DataFrame(records), metadata, candidates=["qrf"])
    assert details.iloc[0].required_wins_for_80 == 6
    assert details.iloc[0].held_fraction_baseline == "5/7"
    assert details.iloc[0].held_fraction_candidate == "6/7"
    assert not details.iloc[0].meets_80_baseline
    assert details.iloc[0].meets_80_candidate
    assert summaries[0]["n_departments_80_candidate"] == 1
