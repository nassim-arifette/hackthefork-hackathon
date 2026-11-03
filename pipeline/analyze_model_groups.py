"""Paired economic diagnostics by groups fixed before inspection of model scores.

Groups available before a contract are kept separate from ex-post explanations.
Every comparison uses the same department-year rows for candidate and baseline;
uncertainty resamples whole years, never individual departments as independent.
"""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KEYS = ["year", "dep"]
KNOWN_GROUPS = ("region", "history", "volatility", "yield_level", "idf_donor")
DIAGNOSTIC_GROUPS = ("original_cohort", "harvest_collapse", "extreme_weather", "wheat_price_shock")
GROUP_DEFINITIONS = {
    "region": "Administrative region of the department, fixed metadata.",
    "history": "Fewer than 8 versus at least 8 usable lentil years strictly before decision.",
    "volatility": "Historical lentil sample SD / mean. Annual tercile cutoffs use only historical department representatives with at least 3 observations.",
    "yield_level": "Historical mean lentil yield, split by the annual median of historical department representatives with at least 3 observations.",
    "idf_donor": "Fixed project donor departments 10, 28, 45, 89 versus other observed departments; not an Ile-de-France field validation.",
    "original_cohort": "133 original archived cases versus 59 added cases. Retrospective audit only, not a deployable selection feature.",
    "harvest_collapse": "Ex post: realised lentil yield below 60% of its strictly historical department mean.",
    "extreme_weather": "Ex post: target-year March-July rain outside historical local P10-P90, or days above 30C exceeding historical local P90.",
    "wheat_price_shock": "Ex post: realised wheat price exceeds 1.2 times the latest earlier annual price.",
}


def build_groups(panel, weather, prices, cohort, original_keys):
    """Prepare both pre-season groups and explicitly labelled ex-post diagnostics."""
    panel = panel.copy()
    panel["dep"] = panel.dep.astype(str).str.zfill(2)
    weather = weather.copy()
    weather["dep"] = weather.dep.astype(str).str.zfill(2)
    lentil = panel[(panel.culture == "lentille") & panel.utilisable].copy()
    final_group_map = panel[panel.culture == "lentille"].drop_duplicates("dep").set_index("dep").serie_groupe
    duplicate_rule = importlib.import_module("01_agreste").flag_duplicates
    rows, thresholds = [], []
    for year, targets in cohort.groupby("year", sort=True):
        hist = lentil[lentil.annee < year]
        stats = hist.groupby("dep").rendement_qha.agg(["mean", "std", "count"])
        stats["cv"] = stats["std"] / stats["mean"]
        flagged = duplicate_rule(hist.copy())
        reps = set(flagged.loc[flagged.dep == flagged.serie_groupe, "dep"])
        fit_stats = stats[(stats.index.isin(reps)) & (stats["count"] >= 3)]
        cv_low, cv_high = fit_stats.cv.quantile([1 / 3, 2 / 3]).to_numpy()
        median_yield = float(fit_stats["mean"].median())
        group_map = flagged.drop_duplicates("dep").set_index("dep").serie_groupe
        last_price = float(prices.loc[prices.annee < year].sort_values("annee").prix_eur_t.iloc[-1])
        target_price = float(prices.loc[prices.annee == year, "prix_eur_t"].iloc[0])
        thresholds.append({"year": int(year), "cv_tercile_low": float(cv_low),
            "cv_tercile_high": float(cv_high), "yield_median_qha": median_yield,
            "n_departments_for_cutoffs": len(fit_stats), "train_max": int(hist.annee.max())})
        for dep in sorted(targets.dep):
            s = stats.loc[dep]
            actual = lentil[(lentil.annee == year) & (lentil.dep == dep)]
            if len(actual) != 1 or s["count"] < 3:
                raise ValueError(f"Missing/duplicate outcome or insufficient history for {year}/{dep}")
            past_weather = weather[(weather.dep == dep) & (weather.annee < year)]
            this_weather = weather[(weather.dep == dep) & (weather.annee == year)]
            if len(this_weather) != 1 or len(past_weather) < 3:
                raise ValueError(f"Incomplete weather for {year}/{dep}")
            rain_low, rain_high = past_weather.pluie_mj.quantile([.1, .9])
            hot_high = float(past_weather.j30_jj.quantile(.9))
            met = this_weather.iloc[0]
            extreme = bool(met.pluie_mj < rain_low or met.pluie_mj > rain_high or met.j30_jj > hot_high)
            ratio = float(actual.iloc[0].rendement_qha / s["mean"])
            rows.append({"year": int(year), "dep": dep,
                "region": str(hist.loc[hist.dep == dep, "region"].iloc[-1]),
                "history": "<8 years" if s["count"] < 8 else ">=8 years",
                "volatility": "low" if s.cv <= cv_low else "medium" if s.cv <= cv_high else "high",
                "yield_level": "low" if s["mean"] <= median_yield else "high",
                "idf_donor": "IDF donor departments" if dep in {"10", "28", "45", "89"} else "other departments",
                "original_cohort": "original 133" if (int(year), dep) in original_keys else "added 59",
                "harvest_collapse": "yield <60% of past mean" if ratio < .6 else "yield >=60% of past mean",
                "extreme_weather": "extreme" if extreme else "within historical thresholds",
                "wheat_price_shock": "price >1.2x last known" if target_price > 1.2 * last_price else "price <=1.2x last known",
                "past_series_group": str(group_map.loc[dep]), "history_n": int(s["count"]),
                "retrospective_final_series_group": str(final_group_map.loc[dep]),
                "past_mean_qha": float(s["mean"]), "past_cv": float(s.cv),
                "realised_yield_ratio": ratio, "actual_lentil_t_ha": float(actual.iloc[0].rendement_qha / 10),
                "rain_p10": float(rain_low), "rain_p90": float(rain_high), "hot_days_p90": hot_high,
                "wheat_price_ratio": target_price / last_price})
    return pd.DataFrame(rows), thresholds


def paired_rows(predictions, baseline, candidate):
    """Refuse implicit denominator changes, duplicates, or inconsistent outcomes."""
    b = predictions[predictions.model == baseline].copy()
    c = predictions[predictions.model == candidate].copy()
    for name, d in [(baseline, b), (candidate, c)]:
        if d.empty or d.duplicated(KEYS).any():
            raise ValueError(f"Empty/duplicate predictions for {name}")
    if set(map(tuple, b[KEYS].to_numpy())) != set(map(tuple, c[KEYS].to_numpy())):
        raise ValueError(f"Different evaluation cohorts for {baseline} and {candidate}")
    merged = b.merge(c, on=KEYS, suffixes=("_baseline", "_candidate"), validate="one_to_one")
    if not np.allclose(merged.realised_break_even_baseline, merged.realised_break_even_candidate, rtol=1e-10, atol=1e-8):
        raise ValueError("Different realised outcomes between compared models")
    return merged


def _weighted_mean(values, weights):
    return float(np.average(np.asarray(values, dtype=float), weights=weights))


def _weighted_quantile(values, weights, q):
    order = np.argsort(values, kind="stable")
    x, w = np.asarray(values)[order], np.asarray(weights)[order]
    return float(x[np.searchsorted(np.cumsum(w) / np.sum(w), q, side="left")])


def paired_summary(d, bootstrap_draws=10000, weighting="year_equal", seed=20261031):
    """Economic metrics and paired year-bootstrap intervals on one fixed subgroup."""
    d = d.copy()
    if weighting == "year_equal":
        d["within_year_weight"] = 1.
    elif weighting == "year_equal_past_series_equal":
        d["within_year_weight"] = 1 / d.groupby(["year", "past_series_group"]).dep.transform("size")
    elif weighting == "year_equal_region_equal":
        d["within_year_weight"] = 1 / d.groupby(["year", "region"]).dep.transform("size")
    elif weighting == "year_equal_final_series_equal_retrospective":
        d["within_year_weight"] = 1 / d.groupby(["year", "retrospective_final_series_group"]).dep.transform("size")
    else:
        raise ValueError(weighting)
    d["distribution_weight"] = d.within_year_weight / d.groupby("year").within_year_weight.transform("sum")
    years = []
    for year, g in d.groupby("year", sort=True):
        row = {"year": int(year)}
        for suffix in ("baseline", "candidate"):
            for metric in ("contract_loss", "held", "price", "shortfall_eur_ha"):
                row[f"{metric}_{suffix}"] = _weighted_mean(g[f"{metric}_{suffix}"], g.within_year_weight)
        row["extra_failure_rate"] = _weighted_mean(g.held_baseline & ~g.held_candidate, g.within_year_weight)
        row["rescued_failure_rate"] = _weighted_mean(~g.held_baseline & g.held_candidate, g.within_year_weight)
        row["cheaper_and_both_held_rate"] = _weighted_mean((g.price_candidate < g.price_baseline) & g.held_candidate & g.held_baseline, g.within_year_weight)
        row["lower_loss_case_rate"] = _weighted_mean(g.contract_loss_candidate < g.contract_loss_baseline, g.within_year_weight)
        years.append(row)
    annual = pd.DataFrame(years)
    result = {"n_cases": len(d), "n_departments": int(d.dep.nunique()), "n_years": len(annual),
        "years": sorted(map(int, d.year.unique())),
        "n_past_series_years": int(d[["year", "past_series_group"]].drop_duplicates().shape[0]),
        "support": "limited: fewer than 3 years or 15 cases" if len(annual) < 3 or len(d) < 15 else "descriptive: at least 3 years and 15 cases",
        "weighting": weighting}
    for suffix in ("baseline", "candidate"):
        for metric in ("contract_loss", "held", "price", "shortfall_eur_ha"):
            result[f"{metric}_{suffix}"] = float(annual[f"{metric}_{suffix}"].mean())
        result[f"held_rows_{suffix}"] = float(d[f"held_{suffix}"].mean())
        result[f"price_median_rows_{suffix}"] = float(d[f"price_{suffix}"].median())
        result[f"shortfall_p90_{suffix}"] = _weighted_quantile(d[f"shortfall_eur_ha_{suffix}"], d.distribution_weight, .9)
        result[f"protection_gap_to_80_{suffix}"] = max(0., .8 - result[f"held_{suffix}"])
    for metric in ("contract_loss", "held", "price", "shortfall_eur_ha"):
        result[f"delta_{metric}"] = result[f"{metric}_candidate"] - result[f"{metric}_baseline"]
    result["relative_loss_gain"] = 1 - result["contract_loss_candidate"] / result["contract_loss_baseline"]
    for name in ("extra_failure_rate", "rescued_failure_rate", "cheaper_and_both_held_rate", "lower_loss_case_rate"):
        result[name] = float(annual[name].mean())
    rng = np.random.default_rng(seed)
    draws = rng.integers(len(annual), size=(bootstrap_draws, len(annual)))
    for metric in ("contract_loss", "held"):
        delta = annual[f"{metric}_candidate"].to_numpy() - annual[f"{metric}_baseline"].to_numpy()
        sampled = delta[draws].mean(axis=1)
        for confidence, bounds in ((80, [.1, .9]), (95, [.025, .975])):
            lo, hi = np.quantile(sampled, bounds)
            result[f"delta_{metric}_ci{confidence}_low"] = float(lo)
            result[f"delta_{metric}_ci{confidence}_high"] = float(hi)
    result["lower_loss_and_no_less_protection"] = bool(result["delta_contract_loss"] < 0 and result["delta_held"] >= 0)
    result["candidate_80_and_lower_mean_price"] = bool(result["held_candidate"] >= .8 and result["delta_price"] < 0)
    result["comparison_class"] = ("dominates_M0_loss_and_protection" if result["lower_loss_and_no_less_protection"]
        else "80_protection_and_lower_price" if result["candidate_80_and_lower_mean_price"]
        else "lower_loss_only" if result["delta_contract_loss"] < 0 else "no_loss_gain")
    return result, annual


def analyze(predictions, metadata, baseline="trend", candidates=None, bootstrap_draws=10000, unavailable_target_history=False):
    candidates = candidates or [name for name in predictions.model.unique() if name != baseline]
    output, annual_output = [], []
    for candidate in candidates:
        paired = paired_rows(predictions, baseline, candidate).merge(metadata, on=KEYS, validate="one_to_one")
        if len(paired) != len(predictions[predictions.model == baseline]):
            raise ValueError("Group metadata changed the comparison denominator")
        groupings = [("all", "all cases", "all", paired)]
        for name in KNOWN_GROUPS + DIAGNOSTIC_GROUPS:
            use = "preseason" if name in KNOWN_GROUPS else "retrospective_only"
            if unavailable_target_history and name in {"history", "volatility", "yield_level"}:
                use = "retrospective_only"
            groupings.extend((name, str(value), use, d) for value, d in paired.groupby(name, sort=True))
        for group_type, group, use, rows in groupings:
            for weighting in ("year_equal", "year_equal_past_series_equal", "year_equal_region_equal", "year_equal_final_series_equal_retrospective"):
                summary, annual = paired_summary(rows, bootstrap_draws, weighting)
                ids = {"baseline": baseline, "candidate": candidate, "group_type": group_type,
                       "group": group, "group_use": use}
                output.append({**ids, **summary})
                for _, row in annual.iterrows():
                    annual_output.append({**ids, "weighting": weighting, **row.to_dict()})
    return pd.DataFrame(output), pd.DataFrame(annual_output)


def department_analysis(predictions, metadata, baseline="trend", candidates=None):
    """The contract is departmental: publish fractions and equal-department scores."""
    candidates = candidates or [name for name in predictions.model.unique() if name != baseline]
    rows, summaries = [], []
    for candidate in candidates:
        paired = paired_rows(predictions, baseline, candidate).merge(metadata, on=KEYS, validate="one_to_one")
        local = []
        for dep, d in paired.groupby("dep", sort=True):
            record = {"baseline": baseline, "candidate": candidate, "dep": dep,
                "region": str(d.region.iloc[0]), "n_years": len(d), "years": sorted(map(int, d.year)),
                "required_wins_for_80": int(np.ceil(.8 * len(d))),
                "support": "at least 5 years" if len(d) >= 5 else "limited: fewer than 5 years"}
            for suffix in ("baseline", "candidate"):
                wins = int(d[f"held_{suffix}"].sum())
                record[f"held_count_{suffix}"] = wins
                record[f"held_fraction_{suffix}"] = f"{wins}/{len(d)}"
                record[f"held_{suffix}"] = wins / len(d)
                record[f"meets_80_{suffix}"] = wins >= record["required_wins_for_80"]
                for metric in ("contract_loss", "price", "shortfall_eur_ha"):
                    record[f"{metric}_{suffix}"] = float(d[f"{metric}_{suffix}"].mean())
            for metric in ("contract_loss", "held", "price", "shortfall_eur_ha"):
                record[f"delta_{metric}"] = record[f"{metric}_candidate"] - record[f"{metric}_baseline"]
            record["dominates_M0_loss_and_protection"] = record["delta_contract_loss"] < 0 and record["delta_held"] >= 0
            record["candidate_80_and_lower_mean_price"] = record["meets_80_candidate"] and record["delta_price"] < 0
            local.append(record)
        table = pd.DataFrame(local)
        for subset_name, subset in [("all departments", table), ("at least 5 years", table[table.n_years >= 5]), ("all 7 years", table[table.n_years == 7])]:
            if subset.empty:
                continue
            row = {"baseline": baseline, "candidate": candidate, "subset": subset_name,
                   "n_departments": len(subset), "n_cases": int(subset.n_years.sum())}
            for suffix in ("baseline", "candidate"):
                for metric in ("contract_loss", "held", "price", "shortfall_eur_ha"):
                    row[f"{metric}_equal_departments_{suffix}"] = float(subset[f"{metric}_{suffix}"].mean())
                row[f"n_departments_80_{suffix}"] = int(subset[f"meets_80_{suffix}"].sum())
                row[f"share_departments_80_{suffix}"] = float(subset[f"meets_80_{suffix}"].mean())
                row[f"held_distribution_{suffix}"] = {str(k): int(v) for k, v in subset[f"held_fraction_{suffix}"].value_counts().sort_index().items()}
            row["n_dominate_loss_and_protection"] = int(subset.dominates_M0_loss_and_protection.sum())
            row["n_80_and_lower_price"] = int(subset.candidate_80_and_lower_mean_price.sum())
            summaries.append(row)
        rows.extend(local)
    return pd.DataFrame(rows), summaries


def make_report(summary, output, report_candidate="qrf_dense", baseline_label="M0", candidate_label="QRF dense", protocol_description=None):
    s = summary[(summary.candidate == report_candidate) & (summary.weighting == "year_equal")]
    if s.empty:
        raise ValueError(f"Report candidate {report_candidate} not in comparisons")
    protocol_description = protocol_description or "M0 désigne ici la famille `trend`, réévaluée dans le même protocole de recherche que QRF, avec le même modèle blé et les mêmes scénarios. Les taux de l'ancien système calibré à 82 % ne sont pas les taux de cette référence à quantiles bruts."
    lines = [f"# Comparaison par groupes : {candidate_label} et {baseline_label}", "",
        protocol_description, "",
        "Chaque ligne compare exactement les mêmes départements et années. La perte, les taux tenus, les prix moyens et les manques moyens donnent le même poids à chaque année. Les prix médians sont calculés sur les cas. Les intervalles rééchantillonnent les années entières, avec les écarts appariés au même M0.", "",
        "L'objectif de 80 % est affiché séparément de la perte économique. Un modèle peut réduire la perte tout en protégeant moins de contrats. Les groupes sont fixés par le script avant inspection des scores ; tous sont publiés, y compris ceux qui régressent. Les résultats par groupes sont exploratoires, pas une règle de sélection validée pour une future campagne.", "",
        "## Groupes connus avant campagne", "",
        f"| Groupe | Cas / années | Perte {baseline_label} → {candidate_label} | Gain perte | Tenus {baseline_label} → {candidate_label} | Δ perte, IC95 % |", "|---|---:|---:|---:|---:|---:|"]
    known = s[(s.group_use != "retrospective_only")]
    for _, r in known.iterrows():
        lines.append(f"| {r.group_type}: {r.group} | {r.n_cases} / {r.n_years} | {r.contract_loss_baseline:.1f} → {r.contract_loss_candidate:.1f} | {r.relative_loss_gain:.1%} | {r.held_baseline:.1%} → {r.held_candidate:.1%} | [{r.delta_contract_loss_ci95_low:.1f} ; {r.delta_contract_loss_ci95_high:.1f}] |")
    lines += ["", "## Diagnostics rétrospectifs", "",
        "Les étiquettes suivantes utilisent la récolte ou la météo réalisée, le prix réalisé, ou l'ancienne sélection globale des départements. Elles expliquent les échecs ; elles ne sont pas disponibles pour choisir un modèle au moment de signer le contrat.", "",
        f"| Groupe | Cas / années | Perte {baseline_label} → {candidate_label} | Tenus {baseline_label} → {candidate_label} | Manque €/ha {baseline_label} → {candidate_label} |", "|---|---:|---:|---:|---:|"]
    for _, r in s[s.group_use == "retrospective_only"].iterrows():
        lines.append(f"| {r.group_type}: {r.group} | {r.n_cases} / {r.n_years} | {r.contract_loss_baseline:.1f} → {r.contract_loss_candidate:.1f} | {r.held_baseline:.1%} → {r.held_candidate:.1%} | {r.shortfall_eur_ha_baseline:.1f} → {r.shortfall_eur_ha_candidate:.1f} |")
    lines += ["", "## Lecture et fichiers", "",
        "- Un groupe avec moins de trois années ou quinze cas porte `support=limited` dans le CSV. Les départements partagent des chocs annuels ; le nombre de cas n'est pas un nombre d'années indépendantes.",
        "- `group_comparisons.csv` publie tous les candidats demandés, toutes les régions et quatre pondérations : années égales, années et groupes Agreste connus égaux, années et régions égales, puis groupes Agreste identifiés sur toute la période. Cette dernière est une sensibilité rétrospective de l'évaluation, jamais une donnée d'entraînement.",
        "- `annual_comparisons.csv` conserve chaque écart annuel. `case_groups.csv` contient les caractéristiques passées et les diagnostics. `group_thresholds.json` documente les seuils estimés avec le passé uniquement.",
        "- `department_comparisons.csv` donne chaque département, ses années testées, les fractions de contrats tenus et le nombre de succès requis pour 80 % (6/7 sur sept ans). `department_summary.json` publie les moyennes à poids égal par département et le nombre de départements atteignant 80 %, séparément pour tous, au moins cinq ans et sept ans complets.",
        "- Les intervalles bootstrap sont descriptifs et non corrigés pour la multiplicité des groupes. Ils servent à distinguer les écarts stables des signaux isolés, pas à annoncer un groupe gagnant garanti.",
        "- Les quatre départements donneurs du projet francilien sont 10, 28, 45 et 89. Leur évaluation ne constitue pas une validation sur des récoltes lentille observées en Île-de-France.", "",
        "La commande exacte figure dans `manifest.json`, champ `command_line`. Le lancement par défaut reproduit l'analyse brute : `python pipeline/analyze_model_groups.py`. Pour ajouter une expérience, renseigner `--prediction-file`, `--baseline`, `--candidates` et `--report-candidate` ; toute cohorte différente est refusée explicitement."]
    (output / "README.md").write_text("\n".join(lines) + "\n")


def plot_regions(summary, output, report_candidate="qrf_dense", baseline_label="M0", candidate_label="QRF dense"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d = summary[(summary.candidate == report_candidate) & (summary.group_type == "region") & (summary.weighting == "year_equal")].sort_values("delta_contract_loss")
    if d.empty:
        return
    fig, ax = plt.subplots(figsize=(11, max(4.5, len(d) * .55)))
    y = np.arange(len(d))
    lo = d.delta_contract_loss - d.delta_contract_loss_ci95_low
    hi = d.delta_contract_loss_ci95_high - d.delta_contract_loss
    ax.errorbar(d.delta_contract_loss, y, xerr=np.vstack([lo, hi]), fmt="o", color="#22577a", ecolor="#a9b6c1", capsize=3)
    ax.axvline(0, color="#333333", linewidth=1)
    ax.set_yticks(y, [f"{r.group.split(' - ', 1)[-1]} ({r.n_cases} cas, {r.n_years} ans)" for _, r in d.iterrows()])
    ax.set_xlabel(f"Écart de perte contrat {candidate_label} − {baseline_label} (€/t) · négatif = mieux")
    ax.set_title("Gain économique par région, mêmes cas et mêmes années\nIntervalles descriptifs à 95 %, bootstrap des années")
    ax.grid(axis="x", alpha=.2)
    fig.tight_layout()
    fig.savefig(output / "regional_loss_comparison.png", dpi=160)
    fig.savefig(output / "regional_loss_comparison.svg")
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(13, max(4.5, len(d) * .55)), sharey=True, gridspec_kw={"width_ratios": [1.1, 1]})
    labels = [f"{r.group.split(' - ', 1)[-1]} ({r.n_cases})" for _, r in d.iterrows()]
    for ax, metric, scale in [(axes[0], "held", 100), (axes[1], "price", 1)]:
        for i, (_, r) in enumerate(d.iterrows()):
            ax.plot([r[f"{metric}_baseline"] * scale, r[f"{metric}_candidate"] * scale], [i, i], color="#b5bec5", zorder=1)
        ax.scatter(d[f"{metric}_baseline"] * scale, y, color="#b36b00", label=baseline_label, zorder=2)
        ax.scatter(d[f"{metric}_candidate"] * scale, y, color="#22577a", label=candidate_label, zorder=3)
        ax.grid(axis="x", alpha=.2)
    axes[0].axvline(80, color="#c53b40", linestyle="--", linewidth=1, label="Objectif 80 %")
    axes[0].set_xlim(max(0, 100 * min(d.held_baseline.min(), d.held_candidate.min()) - 8), 100)
    axes[0].set_yticks(y, labels)
    axes[0].set_xlabel("Contrats tenus · moyenne des taux annuels (%)")
    axes[1].set_xlabel("Prix proposé · moyenne annuelle (€/t)")
    axes[0].legend(loc="upper left", fontsize=9)
    fig.suptitle("Protection et prix : comparaison appariée par région", fontsize=14)
    fig.tight_layout()
    fig.savefig(output / "regional_price_protection.png", dpi=160)
    fig.savefig(output / "regional_price_protection.svg")
    plt.close(fig)


def main(args):
    args.output.mkdir(parents=True, exist_ok=True)
    standard = ROOT / "experiments/colab_2026_10_31/colab_benchmark/predictions.csv"
    dense = ROOT / "experiments/qrf_optimization/predictions.csv"
    files = [standard, dense, *args.prediction_file]
    predictions = [pd.read_csv(standard, dtype={"dep": str}).query("model in ['trend', 'linear', 'qrf']"),
                   pd.read_csv(dense, dtype={"dep": str}).query("model == 'qrf_dense'")]
    predictions += [pd.read_csv(p, dtype={"dep": str}) for p in args.prediction_file]
    all_predictions = pd.concat(predictions, ignore_index=True)
    if all_predictions.duplicated(KEYS + ["model"]).any():
        raise ValueError("Duplicate model/case between input files; give variants distinct names")
    cohort = all_predictions[all_predictions.model == args.baseline][KEYS]
    panel = pd.read_csv(ROOT / "data/panel_rendements.csv", dtype={"dep": str, "serie_groupe": str})
    weather = pd.read_csv(ROOT / "data/meteo_dept.csv", dtype={"dep": str})
    prices = pd.read_csv(ROOT / "data/prix_ble.csv")
    old_file = ROOT / "data/backtest.json"
    old = json.loads(old_file.read_text())["detail"]
    original_keys = {(int(r["annee"]), r["dep"]) for r in old}
    metadata, thresholds = build_groups(panel, weather, prices, cohort, original_keys)
    metadata.to_csv(args.output / "case_groups.csv", index=False)
    (args.output / "group_thresholds.json").write_text(json.dumps(thresholds, indent=2) + "\n")
    summary, annual = analyze(all_predictions, metadata, args.baseline, args.candidates, args.bootstrap_draws, args.unavailable_target_history)
    summary.to_csv(args.output / "group_comparisons.csv", index=False)
    annual.to_csv(args.output / "annual_comparisons.csv", index=False)
    department, department_summary = department_analysis(all_predictions, metadata, args.baseline, args.candidates)
    department.to_csv(args.output / "department_comparisons.csv", index=False)
    (args.output / "department_summary.json").write_text(json.dumps(department_summary, indent=2, ensure_ascii=False) + "\n")
    spec = {"groups_fixed_before_score_inspection": GROUP_DEFINITIONS,
        "preseason_groups": [g for g in KNOWN_GROUPS if not (args.unavailable_target_history and g in {"history", "volatility", "yield_level"})],
        "retrospective_only_groups": list(DIAGNOSTIC_GROUPS) + (["history", "volatility", "yield_level"] if args.unavailable_target_history else []),
        "baseline": args.baseline, "candidates": args.candidates, "bootstrap_draws": args.bootstrap_draws,
        "report_candidate": args.report_candidate, "baseline_label": args.baseline_label,
        "candidate_label": args.candidate_label, "protocol_description": args.protocol_description,
        "unavailable_target_history": args.unavailable_target_history,
        "bootstrap_unit": "whole evaluation year; paired candidate-minus-baseline differences",
        "command_line": [sys.executable, *sys.argv],
        "packages": {"numpy": np.__version__, "pandas": pd.__version__},
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "code_dependency_sha256": {"pipeline/01_agreste.py": hashlib.sha256((ROOT / "pipeline/01_agreste.py").read_bytes()).hexdigest()},
        "input_sha256": {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in files + [old_file] + [ROOT / "data" / name for name in ["panel_rendements.csv", "meteo_dept.csv", "prix_ble.csv"]]},
        "case_count": len(metadata), "comparison_count": len(summary),
        "past_series_year_count": int(metadata[["year", "past_series_group"]].drop_duplicates().shape[0]),
        "interpretation": "Exploratory subgroup diagnostics, not model selection using future subgroup outcomes."}
    (args.output / "manifest.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
    make_report(summary, args.output, args.report_candidate, args.baseline_label, args.candidate_label, args.protocol_description)
    if not args.no_plots:
        plot_regions(summary, args.output, args.report_candidate, args.baseline_label, args.candidate_label)
    print(summary[(summary.candidate == args.report_candidate) & (summary.weighting == "year_equal")][
        ["group_type", "group", "n_cases", "n_years", "relative_loss_gain", "held_baseline", "held_candidate", "delta_contract_loss_ci95_low", "delta_contract_loss_ci95_high"]].to_string(index=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=ROOT / "experiments/model_groups")
    p.add_argument("--prediction-file", type=Path, action="append", default=[])
    p.add_argument("--baseline", default="trend")
    p.add_argument("--candidates", nargs="+", default=["linear", "qrf", "qrf_dense"])
    p.add_argument("--bootstrap-draws", type=int, default=10000)
    p.add_argument("--no-plots", action="store_true")
    p.add_argument("--report-candidate", default="qrf_dense")
    p.add_argument("--baseline-label", default="M0")
    p.add_argument("--candidate-label", default="QRF dense")
    p.add_argument("--protocol-description")
    p.add_argument("--unavailable-target-history", action="store_true", help="For spatial transfer tests, mark target historical yield/CV groups as retrospective diagnostics.")
    main(p.parse_args())
