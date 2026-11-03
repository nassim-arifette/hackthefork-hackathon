"""Fixed direct-Q80 CatBoost challengers, selected using past OOF years only.

Run from the repository root. This is a research experiment, not a production
export. The four candidates and three-year selection window are fixed before
evaluation. 2016--18 predictions warm up selection; 2019--25 are scored.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

import numpy as np
import pandas as pd

from benchmark_contract import FEATURES, make_examples
from benchmark_models import quantile_loss, read_data, representatives, summarize
from common import hypotheses
from model import hyp_values


CONFIGS = {
    "direct_cb_residual_d2": {"target": "residual", "depth": 2, "iterations": 350},
    "direct_cb_price_d2": {"target": "price", "depth": 2, "iterations": 350},
    "direct_cb_residual_d3": {"target": "residual", "depth": 3, "iterations": 500},
    "direct_cb_price_d3": {"target": "price", "depth": 3, "iterations": 500},
}
COMMON_PARAMS = dict(loss_function="Quantile:alpha=0.8", learning_rate=.03,
                     l2_leaf_reg=20, random_seed=42, thread_count=1,
                     verbose=False, allow_writing_files=False)
MODEL_FEATURES = FEATURES + ["baseline"]
ROOT = Path(__file__).resolve().parents[1]


def choose_past(oof, decision_year, candidates=None, window=3):
    """Year-equal validation loss; never inspect decision-year/future outcomes."""
    candidates = list(CONFIGS) if candidates is None else list(candidates)
    past = oof[(oof.year < decision_year) &
               (oof.year >= decision_year - window) & oof.model.isin(candidates)]
    if past.empty:
        return candidates[0], {"validation_years": [], "scores": {}}
    # Each candidate must cover exactly the same historical decisions.
    expected = set(map(tuple, past[["year", "dep"]].drop_duplicates().to_numpy()))
    scores = {}
    for model in candidates:
        d = past[past.model == model]
        actual = set(map(tuple, d[["year", "dep"]].to_numpy()))
        if actual != expected or d.duplicated(["year", "dep"]).any():
            raise ValueError("Candidates have inconsistent OOF cohorts")
        scores[model] = float(d.groupby("year").contract_loss.mean().mean())
    choice = min(candidates, key=lambda model: scores[model])
    return choice, {"validation_years": sorted(map(int, past.year.unique())),
                    "scores": scores, "n_validation_per_candidate": len(expected)}


def validate_baseline(baseline, model, cohort):
    d = baseline[baseline.model == model].copy()
    expected = set(map(tuple, cohort.to_numpy()))
    actual = set(map(tuple, d[["year", "dep"]].to_numpy()))
    if actual != expected or d.duplicated(["year", "dep"]).any():
        raise ValueError(f"Baseline {model} does not match the common cohort")
    return d


def run(args):
    from catboost import CatBoostRegressor

    args.output.mkdir(parents=True, exist_ok=True)
    raw, weather = read_data()
    examples = make_examples(raw, weather, hyp_values(hypotheses()))
    reference = pd.read_csv(args.reference, dtype={"dep": str})
    direct = pd.read_csv(args.direct_reference, dtype={"dep": str})
    cohort = reference[["year", "dep"]].drop_duplicates().sort_values(["year", "dep"])
    if len(cohort) != 192 or set(cohort.year) != set(range(2019, 2026)):
        raise ValueError("Expected the fixed 192-row 2019--25 comparison cohort")
    oof_rows, audit = [], []
    for year in range(2016, 2026):
        reps = representatives(raw[(raw.culture == "lentille") & (raw.annee < year)])
        train = examples[(examples.year < year) & examples.dep.isin(reps) & examples.target.notna()]
        test = examples[(examples.year == year) & examples.dep.isin(reps) & examples.target.notna()]
        if year >= 2019:
            wanted = set(cohort.loc[cohort.year == year, "dep"])
            test = test[test.dep.isin(wanted)]
            if set(test.dep) != wanted:
                raise ValueError(f"Cohort mismatch in {year}")
        weights = 1 / train.groupby("year").year.transform("size").to_numpy()
        # Preserve CatBoost regularisation strength across years as data grow.
        weights = weights / weights.mean()
        for name, config in CONFIGS.items():
            params = {**COMMON_PARAMS, **{k: v for k, v in config.items() if k != "target"}}
            target = train.target.to_numpy().copy()
            if config["target"] == "residual":
                target -= train.baseline.to_numpy()
            model = CatBoostRegressor(**params).fit(train[MODEL_FEATURES], target,
                                                  sample_weight=weights)
            prices = np.asarray(model.predict(test[MODEL_FEATURES]))
            if config["target"] == "residual":
                prices += test.baseline.to_numpy()
            prices = np.maximum(prices, 1.)
            for (_, row), price in zip(test.iterrows(), prices):
                oof_rows.append({"year": year, "dep": row.dep, "model": name,
                    "price": float(price), "realised_break_even": float(row.target),
                    "held": bool(price >= row.target),
                    "contract_loss": float(quantile_loss(row.target, price, .8)),
                    "shortfall_eur_ha": float(max(0., row.target - price) * row.actual_lentil),
                    "pinball": None, "coverage": None, "width": None})
            audit.append({"year": year, "model": name, "train_max": int(train.year.max()),
                          "train_min": int(train.year.min()), "n_train": len(train),
                          "n_test": len(test), "representatives_from_years_before": year})
        pd.DataFrame(oof_rows).to_csv(args.output / "oof_predictions.csv", index=False)
        print(f"Direct CatBoost: {year} complete", flush=True)
    oof = pd.DataFrame(oof_rows)
    detail = oof[oof.year >= 2019].copy()
    selection, selected = [], []
    for year in range(2019, 2026):
        choice, info = choose_past(oof, year)
        selection.append({"year": year, "chosen": choice, **info})
        selected.append(detail[(detail.year == year) & (detail.model == choice)]
                        .assign(model="direct_cb_past_selected"))
    baselines = [validate_baseline(direct, name, cohort)
                 for name in ("direct_qrf", "direct_qrf_cal")]
    baselines.append(validate_baseline(reference, "qrf", cohort))
    detail = pd.concat([detail, *selected, *baselines], ignore_index=True)
    truth = detail.groupby(["year", "dep"]).realised_break_even.agg(["min", "max"])
    if not np.allclose(truth["min"], truth["max"]):
        raise ValueError("Realised outcomes disagree between baselines and challenger")
    detail.to_csv(args.output / "predictions.csv", index=False)
    annual = detail.groupby(["model", "year"])[
        ["contract_loss", "held", "price", "shortfall_eur_ha"]].mean().reset_index()
    annual.to_csv(args.output / "annual_metrics.csv", index=False)
    result = {"objective": "year_equal_pinball_0.8_of_realised_break_even_price_eur_t",
        "features": MODEL_FEATURES, "forecast_time": "before_target_year_no_realised_weather",
        "configurations_fixed_before_run": CONFIGS, "common_catboost_parameters": COMMON_PARAMS,
        "training_weights": "equal total weight per historical year; normalized to mean one",
        "selection_rule": "minimum previous three OOF years' year-equal contract_loss; stable config-order ties",
        "warmup_years": [2016, 2017, 2018], "evaluation_years": list(range(2019, 2026)),
        "summary": summarize(detail), "selection": selection, "audit": audit,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_sha256": {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):
                         hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in [ROOT / "data" / n for n in
                                   ("panel_rendements.csv", "meteo_dept.csv", "prix_ble.csv", "hypotheses.yaml")]
                         + [args.reference.resolve(), args.direct_reference.resolve()]},
        "packages": {name: importlib.metadata.version(name)
                     for name in ("numpy", "pandas", "scikit-learn", "catboost")},
        "limitations": ["Seven evaluation years; correlated departments are not independent trials.",
                        "Candidate comparisons are retrospective diagnostics; only the past-selected policy is the tuning result.",
                        "Q80 refers to the predicted break-even-price quantile; held-rate is not a guaranteed coverage.",
                        "No target-year realised weather or price enters prediction features."]}
    (args.output / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    lines = ["# Direct-Q80 CatBoost experiment", "",
             "Four fixed candidates, trained directly against the Q80 price loss. The residual target subtracts the known pre-season baseline before fitting and adds it back at prediction. Each training year has equal total weight.", "",
             "The deployable experimental policy selects using only the preceding three out-of-time years, starting with 2016–18 for the 2019 decision. No model is chosen using the complete 2019–25 evaluation. All reported models share the same 192 department-year rows.", "",
             "| Model | Year-equal Q80 loss (€/t) | Held (rows) | Median price (€/t) |",
             "|---|---:|---:|---:|"]
    for row in result["summary"]:
        lines.append(f"| {row['model']} | {row['contract_loss']:.2f} | {row['held']:.1%} | {row['median_price']:.2f} |")
    lines += ["", "Loss penalizes a price below realised break-even four times as much as an equal overshoot. Lower price alone is not an improvement. Held means the proposed farmgate price meets realised break-even.", "",
              "Only seven calendar years are evaluated, and departments are correlated. These are research results; production exports are unchanged.", "",
              "Reproduce from repository root (CatBoost and existing benchmark dependencies installed):", "", "```bash",
              "OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -u pipeline/benchmark_direct_catboost.py", "```", "",
              "`results.json` records parameters, input/script hashes, package versions, training-year audits and every past-only selection score. `oof_predictions.csv` includes the warmup years; `predictions.csv` and `annual_metrics.csv` include the comparison cohort and original baselines."]
    (args.output / "README.md").write_text("\n".join(lines) + "\n")
    print(pd.DataFrame(result["summary"])[["model", "contract_loss", "held", "median_price"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=ROOT / "experiments/colab_2026_10_31/colab_benchmark/predictions.csv")
    parser.add_argument("--direct-reference", type=Path, default=ROOT / "experiments/colab_2026_10_31/colab_contract/predictions.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/direct_catboost_optimization")
    run(parser.parse_args())
