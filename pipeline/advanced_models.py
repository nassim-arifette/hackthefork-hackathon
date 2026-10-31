"""Past-only preprocessing and distributional yield candidates.

This module is separate from the published six-model benchmark. It preserves
that benchmark's historical representative/cohort rule while exposing explicit
preprocessing and model settings for temporal economic selection.

Predictions are *relative* yields. Multiply by ``model.levels[dep] / 10`` to
obtain t/ha, exactly as in ``multicrop_models``. Static soil characteristics use
global training statistics; centring them within a department would erase them.
Missing-value median imputation is optional and fitted only on training rows;
it always adds missing indicators. The default is strict rejection.

QRF predicts every requested quantile from its conditional empirical response
distribution. Linear/boosting candidates fit the explicit grid in ``quantiles``
and interpolate only when a different grid is requested. Thus requesting dense
predictions from a three-point fitted grid is not labelled a dense fitted model.
No outcome, test weather, or future row is consulted when fitting these objects.
"""
from __future__ import annotations

from copy import deepcopy

import numpy as np
import pandas as pd
from sklearn.linear_model import QuantileRegressor

from multicrop_models import PreparedTraining, WEATHER, representatives


DENSE_QUANTILES = (.01, .05, .1, .2, .3, .4, .5, .6, .7, .8, .9, .95, .99)
THREE_QUANTILES = (.1, .5, .9)


def checked_quantiles(values):
    values = np.asarray(tuple(values), dtype=float)
    if (values.ndim != 1 or len(values) < 1 or not np.isfinite(values).all()
            or np.any(values <= 0) or np.any(values >= 1)
            or np.any(np.diff(values) <= 0)):
        raise ValueError("Quantiles must be strictly increasing numbers between 0 and 1")
    return values


class AdvancedFeatures:
    """Separate dynamic weather anomalies from globally scaled static inputs."""

    def __init__(self, columns=WEATHER, static_columns=(), mode="anomaly",
                 imputation="strict"):
        self.static_columns = tuple(dict.fromkeys(static_columns))
        self.columns = tuple(c for c in dict.fromkeys(columns) if c not in self.static_columns)
        self.all_columns = self.columns + self.static_columns
        if mode not in ("anomaly", "absolute_anomaly"):
            raise ValueError(f"Unknown feature mode: {mode}")
        if imputation not in ("strict", "median"):
            raise ValueError(f"Unknown imputation: {imputation}")
        self.mode, self.imputation = mode, imputation

    def _numeric(self, rows):
        data = rows[list(self.all_columns)].astype(float)
        if np.isinf(data.to_numpy()).any():
            raise ValueError("Feature values cannot be infinite")
        if self.imputation == "strict" and data.isna().any().any():
            raise ValueError("Feature values contain missing observations")
        return data

    def fit(self, history):
        if history.empty:
            raise ValueError("Cannot fit preprocessing on an empty history")
        data = self._numeric(history)
        self.medians = data.median()
        if self.medians.isna().any():
            raise ValueError("A feature has no observed training value")
        filled = data.fillna(self.medians)
        self.global_mean = filled.mean()
        self.scale = filled.std().replace(0, 1).fillna(1)
        self.centres = filled[list(self.columns)].groupby(history.dep).mean()
        self.feature_names_ = ["year_trend"]
        self.feature_names_ += [f"anomaly:{c}" for c in self.columns]
        if self.mode == "absolute_anomaly":
            self.feature_names_ += [f"absolute:{c}" for c in self.columns]
        self.feature_names_ += [f"static:{c}" for c in self.static_columns]
        if self.imputation == "median":
            self.feature_names_ += [f"missing:{c}" for c in self.all_columns]
        return self

    def transform(self, rows):
        data = self._numeric(rows)
        missing = data.isna().to_numpy(dtype=float)
        filled = data.fillna(self.medians)
        years = rows.annee.to_numpy(dtype=float)
        if not np.isfinite(years).all():
            raise ValueError("Year must be finite")
        blocks = [(years - 2010)[:, None] / 10]
        if self.columns:
            centres = self.centres.reindex(rows.dep).fillna(
                self.global_mean[list(self.columns)]).to_numpy()
            values = filled[list(self.columns)].to_numpy()
            scale = self.scale[list(self.columns)].to_numpy()
            blocks.append((values - centres) / scale)
            if self.mode == "absolute_anomaly":
                blocks.append((values - self.global_mean[list(self.columns)].to_numpy()) / scale)
        if self.static_columns:
            names = list(self.static_columns)
            blocks.append(((filled[names] - self.global_mean[names]) / self.scale[names]).to_numpy())
        if self.imputation == "median":
            blocks.append(missing)
        result = np.column_stack(blocks)
        if not np.isfinite(result).all():
            raise ValueError("Non-finite transformed features")
        return result


def prepare_advanced_training(history, columns=WEATHER, static_columns=(), spec=None):
    """Preserve the old cohort; fit every statistic on supplied history only.

    Shrinkage uses n/(n+strength) times the department mean, plus the remainder
    times the mean of department means in the same region. A missing region
    falls back to the mean of all department means. It does not create synthetic
    observations or add departments without the required three measurements.
    """
    spec = {} if spec is None else spec
    reps = representatives(history)
    proper = history[history.dep.isin(reps)]
    counts = proper.groupby("dep").size()
    proper = proper[proper.dep.isin(counts[counts >= 3].index)].copy()
    if proper.empty:
        raise ValueError("No department with three historical measurements")
    values = proper.rendement_qha.to_numpy(dtype=float)
    if not np.isfinite(values).all() or np.any(values <= 0):
        raise ValueError("Historical yield measurements must be finite and positive")
    levels = proper.groupby("dep").rendement_qha.mean()
    normalization = spec.get("target_normalization", "mean")
    if normalization == "shrinkage":
        strength = float(spec.get("shrinkage_strength", 5.0))
        if not np.isfinite(strength) or strength < 0:
            raise ValueError("shrinkage_strength must be finite and nonnegative")
        anchor = pd.Series(float(levels.mean()), index=levels.index)
        if "region" in proper:
            dep_region = proper.groupby("dep").region.first()
            regional = levels.groupby(dep_region).mean()
            anchor = dep_region.map(regional).fillna(float(levels.mean()))
        weight = counts.reindex(levels.index) / (counts.reindex(levels.index) + strength)
        levels = (weight * levels + (1 - weight) * anchor).rename("rendement_qha")
    elif normalization != "mean":
        raise ValueError(f"Unknown target normalization: {normalization}")
    features = AdvancedFeatures(columns, static_columns,
        mode=spec.get("feature_mode", "anomaly"),
        imputation=spec.get("imputation", "strict")).fit(proper)
    y = values / levels.reindex(proper.dep).to_numpy()
    return PreparedTraining(levels, features, features.transform(proper), y, reps,
                            sorted(map(int, proper.annee.unique())), len(proper))


class AdvancedYieldModel:
    """Yield model with explicit preprocessing, hyperparameters and quantile grid.

    ``spec`` keys: family, params, quantiles, target_normalization,
    shrinkage_strength, feature_mode and imputation. ``params`` are the native
    model's hyperparameters; objective, seed and thread count stay controlled by
    this class. Example: ``{"family": "qrf", "params": {"max_depth": 8}}``.
    """

    def __init__(self, spec, seed=42, threads=1):
        self.spec = deepcopy(spec)
        self.kind = self.spec.get("family", "qrf")
        if self.kind not in ("trend", "linear", "qrf", "lightgbm", "catboost"):
            raise ValueError(f"Unknown model family: {self.kind}")
        self.seed, self.threads = seed, threads
        self.quantiles = tuple(checked_quantiles(self.spec.get("quantiles", DENSE_QUANTILES)))

    def fit(self, history, columns=WEATHER, static_columns=()):
        return self.fit_prepared(prepare_advanced_training(history, columns, static_columns, self.spec))

    def fit_prepared(self, prepared):
        self.prepared = prepared
        self.levels, self.features = prepared.levels, prepared.features
        X, y = prepared.X, prepared.y
        params = dict(self.spec.get("params", {}))
        if self.kind == "trend":
            if params:
                raise ValueError("Trend model does not accept hyperparameters")
            A = np.c_[np.ones(len(X)), X[:, 0]]
            self.coef = np.linalg.lstsq(A, y, rcond=None)[0]
            self.residuals = y - A @ self.coef
        elif self.kind == "linear":
            options = {"alpha": .005, "solver": "highs", **params}
            options.pop("quantile", None)
            self.models = [QuantileRegressor(quantile=q, **options).fit(X, y)
                           for q in self.quantiles]
        elif self.kind == "qrf":
            from quantile_forest import RandomForestQuantileRegressor
            options = {"n_estimators": 300, "min_samples_leaf": 5,
                "max_features": .8, "max_depth": 5, **params,
                "random_state": self.seed, "n_jobs": self.threads}
            self.model = RandomForestQuantileRegressor(**options).fit(X, y)
        elif self.kind == "catboost":
            from catboost import CatBoostRegressor
            options = {"iterations": 400, "depth": 4, "learning_rate": .03,
                "l2_leaf_reg": 5, **params, "random_seed": self.seed,
                "thread_count": self.threads, "verbose": False, "allow_writing_files": False,
                "loss_function": "MultiQuantile:alpha=" + ",".join(map(str, self.quantiles))}
            self.model = CatBoostRegressor(**options).fit(X, y)
        else:
            from lightgbm import LGBMRegressor
            options = {"n_estimators": 150, "learning_rate": .05, "num_leaves": 7,
                "max_depth": 3, "min_child_samples": 20, **params,
                "verbosity": -1, "n_jobs": self.threads, "random_state": self.seed,
                "objective": "quantile"}
            options.pop("alpha", None)
            self.models = [LGBMRegressor(alpha=q, **options).fit(X, y) for q in self.quantiles]
        return self

    def predict_distribution(self, rows, quantiles=None):
        """Return ordered relative-yield quantiles, without using outcomes.

        Quantile rearrangement removes crossings. For non-QRF fitted grids,
        interpolation outside the trained range uses the closest fitted endpoint;
        the simulation's tail assumptions belong to its explicit sampler.
        """
        requested = checked_quantiles(self.quantiles if quantiles is None else quantiles)
        X = self.features.transform(rows)
        if self.kind == "trend":
            q = (np.c_[np.ones(len(X)), X[:, 0]] @ self.coef)[:, None]
            return q + np.quantile(self.residuals, requested)[None, :]
        if self.kind == "qrf":
            q = np.asarray(self.model.predict(X, quantiles=list(requested)))
            return np.sort(q.reshape(len(rows), len(requested)), axis=1)
        if self.kind == "catboost":
            q = np.asarray(self.model.predict(X)).reshape(len(rows), len(self.quantiles))
        else:
            q = np.column_stack([model.predict(X) for model in self.models])
        q = np.sort(q, axis=1)
        if np.array_equal(requested, self.quantiles):
            return q
        return np.vstack([np.interp(requested, self.quantiles, row) for row in q])

    def predict_quantiles(self, rows):
        return self.predict_distribution(rows, THREE_QUANTILES)

