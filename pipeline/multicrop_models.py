"""Past-only yield models for the five-crop contract benchmark.

The three raw quantiles define the simulated distribution. Interval calibration
is deliberately absent: the economic decision is calibrated in a separate step.
Production exports and the historical M1 implementation are not modified.
"""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import QuantileRegressor


ROOT = Path(__file__).resolve().parents[1]
WEATHER = ("pluie_mj", "pluie_avj", "j30_jj", "gel_tardif", "pluie_recolte", "tmax_mj")
QUANTILES = (.1, .5, .9)
MODEL_NAMES = ("trend", "linear", "qrf", "qrf_seasonal", "lightgbm_seasonal", "catboost_seasonal")
CULTURES = ("lentille", "pois_chiche", "haricot", "pois", "feverole")


def read_data(data_dir=ROOT / "data", seasonal_file=None):
    """Read usable measurements; ignore full-period duplicate flags for fitting."""
    data_dir = Path(data_dir)
    panel = pd.read_csv(data_dir / "panel_rendements.csv", dtype={"dep": str, "serie_groupe": str})
    weather = pd.read_csv(data_dir / "meteo_dept_cultures.csv", dtype={"dep": str})
    prices = pd.read_csv(data_dir / "prix_ble.csv").rename(columns={"prix_eur_t": "prix_ble"})
    weather = weather.merge(prices[["annee", "prix_ble"]], on="annee", validate="many_to_one")
    if seasonal_file is not None:
        seasonal = pd.read_csv(seasonal_file, dtype={"dep": str})
        extra = [column for column in seasonal if column not in weather or column in ("dep", "annee")]
        weather = weather.merge(seasonal[extra], on=["dep", "annee"], how="left", validate="one_to_one")
    raw = panel[panel.utilisable].merge(weather, on=["dep", "annee"], validate="many_to_one")
    return raw, weather


def representatives(history, minimum_equal_years=8):
    """Agreste grouping rebuilt from the supplied usable history only.

    Eight equal positive annual yields (rounded to .01 q/ha) connect two
    departments. The largest historical mean cultivated area represents each
    connected component. This is the production rule, with no future data.
    """
    if history.empty:
        return set()
    if history.culture.nunique() != 1:
        raise ValueError("Representatives require exactly one crop")
    wide = history.pivot(index="dep", columns="annee", values="rendement_qha").round(2).sort_index()
    values, deps = wide.to_numpy(), list(wide.index)
    parent = list(range(len(deps)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(deps)):
        equal = ((values[i + 1:] == values[i]) & (values[i] > 0)).sum(axis=1)
        for offset in np.flatnonzero(equal >= minimum_equal_years):
            parent[find(i + 1 + int(offset))] = find(i)
    area = history.groupby("dep").surface_ha.mean()
    groups = {}
    for i, dep in enumerate(deps):
        groups.setdefault(find(i), []).append(dep)
    return {max(members, key=lambda dep: area.get(dep, 0)) for members in groups.values()}


class Features:
    def __init__(self, columns=WEATHER):
        self.columns = tuple(columns)

    def fit(self, history):
        if not self.columns or not np.isfinite(history[list(self.columns)].to_numpy(dtype=float)).all():
            raise ValueError("Historical weather features must be finite and nonempty")
        self.centres = history.groupby("dep")[list(self.columns)].mean()
        self.fallback = history[list(self.columns)].mean()
        self.scale = history[list(self.columns)].std().replace(0, 1).fillna(1)
        return self

    def transform(self, rows):
        values = rows[list(self.columns)].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError("Prediction weather features must be finite")
        centres = self.centres.reindex(rows.dep).fillna(self.fallback).to_numpy()
        anomalies = (values - centres) / self.scale.to_numpy()
        return np.column_stack([(rows.annee.to_numpy() - 2010) / 10, anomalies])


@dataclass
class PreparedTraining:
    levels: pd.Series
    features: Features
    X: np.ndarray
    y: np.ndarray
    representatives: set
    years: list
    n: int


def prepare_training(history, columns=WEATHER):
    reps = representatives(history)
    proper = history[history.dep.isin(reps)]
    counts = proper.groupby("dep").size()
    proper = proper[proper.dep.isin(counts[counts >= 3].index)].copy()
    if proper.empty:
        raise ValueError("No department with three historical measurements")
    levels = proper.groupby("dep").rendement_qha.mean()
    features = Features(columns).fit(proper)
    y = proper.rendement_qha.to_numpy() / levels.reindex(proper.dep).to_numpy()
    return PreparedTraining(levels, features, features.transform(proper), y, reps,
                            sorted(map(int, proper.annee.unique())), len(proper))


class YieldModel:
    def __init__(self, kind, seed=42, threads=1):
        if kind not in MODEL_NAMES:
            raise ValueError(kind)
        self.kind, self.seed, self.threads = kind, seed, threads

    def fit_prepared(self, prepared):
        self.prepared = prepared
        self.levels, self.features = prepared.levels, prepared.features
        X, y = prepared.X, prepared.y
        if self.kind == "trend":
            A = np.c_[np.ones(len(X)), X[:, 0]]
            self.coef = np.linalg.lstsq(A, y, rcond=None)[0]
            self.residual_quantiles = np.quantile(y - A @ self.coef, QUANTILES)
        elif self.kind == "linear":
            self.models = [QuantileRegressor(quantile=q, alpha=.005, solver="highs").fit(X, y)
                           for q in QUANTILES]
        elif self.kind.startswith("qrf"):
            from quantile_forest import RandomForestQuantileRegressor
            self.model = RandomForestQuantileRegressor(n_estimators=300, min_samples_leaf=5,
                max_features=.8, max_depth=5, random_state=self.seed, n_jobs=self.threads).fit(X, y)
        elif self.kind == "catboost_seasonal":
            from catboost import CatBoostRegressor
            self.model = CatBoostRegressor(loss_function="MultiQuantile:alpha=0.1,0.5,0.9",
                iterations=400, depth=4, learning_rate=.03, l2_leaf_reg=5,
                random_seed=self.seed, thread_count=self.threads, verbose=False,
                allow_writing_files=False).fit(X, y)
        else:
            from lightgbm import LGBMRegressor
            self.models = [LGBMRegressor(objective="quantile", alpha=q, n_estimators=150,
                learning_rate=.05, num_leaves=7, max_depth=3, min_child_samples=20,
                verbosity=-1, n_jobs=self.threads, random_state=self.seed).fit(X, y)
                for q in QUANTILES]
        return self

    def fit(self, history, columns=WEATHER):
        return self.fit_prepared(prepare_training(history, columns))

    def predict_quantiles(self, rows):
        X = self.features.transform(rows)
        if self.kind == "trend":
            q = (np.c_[np.ones(len(X)), X[:, 0]] @ self.coef)[:, None] + self.residual_quantiles
        elif self.kind.startswith("qrf"):
            q = self.model.predict(X, quantiles=list(QUANTILES))
        elif self.kind == "catboost_seasonal":
            q = self.model.predict(X)
        else:
            q = np.column_stack([model.predict(X) for model in self.models])
        return np.sort(q, axis=1)


def sample_quantile(q, u):
    """Same Q10/Q50/Q90 piecewise-linear distribution for every model family."""
    q = np.asarray(q)
    q10, q50, q90 = q[:, 0], q[:, 1], q[:, 2]
    out = np.where(u < .5, q50 - (.5 - u) * (q50 - q10) / .4,
                   q50 + (u - .5) * (q90 - q50) / .4)
    return np.clip(out, .02, None)


def scenario_draws(pool_size, year, dep, samples=20000, seed=42):
    """Common random numbers, independent of crop, model and contract order."""
    dep_code = int(str(dep), 36)
    rng = np.random.default_rng(np.random.SeedSequence([seed, int(year), dep_code]))
    return rng.integers(pool_size, size=samples), rng.random(samples), rng.random(samples)


def simulated_yields(pool, crop_model, wheat_model, dep, year, samples=20000, seed=42):
    ix, u_crop, u_wheat = scenario_draws(len(pool), year, dep, samples, seed)
    yc = sample_quantile(crop_model.predict_quantiles(pool)[ix], u_crop) * crop_model.levels[dep] / 10
    yw = sample_quantile(wheat_model.predict_quantiles(pool)[ix], u_wheat) * wheat_model.levels[dep] / 10
    return yc, yw, pool.prix_ble.to_numpy()[ix]
