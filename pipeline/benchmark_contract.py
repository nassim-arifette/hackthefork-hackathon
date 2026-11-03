"""Learn the contract's required price directly, using only pre-season inputs.

Target R=(wheat revenue - wheat cost + lentil cost - support)/lentil yield.
Predict Q80(R), the actual business decision. No realised target-year weather.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import QuantileRegressor
from sklearn.preprocessing import StandardScaler

from benchmark_checkpoint import Checkpoints
from benchmark_models import read_data, representatives, quantile_loss, summarize
from common import hypotheses
from model import hyp_values

FEATURES = ["trend", "level_lentil", "level_wheat", "cv_lentil", "last_lentil",
            "last_wheat", "wheat_price", "wheat_price_change", "years_observed"]
MODELS = ("pooled", "linear", "lightgbm", "qrf", "tabpfn")


def make_examples(raw, weather, h, final_year=2026):
    """Every feature row is rebuilt from years strictly before its decision year."""
    L, W = raw[raw.culture == "lentille"], raw[raw.culture == "ble"]
    prices = weather.groupby("annee").prix_ble.first().sort_index()
    paired = L.merge(W[["dep", "annee", "rendement_qha"]], on=["dep", "annee"], suffixes=("_L", "_W"))
    rows = []
    for dep, observations in paired.groupby("dep"):
        observations = observations.sort_values("annee")
        for year in range(2013, final_year + 1):
            past = observations[observations.annee < year]
            if len(past) < 3:
                continue
            recent = past.tail(5)
            l = float(recent.rendement_qha_L.mean() / 10)
            w = float(recent.rendement_qha_W.mean() / 10)
            pp = prices[prices.index < year]
            p = float(pp.iloc[-1])
            baseline = max(1., (p * w - h["charges_ble"] + h["charges_lentille"] - h["bonus"]) / l)
            real = observations[observations.annee == year]
            target, actual_l = np.nan, np.nan
            if len(real):
                r = real.iloc[0]
                actual_l = float(r.rendement_qha_L / 10)
                target = float((r.prix_ble * r.rendement_qha_W / 10 - h["charges_ble"]
                                + h["charges_lentille"] - h["bonus"]) / actual_l)
            rows.append({"dep": dep, "year": year, "trend": (year - 2010) / 10,
                "level_lentil": l, "level_wheat": w,
                "cv_lentil": float(recent.rendement_qha_L.std() / recent.rendement_qha_L.mean()),
                "last_lentil": float(past.rendement_qha_L.iloc[-1] / 10 / l),
                "last_wheat": float(past.rendement_qha_W.iloc[-1] / 10 / w),
                "wheat_price": p, "wheat_price_change": p / float(pp.tail(3).mean()),
                "years_observed": len(past), "baseline": baseline,
                "target": target, "actual_lentil": actual_l})
    return pd.DataFrame(rows)


class DirectPrice:
    def __init__(self, kind, device="cpu"):
        self.kind, self.device = kind, device

    def fit(self, train):
        if (train.target <= 0).any():
            raise ValueError("Log-ratio model requires positive observed break-even prices")
        X = train[FEATURES].to_numpy()
        self.scaler = StandardScaler().fit(X)
        X = self.scaler.transform(X)
        y = np.log(train.target.to_numpy() / train.baseline.to_numpy())
        if self.kind == "pooled":
            # Give each historical year equal total weight.
            weights = 1 / train.groupby("year").year.transform("size").to_numpy()
            ix = np.argsort(y)
            self.value = y[ix][np.searchsorted(np.cumsum(weights[ix]) / weights.sum(), .8)]
        elif self.kind == "linear":
            self.model = QuantileRegressor(quantile=.8, alpha=.05, solver="highs").fit(X, y)
        elif self.kind == "lightgbm":
            from lightgbm import LGBMRegressor
            self.model = LGBMRegressor(objective="quantile", alpha=.8, n_estimators=150,
                num_leaves=5, max_depth=3, min_child_samples=20, learning_rate=.03,
                n_jobs=1, random_state=42, verbosity=-1).fit(X, y)
        elif self.kind == "qrf":
            from quantile_forest import RandomForestQuantileRegressor
            self.model = RandomForestQuantileRegressor(n_estimators=300, max_depth=5,
                min_samples_leaf=8, max_features=.8, n_jobs=1, random_state=42).fit(X, y)
        elif self.kind == "tabpfn":
            from tabpfn import TabPFNRegressor
            from tabpfn.constants import ModelVersion
            self.model = TabPFNRegressor.create_default_for_version(ModelVersion.V3_5,
                device=self.device, random_state=42).fit(X, y)
        else:
            raise ValueError(self.kind)
        return self

    def predict_logratio(self, rows):
        X = self.scaler.transform(rows[FEATURES].to_numpy())
        if self.kind == "pooled":
            return np.full(len(rows), self.value)
        if self.kind == "qrf":
            return np.asarray(self.model.predict(X, quantiles=.8)).reshape(-1)
        if self.kind == "tabpfn":
            return np.asarray(self.model.predict(X, output_type="quantiles", quantiles=[.8])[0])
        return self.model.predict(X)


def run(args):
    raw, weather = read_data()
    h = hyp_values(hypotheses())
    examples = make_examples(raw, weather, h)
    ref = pd.read_csv(args.reference, dtype={"dep": str}) if args.reference else None
    errors, rows, audit = [], [], []
    checkpoints = Checkpoints(args, "contrat direct", [f"{y}-{k}" for y in range(2016, 2026) for k in args.models])
    # Earlier out-of-time predictions serve only to calibrate later decisions.
    for year in range(2016, 2026):
        pastL = raw[(raw.culture == "lentille") & (raw.annee < year)]
        reps = representatives(pastL)
        train = examples[(examples.year < year) & examples.dep.isin(reps) & examples.target.notna()]
        test = examples[(examples.year == year) & examples.dep.isin(reps) & examples.target.notna()]
        if ref is not None and year >= 2019:
            cohort = set(ref.loc[ref.year == year, "dep"])
            test = test[test.dep.isin(cohort)]
            if set(test.dep) != cohort:
                raise ValueError(f"Direct and yield benchmarks have different cohorts in {year}")
        for kind in args.models:
            key = f"{year}-{kind}"
            saved = checkpoints.get(key)
            if saved is not None:
                errors.extend(saved["errors"])
                rows.extend(saved["rows"])
                audit.extend(saved["audit"])
                checkpoints.progress(key + " repris depuis Drive/disque")
                continue
            checkpoints.progress(f"{year} · {kind} · entraînement")
            start_error, start_row, start_audit = len(errors), len(rows), len(audit)
            model = DirectPrice(kind, args.device).fit(train)
            logp = model.predict_logratio(test)
            # Equal total weight per calendar year, signed one-sided correction.
            past_errors = [e for e in errors if e["kind"] == kind and year - 3 <= e["year"] < year]
            adjustment = 0.
            if past_errors:
                ed = pd.DataFrame(past_errors)
                weights = 1 / ed.groupby("year").year.transform("size").to_numpy()
                ix = np.argsort(ed.error.to_numpy())
                adjustment = float(ed.error.to_numpy()[ix][np.searchsorted(np.cumsum(weights[ix]) / weights.sum(), .8)])
            for i, (_, r) in enumerate(test.iterrows()):
                errors.append({"kind": kind, "year": year,
                               "error": float(np.log(r.target / r.baseline) - logp[i])})
                if year < 2019:
                    continue
                for calibrated, correction in [(False, 0.), (True, adjustment)]:
                    price = float(r.baseline * np.exp(logp[i] + correction))
                    rows.append({"year": year, "dep": r.dep,
                        "model": f"direct_{kind}" + ("_cal" if calibrated else ""),
                        "price": price, "realised_break_even": r.target, "held": price >= r.target,
                        "contract_loss": float(quantile_loss(r.target, price, .8)),
                        "shortfall_eur_ha": float(max(0, r.target - price) * r.actual_lentil),
                        "pinball": None, "coverage": None, "width": None})
            audit.append({"year": year, "model": kind, "train_max": int(train.year.max()),
                          "n_train": len(train), "n_test": len(test), "adjustment_log": adjustment})
            checkpoints.save(key, {"errors": errors[start_error:], "rows": rows[start_row:], "audit": audit[start_audit:]})
            del model
            if rows:
                pd.DataFrame(rows).to_csv(args.output / "predictions.csv", index=False)
        print(f"Direct contract: {year} complete", flush=True)
    detail = pd.DataFrame(rows)
    # Select using past years only, with a single business loss. No final-test cherry-picking.
    selected, selection_log = [], []
    for year in sorted(detail.year.unique()):
        validation = detail[(detail.year < year) & (detail.year >= year - 3)]
        if validation.empty:
            choice = "direct_pooled" if "pooled" in args.models else f"direct_{args.models[0]}"
        else:
            scores = validation.groupby(["model", "year"]).contract_loss.mean().groupby("model").mean()
            choice = scores.idxmin()
        selected.append(detail[(detail.year == year) & (detail.model == choice)].assign(model="direct_auto"))
        selection_log.append({"year": int(year), "chosen": choice})
    detail = pd.concat([detail, *selected], ignore_index=True)
    args.output.mkdir(parents=True, exist_ok=True)
    detail.to_csv(args.output / "predictions.csv", index=False)
    result = {"objective": "pinball_0.8_of_realised_break_even_price", "features": FEATURES,
        "forecast_time": "before_target_year_no_future_weather", "summary": summarize(detail),
        "audit": audit, "selection": selection_log, "models": args.models,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in [Path(__file__).resolve().parents[1] / "data" / n
                                   for n in ("panel_rendements.csv", "meteo_dept.csv", "prix_ble.csv", "hypotheses.yaml")]},
        "packages": {name: importlib.metadata.version(name) for name in ["numpy", "pandas", "scikit-learn", "lightgbm", "quantile-forest"]}}
    (args.output / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    checkpoints.progress("Terminé", "complete")
    print(pd.DataFrame(result["summary"]).to_string(index=False), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS[:-1]))
    p.add_argument("--device", default="cpu")
    p.add_argument("--reference", type=Path, default=Path("experiments/model_benchmark_rolling/predictions.csv"))
    p.add_argument("--output", type=Path, default=Path("experiments/contract_benchmark"))
    run(p.parse_args())
