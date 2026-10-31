"""Data/preprocessing/distribution ablations with past-only economic decisions.

Every arm uses the same original observed cohort, economic assumptions, weather
year draws and wheat-price pairing. The first two arms reproduce the published
M0 and seasonal QRF exactly. Every primary ablation shares its linear wheat
model. ``qrf_wheat_dense`` explicitly changes that comparator yield model too.

2016--2018 supply out-of-time calibration and dependence diagnostics; reported
evaluation starts in 2019. Current observed weather is used ONLY for diagnostic
yield predictions. Contract prices replay earlier weather/prices, with the
trend feature set to the target year. Hyperparameter selection belongs to the
separate ``analyze_advanced`` temporal economic selector, never to this script.

Dense quantile tails are linearly extrapolated from the outer two grid points,
then floored at relative yield .02. Gaussian dependence uses past standardized
out-of-time residuals, shrunk n/(n+30), clipped to +/- .8, with n<20 falling back
to independence. The empirical alternative samples paired residual-rank cells
with independent uniform jitter (checkerboard empirical copula), preserving
uniform marginals. It is not an in-sample correlation or future weather oracle.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd
from scipy.special import ndtr, ndtri

from advanced_models import AdvancedYieldModel, DENSE_QUANTILES, THREE_QUANTILES
from advanced_weather import advanced_columns
from benchmark_multilegumes import (CONTRACTS, assert_common_cohort, atomic_json,
                                    evaluate_contract, legacy_keys, summarize)
from contract_economics import accepted_yield, signed_required_income
from crop_weather import seasonal_columns
from fetch_sim_features import sim_columns
from multicrop_models import (CULTURES, ROOT, WEATHER, YieldModel, prepare_training,
                              read_data, sample_quantile, scenario_draws)


SOIL_COLUMNS = ("soil_ru_mean_mm", "soil_ru_sd_spatial_mm", "soil_ru_q10_mm", "soil_ru_q90_mm",
                "soil_depth_mean_cm", "soil_field_capacity_pct", "soil_wilting_point_pct")
OPTIONAL_FILES = ("meteo_advanced_cultures.csv", "sim_features.csv",
                  "sim_agri_features.csv", "soil_features.csv")
DEPENDENCE_MIN_N = 20
DEPENDENCE_SHRINKAGE = 30
RELATIVE_IQR_FLOOR = .05


def candidate_registry():
    """Finite, prespecified search space; no candidates depend on test scores."""
    result = {
        "trend": {"legacy": "trend", "feature_group": "legacy", "distribution": "three",
                  "ablation_parent": None},
        "qrf_seasonal": {"legacy": "qrf", "feature_group": "seasonal", "distribution": "three",
                         "ablation_parent": "trend"},
    }

    def add(name, group="soil", family="qrf", dense=True, parent="qrf_soil_dense",
            params=None, **extra):
        model_spec = {"family": family, "quantiles": list(DENSE_QUANTILES if dense else THREE_QUANTILES)}
        if params:
            model_spec["params"] = params
        for key in ("target_normalization", "shrinkage_strength", "feature_mode"):
            if key in extra:
                model_spec[key] = extra.pop(key)
        result[name] = {"feature_group": group, "distribution": "dense" if dense else "three",
                        "model_spec": model_spec, "ablation_parent": parent, **extra}

    add("trend_dense", group="legacy", family="trend", parent="trend")
    add("trend_joint_gaussian", group="legacy", family="trend", parent="trend_dense", dependence="gaussian")
    add("trend_joint_empirical", group="legacy", family="trend", parent="trend_dense", dependence="empirical_checkerboard")
    preceding = "qrf_seasonal"
    for group in ("combined", "nasa", "sim", "soil"):
        add(f"qrf_{group}_sparse", group=group, dense=False, parent=preceding)
        preceding = f"qrf_{group}_sparse"
    for group in ("combined", "nasa", "sim", "soil"):
        add(f"qrf_{group}_dense", group=group, parent=f"qrf_{group}_sparse")
    add("qrf_soil_absolute", feature_mode="absolute_anomaly")
    add("qrf_soil_shrinkage", target_normalization="shrinkage", shrinkage_strength=5)
    for leaf, depth in ((3, 3), (3, 8), (5, 8), (10, 3), (10, 8)):
        add(f"qrf_leaf{leaf}_depth{depth}", params={"min_samples_leaf": leaf, "max_depth": depth})
    add("qrf_features05", params={"max_features": .5})
    add("lgb_sparse", family="lightgbm", dense=False, parent="qrf_soil_sparse")
    add("lgb_dense", family="lightgbm", parent="lgb_sparse")
    add("lgb_leaf15", family="lightgbm", parent="lgb_dense",
        params={"num_leaves": 15, "max_depth": 4, "n_estimators": 250, "min_child_samples": 10})
    add("cat_sparse", family="catboost", dense=False, parent="qrf_soil_sparse")
    add("cat_dense", family="catboost", parent="cat_sparse")
    add("cat_depth6", family="catboost", parent="cat_dense",
        params={"depth": 6, "iterations": 500, "l2_leaf_reg": 10})
    add("qrf_lgb_mixture", mixture=["qrf_soil_dense", "lgb_dense"])
    add("qrf_joint_gaussian", dependence="gaussian")
    add("qrf_joint_empirical", dependence="empirical_checkerboard")
    add("qrf_agri_sparse", group="agri", dense=False, parent="qrf_soil_sparse")
    add("qrf_agri_dense", group="agri", parent="qrf_soil_dense")
    add("qrf_cropsoil_dense", group="cropsoil", parent="qrf_soil_dense")
    add("qrf_wheat_dense", wheat_variant="qrf_sim_dense")
    return result


def feature_columns(culture, group):
    static = ()
    if group == "legacy":
        return tuple(WEATHER), static
    if group == "seasonal":
        return seasonal_columns(culture), static
    dynamic = tuple(WEATHER) + seasonal_columns(culture)
    if group in ("nasa", "sim", "soil", "agri", "cropsoil"):
        dynamic += advanced_columns(culture)
    if group in ("sim", "soil", "agri", "cropsoil"):
        dynamic += sim_columns(culture, tag="sim_agri" if group == "agri" else "sim")
    if group in ("soil", "agri"):
        static = SOIL_COLUMNS
    if group == "cropsoil":
        static = tuple(f"{culture}_rpg_{column}" for column in SOIL_COLUMNS) + (f"{culture}_rpg_soil_fallback",)
    return dynamic, static


def load_data(data_dir):
    data_dir = Path(data_dir)
    seasonal = data_dir / "meteo_saisonnier_cultures.csv"
    raw, weather = read_data(data_dir, seasonal_file=seasonal if seasonal.exists() else None)
    files = []
    for name in OPTIONAL_FILES:
        path = data_dir / name
        if name == "sim_agri_features.csv" and not path.exists():
            path = data_dir / "sim_agricultural_features.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path, dtype={"dep": str})
        keys = ["dep", "annee"] if "annee" in frame else ["dep"]
        if frame.duplicated(keys).any():
            raise ValueError(f"Duplicate feature keys in {path}")
        additions = [c for c in frame if c not in weather or c in keys]
        weather = weather.merge(frame[additions], on=keys, how="left", validate="many_to_one")
        raw = raw.merge(frame[additions], on=keys, how="left", validate="many_to_one")
        files.append(path)
    crop_soil_path = data_dir / "soil_features_crop.csv"
    if crop_soil_path.exists() and set(SOIL_COLUMNS).issubset(weather):
        crop_soil = pd.read_csv(crop_soil_path, dtype={"dep": str})
        if crop_soil.duplicated(["dep", "culture"]).any():
            raise ValueError("Duplicate department/crop soil keys")
        base = weather[["dep", *SOIL_COLUMNS]].drop_duplicates().set_index("dep")
        if base.index.has_duplicates:
            raise ValueError("General soil covariates must be static within a department")
        additions = pd.DataFrame(index=base.index)
        for culture in CULTURES:
            selected = crop_soil[crop_soil.culture == culture].set_index("dep").reindex(base.index)
            missing = selected[list(SOIL_COLUMNS)].isna().any(axis=1)
            for column in SOIL_COLUMNS:
                additions[f"{culture}_rpg_{column}"] = selected[column].where(~missing, base[column])
            additions[f"{culture}_rpg_soil_fallback"] = missing.astype(float)
        additions = additions.reset_index()
        weather = weather.merge(additions, on="dep", how="left", validate="many_to_one")
        raw = raw.merge(additions, on="dep", how="left", validate="many_to_one")
        files.append(crop_soil_path)
    return raw, weather, files


def available_candidates(registry, raw, weather, cultures, requested=None):
    selected, unavailable = {}, {}
    unknown = set(requested or ()) - set(registry)
    if unknown:
        raise ValueError(f"Unknown candidate names: {sorted(unknown)}")
    for name, spec in registry.items():
        errors = []
        for culture in cultures:
            columns, static = feature_columns(culture, spec["feature_group"])
            needed = list(columns + static)
            if spec.get("wheat_variant"):
                needed += list(sim_columns("ble"))
            missing = sorted(set(needed) - set(weather))
            if missing:
                errors.append(f"{culture}: absent columns {','.join(missing)}")
            elif not np.isfinite(weather[needed].to_numpy(dtype=float)).all():
                errors.append(f"{culture}: missing or nonfinite feature observations")
        if errors:
            unavailable[name] = errors
        elif requested is None or name in requested:
            selected[name] = deepcopy(spec)
    absent_requested = set(requested or ()) & set(unavailable)
    if absent_requested:
        raise ValueError("Requested data unavailable: " + json.dumps(
            {name: unavailable[name] for name in sorted(absent_requested)}))
    if not selected:
        raise ValueError("No candidate has usable input data")
    return selected, unavailable


def crop_hypotheses(culture, data_dir):
    """Read the chosen data directory, without silently using another scenario."""
    import yaml
    from model import hyp_values
    h = hyp_values(yaml.safe_load((Path(data_dir) / "hypotheses.yaml").read_text()))
    if culture != "lentille":
        c = yaml.safe_load((Path(data_dir) / "cultures.yaml").read_text())[culture]
        h.update(charges_lentille=c["charges_eur_ha"]["valeur"], aide=c["aide_eur_ha"]["valeur"],
                 rotation=c["rotation_eur_ha"]["valeur"], qualite=c["part_refusee"]["valeur"])
        h["bonus"] = h["aide"] + h["rotation"]
    h["charges_culture"] = h["charges_lentille"]
    return h


def inverse_quantiles(q, u, grid, floor=.02):
    """Row-wise inverse CDF, linear interpolation and explicit linear tails."""
    q, u, grid = np.asarray(q, dtype=float), np.asarray(u, dtype=float), np.asarray(grid, dtype=float)
    if q.shape != (len(u), len(grid)) or len(grid) < 2 or np.any(np.diff(grid) <= 0):
        raise ValueError("Invalid quantile sampler shapes or grid")
    if not np.isfinite(q).all() or not np.isfinite(u).all() or np.any((u < 0) | (u > 1)):
        raise ValueError("Quantile sampler requires finite values and uniforms in [0,1]")
    if np.any(np.diff(q, axis=1) < 0):
        raise ValueError("Quantile predictions must be ordered")
    if np.array_equal(grid, THREE_QUANTILES):
        return sample_quantile(q, u)
    upper = np.searchsorted(grid, u, side="right").clip(1, len(grid) - 1)
    lower = upper - 1
    row = np.arange(len(u))
    out = q[row, lower] + (u - grid[lower]) / (grid[upper] - grid[lower]) * (
        q[row, upper] - q[row, lower])
    return np.maximum(out, floor)


def dependence_history(diagnostics, culture, model, year):
    rows = [r for r in diagnostics if r["culture"] == culture and r["model"] == model
            and r["year"] < year]
    if not rows:
        return np.empty((0, 2)), {"rho": 0., "dependence_n": 0,
                                  "dependence_max_year": None, "dependence_fallback": True}
    data = pd.DataFrame(rows).sort_values(["year", "dep"]).drop_duplicates(["year", "dep"])
    pairs = data[["crop_residual_standardized", "wheat_residual_standardized"]].to_numpy()
    finite = np.isfinite(pairs).all(axis=1)
    pairs = pairs[finite]
    n = len(pairs)
    valid = n >= DEPENDENCE_MIN_N and np.all(np.std(pairs, axis=0) > 1e-12)
    raw_rho = float(np.corrcoef(pairs.T)[0, 1]) if valid else 0.
    rho = float(np.clip(raw_rho * n / (n + DEPENDENCE_SHRINKAGE), -.8, .8))
    return pairs, {"rho": rho, "dependence_n": n,
                   "dependence_max_year": int(data.loc[finite, "year"].max()) if n else None,
                   "dependence_fallback": not valid}


def coupled_uniforms(u_crop, u_wheat, pairs, metadata, method, year, dep, seed):
    if not method or metadata["dependence_fallback"]:
        return u_crop, u_wheat
    if method == "gaussian":
        eps = np.finfo(float).eps
        zc = ndtri(np.clip(u_crop, eps, 1 - eps))
        zw = ndtri(np.clip(u_wheat, eps, 1 - eps))
        rho = metadata["rho"]
        return u_crop, ndtr(rho * zc + np.sqrt(1 - rho * rho) * zw)
    if method != "empirical_checkerboard":
        raise ValueError(f"Unknown dependence method {method}")
    rng = np.random.default_rng(np.random.SeedSequence([seed, int(year), int(str(dep), 36), 572]))
    n = len(pairs)
    ranks = np.empty((n, 2), dtype=int)
    for column in range(2):
        # Independent tie breaking keeps each marginal permutation uniform.
        order = np.lexsort((rng.random(n), pairs[:, column]))
        ranks[order, column] = np.arange(n)
    donor = rng.integers(n, size=len(u_crop))
    return (ranks[donor, 0] + u_crop) / n, (ranks[donor, 1] + u_wheat) / n


def create_manifest(args, candidates, unavailable, extra_files):
    modules = ("benchmark_advanced.py", "advanced_models.py", "advanced_weather.py", "crop_weather.py",
               "fetch_sim_features.py", "multicrop_models.py", "benchmark_multilegumes.py",
               "contract_economics.py", "common.py", "model.py")
    files = [ROOT / "pipeline" / name for name in modules]
    files += [args.data_dir / name for name in ("panel_rendements.csv", "meteo_dept_cultures.csv",
        "prix_ble.csv", "hypotheses.yaml", "cultures.yaml", "meteo_saisonnier_cultures.csv")]
    files += list(extra_files)
    files += [args.data_dir / name for name in ("sim_manifest.json", "sim_agri_manifest.json",
        "soil_manifest.json", "soil_crop_manifest.json", "soil_rpg_manifest.json", "meteo_advanced_manifest.json")
        if (args.data_dir / name).exists()]
    packages = {}
    for name in ("numpy", "pandas", "scipy", "scikit-learn", "quantile-forest", "lightgbm", "catboost", "PyYAML"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    options = {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()
               if k not in ("output", "data_dir")}
    spec = {"options": options, "candidates": candidates, "unavailable_candidates": unavailable,
        "packages": packages, "files": {("pipeline/" if p.parent == ROOT / "pipeline" else "data/") + p.name:
            hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()},
        "target": .8, "evaluation_years": [y for y in args.years if y >= 2019],
        "dense_distribution": "13 fitted quantiles; linear tails; relative-yield floor .02",
        "wheat_primary": "published linear six-feature model, common to primary arms",
        "mixture": "50/50 distribution mixture using disjoint uniform intervals, not mean quantiles",
        "dependence": {"source": "previous out-of-time standardized yield residuals only",
            "min_n": DEPENDENCE_MIN_N, "rho_shrinkage": DEPENDENCE_SHRINKAGE,
            "rho_clip": .8, "residual_iqr_floor": RELATIVE_IQR_FLOOR},
        "static_map_availability": "Current static soil map is retrospective environmental information; "
            "2019-2025 evaluation does not claim the map was published before every contract. "
            "Separate 2023-2025 sensitivity must be reported.",
        "agricultural_weights": "CORINE2012 agricultural-area weights for sim_agri. "
            "The separate cropsoil arm uses RPG2015 crop soil weights, with explicit department-soil "
            "fallback when missing (all haricot cases, no 2015PHS records in supplied extract)."}
    signature = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    path = args.output / "manifest.json"
    if path.exists() and json.loads(path.read_text())["signature"] != signature:
        raise ValueError("Source/data/options changed; use a new output directory")
    atomic_json(path, {"signature": signature, "spec": spec})
    return signature


def run(args):
    args.output, args.data_dir = Path(args.output), Path(args.data_dir)
    args.output.mkdir(parents=True, exist_ok=True)
    if args.samples < 1 or not args.years or len(set(args.years)) != len(args.years):
        raise ValueError("Positive sample count and unique nonempty years are required")
    raw, weather, extra_files = load_data(args.data_dir)
    registry = candidate_registry()
    candidates, unavailable = available_candidates(registry, raw, weather, args.cultures, args.models)
    signature = create_manifest(args, candidates, unavailable, extra_files)
    checkpoints = args.output / "checkpoints"
    checkpoints.mkdir(exist_ok=True)
    wheat = raw[raw.culture == "ble"]
    old = {crop: legacy_keys(raw, crop, args.years) for crop in args.cultures}
    all_rows, all_audits, diagnostics = [], [], []
    started, completed = time.monotonic(), 0
    total = len(args.cultures) * len(args.years) * len(candidates)

    def progress(active, status="running"):
        record = {"status": status, "completed": completed, "total": total,
                  "active": active, "elapsed_seconds": round(time.monotonic() - started, 1)}
        atomic_json(args.output / "progress.json", record)
        print(json.dumps(record), flush=True)

    for year in sorted(args.years):
        wheat_model, wheat_advanced = None, None
        real_wheat = wheat[wheat.annee == year].set_index("dep")
        for culture in args.cultures:
            paths = {name: checkpoints / f"{culture}-{year}-{name}.json" for name in candidates}
            if all(path.exists() for path in paths.values()):
                for name, path in paths.items():
                    saved = json.loads(path.read_text())
                    if saved["signature"] != signature:
                        raise ValueError(f"Incompatible checkpoint {path}")
                    all_rows.extend(saved["rows"])
                    all_audits.extend(saved["audits"])
                    diagnostics.extend(saved["diagnostics"])
                    completed += 1
                    progress(f"{culture} {year} {name} resumed")
                continue
            if wheat_model is None:
                wheat_model = YieldModel("linear", args.seed, args.threads).fit(wheat[wheat.annee < year])
            crop = raw[raw.culture == culture]
            history = crop[crop.annee < year]
            prepared = prepare_training(history)
            common = set(prepared.levels.index) & set(wheat_model.levels.index) & set(real_wheat.index)
            test = crop[(crop.annee == year) & crop.dep.isin(common)].sort_values("dep")
            if test.empty:
                raise ValueError(f"No common held-out observations for {culture}/{year}")
            h = crop_hypotheses(culture, args.data_dir)
            local_history = history.groupby("dep").rendement_qha.agg(["size", "mean", "std"])
            fitted = {}

            def fit_candidate(spec):
                columns, static = feature_columns(culture, spec["feature_group"])
                model_spec = deepcopy(spec.get("model_spec", {}))
                # QRF training is independent of requested prediction quantiles.
                if model_spec.get("family") == "qrf":
                    model_spec["quantiles"] = list(DENSE_QUANTILES)
                key = json.dumps({"legacy": spec.get("legacy"), "spec": model_spec,
                                  "columns": columns, "static": static}, sort_keys=True)
                if key not in fitted:
                    if spec.get("legacy"):
                        fitted[key] = YieldModel(spec["legacy"], args.seed, args.threads).fit(history, columns)
                    else:
                        fitted[key] = AdvancedYieldModel(model_spec, args.seed, args.threads).fit(history, columns, static)
                    if set(fitted[key].levels.index) != set(prepared.levels.index):
                        raise AssertionError("Candidate altered the baseline cohort")
                return fitted[key]

            for name, spec in candidates.items():
                path = paths[name]
                if path.exists():
                    saved = json.loads(path.read_text())
                    if saved["signature"] != signature:
                        raise ValueError(f"Incompatible checkpoint {path}")
                    all_rows.extend(saved["rows"])
                    all_audits.extend(saved["audits"])
                    diagnostics.extend(saved["diagnostics"])
                    completed += 1
                    progress(f"{culture} {year} {name} resumed")
                    continue
                progress(f"{culture} {year} {name} fitting")
                model = fit_candidate(spec)
                mixture = [fit_candidate(registry[n]) for n in spec.get("mixture", ())]
                selected_wheat = wheat_model
                if spec.get("wheat_variant"):
                    if wheat_advanced is None:
                        wheat_advanced = AdvancedYieldModel({"family": "qrf"}, args.seed, args.threads).fit(
                            wheat[wheat.annee < year], tuple(WEATHER) + sim_columns("ble"), SOIL_COLUMNS)
                    selected_wheat = wheat_advanced
                q_test = model.predict_quantiles(test)
                if mixture:
                    # Deterministic quadrature is used only for mixture diagnostics.
                    uq = (np.arange(1024) + .5) / 1024
                    parts = []
                    for part in mixture:
                        predictions = part.predict_distribution(test, DENSE_QUANTILES)
                        parts.append(np.vstack([inverse_quantiles(np.repeat(q[None, :], len(uq), axis=0),
                                                                  uq, DENSE_QUANTILES) for q in predictions]))
                    q_test = np.quantile(np.column_stack(parts), THREE_QUANTILES, axis=1).T
                q_wheat_test = selected_wheat.predict_quantiles(test)
                pairs, dep_meta = dependence_history(diagnostics, culture, name, year)
                if not spec.get("dependence"):
                    dep_meta = {"rho": 0., "dependence_n": 0, "dependence_max_year": None,
                                "dependence_fallback": True}
                rows, current_diagnostics = [], []
                for index, (_, observation) in enumerate(test.iterrows()):
                    dep = observation.dep
                    pool = weather[(weather.dep == dep) & (weather.annee < year)].sort_values("annee").copy()
                    historical_years = list(map(int, pool.annee))
                    pool["annee"] = year
                    ix, uc, uw = scenario_draws(len(pool), year, dep, args.samples, args.seed)
                    uc, uw = coupled_uniforms(uc, uw, pairs, dep_meta, spec.get("dependence"), year, dep, args.seed)
                    grid = DENSE_QUANTILES if spec["distribution"] == "dense" else THREE_QUANTILES
                    if mixture:
                        # Independent component assignment and conditional uniform by partition.
                        first = uc < .5
                        within = np.where(first, uc * 2, (uc - .5) * 2)
                        samples = [inverse_quantiles(part.predict_distribution(pool, grid)[ix], within, grid)
                                   * part.levels[dep] / 10 for part in mixture]
                        yc = np.where(first, samples[0], samples[1])
                    else:
                        q_pool = (model.predict_quantiles(pool) if spec.get("legacy")
                                  else model.predict_distribution(pool, grid))
                        yc = inverse_quantiles(q_pool[ix], uc, grid) * model.levels[dep] / 10
                    if spec.get("wheat_variant"):
                        yw = inverse_quantiles(selected_wheat.predict_distribution(pool, DENSE_QUANTILES)[ix],
                                               uw, DENSE_QUANTILES) * selected_wheat.levels[dep] / 10
                    else:
                        yw = sample_quantile(wheat_model.predict_quantiles(pool)[ix], uw) * wheat_model.levels[dep] / 10
                    pw = pool.prix_ble.to_numpy()[ix]
                    net = accepted_yield(yc, h["qualite"])
                    need = signed_required_income(pw, yw, h["charges_ble"], h["charges_culture"], h["aide"], h["rotation"])
                    actual_net = accepted_yield(observation.rendement_qha / 10, h["qualite"])
                    actual_wheat = float(real_wheat.loc[dep, "rendement_qha"] / 10)
                    actual_price = float(observation.prix_ble)
                    actual_need = signed_required_income(actual_price, actual_wheat, h["charges_ble"],
                        h["charges_culture"], h["aide"], h["rotation"])
                    # Fixed common tier boundaries: target shrinkage must not change actual contracts.
                    past_net = float(accepted_yield(prepared.levels[dep] / 10, h["qualite"]))
                    actual_relative = float(observation.rendement_qha / model.levels[dep])
                    q, qw = q_test[index], q_wheat_test[index]
                    error = actual_relative - q
                    pinball = float(np.maximum(np.asarray(THREE_QUANTILES) * error,
                        (np.asarray(THREE_QUANTILES) - 1) * error).mean())
                    crop_residual = float((actual_relative - q[1]) / max(q[2] - q[0], RELATIVE_IQR_FLOOR))
                    wheat_relative = actual_wheat * 10 / selected_wheat.levels[dep]
                    wheat_residual = float((wheat_relative - qw[1]) / max(qw[2] - qw[0], RELATIVE_IQR_FLOOR))
                    diagnostic = {"culture": culture, "year": int(year), "dep": dep, "model": name,
                                  "crop_residual_standardized": crop_residual,
                                  "wheat_residual_standardized": wheat_residual}
                    current_diagnostics.append(diagnostic)
                    common_row = {"culture": culture, "year": int(year), "dep": dep,
                        "region": observation.region, "model": name, "old_cohort": (int(year), dep) in old[culture],
                        "evaluation": year >= 2019, "accepted_yield_actual": float(actual_net),
                        "actual_crop_yield_raw": float(observation.rendement_qha / 10),
                        "actual_wheat_yield": actual_wheat, "actual_wheat_price": actual_price,
                        "actual_need_eur_ha": float(actual_need), "realised_break_even": float(actual_need / actual_net),
                        "past_mean_accepted": past_net, "refused_fraction": h["qualite"],
                        "history_n": int(local_history.loc[dep, "size"]),
                        "history_mean_qha": float(local_history.loc[dep, "mean"]),
                        "history_cv": float(local_history.loc[dep, "std"] / local_history.loc[dep, "mean"]),
                        "q10_rel": float(q[0]), "q50_rel": float(q[1]), "q90_rel": float(q[2]),
                        "q10_t_ha": float(q[0] * model.levels[dep] / 10),
                        "q50_t_ha": float(q[1] * model.levels[dep] / 10),
                        "q90_t_ha": float(q[2] * model.levels[dep] / 10),
                        "actual_rel": actual_relative,
                        "yield_pinball_raw": pinball,
                        "yield_pinball_t_ha": float(pinball * model.levels[dep] / 10),
                        "yield_coverage80_raw": bool(q[0] <= actual_relative <= q[2]),
                        "simulation_history_max": max(historical_years),
                        "dependence_method": spec.get("dependence", "independent"), **dep_meta,
                        "crop_residual_standardized": crop_residual,
                        "wheat_residual_standardized": wheat_residual}
                    for shape in CONTRACTS:
                        rows.append(common_row | evaluate_contract(shape, need, net, pw, past_net,
                            actual_need, actual_net, actual_price, h["tau"]))
                audit = {"culture": culture, "year": int(year), "model": name,
                    "training_years": prepared.years, "training_max": max(prepared.years),
                    "n_train": prepared.n, "n_departments_train": len(prepared.levels),
                    "n_test": len(test), "test_departments": test.dep.tolist(),
                    "representatives": sorted(prepared.representatives),
                    "features": list(model.features.columns),
                    "static_features": list(getattr(model.features, "static_columns", ())),
                    "wheat_n_train": selected_wheat.prepared.n,
                    "wheat_departments_train": len(selected_wheat.levels),
                    "hypotheses": h, "candidate": spec, **dep_meta}
                assert_common_cohort(pd.DataFrame(rows), [name])
                atomic_json(path, {"signature": signature, "rows": rows, "audits": [audit],
                                   "diagnostics": current_diagnostics})
                all_rows.extend(rows)
                all_audits.append(audit)
                diagnostics.extend(current_diagnostics)
                completed += 1
                progress(f"{culture} {year} {name} saved")
    result = pd.DataFrame(all_rows)
    for _, group in result.groupby("culture"):
        assert_common_cohort(group, list(candidates))
    result.to_csv(args.output / "predictions.csv", index=False)
    summary = summarize(result)
    atomic_json(args.output / "summary.json", summary)
    pd.DataFrame(summary).to_csv(args.output / "summary.csv", index=False)
    atomic_json(args.output / "audit.json", all_audits)
    pd.DataFrame(diagnostics).to_csv(args.output / "residual_diagnostics.csv", index=False)
    cohorts = {}
    for culture in args.cultures:
        subset = result[(result.culture == culture) & (result.year >= 2019)]
        current = set(map(tuple, subset[["year", "dep"]].to_numpy()))
        previous = {(year, dep) for year, dep in old[culture] if year >= 2019}
        cohorts[culture] = {"old_n": len(previous), "modern_n": len(current), "common_n": len(current & previous),
            "old_only": [[int(y), d] for y, d in sorted(previous - current)],
            "modern_only": [[int(y), d] for y, d in sorted(current - previous)]}
    atomic_json(args.output / "cohorts.json", cohorts)
    progress("all crops complete", "completed")
    return result


def parser():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=ROOT / "experiments/advanced_benchmark")
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data")
    ap.add_argument("--cultures", nargs="+", choices=CULTURES, default=list(CULTURES))
    ap.add_argument("--models", nargs="+", default=None, help="Default: all data-available prespecified candidates")
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2016, 2026)))
    ap.add_argument("--samples", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--threads", type=int, default=1)
    return ap


if __name__ == "__main__":
    run(parser().parse_args())
