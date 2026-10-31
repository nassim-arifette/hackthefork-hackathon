"""Weather sequences and phase sensitivity from the existing NASA POWER cache.

This extension complements, rather than replaces, the six legacy variables and
the five seasonal variables per crop in ``crop_weather``. It uses no yields,
prices, test outcomes or newly downloaded observations. One row describes one
historical department/year and may be replayed only after that year is observed.

All thresholds and windows below are modelling hypotheses fixed before this
benchmark. Phase windows are the existing crop-specific calendar proxies, not
observed sowing/flowering dates. A dry day has rain <1 mm, a wet day >=1 mm and
heavy rain >=10 mm. Hot days use the existing crop heat thresholds. Degree-days
use max((Tmax+Tmin)/2 - 5, 0); base 5 is a shared exploratory index, not a fitted
or validated phenology model. Shifted reproductive windows move both bounds by
14 days. The top-five rain share describes concentration, including nonadjacent
days; the maximum five-day total describes a consecutive event.

Antecedent rainfall covers January 1 through the day before the vegetative
window. It is not a complete previous winter: the cache starts January 2010.
No previous-December values are invented or silently imputed. Rainfall is not a
soil water balance. Irrigation, soil storage and evapotranspiration are absent.

CLI: ``python pipeline/advanced_weather.py``. The accompanying manifest records
the exact specification and source hashes, including every NASA cache file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from crop_weather import FEATURE_SPECS, PARAMETERS, ROOT, read_daily


SPEC_VERSION = "weather-sequences-v1-2026-10-31"
DRY_THRESHOLD_MM = 1.0
HEAVY_RAIN_MM = 10.0
GDD_BASE_C = 5.0
SHIFT_DAYS = 14
SUFFIXES = (
    "dry_spell_vegetative_days", "dry_spell_reproductive_days",
    "wet_spell_harvest_days", "rain_max5_reproductive_mm",
    "rain_max5_harvest_mm", "rain_top5_share_reproductive",
    "hot_spell_reproductive_days", "gdd5_vegetative_cdays",
    "gdd5_reproductive_cdays", "rain_antecedent_mm",
    "rain_reproductive_early14_mm", "rain_reproductive_late14_mm",
    "heavy_rain_reproductive_days", "hot_dry_reproductive_days",
)


def advanced_columns(culture: str) -> tuple[str, ...]:
    """Added columns only; join legacy and seasonal features separately."""
    if culture not in FEATURE_SPECS:
        raise ValueError(f"Unknown culture: {culture}")
    return tuple(f"{culture}_{suffix}" for suffix in SUFFIXES)


def longest_spell(mask) -> int:
    """Length of the longest contiguous True run, including boundary runs."""
    a = np.asarray(mask, dtype=bool)
    if a.ndim != 1:
        raise ValueError("Spell input must be one-dimensional")
    padded = np.r_[False, a, False].astype(np.int8)
    edges = np.diff(padded)
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    return int((ends - starts).max()) if len(starts) else 0


def _complete_year(daily: pd.DataFrame, year: int) -> pd.DataFrame:
    if not isinstance(daily.index, pd.DatetimeIndex) or not daily.index.is_unique:
        raise ValueError("Daily weather requires unique dates")
    missing = set(PARAMETERS) - set(daily.columns)
    if missing:
        raise ValueError(f"Missing NASA columns: {sorted(missing)}")
    expected = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    g = daily.reindex(expected)[list(PARAMETERS)]
    if not np.isfinite(g.to_numpy(dtype=float)).all():
        raise ValueError(f"Incomplete or non-finite NASA daily weather for {year}")
    if (g.T2M_MIN > g.T2M_MAX).any() or (g.PRECTOTCORR < 0).any():
        raise ValueError(f"Invalid temperatures or negative precipitation for {year}")
    return g


def aggregate_year(daily: pd.DataFrame, year: int) -> dict[str, float | int]:
    """Aggregate a complete historical year, preserving event order."""
    g = _complete_year(daily, year)

    def window(bounds, shift=0):
        start, end = (pd.Timestamp(f"{year}-{b}") + pd.Timedelta(days=shift) for b in bounds)
        if start < g.index[0] or end > g.index[-1]:
            raise ValueError("Advanced weather window falls outside its calendar year")
        return g.loc[start:end]

    def maximum_five_day(frame):
        return float(frame.PRECTOTCORR.rolling(5, min_periods=5).sum().max())

    def degree_days(frame):
        mean_temperature = (frame.T2M_MAX + frame.T2M_MIN) / 2
        return float((mean_temperature - GDD_BASE_C).clip(lower=0).sum())

    result = {}
    for crop, spec in FEATURE_SPECS.items():
        veg, rep, harvest = (window(spec[phase]) for phase in ("vegetative", "reproductive", "harvest"))
        dry = rep.PRECTOTCORR < DRY_THRESHOLD_MM
        hot = rep.T2M_MAX > spec["heat_threshold_c"]
        rain_total = float(rep.PRECTOTCORR.sum())
        antecedent_end = veg.index[0] - pd.Timedelta(days=1)
        values = (
            longest_spell(veg.PRECTOTCORR < DRY_THRESHOLD_MM),
            longest_spell(dry),
            longest_spell(harvest.PRECTOTCORR >= DRY_THRESHOLD_MM),
            maximum_five_day(rep),
            maximum_five_day(harvest),
            float(rep.PRECTOTCORR.nlargest(5).sum() / rain_total) if rain_total else 0.0,
            longest_spell(hot),
            degree_days(veg),
            degree_days(rep),
            float(g.loc[:antecedent_end, "PRECTOTCORR"].sum()),
            float(window(spec["reproductive"], -SHIFT_DAYS).PRECTOTCORR.sum()),
            float(window(spec["reproductive"], SHIFT_DAYS).PRECTOTCORR.sum()),
            int((rep.PRECTOTCORR >= HEAVY_RAIN_MM).sum()),
            int((hot & dry).sum()),
        )
        result.update({name: round(value, 6) if isinstance(value, float) else value
                       for name, value in zip(advanced_columns(crop), values)})
    return result


def build_features(cache_dir=ROOT / "data_raw/nasa_power",
                   base_file=ROOT / "data/meteo_dept_cultures.csv") -> pd.DataFrame:
    """Keep exactly the existing department/year universe and order."""
    base = pd.read_csv(base_file, dtype={"dep": str})[["dep", "annee"]]
    if base.isna().any().any() or base.duplicated(["dep", "annee"]).any():
        raise ValueError("Invalid or duplicate department/year keys")
    rows = []
    for dep, group in base.sort_values(["dep", "annee"]).groupby("dep", sort=True):
        daily = read_daily(Path(cache_dir) / f"{dep}.json")
        for year in group.annee.astype(int):
            rows.append({"dep": dep, "annee": year, **aggregate_year(daily, year)})
    columns = ["dep", "annee"] + [column for crop in FEATURE_SPECS for column in advanced_columns(crop)]
    return pd.DataFrame(rows, columns=columns)


def write_manifest(path, data, output, cache_dir, base_file):
    """Trace source bytes and fixed choices without machine-specific paths."""
    source_paths = [Path(__file__), ROOT / "pipeline/crop_weather.py", Path(base_file)]
    source_paths += [Path(cache_dir) / f"{dep}.json" for dep in sorted(data.dep.unique())]
    sources = {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else p.name:
               hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    spec = {
        "version": SPEC_VERSION, "crop_windows": FEATURE_SPECS,
        "dry_below_mm": DRY_THRESHOLD_MM, "wet_at_least_mm": DRY_THRESHOLD_MM,
        "heavy_rain_at_least_mm": HEAVY_RAIN_MM, "growing_degree_day_base_c": GDD_BASE_C,
        "reproductive_window_shift_days": SHIFT_DAYS, "suffixes": list(SUFFIXES),
        "antecedent_window": "January 1 through day before vegetative start; no previous December",
        "inputs": "historical daily Tmin, Tmax, precipitation only; no targets or test scores",
        "use_at_contract": "replay prior years only; current-season observed weather is unavailable",
        "sources_sha256": sources,
    }
    record = {
        "spec": spec, "signature": hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest(),
        "rows": len(data), "departments": int(data.dep.nunique()),
        "years": sorted(map(int, data.annee.unique())), "columns": list(data.columns),
        "output_sha256": hashlib.sha256(Path(output).read_bytes()).hexdigest(),
    }
    Path(path).write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "data_raw/nasa_power")
    parser.add_argument("--base-file", type=Path, default=ROOT / "data/meteo_dept_cultures.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data/meteo_advanced_cultures.csv")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/meteo_advanced_manifest.json")
    args = parser.parse_args()
    data = build_features(args.cache_dir, args.base_file)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.output, index=False)
    write_manifest(args.manifest, data, args.output, args.cache_dir, args.base_file)
    print(f"{args.output}: {len(data)} rows, {data.dep.nunique()} departments, "
          f"{len(data.columns)-2} added weather features ({SPEC_VERSION})")


if __name__ == "__main__":
    main()
