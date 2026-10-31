"""Five crops, common past-only yield models and three contract shapes.

2016–2018 are out-of-time warm-up predictions for subsequent price calibration;
2019–2025 are the reported evaluation years. This script emits raw contract
coefficients. A separate policy benchmark calibrates/selects them on the past.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

from contract_economics import (accepted_yield, calibrate_coefficient, contract_basis,
    crop_hypotheses, evaluate, expected_unit_cost, required_coefficient,
    signed_required_income, tier_bounds)
from multicrop_models import (CULTURES, MODEL_NAMES, ROOT, WEATHER, YieldModel,
    prepare_training, read_data, simulated_yields)


CONTRACTS = ("fixed", "indexed", "tiers")


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def legacy_keys(raw, culture, years):
    """Historical full-period grouping cohort, for an explicit paired diagnostic."""
    crop = raw[(raw.culture == culture) & ~raw.doublon]
    wheat = raw[(raw.culture == "ble") & ~raw.doublon]
    keys = set()
    for year in years:
        counts = crop[crop.annee < year].groupby("dep").size()
        allowed = set(counts[counts >= 3].index) & set(wheat[wheat.annee < year].dep)
        allowed &= set(wheat[wheat.annee == year].dep)
        keys.update((int(year), dep) for dep in crop[(crop.annee == year) & crop.dep.isin(allowed)].dep)
    return keys


def assert_common_cohort(rows, models, contracts=CONTRACTS):
    """Every candidate sees the same observed crop/department/year cases."""
    expected = None
    for model in models:
        for contract in contracts:
            subset = rows[(rows.model == model) & (rows.contract == contract)]
            if subset.empty or subset.duplicated(["culture", "year", "dep"]).any():
                raise ValueError(f"Invalid cohort for {model}/{contract}")
            keys = set(map(tuple, subset[["culture", "year", "dep"]].to_numpy()))
            if expected is not None and keys != expected:
                raise ValueError("Model or contract comparisons use different cases")
            expected = keys


def summarize(rows, first_test_year=2019):
    evaluated = rows[rows.year >= first_test_year]
    summaries = []
    for (culture, model, contract), group in evaluated.groupby(["culture", "model", "contract"]):
        annual = group.groupby("year")[["held", "expected_unit_cost", "shortfall_eur_ha",
                                          "contract_loss_eur_ha"]].mean()
        annual_paid = group.groupby("year").paid_actual_eur_ha.sum()
        annual_tonnes = group.groupby("year").accepted_yield_actual.sum()
        expected_paid = (group.coefficient * group.simulation_basis_mean).groupby(group.year).sum()
        expected_tonnes = group.groupby("year").simulation_accepted_mean.sum()
        summaries.append({"culture": culture, "model": model, "contract": contract,
            "n": len(group), "n_years": len(annual), "n_held": int(group.held.sum()),
            "held": float(group.held.mean()), "held_year_mean": float(annual.held.mean()),
            "expected_unit_cost_year_mean": float((expected_paid / expected_tonnes).mean()),
            "expected_unit_cost_pooled": float(expected_paid.sum() / expected_tonnes.sum()),
            "realized_unit_cost_year_mean": float((annual_paid / annual_tonnes).mean()),
            "realized_unit_cost_pooled": float(annual_paid.sum() / annual_tonnes.sum()),
            "shortfall_eur_ha": float(annual.shortfall_eur_ha.mean()),
            "contract_loss_eur_ha": float(annual.contract_loss_eur_ha.mean()),
            "old_cohort_n": int(group.old_cohort.sum())})
    return summaries


def evaluate_contract(shape, need, net, wheat_price, past_net, actual_need, actual_net,
                      actual_wheat_price, tau=.8):
    """Calibrate once on past scenarios, then judge the held-out observation."""
    basis = contract_basis(shape, net, p_w=wheat_price, past_mean_accepted=past_net)
    coefficient = calibrate_coefficient(need, basis, tau)
    simulated = evaluate(coefficient, basis, need, net)
    if float(np.mean(simulated["held"])) < tau - 1e-12:
        raise AssertionError("Exact empirical contract target not reached")
    actual_basis = contract_basis(shape, actual_net, p_w=actual_wheat_price,
                                  past_mean_accepted=past_net)
    result = evaluate(coefficient, actual_basis, actual_need, actual_net)
    residual_income = float(actual_need - result["paid_eur_ha"])
    return {"contract": shape, "coefficient": coefficient,
        "required_coefficient": float(required_coefficient(actual_need, actual_basis)),
        "actual_basis": float(actual_basis), "paid_actual_eur_ha": float(result["paid_eur_ha"]),
        "held": bool(result["held"]), "shortfall_eur_ha": float(result["shortfall_eur_ha"]),
        "effective_price_actual": float(result["effective_price_eur_t"]),
        "expected_unit_cost": expected_unit_cost(coefficient, basis, net),
        "simulation_basis_mean": float(np.mean(basis)),
        "simulation_accepted_mean": float(np.mean(net)),
        "simulated_protection": float(np.mean(simulated["held"])),
        "contract_loss_eur_ha": max(tau * residual_income, (tau - 1) * residual_income),
        "tier_bound_1": tier_bounds(past_net)[0] if shape == "tiers" else None,
        "tier_bound_2": tier_bounds(past_net)[1] if shape == "tiers" else None}


def create_manifest(args, seasonal_columns):
    files = [ROOT / "pipeline" / name for name in
             ("multicrop_models.py", "benchmark_multilegumes.py", "contract_economics.py",
              "common.py", "model.py")]
    files += [ROOT / "data" / name for name in ("panel_rendements.csv", "meteo_dept_cultures.csv",
                                               "prix_ble.csv", "hypotheses.yaml", "cultures.yaml")]
    if args.seasonal_file:
        files.append(Path(args.seasonal_file))
        files.append(ROOT / "pipeline/crop_weather.py")
    packages = {}
    for name in ("numpy", "pandas", "scipy", "scikit-learn", "quantile-forest", "lightgbm", "catboost", "PyYAML"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    options = {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items() if k != "output"}
    # Absolute checkout paths do not affect a model or its provenance hash.
    options["seasonal_file"] = Path(args.seasonal_file).name if args.seasonal_file else None
    spec = {"options": options, "seasonal_columns": seasonal_columns,
        "packages": packages,
        "files": {str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else path.name:
                  hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
        "distribution": "raw Q10/Q50/Q90, piecewise-linear tails, relative-yield floor .02",
        "wheat_model": "linear, six legacy weather features, all available 87 weather departments",
        "economic_basis": "euros per accepted tonne; fixed scenario hypotheses; need remains signed",
        "target": .8, "evaluation_years": [year for year in args.years if year >= 2019],
        "warmup_years": [year for year in args.years if year < 2019]}
    signature = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    path = args.output / "manifest.json"
    if path.exists() and json.loads(path.read_text())["signature"] != signature:
        raise ValueError("Source/data/options changed; use a new output directory")
    atomic_json(path, {"signature": signature, "spec": spec})
    return signature


def run(args):
    args.output.mkdir(parents=True, exist_ok=True)
    raw, weather = read_data(seasonal_file=args.seasonal_file)
    seasonal_columns = {}
    if any(name.endswith("_seasonal") for name in args.models):
        if not args.seasonal_file:
            raise ValueError("Seasonal candidates require --seasonal-file")
        from crop_weather import seasonal_columns as columns_for_crop
        seasonal_columns = {culture: list(args.seasonal_columns or columns_for_crop(culture))
                            for culture in args.cultures}
        all_columns = sorted(set(column for values in seasonal_columns.values() for column in values))
        if not all_columns:
            raise ValueError("No seasonal features found")
        if not np.isfinite(weather[all_columns].to_numpy(dtype=float)).all():
            raise ValueError("Seasonal weather features contain missing/nonfinite values")
    signature = create_manifest(args, seasonal_columns)
    checkpoint_dir = args.output / "checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    wheat = raw[raw.culture == "ble"]
    old = {culture: legacy_keys(raw, culture, args.years) for culture in args.cultures}
    all_rows, all_audits = [], []
    started, completed = time.monotonic(), 0
    total = len(args.cultures) * len(args.years) * len(args.models)

    def progress(active, status="running"):
        record = {"status": status, "completed": completed, "total": total,
                  "active": active, "elapsed_seconds": round(time.monotonic() - started, 1)}
        atomic_json(args.output / "progress.json", record)
        print(json.dumps(record), flush=True)

    for year in sorted(args.years):
        progress(f"wheat {year}")
        wheat_model = None
        real_wheat = wheat[wheat.annee == year].set_index("dep")
        for culture in args.cultures:
            paths = {name: checkpoint_dir / f"{culture}-{year}-{name}.json" for name in args.models}
            if all(path.exists() for path in paths.values()):
                for name, checkpoint in paths.items():
                    saved = json.loads(checkpoint.read_text())
                    if saved["signature"] != signature:
                        raise ValueError(f"Incompatible checkpoint {checkpoint}")
                    all_rows.extend(saved["rows"])
                    all_audits.extend(saved["audits"])
                    completed += 1
                    progress(f"{culture} {year} {name} resumed")
                continue
            if wheat_model is None:
                wheat_model = YieldModel("linear", args.seed, args.threads).fit(wheat[wheat.annee < year])
            crop = raw[raw.culture == culture]
            history = crop[crop.annee < year]
            prepared = prepare_training(history)
            seasonal = prepare_training(history, seasonal_columns.get(culture)) if any(
                name.endswith("_seasonal") for name in args.models) else None
            common = set(prepared.levels.index) & set(wheat_model.levels.index) & set(real_wheat.index)
            test = crop[(crop.annee == year) & crop.dep.isin(common)].sort_values("dep")
            if test.empty:
                raise ValueError(f"No held-out common cases for {culture}/{year}")
            h = crop_hypotheses(culture)
            local_history = history.groupby("dep").rendement_qha.agg(["size", "mean", "std"])
            for name in args.models:
                checkpoint = paths[name]
                if checkpoint.exists():
                    saved = json.loads(checkpoint.read_text())
                    if saved["signature"] != signature:
                        raise ValueError(f"Incompatible checkpoint {checkpoint}")
                    all_rows.extend(saved["rows"])
                    all_audits.extend(saved["audits"])
                    completed += 1
                    progress(f"{culture} {year} {name} resumed")
                    continue
                rows, audits = [], []
                progress(f"{culture} {year} {name}")
                model = YieldModel(name, args.seed, args.threads).fit_prepared(
                    seasonal if name.endswith("_seasonal") else prepared)
                if set(model.levels.index) != set(prepared.levels.index):
                    raise AssertionError("Feature sets changed the available cohort")
                q_test = model.predict_quantiles(test)
                for index, (_, observation) in enumerate(test.iterrows()):
                    dep = observation.dep
                    pool = weather[(weather.dep == dep) & (weather.annee < year)].sort_values("annee").copy()
                    historical_years = list(map(int, pool.annee))
                    pool["annee"] = year
                    yc, yw, pw = simulated_yields(pool, model, wheat_model, dep, year,
                                                  samples=args.samples, seed=args.seed)
                    net = accepted_yield(yc, h["qualite"])
                    need = signed_required_income(pw, yw, h["charges_ble"], h["charges_culture"],
                                                  h["aide"], h["rotation"])
                    actual_net = accepted_yield(observation.rendement_qha / 10, h["qualite"])
                    actual_wheat_yield = float(real_wheat.loc[dep, "rendement_qha"] / 10)
                    actual_wheat_price = float(observation.prix_ble)
                    actual_need = signed_required_income(actual_wheat_price, actual_wheat_yield,
                        h["charges_ble"], h["charges_culture"], h["aide"], h["rotation"])
                    past_net = float(accepted_yield(model.levels[dep] / 10, h["qualite"]))
                    actual_relative = float(observation.rendement_qha / model.levels[dep])
                    q = q_test[index]
                    error = actual_relative - q
                    pinball = float(np.maximum(np.asarray((.1, .5, .9)) * error,
                                                (np.asarray((.1, .5, .9)) - 1) * error).mean())
                    common_row = {"culture": culture, "year": int(year), "dep": dep,
                        "region": observation.region, "model": name,
                        "old_cohort": (int(year), dep) in old[culture],
                        "evaluation": year >= 2019, "accepted_yield_actual": float(actual_net),
                        "actual_crop_yield_raw": float(observation.rendement_qha / 10),
                        "actual_wheat_yield": actual_wheat_yield,
                        "actual_wheat_price": actual_wheat_price,
                        "actual_need_eur_ha": float(actual_need),
                        "realised_break_even": float(actual_need / actual_net),
                        "past_mean_accepted": past_net, "refused_fraction": h["qualite"],
                        "history_n": int(local_history.loc[dep, "size"]),
                        "history_mean_qha": float(local_history.loc[dep, "mean"]),
                        "history_cv": float(local_history.loc[dep, "std"] / local_history.loc[dep, "mean"]),
                        "q10_rel": float(q[0]), "q50_rel": float(q[1]), "q90_rel": float(q[2]),
                        "actual_rel": actual_relative, "yield_pinball_raw": pinball,
                        "yield_coverage80_raw": bool(q[0] <= actual_relative <= q[2]),
                        "simulation_history_max": max(historical_years)}
                    for shape in CONTRACTS:
                        contract = evaluate_contract(shape, need, net, pw, past_net,
                            actual_need, actual_net, actual_wheat_price, h["tau"])
                        rows.append(common_row | contract)
                audits.append({"culture": culture, "year": int(year), "model": name,
                    "training_years": prepared.years, "training_max": max(prepared.years),
                    "n_train": prepared.n, "n_departments_train": len(prepared.levels),
                    "n_test": len(test), "test_departments": test.dep.tolist(),
                    "representatives": sorted(prepared.representatives),
                    "features": list(model.features.columns),
                    "wheat_n_train": wheat_model.prepared.n,
                    "wheat_departments_train": len(wheat_model.levels),
                    "hypotheses": h})
                assert_common_cohort(pd.DataFrame(rows), [name])
                atomic_json(checkpoint, {"signature": signature, "rows": rows, "audits": audits})
                all_rows.extend(rows)
                all_audits.extend(audits)
                completed += 1
                progress(f"{culture} {year} {name} saved")
    result = pd.DataFrame(all_rows)
    for _, group in result.groupby("culture"):
        assert_common_cohort(group, args.models)
    result.to_csv(args.output / "predictions.csv", index=False)
    summary = summarize(result)
    atomic_json(args.output / "summary.json", summary)
    pd.DataFrame(summary).to_csv(args.output / "summary.csv", index=False)
    atomic_json(args.output / "audit.json", all_audits)
    cohort_summary = {}
    for culture in args.cultures:
        subset = result[(result.culture == culture) & (result.year >= 2019)]
        current_keys = set(map(tuple, subset[["year", "dep"]].to_numpy()))
        old_keys = {(year, dep) for year, dep in old[culture] if year >= 2019}
        cohort_summary[culture] = {"old_n": len(old_keys), "modern_n": len(current_keys),
            "common_n": len(old_keys & current_keys),
            "old_only": [[int(year), dep] for year, dep in sorted(old_keys - current_keys)],
            "modern_only": [[int(year), dep] for year, dep in sorted(current_keys - old_keys)]}
    atomic_json(args.output / "cohorts.json", cohort_summary)
    progress("all crops complete", "completed")
    return result


def parser():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=ROOT / "experiments/multilegumes_benchmark")
    ap.add_argument("--cultures", nargs="+", choices=CULTURES, default=list(CULTURES))
    ap.add_argument("--models", nargs="+", choices=MODEL_NAMES, default=list(MODEL_NAMES))
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2016, 2026)))
    ap.add_argument("--samples", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--seasonal-file", type=Path)
    ap.add_argument("--seasonal-columns", nargs="+")
    return ap


if __name__ == "__main__":
    run(parser().parse_args())
