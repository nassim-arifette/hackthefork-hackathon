"""Economic selection must be past-only, paired and aligned with the objective."""
from argparse import Namespace
import json

import numpy as np
import pandas as pd
import pytest

from analyze_advanced import (REFERENCE, _paired_record, ablation_table,
    calibrate_compact, grouped_period_summaries, paired_baselines,
    paired_subgroups, run, select_temporal, validate_advanced, yield_diagnostics)
from analyze_multilegumes import add_groups, calibrate_policies, grouped_summaries


def sample():
    records = []
    for year in range(2016, 2025):
        for dep, tonnes, need in (("01", 1., -20.), ("77", 2., 85.), ("03", 3., 130.)):
            for model, coefficient in (("trend", 100.), (REFERENCE, 95.), ("qrf_nasa_sparse", 90.)):
                records.append({"culture": "lentille", "contract": "fixed", "year": year,
                    "dep": dep, "region": "IDF" if dep == "77" else "Autre", "model": model,
                    "coefficient": coefficient, "required_coefficient": need,
                    "actual_basis": tonnes, "actual_need_eur_ha": tonnes * need,
                    "accepted_yield_actual": tonnes, "simulation_basis_mean": tonnes,
                    "simulation_accepted_mean": tonnes, "old_cohort": dep != "03",
                    "history_n": year - 2010, "history_cv": .1 if dep == "01" else .5,
                    "simulated_protection": .8, "actual_rel": 1., "q10_rel": .6,
                    "q50_rel": .9, "q90_rel": 1.3, "yield_pinball_raw": .1})
    return pd.DataFrame(records)


def evaluated(raw=None):
    policies = calibrate_compact(sample() if raw is None else raw)
    selected, decisions, search = select_temporal(policies)
    return pd.concat([policies[policies.year >= 2019], selected], ignore_index=True), decisions, search


def test_compact_calibration_matches_previous_procedure_exactly():
    raw = sample()
    old = calibrate_policies(raw)
    old = old[old.product_eligible].reset_index(drop=True)
    new = calibrate_compact(raw)
    columns = ["culture", "contract", "year", "dep", "policy", "coefficient", "held",
               "paid_actual_eur_ha", "calibration_correction", "calibration_max_year"]
    pd.testing.assert_frame_equal(new[columns], old[columns])
    assert (new.coefficient >= new.raw_coefficient).all()
    assert (new.loc[new.calibration_n > 0, "calibration_max_year"] <
            new.loc[new.calibration_n > 0, "year"]).all()


def test_future_outcomes_never_change_earlier_choices_or_calibration():
    before = sample()
    after = before.copy()
    after.loc[after.year >= 2022, "required_coefficient"] = 1e6
    after.loc[after.year >= 2022, "actual_need_eur_ha"] = 1e6 * after.loc[after.year >= 2022, "actual_basis"]
    a, b = calibrate_compact(before), calibrate_compact(after)
    columns = ["year", "dep", "model", "policy", "coefficient", "calibration_correction"]
    pd.testing.assert_frame_equal(a[a.year <= 2022][columns].reset_index(drop=True),
                                  b[b.year <= 2022][columns].reset_index(drop=True))
    _, da, sa = select_temporal(a)
    _, db, sb = select_temporal(b)
    pd.testing.assert_frame_equal(da[da.year <= 2022].reset_index(drop=True), db[db.year <= 2022].reset_index(drop=True))
    pd.testing.assert_frame_equal(sa[sa.decision_year <= 2022].reset_index(drop=True), sb[sb.decision_year <= 2022].reset_index(drop=True))
    assert (da.past_max_year < da.year).all()
    assert (sa.past_max_year < sa.decision_year).all()


def test_references_share_rule_and_forbidden_calibration_cannot_enter():
    policies = calibrate_compact(sample())
    rows, decisions, search = select_temporal(policies)
    assert set(decisions.selector) == {"all_models", "m0_only", "m0_extended", "qrf_reference"}
    assert decisions[decisions.selector == "m0_only"].selected_policy.str.startswith("trend/").all()
    assert decisions[decisions.selector == "qrf_reference"].selected_policy.str.startswith(REFERENCE + "/").all()
    assert (search.groupby(["culture", "contract", "decision_year", "selector"]).selected.sum() == 1).all()
    assert set(rows.groupby(["policy", "year"]).size()) == {3}
    bad = policies.copy()
    bad.loc[0, "calibration"] = "signed95"
    with pytest.raises(ValueError, match="nonnegative"):
        select_temporal(bad)


def test_common_cohort_and_previous_qrf_are_required():
    raw = sample()
    with pytest.raises(ValueError, match="Previous QRF"):
        validate_advanced(raw[raw.model != REFERENCE])
    with pytest.raises(ValueError, match="same observed cohort"):
        validate_advanced(raw.iloc[1:])
    policies = calibrate_compact(raw)
    bad = policies[~((policies.model == REFERENCE) & (policies.year == 2018) & (policies.dep == "77"))]
    with pytest.raises(ValueError, match="different past cohorts"):
        select_temporal(bad)


def test_extended_m0_scope_gives_simulator_upgrades_to_the_baseline():
    raw = sample()
    upgraded = raw[raw.model == "trend"].assign(model="trend_dense", coefficient=90.)
    raw = pd.concat([raw, upgraded], ignore_index=True)
    rows, decisions, _ = evaluated(raw)
    assert (decisions[decisions.selector == "m0_only"].n_candidates == 4).all()
    assert (decisions[decisions.selector == "m0_extended"].n_candidates == 8).all()
    comparisons = paired_baselines(rows, bootstrap_samples=10)
    assert "same_selector_M0_extended" in set(comparisons.comparison)
    assert not comparisons[comparisons.comparison == "same_selector_M0_extended"].empty


def test_physical_yield_loss_is_preserved_for_normalization_comparisons():
    raw = sample()
    raw["yield_pinball_t_ha"] = np.where(raw.model == "trend", .2, .3)
    diagnostic = yield_diagnostics(raw)
    assert diagnostic[diagnostic.model == "trend"].pinball_t_ha.iloc[0] == pytest.approx(.2)
    assert (diagnostic.n == 18).all()


def test_equality_and_negative_need_are_wins_at_zero_payment():
    raw = sample()
    raw["coefficient"] = 0.
    raw["required_coefficient"] = np.where(raw.dep == "01", -20., 0.)
    raw["actual_need_eur_ha"] = raw.required_coefficient * raw.actual_basis
    policies = calibrate_compact(raw)
    assert policies.held.all()
    assert (policies.paid_actual_eur_ha == 0).all()


def test_paired_bootstrap_and_subgroups_keep_exact_cases():
    rows, _, _ = evaluated()
    comparisons = paired_baselines(rows, bootstrap_samples=100)
    assert set(comparisons.period) == {"full", "since_2023"}
    identity = comparisons[(comparisons.policy == "trend/cal95") &
                           (comparisons.comparison == "same_calibration_M0")]
    assert (identity.delta_held == 0).all()
    assert (identity.delta_unit_cost == 0).all()
    assert (identity.delta_unit_cost_year_bootstrap_low == 0).all()
    summary = grouped_period_summaries(rows)
    assert "idf" in set(summary.group_type)
    departments = summary[(summary.period == "full") & (summary.group_type == "department")]
    assert set(departments.group) == {"01", "77", "03"}
    assert (departments.n == 6).all()
    assert (departments.n_departments == 1).all()
    local = departments[(departments.group == "77") & (departments.policy == "trend/raw")].iloc[0]
    reference_rows = rows[(rows.dep == "77") & (rows.policy == "trend/raw")]
    assert local.realized_unit_cost == pytest.approx(
        reference_rows.paid_actual_eur_ha.sum() / reference_rows.accepted_yield_actual.sum())
    idf = summary[(summary.period == "full") & (summary.group_type == "idf") & (summary.group == "Île-de-France")]
    assert (idf.n == 6).all()
    later = summary[(summary.period == "since_2023") & (summary.group_type == "all")]
    assert (later.n == 6).all()
    subgroup = paired_subgroups(summary)
    assert len(subgroup) == 2 * len(summary)
    baseline = rows[rows.policy == "trend/raw"]
    with pytest.raises(ValueError, match="identical cases"):
        _paired_record(baseline.iloc[1:], baseline)


def test_vectorized_subgroups_match_the_existing_metric_definition():
    rows, _, _ = evaluated()
    old = grouped_summaries(add_groups(rows))
    new = grouped_period_summaries(rows)
    new = new[(new.period == "full") & ~new.group_type.isin(["idf", "department"])]
    keys = ["culture", "contract", "policy", "group_type", "group"]
    new = new.sort_values(keys).reset_index(drop=True)
    old = old.sort_values(keys).reset_index(drop=True)
    pd.testing.assert_frame_equal(new[old.columns], old, check_dtype=False, rtol=1e-12, atol=1e-12)


def test_ablation_metadata_names_parent_and_counts_rescued_cases():
    rows, _, _ = evaluated()
    table = ablation_table(rows, {"qrf_nasa_sparse": {"ablation_parent": REFERENCE}})
    assert len(table) == 2
    assert set(table.calibration) == {"raw", "cal95"}
    assert set(table.parent) == {REFERENCE}
    assert (table.n == 18).all()


def test_end_to_end_writes_compact_reproducible_outputs(tmp_path):
    raw = sample()
    input_path = tmp_path / "predictions.csv.gz"
    raw.to_csv(input_path, index=False, compression="gzip")
    manifest_path = tmp_path / "benchmark.json"
    manifest_path.write_text(json.dumps({"signature": "test-input", "spec": {"candidates": {
        "qrf_nasa_sparse": {"ablation_parent": REFERENCE, "feature_group": "nasa"}}}}))
    output = tmp_path / "analysis"
    args = Namespace(input=input_path, output=output, benchmark_manifest=manifest_path,
                     first_test_year=2019, sensitivity_year=2023, calibration_window=3,
                     calibration_weighting="pooled", selection_window=3, bootstrap_samples=50, seed=42)
    run(args)
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["n_models"] == 3
    assert manifest["benchmark_signature"] == "test-input"
    assert manifest["target"] == .8
    decisions = pd.read_csv(output / "policy_decisions.csv.gz")
    assert len(decisions) == 18 * 16
    assert not (output / "policy_predictions.csv.gz").exists()
    assert "actual_need_eur_ha" not in decisions.columns
    assert (output / "yield_diagnostics.csv").exists()
    assert "diagnostic rétrospectif" in (output / "REPORT.md").read_text()
