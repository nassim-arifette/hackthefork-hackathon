"""Calibrate contract prices and select under a past 80% protection constraint.

All corrections use earlier out-of-time break-even-price predictions. The same
corrections are applied to M0 (trend) and QRF, and every evaluated policy shares
the same department/year cohort. Production exports are never modified.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BASES = ("trend", "qrf")
TAU = .8
# Fixed before evaluation. Each signed correction has its one-sided counterpart.
CONFIGS = {"raw": {"kind": "raw", "window": None, "uplift_only": False}}
for _label, _kind, _window in [
    ("log_expanding", "log", None), ("log_5y", "log", 5),
    ("log_3y", "log", 3), ("add_expanding", "add", None),
    ("regional_expanding", "regional", None),
]:
    for _uplift in (False, True):
        CONFIGS[_label + ("_uplift" if _uplift else "_signed")] = {
            "kind": _kind, "window": _window, "uplift_only": _uplift}


def weighted_quantile(values, weights, tau=TAU):
    """Smallest value whose cumulative empirical weight reaches tau (ties win)."""
    values, weights = np.asarray(values, dtype=float), np.asarray(weights, dtype=float)
    if not len(values) or len(values) != len(weights):
        raise ValueError("Empty or mismatched quantile sample")
    if not np.isfinite(values).all() or not np.isfinite(weights).all() or (weights <= 0).any():
        raise ValueError("Quantile values and positive weights must be finite")
    if not 0 < tau <= 1:
        raise ValueError("tau must lie in (0, 1]")
    order = np.argsort(values, kind="stable")
    cumulative = np.cumsum(weights[order])
    # The small tolerance prevents roundoff from moving an exact boundary up.
    cutoff = tau * cumulative[-1]
    index = np.searchsorted(cumulative, cutoff - np.finfo(float).eps * cumulative[-1] * 4, side="left")
    return float(values[order[min(index, len(values) - 1)]])


def year_weights(rows):
    return 1. / rows.groupby("year").year.transform("size").to_numpy()


def calibration(history, decision_year, config, region=None):
    """Correction score and audit based strictly on years before the decision."""
    past = history[history.year < decision_year]
    if config["window"] is not None:
        past = past[past.year >= decision_year - config["window"]]
    audit = {"calibration_years": sorted(map(int, past.year.unique())),
             "n_calibration": len(past), "region": region, "n_region": 0,
             "regional_shrink_weight": 0., "fallback_raw": past.empty}
    kind = config["kind"]
    if kind == "raw" or past.empty:
        return 0., audit
    if kind in ("log", "regional"):
        if (past.price <= 0).any() or (past.realised_break_even <= 0).any():
            raise ValueError("Log calibration requires positive prices and break-even targets")
        scores = np.log(past.realised_break_even.to_numpy() / past.price.to_numpy())
    else:
        scores = past.realised_break_even.to_numpy() - past.price.to_numpy()
    correction = weighted_quantile(scores, year_weights(past))
    if kind == "regional":
        mask = past.region == region
        local = past[mask]
        if len(local):
            local_correction = weighted_quantile(scores[mask.to_numpy()], year_weights(local))
            n_years = local.year.nunique()
            weight = n_years / (n_years + 5.)
            correction = weight * local_correction + (1. - weight) * correction
            audit.update(n_region=len(local), regional_shrink_weight=weight)
    if config["uplift_only"]:
        correction = max(0., correction)
    return correction, audit


def check_cohorts(rows, names, column="model"):
    expected = None
    for name in names:
        d = rows[rows[column] == name]
        keys = set(map(tuple, d[["year", "dep"]].to_numpy()))
        if d.duplicated(["year", "dep"]).any() or not len(d):
            raise ValueError(f"Invalid comparison cohort for {name}")
        if expected is not None and keys != expected:
            raise ValueError("Candidates have inconsistent comparison cohorts")
        expected = keys


def choose_protection_policy(detail, decision_year, candidates, region=None):
    """Minimise past mean price among policies with >=80% year-equal held rate.

    Regional selection needs three validation years and at least 12 distinct
    cases per policy. Otherwise it falls back to the same global selector.
    If no policy is feasible, maximise protection, breaking ties by mean price.
    """
    past = detail[(detail.year < decision_year) & (detail.year >= decision_year - 3)
                  & detail.model.isin(candidates)]
    check_cohorts(past, candidates) if len(past) else None
    scope, requested_region = "global", region
    if region is not None and len(past):
        local = past[past.region == region]
        n = len(local[["year", "dep"]].drop_duplicates())
        if local.year.nunique() >= 3 and n >= 12:
            past, scope = local, "region"
    audit = {"validation_years": sorted(map(int, past.year.unique())),
             "n_validation_per_candidate": len(past[["year", "dep"]].drop_duplicates()),
             "scope": scope, "requested_region": requested_region,
             "feasible": False, "scores": {}, "insufficient_history": past.year.nunique() < 3}
    if past.year.nunique() < 3:
        raw = next((name for name in candidates if name.endswith("__raw")), candidates[0])
        return raw, audit
    check_cohorts(past, candidates)
    scores = past.groupby(["model", "year"])[["held", "price"]].mean().groupby("model").mean()
    audit["scores"] = {name: {"held_year_mean": float(scores.loc[name, "held"]),
                              "mean_price": float(scores.loc[name, "price"])} for name in candidates}
    admissible = [name for name in candidates if scores.loc[name, "held"] >= TAU - 1e-12]
    if admissible:
        chosen = min(admissible, key=lambda name: scores.loc[name, "price"])
        audit["feasible"] = True
    else:
        chosen = min(candidates, key=lambda name: (-scores.loc[name, "held"], scores.loc[name, "price"]))
    return chosen, audit


def evaluate_rows(rows):
    rows = rows.copy()
    residual = rows.realised_break_even - rows.price
    rows["held"] = rows.price >= rows.realised_break_even
    rows["contract_loss"] = np.maximum(TAU * residual, (TAU - 1.) * residual)
    rows["shortfall_eur_ha"] = np.maximum(residual, 0.) * rows.actual_lentil_t_ha
    rows["margin_surplus_eur_ha"] = np.maximum(-residual, 0.) * rows.actual_lentil_t_ha
    return rows


def build_policies(base):
    check_cohorts(base, BASES)
    frames, audits = [], []
    for kind in BASES:
        history = base[base.model == kind]
        for year in sorted(history.year.unique()):
            current = history[history.year == year]
            for label, config in CONFIGS.items():
                for region, regional_current in current.groupby("region"):
                    correction, audit = calibration(history, year, config, region)
                    out = regional_current.copy()
                    out["base_model"], out["model"] = kind, kind + "__" + label
                    out["base_price"] = out.price
                    if config["kind"] in ("log", "regional"):
                        out["price"] = out.price * np.exp(correction)
                    elif config["kind"] == "add":
                        # Zero is the economic non-negative price boundary, not an
                        # additional safety floor fitted to the evaluation set.
                        out["price"] = np.maximum(0., out.price + correction)
                    out["calibration_score"] = correction
                    frames.append(evaluate_rows(out))
                    audits.append({"year": int(year), "model": kind + "__" + label,
                                   "correction_score": correction, **audit})
    detail = pd.concat(frames, ignore_index=True)
    selections, selected = [], []
    all_candidates = [kind + "__" + label for kind in BASES for label in CONFIGS]
    for year in sorted(base.year.unique()):
        current = detail[detail.year == year]
        selectors = {
            "trend__past_selected": [name for name in all_candidates if name.startswith("trend__")],
            "qrf__past_selected": [name for name in all_candidates if name.startswith("qrf__")],
            "hybrid__global_selected": all_candidates,
        }
        for label, candidates in selectors.items():
            chosen, audit = choose_protection_policy(detail, year, candidates)
            selected.append(current[current.model == chosen].assign(model=label, selected_policy=chosen))
            selections.append({"year": int(year), "model": label, "chosen": chosen, **audit})
        for region in sorted(current.region.unique()):
            chosen, audit = choose_protection_policy(detail, year, all_candidates, region)
            selected.append(current[(current.model == chosen) & (current.region == region)]
                            .assign(model="hybrid__regional_selected", selected_policy=chosen))
            selections.append({"year": int(year), "model": "hybrid__regional_selected", "chosen": chosen, **audit})
    return pd.concat([detail, *selected], ignore_index=True), audits, selections


def metrics(rows):
    annual = rows.groupby("year")[["held", "price", "contract_loss", "shortfall_eur_ha", "margin_surplus_eur_ha"]].mean()
    department = rows.groupby("dep").held.mean()
    return {"n": len(rows), "years": int(rows.year.nunique()), "departments": int(rows.dep.nunique()),
            "held": float(rows.held.mean()), "held_year_mean": float(annual.held.mean()),
            "years_held_at_least_80": int((annual.held >= TAU - 1e-12).sum()),
            "departments_held_at_least_80": int((department >= TAU - 1e-12).sum()),
            "minimum_annual_held": float(annual.held.min()),
            "median_price": float(rows.price.median()), "mean_price": float(annual.price.mean()),
            "contract_loss": float(annual.contract_loss.mean()),
            "shortfall_eur_ha": float(annual.shortfall_eur_ha.mean()),
            "shortfall_p90_eur_ha": float(np.quantile(rows.shortfall_eur_ha, .9, method="inverted_cdf")),
            "margin_surplus_eur_ha": float(annual.margin_surplus_eur_ha.mean())}


def paired_comparisons(evaluation):
    """QRF versus M0 under each identical calibration/selection recipe."""
    comparisons = []
    for label in [*CONFIGS, "past_selected"]:
        left = evaluation[evaluation.model == "trend__" + label]
        right = evaluation[evaluation.model == "qrf__" + label]
        pair = left.merge(right, on=["year", "dep"], suffixes=("_m0", "_qrf"), validate="one_to_one")
        if len(pair) != len(left) or len(pair) != len(right):
            raise ValueError("Paired M0/QRF cohorts differ")
        groups = {"all": pair}
        if "old_cohort_m0" in pair:
            groups.update(old_133=pair[pair.old_cohort_m0], added_59=pair[~pair.old_cohort_m0])
        groups.update({"region:" + str(region): d for region, d in pair.groupby("region_m0")})
        for group, d in groups.items():
            if d.empty:
                continue
            annual = d.groupby("year")[["held_m0", "held_qrf", "price_m0", "price_qrf",
                "contract_loss_m0", "contract_loss_qrf", "shortfall_eur_ha_m0", "shortfall_eur_ha_qrf"]].mean()
            delta_loss = (annual.contract_loss_qrf - annual.contract_loss_m0).to_numpy()
            delta_held = (annual.held_qrf - annual.held_m0).to_numpy()
            rng = np.random.default_rng(816)
            indexes = rng.integers(len(annual), size=(5000, len(annual)))
            boot_loss = delta_loss[indexes].mean(axis=1)
            boot_held = delta_held[indexes].mean(axis=1)
            price_m0, price_qrf = float(annual.price_m0.mean()), float(annual.price_qrf.mean())
            held_m0, held_qrf = float(annual.held_m0.mean()), float(annual.held_qrf.mean())
            comparisons.append({"recipe": label, "group": group, "n": len(d), "years": len(annual),
                "small_group": len(d) < 15 or len(annual) < 3,
                "mean_price_m0": price_m0, "mean_price_qrf": price_qrf,
                "delta_price_qrf_minus_m0": price_qrf - price_m0,
                "held_year_mean_m0": held_m0, "held_year_mean_qrf": held_qrf,
                "delta_held_qrf_minus_m0": held_qrf - held_m0,
                "held_qrf_at_least_80": held_qrf >= TAU - 1e-12,
                "held_m0_at_least_80": held_m0 >= TAU - 1e-12,
                "contract_loss_m0": float(annual.contract_loss_m0.mean()),
                "contract_loss_qrf": float(annual.contract_loss_qrf.mean()),
                "delta_loss_qrf_minus_m0": float(delta_loss.mean()),
                "delta_shortfall_qrf_minus_m0": float((annual.shortfall_eur_ha_qrf - annual.shortfall_eur_ha_m0).mean()),
                "loss_delta_ci80_low": float(np.quantile(boot_loss, .1)),
                "loss_delta_ci80_high": float(np.quantile(boot_loss, .9)),
                "held_delta_ci80_low": float(np.quantile(boot_held, .1)),
                "held_delta_ci80_high": float(np.quantile(boot_held, .9)),
                "qrf_lower_price_and_no_lower_protection": price_qrf < price_m0 and held_qrf >= held_m0})
    return pd.DataFrame(comparisons)


def run(args):
    args.output.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(args.input, dtype={"dep": str})
    base = data[(data.protocol == "modern_raw_raw") & data.model.isin(BASES)].copy()
    if not set(range(2016, 2026)).issubset(set(base.year)):
        raise ValueError("Expected out-of-time 2016--25 predictions including warmup")
    panel = pd.read_csv(args.panel, dtype={"dep": str})
    metadata = panel[panel.culture == "lentille"][["dep", "annee", "region", "rendement_qha"]]
    metadata = metadata.rename(columns={"annee": "year", "rendement_qha": "actual_lentil_t_ha"})
    metadata.actual_lentil_t_ha /= 10.
    base = base.drop(columns=[c for c in ("region", "actual_lentil_t_ha") if c in base])
    base = base.merge(metadata, on=["year", "dep"], validate="many_to_one")
    if base.region.isna().any() or base.actual_lentil_t_ha.isna().any():
        raise ValueError("Missing observed outcome metadata")
    detail, audits, selections = build_policies(base)
    detail.to_csv(args.output / "predictions_with_warmup.csv", index=False)
    evaluation = detail[(detail.year >= 2019) & (detail.year <= 2025)].copy()
    names = sorted(evaluation.model.unique())
    check_cohorts(evaluation, names)
    if len(evaluation[evaluation.model == names[0]]) != 192:
        raise ValueError("Expected the fixed 192-row evaluation cohort")
    evaluation.to_csv(args.output / "predictions.csv", index=False)
    summary = [{"model": name, **metrics(rows)} for name, rows in evaluation.groupby("model")]
    annual = evaluation.groupby(["model", "year"])[["held", "price", "contract_loss", "shortfall_eur_ha", "margin_surplus_eur_ha"]].mean().reset_index()
    annual.to_csv(args.output / "annual_metrics.csv", index=False)
    regional = [{"model": name, "region": region, **metrics(rows)}
                for (name, region), rows in evaluation.groupby(["model", "region"])]
    pd.DataFrame(regional).to_csv(args.output / "regional_metrics.csv", index=False)
    department = [{"model": name, "dep": dep, "region": rows.region.iloc[0], **metrics(rows)}
                  for (name, dep), rows in evaluation.groupby(["model", "dep"])]
    pd.DataFrame(department).to_csv(args.output / "department_metrics.csv", index=False)
    paired_comparisons(evaluation).to_csv(args.output / "paired_m0_qrf.csv", index=False)
    subgroups = []
    if "old_cohort" in evaluation:
        for (name, old), rows in evaluation.groupby(["model", "old_cohort"]):
            subgroups.append({"model": name, "group": "old_133" if old else "added_59", **metrics(rows)})
    pd.DataFrame(subgroups).to_csv(args.output / "cohort_metrics.csv", index=False)
    result = {"objective": "minimum past mean price subject to at least 80% year-equal held rate",
        "bases": list(BASES), "configurations_fixed_before_evaluation": CONFIGS,
        "comparison": "Identical corrections and selection rules applied to M0 and QRF",
        "calibration": "Earlier out-of-time price errors only, equal total weight per year",
        "regional_shrinkage": "n_region_years / (n_region_years + 5), in log correction score",
        "selector": "Previous three years; minimum mean price among feasible candidates; otherwise highest held then lowest price",
        "regional_selector_minimum": {"years": 3, "cases": 12},
        "warmup_years": [2016, 2017, 2018], "evaluation_years": list(range(2019, 2026)),
        "summary": sorted(summary, key=lambda row: row["contract_loss"]),
        "selection": selections, "calibration_audit": audits,
        "sha256": {"script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   "input_predictions": hashlib.sha256(args.input.read_bytes()).hexdigest(),
                   "panel": hashlib.sha256(args.panel.read_bytes()).hexdigest()},
        "packages": {n: importlib.metadata.version(n) for n in ("numpy", "pandas")},
        "interpretation": ["80% is an empirical past feasibility constraint, not known future coverage.",
            "A higher held rate obtained by a higher price alone is not model dominance.",
            "Regions are fixed administrative groups known before signing; no outcome-defined deployment group.",
            "All fixed policies are reported; selection never uses current/future outcomes."]}
    (args.output / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    focus = ["trend__raw", "qrf__raw", "trend__log_expanding_signed", "qrf__log_expanding_signed",
             "trend__regional_expanding_signed", "qrf__regional_expanding_signed",
             "trend__past_selected", "qrf__past_selected", "hybrid__global_selected", "hybrid__regional_selected"]
    table = pd.DataFrame(summary).set_index("model").loc[focus]
    print(table[["contract_loss", "held", "held_year_mean", "mean_price", "shortfall_eur_ha"]].to_string(), flush=True)
    lines = ["# Politiques de prix centrées sur la protection à 80 %", "",
        "Les mêmes corrections sont appliquées à M0 et QRF. Chaque correction utilise uniquement les erreurs de prix issues des prévisions temporelles des années antérieures. Les sélecteurs recherchent le prix moyen le plus bas parmi les politiques ayant tenu au moins 80 % des contrats, en moyenne annuelle, pendant les trois années précédentes. À défaut, ils retiennent la meilleure protection passée, puis le prix le plus bas.", "",
        "Les 22 politiques fixes et quatre sélecteurs sont tous rapportés. Les trois premières années servent à initialiser les corrections et sélecteurs ; les 192 cas 2019–2025 constituent la comparaison. Une hausse de prix peut augmenter la protection sans améliorer la qualité du modèle.", "",
        "| Politique | Perte contrat €/t ↓ | Tenus, cas | Tenus, années | Prix moyen €/t | Manque moyen €/ha |",
        "|---|---:|---:|---:|---:|---:|"]
    for name, row in table.iterrows():
        lines.append(f"| {name} | {row.contract_loss:.2f} | {row.held:.1%} | {row.held_year_mean:.1%} | {row.mean_price:.0f} | {row.shortfall_eur_ha:.2f} |")
    lines += ["", "Les tableaux complets, scores annuels, régionaux et départementaux, prix par cas et décisions de sélection sont dans les CSV et `results.json`. `paired_m0_qrf.csv` compare les deux familles sous la même recette de correction et rééchantillonne les années pour les intervalles descriptifs des écarts ; les petits groupes sont signalés. Une protection groupée de 80 % ne signifie pas 80 % dans chaque département. Les groupes régionaux sont administratifs et connus à la signature. Le sélecteur régional exige trois années et douze cas antérieurs ; sinon il utilise le choix global. La correction régionale est ramenée vers la correction globale avec un poids de `n_annees / (n_annees + 5)`.", "",
        "Les corrections globales signées utilisent le plus petit quantile empirique couvrant 80 % du poids des observations passées. Chaque année reçoit un poids total identique. La correction régionale mélange deux quantiles : ce retrait vers le global est une heuristique, pas le quantile exact d'un groupe. Les politiques `uplift` empêchent une baisse sous le prix brut et ne sont donc pas minimales quand la correction signée serait négative. La frontière économique de prix nul est appliquée à la correction additive. `margin_surplus_eur_ha` désigne l'excédent de marge de la lentille sur le blé dans les cas gagnants ; ce n'est pas un montant économiquement trop payé.", "",
        "Reproduire depuis la racine :", "", "```bash", "python pipeline/benchmark_contract_policies.py", "```", "",
        "Aucune donnée de l'année à prédire n'entre dans la correction ni dans le choix de politique. Les résultats décrivent le backtest ; atteindre la contrainte sur le passé ne force pas son respect sur l'année suivante."]
    (args.output / "README.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "experiments/protocol_attribution/predictions_with_warmup.csv")
    parser.add_argument("--panel", type=Path, default=ROOT / "data/panel_rendements.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/contract_policies")
    run(parser.parse_args())
