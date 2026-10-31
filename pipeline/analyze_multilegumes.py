"""Past-only decision calibration and paired audit of the multi-crop benchmark.

The product target stays 80%. ``cal90`` and ``cal95`` refer to quantiles of past
out-of-time coefficient errors, not to a different product promise. Corrections
are additive because required prices can be negative under the economic
scenario. Main policies never lower the raw coefficient, retaining its 80%
simulated protection. Separate ``signed`` ablations allow negative corrections;
they cannot be selected for the product policy.

The selector is evaluated as an algorithm: for each crop/contract/year it uses
only the previous three observed years, chooses the cheapest policy reaching
80%, or the best protection if none reaches it. The M0-only selector is evaluated
by exactly the same rule. No winner is picked retrospectively for the test years.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from contract_economics import evaluate


ROOT = Path(__file__).resolve().parents[1]
KEYS = ["culture", "contract", "year", "dep"]
CALIBRATIONS = {"raw": None, "cal80": .8, "cal90": .9, "cal95": .95,
                "signed80": .8, "signed90": .9, "signed95": .95}
REQUIRED_COLUMNS = set(KEYS + ["model", "coefficient", "required_coefficient",
    "actual_basis", "actual_need_eur_ha", "accepted_yield_actual",
    "simulation_basis_mean", "simulation_accepted_mean"])


def validate_raw(raw):
    missing = sorted(REQUIRED_COLUMNS - set(raw.columns))
    if missing:
        raise ValueError(f"Missing raw benchmark columns: {missing}")
    if raw.duplicated(KEYS + ["model"]).any():
        raise ValueError("Duplicate crop/contract/year/department/model observations")
    if raw[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("Missing values in required raw benchmark columns")
    for (_, _), group in raw.groupby(["culture", "contract"]):
        cohorts = [set(map(tuple, frame[["year", "dep"]].to_numpy()))
                   for _, frame in group.groupby("model")]
        if not cohorts or any(cohort != cohorts[0] for cohort in cohorts[1:]):
            raise ValueError("Model comparisons require the same observed cohort")
        if "trend" not in set(group.model):
            raise ValueError("Every crop/contract must include the true M0 trend baseline")
    actual_columns = ["actual_basis", "actual_need_eur_ha", "accepted_yield_actual", "required_coefficient"]
    if (raw.groupby(KEYS)[actual_columns].nunique(dropna=False) > 1).any().any():
        raise ValueError("Observed outcomes or economic assumptions differ between model candidates")
    return raw


def _policy_economics(rows, coefficients):
    """Reprice a fixed contract basis, preserving equality and negative needs."""
    rows = rows.copy()
    coefficients = np.asarray(coefficients, dtype=float)
    assessed = evaluate(coefficients, rows.actual_basis.to_numpy(),
                        rows.actual_need_eur_ha.to_numpy(), rows.accepted_yield_actual.to_numpy())
    rows["coefficient"] = coefficients
    rows["paid_actual_eur_ha"] = assessed["paid_eur_ha"]
    rows["held"] = assessed["held"]
    rows["shortfall_eur_ha"] = assessed["shortfall_eur_ha"]
    rows["effective_price_actual"] = assessed["effective_price_eur_t"]
    rows["expected_paid_eur_ha"] = coefficients * rows.simulation_basis_mean
    rows["expected_unit_cost"] = np.divide(
        rows.expected_paid_eur_ha, rows.simulation_accepted_mean,
        out=np.full(len(rows), np.nan), where=rows.simulation_accepted_mean.to_numpy() > 0)
    residual = rows.actual_need_eur_ha - rows.paid_actual_eur_ha
    rows["contract_loss_eur_ha"] = np.maximum(.8 * residual, -.2 * residual)
    return rows


def weighted_empirical_quantile(values, quantile, weights=None):
    """Leftmost support value reaching the requested empirical mass."""
    values = np.asarray(values, dtype=float)
    if not len(values) or not 0 < quantile <= 1:
        raise ValueError("A nonempty sample and quantile in (0, 1] are required")
    if weights is None:
        return float(np.quantile(values, quantile, method="inverted_cdf"))
    weights = np.asarray(weights, dtype=float)
    if weights.shape != values.shape or np.any(weights <= 0) or not np.isfinite(weights).all():
        raise ValueError("Quantile weights must be finite, positive and match the sample")
    order = np.argsort(values, kind="stable")
    cumulative = np.cumsum(weights[order])
    index = min(len(values) - 1, int(np.searchsorted(cumulative, quantile * cumulative[-1], side="left")))
    return float(values[order[index]])


def calibrate_policies(raw, calibration_window=3, calibration_weighting="pooled"):
    """Out-of-time additive calibration, independently by crop/model/contract.

    A first warm-up year with no prior residuals falls back to the raw policy.
    All candidates therefore retain the same cohort even during warm-up. Counts
    and last calibration year are exported, making this fallback auditable.
    """
    validate_raw(raw)
    if calibration_window < 1:
        raise ValueError("Calibration window must contain at least one year")
    if calibration_weighting not in ("pooled", "year"):
        raise ValueError("Calibration weighting must be pooled or year")
    output = []
    for (culture, contract, model), group in raw.groupby(["culture", "contract", "model"], sort=True):
        group = group.sort_values(["year", "dep"])
        for year, current in group.groupby("year", sort=True):
            past = group[(group.year < year) & (group.year >= year - calibration_window)]
            residual = (past.required_coefficient - past.coefficient).to_numpy()
            weights = (1 / past.groupby("year").year.transform("size").to_numpy()
                       if calibration_weighting == "year" else None)
            for label, quantile in CALIBRATIONS.items():
                correction = (weighted_empirical_quantile(residual, quantile, weights)
                              if quantile is not None and len(past) else 0.0)
                if not np.isfinite(correction):
                    raise ValueError(f"Nonfinite correction for {culture}/{contract}/{model}/{year}")
                applied = correction if label.startswith("signed") else max(0., correction)
                rows = _policy_economics(current, np.maximum(0, current.coefficient + applied))
                rows["raw_coefficient"] = current.coefficient.to_numpy()
                rows["calibration"] = label
                rows["policy"] = f"{model}/{label}"
                rows["calibration_quantile"] = np.nan if quantile is None else quantile
                rows["calibration_correction"] = applied
                rows["calibration_estimated_correction"] = correction
                rows["calibration_weighting"] = calibration_weighting
                rows["product_eligible"] = not label.startswith("signed")
                rows["calibration_n"] = len(past) if quantile is not None else 0
                rows["calibration_n_years"] = past.year.nunique() if quantile is not None else 0
                rows["calibration_max_year"] = int(past.year.max()) if quantile is not None and len(past) else np.nan
                rows["calibration_fallback"] = quantile is not None and not len(past)
                # Raw protection was computed for a different coefficient.
                if "simulated_protection" in rows and applied != 0:
                    rows["simulated_protection"] = np.nan
                rows["simulation_target_retained"] = applied >= 0
                output.append(rows)
    return pd.concat(output, ignore_index=True).sort_values(KEYS + ["policy"]).reset_index(drop=True)


def summarize_group(group):
    """All tonnes are accepted tonnes; €/t is a ratio of sums, never mean ratios."""
    paid, tonnes = group.paid_actual_eur_ha.sum(), group.accepted_yield_actual.sum()
    expected_paid = group.expected_paid_eur_ha.sum()
    expected_tonnes = group.simulation_accepted_mean.sum()
    annual = group.groupby("year")
    annual_held = annual.held.mean()
    annual_cost = annual.paid_actual_eur_ha.sum() / annual.accepted_yield_actual.sum()
    fail = group.loc[~group.held.astype(bool), "shortfall_eur_ha"]
    return {
        "n": len(group), "n_years": group.year.nunique(), "n_departments": group.dep.nunique(),
        "n_held": int(group.held.sum()), "held": float(group.held.mean()),
        "held_year_mean": float(annual_held.mean()), "held_worst_year": float(annual_held.min()),
        "years_at_target": int((annual_held >= .8).sum()),
        "paid_eur_ha_mean": float(group.paid_actual_eur_ha.mean()),
        "accepted_yield_mean": float(group.accepted_yield_actual.mean()),
        "realized_unit_cost": float(paid / tonnes) if tonnes > 0 else np.nan,
        "realized_unit_cost_year_mean": float(annual_cost.mean()),
        "expected_unit_cost": float(expected_paid / expected_tonnes) if expected_tonnes > 0 else np.nan,
        "shortfall_eur_ha": float(group.shortfall_eur_ha.mean()),
        "shortfall_failure_mean": float(fail.mean()) if len(fail) else 0.,
        "shortfall_failure_q90": float(fail.quantile(.9)) if len(fail) else 0.,
        "contract_loss_eur_ha": float(group.contract_loss_eur_ha.mean()),
        "zero_price_n": int((group.coefficient == 0).sum()),
        "negative_required_n": int((group.required_coefficient < 0).sum()),
        "coefficient_mean": float(group.coefficient.mean()),
    }


def select_policies(policies, first_test_year=2019, selection_window=3, target=.8):
    """Nested temporal selector; return selections and their past decision log."""
    selected, decisions = [], []
    policies = policies[policies.product_eligible]
    for (culture, contract), group in policies.groupby(["culture", "contract"], sort=True):
        for year in sorted(group.loc[group.year >= first_test_year, "year"].unique()):
            for selector, scope in (("all_models", group), ("m0_only", group[group.model == "trend"])):
                past = scope[(scope.year < year) & (scope.year >= year - selection_window)]
                current = scope[scope.year == year]
                candidates = []
                for policy, history in past.groupby("policy", sort=True):
                    metrics = summarize_group(history)
                    candidates.append({"policy": policy, **metrics})
                if not candidates:
                    raise ValueError(f"No past out-of-time predictions for selector at {year}")
                table = pd.DataFrame(candidates)
                # Common histories avoid selecting on easier/missing cases.
                histories = [set(map(tuple, frame[["year", "dep"]].to_numpy()))
                             for _, frame in past.groupby("policy")]
                if any(keys != histories[0] for keys in histories[1:]):
                    raise ValueError("Selector candidates require identical past cohorts")
                qualified = table[table.held >= target]
                if len(qualified):
                    winner = qualified.sort_values(["realized_unit_cost", "shortfall_eur_ha", "policy"]).iloc[0]
                    reason = "cheapest_with_past_target"
                else:
                    winner = table.sort_values(["held", "realized_unit_cost", "policy"],
                                                ascending=[False, True, True]).iloc[0]
                    reason = "best_past_protection_target_unmet"
                decision = {"culture": culture, "contract": contract, "year": int(year),
                    "selector": selector, "selected_policy": winner.policy, "reason": reason,
                    "past_min_year": int(past.year.min()), "past_max_year": int(past.year.max()),
                    "past_n": int(winner.n), "past_n_years": int(winner.n_years),
                    "past_held": float(winner.held), "past_unit_cost": float(winner.realized_unit_cost),
                    "n_candidates": len(table), "n_qualified": len(qualified)}
                decisions.append(decision)
                rows = current[current.policy == winner.policy].copy()
                if rows.empty:
                    raise ValueError("Selected policy is missing from the current cohort")
                rows["selected_policy"] = winner.policy
                rows["policy"] = f"selector/{selector}"
                rows["selector_past_max_year"] = decision["past_max_year"]
                selected.append(rows)
    return pd.concat(selected, ignore_index=True), pd.DataFrame(decisions)


def grouped_summaries(evaluated, include_groups=True):
    blocks = []
    specifications = [("all", None), ("year", "year"), ("region", "region"),
                      ("old_cohort", "old_cohort"), ("history", "history_group"),
                      ("past_volatility", "volatility_group")]
    if not include_groups:
        specifications = specifications[:1]
    for kind, extra in specifications:
        if extra is not None and extra not in evaluated:
            continue
        columns = ["culture", "contract", "policy"] + ([extra] if extra else [])
        for key, group in evaluated.groupby(columns, sort=True, dropna=False, observed=True):
            key = key if isinstance(key, tuple) else (key,)
            blocks.append({"culture": key[0], "contract": key[1], "policy": key[2],
                "group_type": kind, "group": str(key[3]) if extra else "all", **summarize_group(group)})
    return pd.DataFrame(blocks)


def paired_comparisons(evaluated, bootstrap_samples=2000, seed=42):
    """Paired candidates versus raw M0 and equally calibrated M0.

    Intervals resample whole years, preserving departmental dependence. With
    seven test years they describe sensitivity to those years, not future-year
    probability. No IID binomial interval is attached to department-year counts.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for (culture, contract), group in evaluated.groupby(["culture", "contract"], sort=True):
        policies = dict(tuple(group.groupby("policy", sort=True)))
        for policy, candidate in policies.items():
            if policy.startswith("selector/"):
                equal_baseline = "selector/m0_only"
            else:
                equal_baseline = "trend/" + policy.split("/", 1)[1]
            for comparison, baseline_name in (("raw_M0", "trend/raw"), ("same_policy_M0", equal_baseline)):
                if baseline_name not in policies:
                    raise ValueError(f"Missing paired baseline {baseline_name}")
                baseline = policies[baseline_name]
                merged = candidate.merge(baseline, on=KEYS, suffixes=("_candidate", "_baseline"),
                                         validate="one_to_one")
                if len(merged) != len(candidate) or len(merged) != len(baseline):
                    raise ValueError("Paired comparison lost observations")
                a, b = summarize_group(candidate), summarize_group(baseline)
                record = {"culture": culture, "contract": contract, "policy": policy,
                    "comparison": comparison, "baseline": baseline_name, "n": len(merged),
                    "held_candidate": a["held"], "held_baseline": b["held"],
                    "delta_held": a["held"] - b["held"],
                    "delta_unit_cost": a["realized_unit_cost"] - b["realized_unit_cost"],
                    "delta_shortfall": a["shortfall_eur_ha"] - b["shortfall_eur_ha"],
                    "delta_loss": a["contract_loss_eur_ha"] - b["contract_loss_eur_ha"],
                    "rescued_n": int((merged.held_candidate & ~merged.held_baseline).sum()),
                    "lost_n": int((~merged.held_candidate & merged.held_baseline).sum()),
                    "cheaper_n": int((merged.paid_actual_eur_ha_candidate < merged.paid_actual_eur_ha_baseline).sum())}
                annual = merged.assign(
                    held_difference=merged.held_candidate.astype(float) - merged.held_baseline.astype(float),
                    paid_difference=merged.paid_actual_eur_ha_candidate - merged.paid_actual_eur_ha_baseline,
                    loss_difference=merged.contract_loss_eur_ha_candidate - merged.contract_loss_eur_ha_baseline,
                ).groupby("year").agg(n=("dep", "size"), held_delta=("held_difference", "sum"),
                    paid_delta=("paid_difference", "sum"), tonnes=("accepted_yield_actual_candidate", "sum"),
                    loss_delta=("loss_difference", "sum"))
                if bootstrap_samples and len(annual) > 1:
                    sample = rng.integers(0, len(annual), size=(bootstrap_samples, len(annual)))
                    values = annual.to_numpy()[sample].sum(axis=1)
                    for label, distribution in (
                        ("held", values[:, 1] / values[:, 0]),
                        ("unit_cost", values[:, 2] / values[:, 3]),
                        ("loss", values[:, 4] / values[:, 0])):
                        record[f"delta_{label}_year_bootstrap_low"] = float(np.quantile(distribution, .025))
                        record[f"delta_{label}_year_bootstrap_high"] = float(np.quantile(distribution, .975))
                rows.append(record)
    return pd.DataFrame(rows)


def subgroup_comparisons(summary):
    """Pair all reported subgroup cells with M0 under identical rules."""
    join = ["culture", "contract", "group_type", "group"]
    metrics = ["n", "n_years", "held", "realized_unit_cost", "shortfall_eur_ha", "contract_loss_eur_ha"]
    candidates = summary[join + ["policy"] + metrics].copy()
    output = []
    for comparison in ("raw_M0", "same_policy_M0"):
        candidates["baseline"] = ("trend/raw" if comparison == "raw_M0" else
            candidates.policy.map(lambda policy: "selector/m0_only" if policy.startswith("selector/")
                                  else "trend/" + policy.split("/", 1)[1]))
        paired = candidates.merge(summary[join + ["policy"] + metrics],
            left_on=join + ["baseline"], right_on=join + ["policy"],
            suffixes=("", "_baseline"), validate="many_to_one")
        if len(paired) != len(candidates) or not (paired.n == paired.n_baseline).all():
            raise ValueError("Subgroup comparison requires identical baseline cases")
        paired["comparison"] = comparison
        paired["delta_held"] = paired.held - paired.held_baseline
        paired["delta_unit_cost"] = paired.realized_unit_cost - paired.realized_unit_cost_baseline
        paired["delta_shortfall"] = paired.shortfall_eur_ha - paired.shortfall_eur_ha_baseline
        paired["delta_loss"] = paired.contract_loss_eur_ha - paired.contract_loss_eur_ha_baseline
        paired["target_met"] = paired.held >= .8
        paired["target_and_cheaper_than_baseline"] = paired.target_met & (paired.delta_unit_cost < 0)
        paired["protection_not_worse_and_cheaper"] = (paired.delta_held >= 0) & (paired.delta_unit_cost < 0)
        output.append(paired.drop(columns=["policy_baseline", "n_baseline"]))
    return pd.concat(output, ignore_index=True)


def add_groups(rows):
    rows = rows.copy()
    # Thresholds are fixed before comparing model scores and use historical data.
    if "history_n" in rows:
        rows["history_group"] = pd.cut(rows.history_n, [0, 5, 9, np.inf],
            labels=["3–5 observations passées", "6–9 observations passées", "10+ observations passées"])
    if "history_cv" in rows:
        rows["volatility_group"] = pd.cut(rows.history_cv, [-np.inf, .2, .4, np.inf],
            labels=["CV passé ≤20%", "CV passé 20–40%", "CV passé >40%"])
    return rows


def reconcile_cohorts(raw, first_test_year=2019):
    """Explain entries and exits against the production grouping convention.

    This is a data audit of the same repository inputs, not a second model fit.
    Whole-period legacy grouping is used only to label the comparison cohort.
    """
    from benchmark_multilegumes import legacy_keys
    from multicrop_models import read_data

    panel, _ = read_data()
    rows = []
    for culture, sample in raw[raw.year >= first_test_year].groupby("culture"):
        years = sorted(map(int, sample.year.unique()))
        old = legacy_keys(panel, culture, years)
        new = set(map(tuple, sample[["year", "dep"]].drop_duplicates().to_numpy()))
        intersection = old & new
        flagged = set(map(tuple, sample.loc[sample.old_cohort, ["year", "dep"]].drop_duplicates().to_numpy()))
        if flagged != intersection:
            raise ValueError("Raw cohort flags disagree with this checkout's source data")
        rows.append({"culture": culture, "old_n": len(old), "new_n": len(new),
            "intersection_n": len(intersection), "added_n": len(new - old), "removed_n": len(old - new),
            "added_keys": json.dumps(sorted(new - old)), "removed_keys": json.dumps(sorted(old - new))})
    return pd.DataFrame(rows)


def _markdown_table(frame, columns, labels=None):
    labels = labels or columns
    lines = ["| " + " | ".join(labels) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for _, row in frame.iterrows():
        formatted = []
        for column in columns:
            value = row[column]
            if isinstance(value, (float, np.floating)):
                value = f"{value:.2%}" if column.startswith("held") else f"{value:,.1f}".replace(",", " ")
            formatted.append(str(value))
        lines.append("| " + " | ".join(formatted) + " |")
    return "\n".join(lines)


def plot_tradeoffs(summary, output):
    """Show the economic trade-off, including expensive calibrated candidates."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import PercentFormatter

    names = {"trend": "M0 · tendance", "linear": "M1 · linéaire", "qrf": "QRF",
        "qrf_seasonal": "QRF · fenêtres culture", "lightgbm_seasonal": "LightGBM · culture",
        "catboost_seasonal": "CatBoost · culture"}
    crops = {"lentille": "Lentille", "pois_chiche": "Pois chiche", "haricot": "Haricot sec",
             "pois": "Pois protéagineux", "feverole": "Féverole"}
    colors = dict(zip(names, ["#475569", "#a16207", "#0284c7", "#16a34a", "#7c3aed", "#db2777"]))
    markers = {"raw": "o", "cal80": "^", "cal90": "s", "cal95": "D"}
    overall = summary[summary.group_type == "all"]
    with plt.rc_context({"font.size": 9, "svg.fonttype": "none", "svg.hashsalt": "hackthefork-multilegumes"}):
        for contract, title in (("fixed", "Prix fixé avant campagne"),
                                ("indexed", "Multiplicateur du prix du blé"),
                                ("tiers", "Barème par tranches de rendement")):
            data = overall[overall.contract == contract]
            figure, axes = plt.subplots(3, 2, figsize=(11, 10), constrained_layout=True)
            for ax, (crop, crop_name) in zip(axes.flat, crops.items()):
                sample = data[data.culture == crop]
                eligible = sample[~sample.policy.str.contains("signed")]
                for model, color in colors.items():
                    points = sample[sample.policy.str.startswith(model + "/") & ~sample.policy.str.contains("signed")]
                    points = points.assign(variant=points.policy.str.split("/").str[1]).set_index("variant")
                    for variant, point in points.iterrows():
                        ax.scatter(point.realized_unit_cost, point.held, color=color, marker=markers[variant],
                                   s=37, edgecolor="white", linewidth=.45, zorder=3)
                for policy, fill, edge, label, size in (
                        ("selector/m0_only", "white", "#dc2626", "Sélecteur M0 seul", 230),
                        ("selector/all_models", "#111827", "#111827", "Sélecteur tous modèles", 120)):
                    point = sample[sample.policy == policy].iloc[0]
                    ax.scatter(point.realized_unit_cost, point.held, marker="*", s=size,
                               facecolor=fill, edgecolor=edge, linewidth=1.3, zorder=5, label=label)
                ax.axhline(.8, color="#64748b", linewidth=1, linestyle="--", zorder=1)
                ax.set_title(f"{crop_name} · {int(sample.iloc[0].n)} cas", fontweight="bold")
                ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
                lower = max(0., min(.7, np.floor((eligible.held.min() - .06) * 10) / 10))
                ax.set_ylim(lower, 1.025)
                ax.set_yticks(np.arange(lower, 1.001, .1))
                ax.set_xlabel("Paiement producteur / tonne acceptée (€/t)")
                ax.set_ylabel("Marge au moins égale au blé")
                ax.grid(axis="both", color="#e2e8f0", linewidth=.6, zorder=0)
                ax.spines[["top", "right"]].set_visible(False)
            legend = axes.flat[-1]
            legend.axis("off")
            handles = [Line2D([0], [0], marker="o", color=color, label=names[model], linestyle="", markersize=6)
                       for model, color in colors.items()]
            handles += [Line2D([0], [0], marker=marker, color="#64748b", label=("Brut · minimum simulé" if variant == "raw"
                        else f"{variant} · correction passée ≥ 0"), linestyle="", markersize=6)
                        for variant, marker in markers.items()]
            handles += [Line2D([0], [0], marker="*", color="#111827", label="Sélecteur tous modèles", linestyle="", markersize=12),
                        Line2D([0], [0], marker="*", markerfacecolor="white", markeredgecolor="#dc2626",
                               label="Sélecteur M0 seul", linestyle="", markersize=12)]
            legend.legend(handles=handles, loc="center", frameon=False, fontsize=9, labelspacing=.7)
            figure.suptitle(f"{title}\nCoût et protection hors échantillon · 2019–2025", fontsize=15, fontweight="bold")
            figure.savefig(output / f"coverage_cost_{contract}.svg", metadata={"Date": None})
            figure.savefig(output / f"coverage_cost_{contract}.png", dpi=150)
            plt.close(figure)


def write_report(summary, comparisons, decisions, output, input_path, manifest, cohorts=None):
    input_path = Path(input_path)
    input_label = (str(input_path.resolve().relative_to(ROOT))
                   if input_path.resolve().is_relative_to(ROOT) else str(input_path))
    overall = summary[summary.group_type == "all"]
    focus = overall[overall.policy.isin(["trend/raw", "linear/raw", "qrf/raw", "qrf_seasonal/raw",
                                        "lightgbm_seasonal/raw", "catboost_seasonal/raw",
                                        "selector/m0_only", "selector/all_models"])]
    lines = ["# Audit des cinq légumineuses : prix, contrats et sélection temporelle", "",
        "Le résultat recherché est un paiement producteur aussi faible que possible, tout en égalant ou dépassant la marge du blé dans au moins 80 % des cas testés. Les égalités comptent comme tenues. La comparaison porte sur les mêmes départements et années pour chaque modèle.", "",
        "## Protocole et unités", "",
        "- Années évaluées : 2019–2025. Prédictions hors temps 2016–2018 pour amorcer la calibration et la sélection ; aucune année test n'est utilisée avant sa date.",
        "- M0 est la tendance linéaire des rendements relatifs avec quantiles de résidus. M1 ajoute les six variables météo historiques ; les candidats QRF, LightGBM et CatBoost utilisent la même cohorte, avec une variante de fenêtres agronomiques par culture.",
        "- Prix fixe : €/t acceptée fixé avant campagne. Indexé : multiplicateur fixé avant campagne, appliqué au prix du blé à la récolte. Tranches : premier prix fixé avant campagne, deuxième et troisième prix à 70 % et 40 %, bornes à 0,7 et 1,4 fois le rendement net moyen passé.",
        "- Coût producteur moyen par tonne acceptée = somme des paiements / somme des rendements acceptés. Il exclut collecte, tri, séchage et autres coûts acheteur. Les lignes département–année ont le même poids de surface (1 ha) ; ce n'est pas un budget national pondéré par les surfaces réelles.",
        "- Le coefficient brut est le minimum non négatif atteignant 80 % dans l'échantillon simulé (quantile empirique exact, égalités incluses). Un coefficient corrigé est un prix calibré visant 80 % hors échantillon ; il ne se présente plus comme le minimum exact des simulations brutes.",
        "- Hypothèses v4 : charges blé 700 €/ha ; charges propres à chaque culture, aide 105 €/ha, rotation 150 €/ha et refus de 5 % ou 10 % selon `cultures.yaml`. Ce sont des scénarios économiques fixes appliqués aux rendements et prix historiques.",
        "- `cal80/90/95` ajoute au coefficient brut la partie positive du quantile correspondant des erreurs de coefficient des trois années passées, séparément par culture, modèle et contrat. La cible commerciale reste 80 %. Le coefficient brut constitue un plancher : sa protection dans au moins 80 % des simulations est préservée. Les ablations `signed80/90/95` autorisent une correction négative et restent exclues du sélecteur produit.",
        f"- Pondération de la calibration : `{manifest['calibration_weighting']}` (pooled = un poids par département–année ; year = une même masse totale par année).",
        "- Le sélecteur choisit, sur les trois années passées, la politique la moins chère atteignant 80 %. Si aucune ne passe, il prend la meilleure protection passée. Il sélectionne une seule politique pour la culture et le contrat, pas un gagnant rétrospectif par département. Le sélecteur M0 seul applique la même règle aux quatre variantes de M0.",
        f"- La recherche porte sur {int(decisions[decisions.selector == 'all_models'].n_candidates.max())} candidats admissibles par culture et forme de contrat. Le sélecteur minimise le coût dans cet ensemble fini, sans prétendre à un optimum global parmi tous les modèles et contrats possibles.",
        "- Les intervalles des différences rééchantillonnent des années entières, pas des lignes supposées indépendantes. Ils résument la sensibilité aux sept années disponibles. Aucun résultat de sous-groupe ne sert à redéfinir le test.", "",
        "## Cohortes comparables", ""]
    if cohorts is not None:
        lines.extend([_markdown_table(cohorts,
            ["culture", "old_n", "new_n", "intersection_n", "added_n", "removed_n"],
            ["Culture", "Ancienne cohorte", "Nouvelle", "Intersection", "Entrants", "Sortants"]), "",
            "Le regroupement de séries Agreste est reconstruit sur le passé de chaque pli. Un département représentant peut donc changer : la nouvelle cohorte n'est pas nécessairement un simple ajout à l'ancienne. Le détail des clés département–année est conservé dans `cohort_reconciliation.csv`. Les comparaisons de modèles utilisent toutes exactement la nouvelle cohorte ; la colonne ancienne cohorte désigne son intersection avec l'ancienne.", ""])
    lines.extend(["## Résultats sur les cas communs", ""])
    for contract, title in (("fixed", "Prix fixe"), ("indexed", "Indexation blé"), ("tiers", "Tranches de rendement")):
        lines.extend([f"### {title}", "", f"![Coût et protection — {title}](coverage_cost_{contract}.svg)", "", _markdown_table(
            focus[focus.contract == contract].sort_values(["culture", "policy"]),
            ["culture", "policy", "n", "held", "realized_unit_cost", "shortfall_eur_ha", "contract_loss_eur_ha"],
            ["Culture", "Politique", "Cas", "Marge ≥ blé", "Paiement €/t nette", "Déficit €/ha", "Perte asymétrique €/ha"]), ""])
    lines.extend(["## Lecture des gains et des échecs", ""])
    for culture in sorted(overall.culture.unique()):
        for contract in ("fixed", "indexed", "tiers"):
            selected = overall[(overall.culture == culture) & (overall.contract == contract) &
                               (overall.policy == "selector/all_models")].iloc[0]
            base = overall[(overall.culture == culture) & (overall.contract == contract) &
                           (overall.policy == "selector/m0_only")].iloc[0]
            delta = selected.realized_unit_cost - base.realized_unit_cost
            verdict = "cible atteinte" if selected.held >= .8 else "cible non atteinte"
            lines.append(f"- **{culture}, {contract}** : sélection temporelle {selected.held:.2%} ({verdict}), "
                f"{selected.realized_unit_cost:.0f} €/t nette ; M0 sélectionné de la même façon {base.held:.2%}, "
                f"{base.realized_unit_cost:.0f} €/t. Écart de coût {delta:+.0f} €/t ; "
                f"pire année {selected.held_worst_year:.2%}, {int(selected.years_at_target)}/{int(selected.n_years)} années au-dessus de 80 %.")
    lines.extend(["", "Les tableaux de sous-groupes comprennent toutes les années, régions, classes d'historique et de volatilité disponibles, ainsi que l'ancienne cohorte et les cas ajoutés. Les petites cellules restent visibles avec leurs effectifs et leur nombre d'années ; elles servent à identifier les situations à approfondir.", "",
        "## Fichiers reproductibles", "",
        f"- Prédictions brutes : `{input_label}` ; SHA-256 `{manifest['input_sha256']}`.",
        "- `global_summary.csv` : résultats globaux lisibles ; `summary.csv` (ou sa publication `summary.csv.gz`) : tous les modèles et calibrages, avec groupes et années.",
        "- `paired_baselines.csv` : écarts appariés contre M0 brut et M0 soumis au même calibrage/sélecteur ; cas gagnés/perdus et intervalles par blocs d'années.",
        "- `subgroup_comparisons.csv` : mêmes comparaisons, pour chaque année, région, historique, volatilité et cohorte ; gains et pertes sont tous conservés.",
        "- `selection_decisions.csv` : choix annuels et performances passées qui ont déclenché chaque choix.",
        "- `policy_predictions.csv.gz` : coefficients, paiements, marges et provenance temporelle ligne par ligne.",
        "- `manifest.json` : paramètres, empreinte du fichier d'entrée et empreinte du script d'analyse.", "",
        "Les contrats indexés et les tranches sont des produits différents du prix fixe. Une économie d'indexation ne prouve pas une amélioration du seul modèle de rendement. Les résultats sont rétrospectifs sous hypothèses fixes ; les lignes simulées ne constituent pas de nouvelles années observées.", ""])
    (output / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def run(args):
    args.output.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(args.input, dtype={"dep": str}, float_precision="round_trip")
    cohorts = reconcile_cohorts(raw, args.first_test_year) if not args.summary_only else None
    policies = calibrate_policies(raw, args.calibration_window, args.calibration_weighting)
    selected, decisions = select_policies(policies, args.first_test_year, args.selection_window)
    evaluated = add_groups(pd.concat([policies[policies.year >= args.first_test_year], selected], ignore_index=True))
    summary = grouped_summaries(evaluated, include_groups=not args.summary_only)
    manifest = {"input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "first_test_year": args.first_test_year, "calibration_window": args.calibration_window,
        "calibration_weighting": args.calibration_weighting,
        "selection_window": args.selection_window, "calibration_quantiles": CALIBRATIONS,
        "target": .8, "selector_objective": "past pooled protection >=80%, then paid/accepted tonnes",
        "bootstrap_unit": "year", "bootstrap_samples": args.bootstrap_samples, "seed": args.seed,
        "raw_rows": len(raw), "evaluation_rows": len(evaluated),
        "input": str(args.input), "negative_calibration_corrections_allowed": "signed ablations only",
        "selector_requires_raw_simulation_floor": True, "output_summary_only": args.summary_only}
    summary.to_csv(args.output / "summary.csv", index=False)
    if not args.summary_only:
        summary[summary.group_type == "all"].to_csv(args.output / "global_summary.csv", index=False)
    comparisons = pd.DataFrame()
    if not args.summary_only:
        comparisons = paired_comparisons(evaluated, args.bootstrap_samples, args.seed)
        subgroups = subgroup_comparisons(summary)
        plot_tradeoffs(summary, args.output)
        comparisons.to_csv(args.output / "paired_baselines.csv", index=False)
        subgroups.to_csv(args.output / "subgroup_comparisons.csv", index=False)
        decisions.to_csv(args.output / "selection_decisions.csv", index=False)
        cohorts.to_csv(args.output / "cohort_reconciliation.csv", index=False)
        evaluated.to_csv(args.output / "policy_predictions.csv.gz", index=False, compression="gzip")
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    if not args.summary_only:
        write_report(summary, comparisons, decisions, args.output, args.input, manifest, cohorts)
    print(json.dumps({"status": "complete", "output": str(args.output), "rows": len(evaluated),
                      "summary_rows": len(summary), "comparisons": len(comparisons)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/multilegumes_policies")
    parser.add_argument("--first-test-year", type=int, default=2019)
    parser.add_argument("--calibration-window", type=int, default=3)
    parser.add_argument("--calibration-weighting", choices=("pooled", "year"), default="pooled")
    parser.add_argument("--summary-only", action="store_true",
                        help="Write only global summary and manifest for a compact sensitivity run")
    parser.add_argument("--selection-window", type=int, default=3)
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    run(parser.parse_args())
