import numpy as np
import pandas as pd
import pytest

from analyze_multilegumes import (add_groups, calibrate_policies, grouped_summaries,
    paired_comparisons, select_policies, summarize_group, validate_raw,
    weighted_empirical_quantile, subgroup_comparisons)


def raw_sample():
    records = []
    for year in range(2016, 2022):
        for dep, net, required in (("01", 1., -20.), ("02", 2., 85.), ("03", 3., 130.)):
            for model, coefficient in (("trend", 100.), ("qrf", 90.)):
                records.append({"culture": "lentille", "contract": "fixed", "year": year,
                    "dep": dep, "region": "A" if dep != "03" else "B", "model": model,
                    "coefficient": coefficient, "required_coefficient": required,
                    "actual_basis": net, "actual_need_eur_ha": net * required,
                    "accepted_yield_actual": net, "simulation_basis_mean": net,
                    "simulation_accepted_mean": net, "old_cohort": dep != "03",
                    "history_n": year - 2010, "history_cv": .1 if dep == "01" else .5,
                    "simulated_protection": .8})
    return pd.DataFrame(records)


def test_negative_required_prices_are_kept_and_zero_floor_is_valid():
    raw = raw_sample()
    raw["required_coefficient"] = -20.
    raw["actual_need_eur_ha"] = -20. * raw.actual_basis
    rows = calibrate_policies(raw)
    signed = rows[(rows.year == 2017) & (rows.calibration == "signed80")]
    assert len(signed) == 6
    assert (signed.coefficient == 0).all()
    assert signed.held.all()
    assert (signed.shortfall_eur_ha == 0).all()
    main = rows[rows.product_eligible]
    assert (main.coefficient >= main.raw_coefficient).all()
    assert main.simulation_target_retained.all()


def test_calibration_preserves_equalities_without_redividing_zero_prices():
    raw = raw_sample()
    raw["coefficient"] = 0.
    raw["required_coefficient"] = 0.
    raw["actual_need_eur_ha"] = 0.
    rows = calibrate_policies(raw)
    assert rows.held.all()
    assert (rows.paid_actual_eur_ha == 0).all()
    assert (rows.expected_unit_cost == 0).all()


def test_future_observations_do_not_change_past_coefficients_or_selection():
    original = raw_sample()
    changed = original.copy()
    changed.loc[changed.year >= 2020, "required_coefficient"] = 1e6
    changed.loc[changed.year >= 2020, "actual_need_eur_ha"] = changed.actual_basis * 1e6
    first = calibrate_policies(original)
    second = calibrate_policies(changed)
    order = ["culture", "contract", "year", "dep", "model", "calibration"]
    columns = order + ["coefficient", "calibration_correction", "calibration_max_year"]
    pd.testing.assert_frame_equal(first[first.year <= 2020][columns].reset_index(drop=True),
                                  second[second.year <= 2020][columns].reset_index(drop=True))
    _, before = select_policies(first)
    _, after = select_policies(second)
    pd.testing.assert_frame_equal(before[before.year <= 2020].reset_index(drop=True),
                                  after[after.year <= 2020].reset_index(drop=True))
    assert (before.past_max_year < before.year).all()


def test_warmup_fallback_and_strictly_past_calibration_are_exported():
    rows = calibrate_policies(raw_sample())
    warm = rows[(rows.year == 2016) & (rows.calibration != "raw")]
    assert warm.calibration_fallback.all()
    assert (warm.calibration_n == 0).all()
    calibrated = rows[rows.calibration_n > 0]
    assert (calibrated.calibration_max_year < calibrated.year).all()
    assert (calibrated.calibration_n_years <= 3).all()
    assert (calibrated.calibration_n == 3 * calibrated.calibration_n_years).all()


def test_calibration_groups_do_not_mix_crops_or_models():
    first = raw_sample()
    second = first.assign(culture="haricot", coefficient=1e5,
                          required_coefficient=2e5, actual_need_eur_ha=lambda x: 2e5 * x.actual_basis)
    alone = calibrate_policies(first)
    together = calibrate_policies(pd.concat([first, second], ignore_index=True))
    pd.testing.assert_frame_equal(alone, together[together.culture == "lentille"].reset_index(drop=True))


def test_unit_cost_is_ratio_of_sums_not_mean_of_ratios():
    rows = calibrate_policies(raw_sample())
    pair = rows[(rows.year == 2019) & (rows.policy == "trend/raw")].iloc[:2].copy()
    pair["paid_actual_eur_ha"] = [100., 900.]
    pair["accepted_yield_actual"] = [1., 3.]
    pair["expected_paid_eur_ha"] = [100., 900.]
    pair["simulation_accepted_mean"] = [1., 3.]
    summary = summarize_group(pair)
    assert summary["realized_unit_cost"] == 250.
    assert summary["expected_unit_cost"] == 250.


def test_selector_cannot_use_signed_ablation_and_uses_identical_m0_rule():
    policies = calibrate_policies(raw_sample())
    # Make forbidden signed policies look artificially attractive in history.
    ablation = policies.calibration.str.startswith("signed")
    policies.loc[ablation, "held"] = True
    policies.loc[ablation, "paid_actual_eur_ha"] = 0.
    selected, decisions = select_policies(policies)
    assert not selected.selected_policy.str.contains("signed").any()
    assert set(decisions.selector) == {"all_models", "m0_only"}
    assert decisions[decisions.selector == "m0_only"].selected_policy.str.startswith("trend/").all()
    assert (decisions.past_max_year < decisions.year).all()
    assert selected.simulation_target_retained.all()


def test_mismatched_model_cohorts_are_rejected():
    raw = raw_sample().iloc[1:]
    with pytest.raises(ValueError, match="same observed cohort"):
        validate_raw(raw)


def test_year_weighting_gives_each_year_equal_total_mass():
    values = np.array([1.] * 9 + [10.])
    weights = np.array([1 / 9] * 9 + [1.])
    assert weighted_empirical_quantile(values, .8) == 1.
    assert weighted_empirical_quantile(values, .8, weights) == 10.
    assert weighted_empirical_quantile([1., 2., 3.], 1., [1., 1., 1.]) == 3.


def test_paired_baselines_and_subgroups_retain_the_full_test_cohort():
    policies = calibrate_policies(raw_sample())
    selected, _ = select_policies(policies)
    rows = add_groups(pd.concat([policies[policies.year >= 2019], selected]))
    summaries = grouped_summaries(rows)
    assert set(summaries.group_type) == {"all", "year", "region", "old_cohort", "history", "past_volatility"}
    assert (summaries[summaries.group_type == "all"].n == 9).all()
    pairs = paired_comparisons(rows, bootstrap_samples=100)
    identity = pairs[(pairs.policy == "trend/raw") & (pairs.comparison == "raw_M0")].iloc[0]
    assert identity.delta_held == identity.delta_unit_cost == identity.delta_loss == 0.
    assert identity.rescued_n == identity.lost_n == 0
    assert identity.delta_held_year_bootstrap_low == identity.delta_held_year_bootstrap_high == 0.
    assert (pairs.n == 9).all()
    cells = subgroup_comparisons(summaries)
    assert len(cells) == 2 * len(summaries)
    identity_cells = cells[(cells.policy == "trend/raw") & (cells.comparison == "raw_M0")]
    assert (identity_cells.delta_held == 0).all()
    assert (identity_cells.delta_unit_cost == 0).all()


def test_year_weighted_calibration_is_available_and_stays_past_only():
    policies = calibrate_policies(raw_sample(), calibration_weighting="year")
    assert set(policies.calibration_weighting) == {"year"}
    calibrated = policies[policies.calibration_n > 0]
    assert (calibrated.calibration_max_year < calibrated.year).all()
    with pytest.raises(ValueError, match="weighting"):
        calibrate_policies(raw_sample(), calibration_weighting="bad")
