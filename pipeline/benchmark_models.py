"""Research benchmark; never overwrites production exports.

Temporal split, training-only deduplication, levels and weather preprocessing.
The fitted predictor is frozen before calibration. Pooled CQR is diagnostic:
dependent departments and nonstationary years preclude an IID coverage guarantee.
"""
import argparse
import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import time

import numpy as np
import pandas as pd
from sklearn.linear_model import QuantileRegressor

from benchmark_checkpoint import Checkpoints
from common import DATA, hypotheses
from model import WEATHER, hyp_values, sample_quantile

QS = np.array([0.1, 0.5, 0.9])
KINDS = ("trend", "linear", "lightgbm", "qrf", "catboost", "ensemble", "tabpfn")
DEFAULT_MODELS = ("trend", "linear", "lightgbm", "qrf", "ensemble")


def read_data():
    panel = pd.read_csv(DATA / "panel_rendements.csv", dtype={"dep": str, "serie_groupe": str})
    weather = pd.read_csv(DATA / "meteo_dept.csv", dtype={"dep": str})
    prices = pd.read_csv(DATA / "prix_ble.csv").rename(columns={"prix_eur_t": "prix_ble"})
    weather = weather.merge(prices[["annee", "prix_ble"]], on="annee", validate="many_to_one")
    # Deliberately ignore the full-period doublon and serie_groupe flags.
    raw = panel[panel.utilisable].merge(weather, on=["dep", "annee"], validate="many_to_one")
    return raw, weather


def representatives(history):
    """Same grouping rule as production, recomputed using supplied past only."""
    flagged = importlib.import_module("01_agreste").flag_duplicates(history.copy())
    return set(flagged.loc[flagged.dep == flagged.serie_groupe, "dep"])


class Features:
    def fit(self, df):
        self.centres = df.groupby("dep")[WEATHER].mean()
        self.fallback = df[WEATHER].mean()
        self.scale = df[WEATHER].std().replace(0, 1).fillna(1)
        return self

    def transform(self, df):
        centre = self.centres.reindex(df.dep).fillna(self.fallback).to_numpy()
        anomalies = (df[WEATHER].to_numpy() - centre) / self.scale.to_numpy()
        return np.column_stack([(df.annee.to_numpy() - 2010) / 10, anomalies])


class Predictor:
    def __init__(self, kind, seed=42, device="cpu"):
        self.kind, self.seed, self.device = kind, seed, device

    def fit(self, X, y):
        if self.kind == "trend":
            A = np.c_[np.ones(len(X)), X[:, 0]]
            self.coef = np.linalg.lstsq(A, y, rcond=None)[0]
            self.res = np.quantile(y - A @ self.coef, QS)
        elif self.kind == "linear":
            self.models = [QuantileRegressor(quantile=q, alpha=0.005, solver="highs").fit(X, y) for q in QS]
        elif self.kind == "lightgbm":
            from lightgbm import LGBMRegressor
            self.models = [LGBMRegressor(objective="quantile", alpha=q, n_estimators=150,
                learning_rate=0.05, num_leaves=7, max_depth=3, min_child_samples=20,
                verbosity=-1, n_jobs=1, random_state=self.seed).fit(X, y) for q in QS]
        elif self.kind == "qrf":
            from quantile_forest import RandomForestQuantileRegressor
            self.model = RandomForestQuantileRegressor(n_estimators=300, min_samples_leaf=5,
                max_features=0.8, max_depth=5, random_state=self.seed, n_jobs=1).fit(X, y)
        elif self.kind == "catboost":
            from catboost import CatBoostRegressor
            self.model = CatBoostRegressor(loss_function="MultiQuantile:alpha=0.1,0.5,0.9",
                iterations=300, depth=3, learning_rate=0.03, l2_leaf_reg=10,
                random_seed=self.seed, thread_count=1, verbose=False,
                allow_writing_files=False).fit(X, y)
        elif self.kind == "ensemble":
            self.models = [Predictor(k, self.seed, self.device).fit(X, y)
                           for k in ("linear", "lightgbm", "qrf")]
        elif self.kind == "tabpfn":
            from tabpfn import TabPFNRegressor
            from tabpfn.constants import ModelVersion
            self.model = TabPFNRegressor.create_default_for_version(
                ModelVersion.V3_5, device=self.device, random_state=self.seed).fit(X, y)
        else:
            raise ValueError(self.kind)
        return self

    def predict(self, X):
        if self.kind == "trend":
            q = (np.c_[np.ones(len(X)), X[:, 0]] @ self.coef)[:, None] + self.res
        elif self.kind == "qrf":
            q = self.model.predict(X, quantiles=QS.tolist())
        elif self.kind == "catboost":
            q = self.model.predict(X)
        elif self.kind == "tabpfn":
            q = np.column_stack(self.model.predict(X, output_type="quantiles", quantiles=QS.tolist()))
        elif self.kind == "ensemble":
            q = np.mean([m.predict(X) for m in self.models], axis=0)
        else:
            q = np.column_stack([m.predict(X) for m in self.models])
        return np.sort(q, axis=1)


def conformal_adjustment(scores, alpha=0.2):
    """Finite-sample order statistic, not a rounded interpolation quantile."""
    scores = np.asarray(scores)
    if not len(scores):
        raise ValueError("Empty calibration set")
    rank = int(np.ceil((len(scores) + 1) * (1 - alpha)))
    if rank > len(scores):
        raise ValueError("Too few calibration observations for a finite bound")
    # Widen only, preserving quantile order. This is conservative under IID CQR.
    return max(0., float(np.partition(scores, rank - 1)[rank - 1]))


class FrozenSplit:
    def __init__(self, kind, seed=42, device="cpu"):
        self.kind, self.seed, self.device = kind, seed, device

    def fit(self, history):
        years = sorted(history.annee.unique())
        if len(years) < 6:
            raise ValueError("Need at least six historical years")
        self.calibration_years = years[-3:]
        proper = history[history.annee < self.calibration_years[0]].copy()
        self.reps = representatives(proper)
        proper = proper[proper.dep.isin(self.reps)]
        counts = proper.groupby("dep").size()
        proper = proper[proper.dep.isin(counts[counts >= 3].index)]
        self.levels = proper.groupby("dep").rendement_qha.mean()
        cal = history[history.annee.isin(self.calibration_years) & history.dep.isin(self.levels.index)]
        self.features = Features().fit(proper)
        y = proper.rendement_qha.to_numpy() / self.levels.reindex(proper.dep).to_numpy()
        self.model = Predictor(self.kind, self.seed, self.device).fit(self.features.transform(proper), y)
        q = self.model.predict(self.features.transform(cal))
        yc = cal.rendement_qha.to_numpy() / self.levels.reindex(cal.dep).to_numpy()
        scores = np.maximum(q[:, 0] - yc, yc - q[:, 2])
        self.qhat = conformal_adjustment(scores)
        self.proper_years = sorted(proper.annee.unique())
        self.n_proper, self.n_cal = len(proper), len(cal)
        # DO NOT refit on calibration outcomes.
        return self

    def predict(self, df):
        q = self.model.predict(self.features.transform(df))
        q[:, 0] -= self.qhat
        q[:, 2] += self.qhat
        return np.clip(q, 0.02, None)


class RollingCalibrated(FrozenSplit):
    """Prequential residual calibration, followed by a fit on all past data.

    This deliberately IS NOT split CQR and has no finite-sample IID guarantee.
    Each calibration forecast has its own past-only levels, groups and features.
    It avoids freezing the predictor three years behind the decision date.
    """
    def fit_base(self, history):
        self.reps = representatives(history)
        proper = history[history.dep.isin(self.reps)]
        counts = proper.groupby("dep").size()
        proper = proper[proper.dep.isin(counts[counts >= 3].index)]
        self.levels = proper.groupby("dep").rendement_qha.mean()
        self.features = Features().fit(proper)
        y = proper.rendement_qha.to_numpy() / self.levels.reindex(proper.dep).to_numpy()
        self.model = Predictor(self.kind, self.seed, self.device).fit(self.features.transform(proper), y)
        self.proper_years = sorted(proper.annee.unique())
        self.n_proper = len(proper)
        self.qhat = 0.
        return self

    def fit(self, history):
        years = sorted(history.annee.unique())
        if len(years) < 6:
            raise ValueError("Need at least six historical years")
        self.calibration_years = years[-3:]
        scores, self.calibration_audit = [], []
        for year in self.calibration_years:
            base = RollingCalibrated(self.kind, self.seed, self.device).fit_base(history[history.annee < year])
            cal = history[(history.annee == year) & history.dep.isin(base.levels.index)]
            q = base.model.predict(base.features.transform(cal))
            y = cal.rendement_qha.to_numpy() / base.levels.reindex(cal.dep).to_numpy()
            scores.extend(np.maximum(q[:, 0] - y, y - q[:, 2]))
            self.calibration_audit.append({"year": int(year), "train_max": int(max(base.proper_years))})
        self.fit_base(history)
        self.qhat = conformal_adjustment(scores)
        self.n_cal = len(scores)
        return self


def quantile_loss(y, q, tau):
    e = np.asarray(y) - np.asarray(q)
    return np.maximum(tau * e, (tau - 1) * e)


def simulate(pool, mL, mW, dep, h, n=20000, seed=42):
    rng = np.random.default_rng(seed)
    qL, qW = mL.predict(pool), mW.predict(pool)
    ix = rng.integers(len(pool), size=n)
    yL = sample_quantile(qL[ix], rng.random(n)) * mL.levels[dep] / 10
    yW = sample_quantile(qW[ix], rng.random(n)) * mW.levels[dep] / 10
    numerator = pool.prix_ble.to_numpy()[ix] * yW - h["charges_ble"] + h["charges_lentille"] - h["bonus"]
    return np.quantile(numerator / yL, h["tau"], method="inverted_cdf")


def summarize(detail):
    rows = []
    for kind, d in detail.groupby("model"):
        # Years are the uncertainty unit, not department-year rows.
        yearly = d.groupby("year")[["contract_loss", "held", "price", "shortfall_eur_ha"]].mean()
        rng = np.random.default_rng(734)
        boot = yearly.held.to_numpy()[rng.integers(len(yearly), size=(10000, len(yearly)))].mean(axis=1)
        row = {"model": kind, "n": len(d), "years": len(yearly),
            "held": float(d.held.mean()), "held_year_mean": float(yearly.held.mean()),
            "held_year_bootstrap_80": np.quantile(boot, [.1, .9]).tolist(),
            "contract_loss": float(yearly.contract_loss.mean()),
            "median_price": float(d.price.median()),
            "shortfall_eur_ha": float(yearly.shortfall_eur_ha.mean())}
        for metric in ("pinball", "coverage", "width"):
            row[metric] = float(d.groupby("year")[metric].mean().mean()) if d[metric].notna().any() else None
        rows.append(row)
    return sorted(rows, key=lambda r: r["contract_loss"])


def run(args):
    raw, weather = read_data()
    h = hyp_values(hypotheses())
    L, W = raw[raw.culture == "lentille"], raw[raw.culture == "ble"]
    detail, audit = [], []
    args.output.mkdir(parents=True, exist_ok=True)
    checkpoints = Checkpoints(args, "rendements", [f"{y}-{k}" for y in args.years for k in [*args.models, "paired_history"]])
    started = time.monotonic()
    model_class = FrozenSplit if args.calibration == "split" else RollingCalibrated
    for year in args.years:
        keys = [f"{year}-{k}" for k in [*args.models, "paired_history"]]
        if all(checkpoints.get(key) is not None for key in keys):
            for key in keys:
                saved = checkpoints.get(key)
                detail.extend(saved["rows"])
                audit.extend(saved["audit"])
            checkpoints.progress(f"{year} repris depuis Drive/disque")
            continue
        checkpoints.progress(f"{year} · préparation blé et cohorte")
        pastL, pastW = L[L.annee < year], W[W.annee < year]
        wheat = model_class("linear", args.seed).fit(pastW)
        # Common evaluation cohort, independent of model choice.
        cohort_history = pastL
        if args.calibration == "split":
            cohort_history = pastL[pastL.annee < sorted(pastL.annee.unique())[-3]]
        counts = cohort_history[cohort_history.dep.isin(representatives(cohort_history))].groupby("dep").size()
        eligible = set(wheat.levels.index) & set(counts[counts >= 3].index)
        test = L[(L.annee == year) & L.dep.isin(eligible)]
        realW = W[W.annee == year].set_index("dep")
        test = test[test.dep.isin(realW.index)].sort_values("dep")
        for kind in args.models:
            key = f"{year}-{kind}"
            saved = checkpoints.get(key)
            if saved is not None:
                detail.extend(saved["rows"])
                audit.extend(saved["audit"])
                continue
            checkpoints.progress(f"{year} · {kind} · calibration et entraînement")
            start_row, start_audit = len(detail), len(audit)
            m = model_class(kind, args.seed, args.device).fit(pastL)
            assert set(test.dep).issubset(m.levels.index), "Model changed the evaluation cohort"
            q = m.predict(test)
            yr = test.rendement_qha.to_numpy() / m.levels.reindex(test.dep).to_numpy()
            audit.append({"year": year, "model": kind, "proper_years": [int(x) for x in m.proper_years],
                "calibration_years": [int(x) for x in m.calibration_years],
                "n_proper": m.n_proper, "n_cal": m.n_cal, "n_test": len(test), "qhat": m.qhat,
                "calibration_audit": getattr(m, "calibration_audit", [])})
            for i, (_, r) in enumerate(test.iterrows()):
                pool = weather[(weather.dep == r.dep) & (weather.annee < year)].copy()
                pool["annee"] = year  # trend projected, historical weather and price replayed
                price = simulate(pool, m, wheat, r.dep, h, args.samples, args.seed + year * 100)
                yL, yW = r.rendement_qha / 10, realW.loc[r.dep, "rendement_qha"] / 10
                realised = (r.prix_ble * yW - h["charges_ble"] + h["charges_lentille"] - h["bonus"]) / yL
                row = {"year": int(year), "dep": r.dep, "model": kind, "price": float(price),
                    "realised_break_even": float(realised), "held": bool(price >= realised),
                    "contract_loss": float(quantile_loss(realised, price, h["tau"])),
                    "shortfall_eur_ha": float(max(0, (realised - price) * yL)),
                    "pinball": float(quantile_loss(yr[i], q[i], QS).mean()),
                    "coverage": bool(q[i, 0] <= yr[i] <= q[i, 2]), "width": float(q[i, 2] - q[i, 0])}
                detail.append(row)
            checkpoints.save(key, {"rows": detail[start_row:], "audit": audit[start_audit:]})
            del m
        start_row = len(detail)
        # Joint historical yield-price baseline: paired observations, no independent residual draws.
        for _, r in test.iterrows():
            pair = pastL[pastL.dep == r.dep].merge(pastW[pastW.dep == r.dep], on="annee", suffixes=("_L", "_W"))
            R = (pair.prix_ble_L * pair.rendement_qha_W / 10 - h["charges_ble"] + h["charges_lentille"] - h["bonus"]) / (pair.rendement_qha_L / 10)
            ps = float(np.quantile(R, h["tau"], method="higher"))
            base = next(x for x in detail if x["year"] == year and x["dep"] == r.dep)
            real = base["realised_break_even"]
            detail.append({**base, "model": "paired_history", "price": ps, "held": ps >= real,
                "contract_loss": float(quantile_loss(real, ps, h["tau"])),
                "shortfall_eur_ha": float(max(0, (real - ps) * r.rendement_qha / 10)),
                "pinball": None, "coverage": None, "width": None})
        checkpoints.save(f"{year}-paired_history", {"rows": detail[start_row:], "audit": []})
        df = pd.DataFrame(detail)
        df.to_csv(args.output / "predictions.csv", index=False)
        print(f"{year}: {len(test)} departments; " + "; ".join(
            f"{k}: held={g.held.mean():.0%}, loss={g.contract_loss.mean():.1f}"
            for k, g in df[df.year == year].groupby("model")), flush=True)
    pd.DataFrame(detail).to_csv(args.output / "predictions.csv", index=False)
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"
    packages = {}
    for name in ("numpy", "pandas", "scipy", "scikit-learn", "lightgbm", "quantile-forest", "catboost", "tabpfn"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    result = {"status": "exploratory_not_unseen_validation", "source_commit": commit,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(), "packages": packages,
        "data_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in [DATA / n for n in ("panel_rendements.csv", "meteo_dept.csv", "prix_ble.csv", "hypotheses.yaml")]},
        "seed": args.seed, "samples": args.samples, "calibration": args.calibration,
        "models": args.models, "elapsed_seconds": time.monotonic() - started,
        "summary": summarize(pd.DataFrame(detail)), "audit": audit,
        "caveats": ["2019-2025 already examined: research comparison, not fresh confirmatory evidence.",
            "Dependent departments and temporal drift: no 80% population coverage guarantee.",
            "Historical data are latest-vintage, not publication-time snapshots.",
            "Training-only duplicate detection may miss groups with fewer than eight past matches.",
            "Conditional yield scores use realised weather; contract prices use historical weather only.",
            "Monte Carlo keeps independent crop residuals and three-quantile tail interpolation as controls.",
            "No validation of transfer to unobserved Ile-de-France lentil yields."]}
    (args.output / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    checkpoints.progress("Terminé", "complete")
    print(pd.DataFrame(result["summary"]).to_string(index=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", choices=KINDS, default=list(DEFAULT_MODELS))
    parser.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    parser.add_argument("--samples", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--calibration", choices=["split", "rolling"], default="split")
    parser.add_argument("--output", type=Path, default=Path("experiments/model_benchmark"))
    run(parser.parse_args())
