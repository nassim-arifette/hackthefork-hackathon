"""Optional exact QRF prediction batching around the frozen benchmark.

This changes execution layout only: fitted model parameters, input values,
requested quantiles, random draws and economic calculations stay untouched.
Install before ``benchmark_advanced.run``; ``uninstall`` restores every method.
The frozen benchmark source files need not be edited. Execution wrappers must
archive this helper and record its hash separately from the logical manifest.

QRF's tree traversal is expensive when repeatedly called on 10--15 rows. For
each fitted instance and target year, this helper calls the original prediction
method once on its complete known-department historical weather table through
that year, with the trend year set to the target. Contract lookup still uses
only the individual earlier-year inputs passed by the unchanged benchmark.
Current-year values are available only for its existing yield diagnostics; no
future-year values are included in the batch.

Keys contain full float64 input bytes (not a lossy hash), department and target
year. Unsupported grids, missing covariates and unmatched inputs fall back to
the original implementation. Fits and newly loaded data invalidate the cache.
Every returned array is independent so caller mutation cannot poison reuse.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


_ACTIVE = None


def _keys(rows, columns):
    values = rows[["annee", *columns]].to_numpy(dtype=np.float64)
    if not np.isfinite(values).all():
        return None
    return [(str(dep), row.tobytes()) for dep, row in zip(rows.dep, values)]


@dataclass
class PredictionBatching:
    """Installation handle with execution counters and reversible patches."""
    benchmark: object
    model_class: object
    original_load: object
    original_predict: object
    original_fit: object
    state: dict
    installed: bool = True

    @property
    def stats(self):
        return {k: v for k, v in self.state.items() if k not in ("weather", "owner")}

    def uninstall(self):
        global _ACTIVE
        if self.installed:
            self.benchmark.load_data = self.original_load
            self.model_class.predict_distribution = self.original_predict
            self.model_class.fit_prepared = self.original_fit
            self.installed = False
            if _ACTIVE is self:
                _ACTIVE = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.uninstall()


def install_batched_predictions(benchmark):
    """Wrap only QRF prediction calls; no benchmark source or result is edited."""
    global _ACTIVE
    if _ACTIVE is not None:
        raise RuntimeError("A prediction batching installation is already active")
    model_class = benchmark.AdvancedYieldModel
    original_load = benchmark.load_data
    original_predict = model_class.predict_distribution
    original_fit = model_class.fit_prepared
    state = {"weather": None, "owner": object(), "generation": 0, "batches": 0,
             "batched_rows": 0, "cache_calls": 0, "cache_rows": 0, "fallback_calls": 0}

    def load_data(*args, **kwargs):
        result = original_load(*args, **kwargs)
        state["weather"] = result[1]
        state["generation"] += 1
        return result

    def fit_prepared(self, prepared):
        self._exact_batch_cache = {}
        self._exact_batch_owner = state["owner"]
        return original_fit(self, prepared)

    def predict_distribution(self, rows, quantiles=None):
        def fallback():
            state["fallback_calls"] += 1
            return original_predict(self, rows, quantiles)

        weather = state["weather"]
        if self.kind != "qrf" or weather is None or rows.empty:
            return fallback()
        requested = tuple(self.quantiles if quantiles is None else quantiles)
        grid = tuple(self.quantiles)
        if not requested or any(q not in grid for q in requested) or any(
                a >= b for a, b in zip(requested, requested[1:])):
            return fallback()
        years = rows.annee.unique()
        if len(years) != 1 or not np.isfinite(years[0]):
            return fallback()
        year = years[0]
        columns = tuple(self.features.all_columns)
        if not set(("dep", "annee", *columns)).issubset(weather.columns):
            return fallback()
        keys = _keys(rows, columns)
        if keys is None:
            return fallback()
        if getattr(self, "_exact_batch_owner", None) is not state["owner"]:
            self._exact_batch_cache = {}
            self._exact_batch_owner = state["owner"]
        cache_key = (state["generation"], float(year), columns, grid)
        if cache_key not in self._exact_batch_cache:
            batch = weather[(weather.annee <= year) & weather.dep.isin(self.levels.index)].copy()
            if batch.empty:
                self._exact_batch_cache[cache_key] = None
                return fallback()
            batch["annee"] = year
            batch_keys = _keys(batch, columns)
            if batch_keys is None:
                self._exact_batch_cache[cache_key] = None
                return fallback()
            predictions = original_predict(self, batch, grid)
            table = {}
            for key, prediction in zip(batch_keys, predictions):
                if key in table and not np.array_equal(table[key], prediction):
                    # The optimization is invalid for any row-order-dependent predictor.
                    self._exact_batch_cache[cache_key] = None
                    return fallback()
                table[key] = prediction.copy()
            self._exact_batch_cache[cache_key] = table
            state["batches"] += 1
            state["batched_rows"] += len(batch)
        table = self._exact_batch_cache[cache_key]
        if table is None or any(key not in table for key in keys):
            return fallback()
        indices = [grid.index(q) for q in requested]
        output = np.vstack([table[key] for key in keys])[:, indices].copy()
        state["cache_calls"] += 1
        state["cache_rows"] += len(keys)
        return output

    handle = PredictionBatching(benchmark, model_class, original_load, original_predict, original_fit, state)
    benchmark.load_data = load_data
    model_class.predict_distribution = predict_distribution
    model_class.fit_prepared = fit_prepared
    _ACTIVE = handle
    return handle
