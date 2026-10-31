"""Economic calibration, temporal model selection and paired advanced-data audit.

The automatic policy is an evaluated algorithm, not the retrospectively best
row in the results. Each crop/contract/year chooses using only earlier held-out
predictions, under the same rule for the full grid, M0 and the previous QRF.
Only raw/cal80/cal90/cal95 are eligible; no signed downward correction is used.
All evaluated candidates see the same cases. Tables retain failing candidates.

Example::
    python pipeline/analyze_advanced.py --input experiments/advanced/predictions.csv.gz \
        --output experiments/advanced_policies
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_multilegumes import (KEYS, REQUIRED_COLUMNS, _markdown_table,
    _policy_economics, add_groups, grouped_summaries, summarize_group,
    validate_raw, weighted_empirical_quantile)


ROOT = Path(__file__).resolve().parents[1]
CALIBRATIONS = {"raw": None, "cal80": .8, "cal90": .9, "cal95": .95}
REFERENCE = "qrf_seasonal"
SELECTOR_SCOPES = {"all_models": None, "m0_only": "trend",
                   "m0_extended": "trend*", "qrf_reference": REFERENCE}
OPTIONAL_COLUMNS = ["region", "old_cohort", "history_n", "history_cv",
                    "simulated_protection", "yield_pinball_raw", "actual_rel",
                    "q10_rel", "q50_rel", "q90_rel"]


def validate_advanced(raw):
    validate_raw(raw)
    for (culture, contract), group in raw.groupby(["culture", "contract"]):
        if REFERENCE not in set(group.model):
            raise ValueError(f"Previous QRF reference {REFERENCE} missing for {culture}/{contract}")
    numeric = list(REQUIRED_COLUMNS - set(KEYS) - {"model"})
    if not np.isfinite(raw[numeric].to_numpy(dtype=float)).all():
        raise ValueError("Nonfinite raw economic values")
    if (raw.coefficient < 0).any() or (raw.accepted_yield_actual <= 0).any():
        raise ValueError("Nonnegative coefficients and positive accepted yields are required")
    return raw


def calibrate_compact(raw, window=3, weighting="pooled"):
    """Same additive past calibration as the prior audit, without signed copies."""
    validate_advanced(raw)
    if window < 1 or weighting not in ("pooled", "year"):
        raise ValueError("Invalid calibration window or weighting")
    keep = list(dict.fromkeys(KEYS + ["model"] + sorted(REQUIRED_COLUMNS - set(KEYS) - {"model"})
                             + [c for c in OPTIONAL_COLUMNS if c in raw]))
    raw = raw[keep].copy()
    output = []
    for _, group in raw.groupby(["culture", "contract", "model"], sort=True):
        group = group.sort_values(["year", "dep"])
        for year, current in group.groupby("year", sort=True):
            past = group[(group.year < year) & (group.year >= year - window)]
            errors = (past.required_coefficient - past.coefficient).to_numpy()
            weights = (1 / past.groupby("year").year.transform("size").to_numpy()
                       if weighting == "year" else None)
            for label, quantile in CALIBRATIONS.items():
                estimated = (weighted_empirical_quantile(errors, quantile, weights)
                             if quantile is not None and len(past) else 0.)
                correction = max(0., estimated)
                rows = _policy_economics(current, current.coefficient.to_numpy() + correction)
                rows["raw_coefficient"] = current.coefficient.to_numpy()
                rows["calibration"] = label
                rows["policy"] = rows.model + "/" + label
                rows["calibration_correction"] = correction
                rows["calibration_estimated_correction"] = estimated
                rows["calibration_n"] = len(past) if quantile is not None else 0
                rows["calibration_max_year"] = int(past.year.max()) if quantile is not None and len(past) else np.nan
                rows["calibration_fallback"] = quantile is not None and not len(past)
                rows["simulation_target_retained"] = True
                if "simulated_protection" in rows and correction:
                    rows["simulated_protection"] = np.nan
                output.append(rows)
    return pd.concat(output, ignore_index=True).sort_values(KEYS + ["policy"]).reset_index(drop=True)


def select_temporal(policies, first_test_year=2019, window=3, target=.8):
    """Equal-procedure selectors, with complete past candidate metrics."""
    if window < 1 or not 0 < target <= 1:
        raise ValueError("Invalid selection window or target")
    if not set(policies.calibration).issubset(CALIBRATIONS):
        raise ValueError("Only nonnegative product calibrations can enter selection")
    selected, decisions, search = [], [], []
    for (culture, contract), group in policies.groupby(["culture", "contract"], sort=True):
        for year in sorted(group.loc[group.year >= first_test_year, "year"].unique()):
            past = group[(group.year < year) & (group.year >= year - window)]
            current = group[group.year == year]
            metrics, expected_keys = [], None
            for policy, history in past.groupby("policy", sort=True):
                keys = set(map(tuple, history[["year", "dep"]].to_numpy()))
                if expected_keys is not None and keys != expected_keys:
                    raise ValueError("Selection candidates have different past cohorts")
                expected_keys = keys
                metrics.append({"policy": policy, "model": history.model.iloc[0],
                                **summarize_group(history)})
            if not metrics:
                raise ValueError(f"No past predictions for selection at {year}")
            table = pd.DataFrame(metrics)
            current_keys = set(map(tuple, current.loc[current.model == "trend", ["year", "dep"]].drop_duplicates().to_numpy()))
            for selector, model in SELECTOR_SCOPES.items():
                if model is None:
                    scope = table
                elif model == "trend*":
                    scope = table[(table.model == "trend") | table.model.str.startswith("trend_")]
                else:
                    scope = table[table.model == model]
                if scope.empty:
                    raise ValueError(f"Missing selector reference {model}")
                qualified = scope[scope.held >= target]
                if len(qualified):
                    winner = qualified.sort_values(["realized_unit_cost", "shortfall_eur_ha", "policy"]).iloc[0]
                    reason = "cheapest_with_past_target"
                else:
                    winner = scope.sort_values(["held", "realized_unit_cost", "policy"],
                                                ascending=[False, True, True]).iloc[0]
                    reason = "best_past_protection_target_unmet"
                log = {"culture": culture, "contract": contract, "year": int(year),
                       "selector": selector, "selected_policy": winner.policy,
                       "selected_model": winner.model, "reason": reason,
                       "past_min_year": int(past.year.min()), "past_max_year": int(past.year.max()),
                       "past_n": int(winner.n), "past_n_years": int(winner.n_years),
                       "past_held": float(winner.held), "past_unit_cost": float(winner.realized_unit_cost),
                       "n_candidates": len(scope), "n_qualified": len(qualified)}
                decisions.append(log)
                rows = current[current.policy == winner.policy].copy()
                if set(map(tuple, rows[["year", "dep"]].to_numpy())) != current_keys:
                    raise ValueError("Selected policy lost current comparison cases")
                rows["selected_policy"] = winner.policy
                rows["policy"] = f"selector/{selector}"
                rows["selector_past_max_year"] = log["past_max_year"]
                selected.append(rows)
                audit = scope.copy()
                audit.insert(0, "decision_year", int(year))
                audit.insert(0, "contract", contract)
                audit.insert(0, "culture", culture)
                audit["selector"] = selector
                audit["qualified"] = audit.held >= target
                audit["selected"] = audit.policy == winner.policy
                audit["past_max_year"] = log["past_max_year"]
                search.append(audit)
    if not selected:
        raise ValueError("No evaluation years available")
    return pd.concat(selected, ignore_index=True), pd.DataFrame(decisions), pd.concat(search, ignore_index=True)


def _summarize_many(rows, keys):
    """Vectorized equivalent of summarize_group for thousands of subgroup cells."""
    rows = rows.assign(zero_price=rows.coefficient == 0,
                       negative_required=rows.required_coefficient < 0)
    group = rows.groupby(keys, sort=True, observed=True, dropna=False)
    summary = group.agg(n=("dep", "size"), n_years=("year", "nunique"),
        n_departments=("dep", "nunique"), n_held=("held", "sum"), held=("held", "mean"),
        paid_eur_ha_mean=("paid_actual_eur_ha", "mean"), accepted_yield_mean=("accepted_yield_actual", "mean"),
        shortfall_eur_ha=("shortfall_eur_ha", "mean"), contract_loss_eur_ha=("contract_loss_eur_ha", "mean"),
        zero_price_n=("zero_price", "sum"), negative_required_n=("negative_required", "sum"),
        coefficient_mean=("coefficient", "mean"), paid_sum=("paid_actual_eur_ha", "sum"),
        tonnes_sum=("accepted_yield_actual", "sum"), expected_paid_sum=("expected_paid_eur_ha", "sum"),
        expected_tonnes_sum=("simulation_accepted_mean", "sum"))
    annual_keys = list(dict.fromkeys(keys + ["year"]))
    annual = rows.groupby(annual_keys, sort=True, observed=True, dropna=False).agg(
        annual_held=("held", "mean"), annual_paid=("paid_actual_eur_ha", "sum"),
        annual_tonnes=("accepted_yield_actual", "sum")).reset_index()
    annual["annual_cost"] = annual.annual_paid / annual.annual_tonnes
    annual["at_target"] = annual.annual_held >= .8
    annual_summary = annual.groupby(keys, sort=True, observed=True, dropna=False).agg(
        held_year_mean=("annual_held", "mean"), held_worst_year=("annual_held", "min"),
        years_at_target=("at_target", "sum"), realized_unit_cost_year_mean=("annual_cost", "mean"))
    summary = summary.join(annual_summary)
    fail = rows[~rows.held.astype(bool)].groupby(keys, sort=True, observed=True, dropna=False).shortfall_eur_ha
    summary = summary.join(fail.mean().rename("shortfall_failure_mean"))
    summary = summary.join(fail.quantile(.9).rename("shortfall_failure_q90"))
    summary[["shortfall_failure_mean", "shortfall_failure_q90"]] = summary[
        ["shortfall_failure_mean", "shortfall_failure_q90"]].fillna(0.)
    summary["realized_unit_cost"] = summary.paid_sum / summary.tonnes_sum.replace(0, np.nan)
    summary["expected_unit_cost"] = summary.expected_paid_sum / summary.expected_tonnes_sum.replace(0, np.nan)
    return summary.drop(columns=["paid_sum", "tonnes_sum", "expected_paid_sum", "expected_tonnes_sum"]).reset_index()


def grouped_period_summaries(evaluated, first_test_year=2019, sensitivity_year=2023):
    """Full groups for the main period and the static-map-vintage sensitivity."""
    rows = add_groups(evaluated)
    rows["idf_group"] = np.where(rows.dep.astype(str).isin(["75", "77", "78", "91", "92", "93", "94", "95"]),
                                 "Île-de-France", "Hors Île-de-France")
    blocks = []
    for label, first in (("full", first_test_year), (f"since_{sensitivity_year}", sensitivity_year)):
        current = rows[rows.year >= first]
        if current.empty:
            continue
        parts = []
        for kind, column in (("all", None), ("year", "year"), ("region", "region"),
                             ("department", "dep"),
                             ("old_cohort", "old_cohort"), ("history", "history_group"),
                             ("past_volatility", "volatility_group"), ("idf", "idf_group")):
            if column is not None and column not in current:
                continue
            keys = ["culture", "contract", "policy"] + ([column] if column else [])
            part = _summarize_many(current, keys)
            part["group_type"] = kind
            part["group"] = part[column].astype(str) if column else "all"
            if column:
                part = part.drop(columns=[column])
            parts.append(part)
        summary = pd.concat(parts, ignore_index=True)
        summary.insert(0, "period", label)
        summary["evaluation_min_year"] = int(current.year.min())
        summary["evaluation_max_year"] = int(current.year.max())
        blocks.append(summary)
    return pd.concat(blocks, ignore_index=True)


def _paired_record(candidate, baseline, sample=None):
    """Join every case; the same bootstrap year draws are reused for each arm."""
    cols = KEYS + ["held", "paid_actual_eur_ha", "accepted_yield_actual", "shortfall_eur_ha", "contract_loss_eur_ha"]
    merged = candidate[cols].merge(baseline[cols], on=KEYS, suffixes=("_candidate", "_baseline"), validate="one_to_one")
    if len(merged) != len(candidate) or len(merged) != len(baseline):
        raise ValueError("Paired comparison requires identical cases")
    if not np.allclose(merged.accepted_yield_actual_candidate, merged.accepted_yield_actual_baseline, rtol=0, atol=0):
        raise ValueError("Paired actual tonnes differ")
    a, b = summarize_group(candidate), summarize_group(baseline)
    record = {"n": len(merged), "n_years": int(merged.year.nunique()),
              "held_candidate": a["held"], "held_baseline": b["held"],
              "unit_cost_candidate": a["realized_unit_cost"], "unit_cost_baseline": b["realized_unit_cost"],
              "delta_held": a["held"] - b["held"],
              "delta_unit_cost": a["realized_unit_cost"] - b["realized_unit_cost"],
              "relative_delta_unit_cost": a["realized_unit_cost"] / b["realized_unit_cost"] - 1 if b["realized_unit_cost"] else np.nan,
              "delta_shortfall": a["shortfall_eur_ha"] - b["shortfall_eur_ha"],
              "delta_loss": a["contract_loss_eur_ha"] - b["contract_loss_eur_ha"],
              "rescued_n": int((merged.held_candidate.astype(bool) & ~merged.held_baseline.astype(bool)).sum()),
              "lost_n": int((~merged.held_candidate.astype(bool) & merged.held_baseline.astype(bool)).sum())}
    annual = merged.assign(
        held_delta=merged.held_candidate.astype(float) - merged.held_baseline.astype(float),
        paid_delta=merged.paid_actual_eur_ha_candidate - merged.paid_actual_eur_ha_baseline,
        loss_delta=merged.contract_loss_eur_ha_candidate - merged.contract_loss_eur_ha_baseline,
    ).groupby("year", sort=True).agg(n=("dep", "size"), held_delta=("held_delta", "sum"),
        paid_delta=("paid_delta", "sum"), tonnes=("accepted_yield_actual_candidate", "sum"),
        loss_delta=("loss_delta", "sum"))
    if sample is not None and len(sample) and len(annual) > 1:
        if sample.shape[1] != len(annual):
            raise ValueError("Bootstrap years do not match compared years")
        totals = annual.to_numpy()[sample].sum(axis=1)
        for name, values in (("held", totals[:, 1] / totals[:, 0]),
                             ("unit_cost", totals[:, 2] / totals[:, 3]),
                             ("loss", totals[:, 4] / totals[:, 0])):
            record[f"delta_{name}_year_bootstrap_low"] = float(np.quantile(values, .025))
            record[f"delta_{name}_year_bootstrap_high"] = float(np.quantile(values, .975))
    return record


def paired_baselines(evaluated, first_test_year=2019, sensitivity_year=2023, bootstrap_samples=2000, seed=42):
    rng = np.random.default_rng(seed)
    records = []
    for period, first in (("full", first_test_year), (f"since_{sensitivity_year}", sensitivity_year)):
        for (culture, contract), group in evaluated[evaluated.year >= first].groupby(["culture", "contract"], sort=True):
            policies = dict(tuple(group.groupby("policy", sort=True)))
            n_years = int(group.year.nunique())
            sample = rng.integers(0, n_years, size=(bootstrap_samples, n_years)) if bootstrap_samples else None
            for policy, candidate in policies.items():
                if policy.startswith("selector/"):
                    references = (("same_selector_M0", "selector/m0_only"),
                                  ("same_selector_M0_extended", "selector/m0_extended"),
                                  ("same_selector_previous_QRF", "selector/qrf_reference"))
                else:
                    calibration = policy.rsplit("/", 1)[1]
                    references = (("same_calibration_M0", "trend/" + calibration),
                                  ("same_calibration_previous_QRF", REFERENCE + "/" + calibration))
                for comparison, baseline in references:
                    if baseline not in policies:
                        raise ValueError(f"Missing paired reference {baseline}")
                    records.append({"period": period, "culture": culture, "contract": contract,
                        "policy": policy, "comparison": comparison, "baseline": baseline,
                        **_paired_record(candidate, policies[baseline], sample)})
    return pd.DataFrame(records)


def paired_subgroups(summary):
    """Every group against equally calibrated/selected M0 and previous QRF."""
    keys = ["period", "culture", "contract", "group_type", "group"]
    metrics = ["n", "n_years", "held", "realized_unit_cost", "shortfall_eur_ha"]
    blocks = []
    for name, fixed, selected in (("M0", "trend", "selector/m0_only"),
                                  ("previous_QRF", REFERENCE, "selector/qrf_reference")):
        candidate = summary[keys + ["policy"] + metrics].copy()
        candidate["baseline"] = candidate.policy.map(lambda p: selected if p.startswith("selector/") else fixed + "/" + p.rsplit("/", 1)[1])
        paired = candidate.merge(summary[keys + ["policy"] + metrics],
            left_on=keys + ["baseline"], right_on=keys + ["policy"], suffixes=("", "_baseline"), validate="many_to_one")
        if len(paired) != len(candidate) or not (paired.n == paired.n_baseline).all():
            raise ValueError("Subgroup comparisons lost common cases")
        paired["comparison"] = name
        for target, metric in (("held", "held"), ("unit_cost", "realized_unit_cost"), ("shortfall", "shortfall_eur_ha")):
            paired[f"delta_{target}"] = paired[metric] - paired[f"{metric}_baseline"]
        paired["target_met"] = paired.held >= .8
        paired["target_and_cheaper"] = paired.target_met & (paired.delta_unit_cost < 0)
        blocks.append(paired.drop(columns=["policy_baseline", "n_baseline"]))
    return pd.concat(blocks, ignore_index=True)


DEFAULT_PARENTS = {
    "qrf_combined_sparse": "qrf_seasonal", "qrf_nasa_sparse": "qrf_combined_sparse",
    "qrf_sim_sparse": "qrf_nasa_sparse", "qrf_soil_sparse": "qrf_sim_sparse",
    "qrf_combined_dense": "qrf_combined_sparse", "qrf_nasa_dense": "qrf_nasa_sparse",
    "qrf_sim_dense": "qrf_sim_sparse", "qrf_soil_dense": "qrf_soil_sparse",
    "qrf_soil_absolute": "qrf_soil_dense", "qrf_soil_shrinkage": "qrf_soil_dense",
    "qrf_leaf3_depth3": "qrf_soil_dense", "qrf_leaf3_depth8": "qrf_soil_dense",
    "qrf_leaf5_depth8": "qrf_soil_dense", "qrf_leaf10_depth3": "qrf_soil_dense",
    "qrf_leaf10_depth8": "qrf_soil_dense", "qrf_features05": "qrf_soil_dense",
    "lgb_dense": "lgb_sparse", "lgb_leaf15": "lgb_dense",
    "cat_dense": "cat_sparse", "cat_depth6": "cat_dense",
    "qrf_lgb_mixture": "qrf_soil_dense", "qrf_joint_gaussian": "qrf_soil_dense",
    "qrf_joint_empirical": "qrf_soil_dense", "qrf_wheat_dense": "qrf_soil_dense",
    "qrf_agri_sparse": "qrf_soil_sparse", "qrf_agri_dense": "qrf_soil_dense",
}


def ablation_table(evaluated, catalog=None, first_test_year=2019):
    parents = dict(DEFAULT_PARENTS)
    for name, spec in (catalog or {}).items():
        if spec.get("ablation_parent"):
            parents[name] = spec["ablation_parent"]
    records = []
    for (culture, contract), group in evaluated[evaluated.year >= first_test_year].groupby(["culture", "contract"], sort=True):
        policies = dict(tuple(group.groupby("policy", sort=True)))
        for child, parent in sorted(parents.items()):
            for calibration in ("raw", "cal95"):
                name, before = f"{child}/{calibration}", f"{parent}/{calibration}"
                if name not in policies or before not in policies:
                    continue
                records.append({"culture": culture, "contract": contract, "calibration": calibration,
                                "candidate": child, "parent": parent,
                                **_paired_record(policies[name], policies[before])})
    return pd.DataFrame(records)


def yield_diagnostics(raw, first_test_year=2019):
    """Observed-season weather diagnostic; never an input to contract selection."""
    columns = {"yield_pinball_raw", "actual_rel", "q10_rel", "q50_rel", "q90_rel"}
    if not columns.issubset(raw.columns):
        return pd.DataFrame()
    frame = raw[raw.year >= first_test_year].drop_duplicates(["culture", "model", "year", "dep"]).copy()
    frame["relative_median_abs_error"] = abs(frame.actual_rel - frame.q50_rel)
    frame["raw_interval_covered"] = (frame.actual_rel >= frame.q10_rel) & (frame.actual_rel <= frame.q90_rel)
    aggregations = dict(
        n=("dep", "size"), pinball_relative=("yield_pinball_raw", "mean"),
        median_mae_relative=("relative_median_abs_error", "mean"),
        q10_q90_observed_weather_coverage=("raw_interval_covered", "mean"))
    if "yield_pinball_t_ha" in frame:
        aggregations["pinball_t_ha"] = ("yield_pinball_t_ha", "mean")
    if {"actual_crop_yield_raw", "q50_t_ha"}.issubset(frame.columns):
        frame["physical_median_abs_error"] = abs(frame.actual_crop_yield_raw - frame.q50_t_ha)
        aggregations["median_mae_t_ha"] = ("physical_median_abs_error", "mean")
    return frame.groupby(["culture", "model"], sort=True).agg(**aggregations).reset_index()


def read_catalog(path):
    if path is None or not Path(path).exists():
        return {}, {}
    manifest = json.loads(Path(path).read_text())
    specs = manifest.get("spec", {}).get("candidates", manifest.get("candidates", {}))
    if isinstance(specs, list):
        specs = {str(item.get("name", item.get("model"))): item for item in specs}
    return specs, manifest


def write_report(summary, pairs, decisions, output, manifest, catalog):
    overall = summary[(summary.period == "full") & (summary.group_type == "all")]
    references = ["trend/cal95", REFERENCE + "/cal95", *["selector/" + scope for scope in SELECTOR_SCOPES]]
    focus = overall[overall.policy.isin(references)]
    lines = ["# Données, preprocessing et optimisation économique : audit avancé", "",
        "Le prix fixe minimal assurant une marge au moins égale au blé dans 80 % des scénarios reste l'objectif initial. L'évaluation porte sur les mêmes cas observés pour chaque candidat. Les comparaisons de contrats indexés ou par tranches restent séparées.", "",
        "## Ce qui est évalué", "",
        f"- {manifest['n_models']} configurations de modèles/variables/distributions, quatre calibrages admissibles, cible économique toujours **80 %**.",
        "- M0 `trend` et le QRF saisonnier antérieur sont conservés comme références. Chaque concurrent est apparié à chacune de ces références sous le même calibrage ; les sélecteurs sont comparés à des sélecteurs restreints à M0 ou à l'ancien QRF. Le sélecteur supplémentaire `m0_extended` autorise aussi les variantes M0 de distribution/dépendance, pour vérifier si les améliorations du simulateur profitent également à la baseline.",
        "- `raw/cal80/cal90/cal95` : coefficient brut ou correction additive positive estimée sur les trois années hors temps précédentes. Les nombres 90 et 95 désignent des quantiles de correction, pas une promesse de protection à 90 % ou 95 %.",
        "- Sélection automatique des variables, réglages, familles et calibrages : parmi les configurations disponibles, choisir sur les trois années antérieures le coût le plus bas atteignant 80 % ; à défaut retenir la meilleure protection passée. Une configuration commune est choisie pour une culture et une forme de contrat, sans utiliser les résultats de l'année à prédire.",
        "- Paiement €/t acceptée = somme des paiements / somme des rendements acceptés. Il exclut transport et tri ; chaque département–année représente ici un hectare, sans pondération par les surfaces nationales.",
        "- La distribution simulée, les données statiques, les interactions et les réglages de chaque configuration sont détaillés dans `candidate_catalog.json` et le manifeste du benchmark. Les gains d'une configuration modifiant plusieurs éléments ne sont pas attribués à un seul élément.",
        "- La météo de l'année test ne sert qu'au diagnostic de rendement après récolte. Le prix avant campagne rejoue les historiques antérieurs. Une carte de sol récente apporte une information structurelle rétrospective ; elle ne doit pas être présentée comme disponible à toutes les anciennes dates de décision.",
        f"- La fenêtre `since_{manifest['sensitivity_year']}` fournit une sensibilité à la date des cartes ; la source INRAE BDGSF/CLC2012 utilisée pour les sols a été publiée en 2022. Elle réutilise les décisions temporelles déjà produites et ne constitue pas une nouvelle période de sélection ni une preuve que toutes les versions des données étaient disponibles à leur date historique.",
        "- Les intervalles rééchantillonnent des années entières avec les mêmes tirages pour chaque candidat. Ils décrivent la sensibilité aux années observées, pas la probabilité de réussite future.", "",
        "## Algorithmes évalués et références", ""]
    for contract in sorted(overall.contract.unique()):
        lines.extend([f"### {contract}", "", _markdown_table(focus[focus.contract == contract].sort_values(["culture", "policy"]),
            ["culture", "policy", "n", "held", "realized_unit_cost", "shortfall_eur_ha"],
            ["Culture", "Politique", "Cas", "Marge ≥ blé", "Paiement €/t acceptée", "Déficit €/ha"]), ""])
    winners = []
    for (culture, contract), group in overall[~overall.policy.str.startswith("selector/")].groupby(["culture", "contract"]):
        qualified = group[group.held >= .8]
        if len(qualified):
            winner = qualified.sort_values(["realized_unit_cost", "policy"]).iloc[0].to_dict()
            winner["selection_status"] = "moins cher parmi candidats testés ≥80 %"
        else:
            winner = group.sort_values(["held", "realized_unit_cost", "policy"], ascending=[False, True, True]).iloc[0].to_dict()
            winner["selection_status"] = "aucun candidat à 80 % ; meilleure protection observée"
        winners.append(winner)
    winner_table = pd.DataFrame(winners)
    winner_table.to_csv(output / "retrospective_candidates.csv", index=False)
    lines.extend(["## Candidats retenus après comparaison : diagnostic rétrospectif", "",
        "Ce tableau choisit après lecture des résultats. Ses scores ne sont pas ceux du sélecteur automatique et ne constituent pas un test indépendant de ce choix.", "",
        _markdown_table(winner_table, ["culture", "contract", "policy", "n", "held", "realized_unit_cost", "selection_status"],
            ["Culture", "Contrat", "Candidat rétrospectif", "Cas", "Marge ≥ blé", "Paiement €/t", "Statut"]), "",
        "## Décomposition et sous-groupes", "",
        "`ablation.csv` publie les transitions de variables, distributions et paramètres en brut et avec cal95, avec les cas sauvés et perdus. Les colonnes `parent` et `candidate` identifient exactement les deux configurations ; le catalogue précise toute autre différence.",
        "`summary.csv.gz` et `subgroup_comparisons.csv.gz` incluent tous les groupes, favorables et défavorables : année, région, département, Île-de-France, historique, volatilité passée, ancienne/nouvelle cohorte. Les effectifs sont conservés. Aucun sous-groupe n'est créé après sélection d'un résultat favorable.", "",
        "## Reproduction et traçabilité", "",
        f"- `global_summary.csv` : tous les candidats et sélecteurs, périodes complète et depuis {manifest['sensitivity_year']}.",
        "- `paired_baselines.csv` : écarts appariés contre M0 et ancien QRF, calibrages identiques, intervalles par années.",
        "- `selection_decisions.csv` : décision retenue et dernières années utilisées ; `selection_candidates.csv.gz` : tous les candidats et leurs scores passés avant chaque choix.",
        "- `policy_decisions.csv.gz` : décisions compactes, à joindre aux prédictions brutes par culture/contrat/année/département/modèle pour retrouver les données économiques complètes.",
        "- `yield_diagnostics.csv` : diagnostic avec météo réalisée, séparé de l'objectif contractuel et non utilisé pour choisir les politiques. La perte quantile en t/ha, lorsqu'elle est fournie, sert à comparer les normalisations ; les pertes relatives ne sont pas directement comparables entre cibles normalisées différemment.",
        "- `candidate_catalog.json` : configurations exécutées ; `manifest.json` : entrées, empreintes et paramètres d'analyse.", ""])
    (output / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def run(args):
    args.output.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(args.input, dtype={"dep": str}, float_precision="round_trip")
    validate_advanced(raw)
    catalog_path = args.benchmark_manifest or args.input.parent / "manifest.json"
    catalog, benchmark_manifest = read_catalog(catalog_path)
    policies = calibrate_compact(raw, args.calibration_window, args.calibration_weighting)
    selected, decisions, search = select_temporal(policies, args.first_test_year, args.selection_window)
    evaluated = pd.concat([policies[policies.year >= args.first_test_year], selected], ignore_index=True)
    summary = grouped_period_summaries(evaluated, args.first_test_year, args.sensitivity_year)
    pairs = paired_baselines(evaluated, args.first_test_year, args.sensitivity_year, args.bootstrap_samples, args.seed)
    summary.to_csv(args.output / "summary.csv.gz", index=False, compression="gzip")
    summary[summary.group_type == "all"].to_csv(args.output / "global_summary.csv", index=False)
    pairs.to_csv(args.output / "paired_baselines.csv", index=False)
    paired_subgroups(summary).to_csv(args.output / "subgroup_comparisons.csv.gz", index=False, compression="gzip")
    ablation_table(evaluated, catalog, args.first_test_year).to_csv(args.output / "ablation.csv", index=False)
    decisions.to_csv(args.output / "selection_decisions.csv", index=False)
    search.to_csv(args.output / "selection_candidates.csv.gz", index=False, compression="gzip")
    compact = KEYS + ["policy", "model", "calibration", "coefficient", "raw_coefficient",
        "paid_actual_eur_ha", "held", "shortfall_eur_ha", "expected_paid_eur_ha", "contract_loss_eur_ha",
        "calibration_correction", "calibration_n", "calibration_max_year", "calibration_fallback",
        "selected_policy", "selector_past_max_year"]
    evaluated[[c for c in compact if c in evaluated]].to_csv(args.output / "policy_decisions.csv.gz", index=False, compression="gzip")
    yield_diagnostics(raw, args.first_test_year).to_csv(args.output / "yield_diagnostics.csv", index=False)
    (args.output / "candidate_catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")
    paths = [Path(__file__), ROOT / "pipeline/analyze_multilegumes.py", ROOT / "pipeline/contract_economics.py"]
    manifest = {"input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "input": str(args.input), "benchmark_signature": benchmark_manifest.get("signature"),
        "analysis_sources_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "first_test_year": args.first_test_year, "sensitivity_year": args.sensitivity_year,
        "calibration_window": args.calibration_window, "calibration_weighting": args.calibration_weighting,
        "selection_window": args.selection_window, "calibrations": CALIBRATIONS,
        "target": .8, "selection_scopes": SELECTOR_SCOPES,
        "selection_objective": "past protection >=80%, then sum(paid)/sum(accepted tonnes)",
        "n_models": int(raw.model.nunique()), "raw_rows": len(raw), "evaluation_rows": len(evaluated),
        "bootstrap_samples": args.bootstrap_samples, "bootstrap_unit": "year", "seed": args.seed,
        "vintage_note": f"Static maps may postdate early cases; since_{args.sensitivity_year} is a sensitivity, not a reconstructed data-vintage backtest"}
    write_report(summary, pairs, decisions, args.output, manifest, catalog)
    manifest["output_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(args.output.iterdir()) if p.is_file() and p.name != "manifest.json"}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"status": "complete", "models": manifest["n_models"], "evaluated_rows": len(evaluated),
                      "summaries": len(summary), "paired_comparisons": len(pairs), "output": str(args.output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/advanced_policies")
    parser.add_argument("--benchmark-manifest", type=Path)
    parser.add_argument("--first-test-year", type=int, default=2019)
    parser.add_argument("--sensitivity-year", type=int, default=2023)
    parser.add_argument("--calibration-window", type=int, default=3)
    parser.add_argument("--calibration-weighting", choices=("pooled", "year"), default="pooled")
    parser.add_argument("--selection-window", type=int, default=3)
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    run(parser.parse_args())
