"""Fixed crop-specific calendar proxies from the existing NASA POWER cache.

Run from any directory: ``python pipeline/crop_weather.py``. No download, yield,
price, satellite image or test score is used. The output has one row per
department/year, so it can join ``meteo_dept_cultures.csv`` one-to-one.

These windows are HYPOTHESES chosen before the benchmark, not observed sowing,
flowering or harvesting dates. Agreste does not distinguish winter/spring peas
or faba beans, irrigation, varieties or organic production in this panel. The
calendar proxies below must not be presented as those missing observations.
They describe historical weather; current-season realised weather is unavailable
when setting a pre-season contract. Replay only prior years in that decision.

Technical motivation (not empirical validation of these particular windows):
* Lentil: Terres Inovia, spring cycle and geographical variation in flowering:
  https://www.terresinovia.fr/fr/informations-techniques/lentille/le-cycle-de-la-culture-de-la-lentille
* Chickpea: Terres Inovia guide 2026, p.18, flowering mean <15 C / maximum >35 C:
  https://www.terresinovia.fr/sites/default/files/2026-04/guide_culture_pois-chiche_2026_terresinovia.pdf
* Spring faba bean: Terres Inovia, heat effects above 25 C:
  https://www.terresinovia.fr/fr/informations-techniques/feverole-de-printemps/accidents-climatiques-de-la-feverole-secheresse-et
* Spring peas/faba beans: Terres Inovia, sowing and reproductive water stress:
  https://www.terresinovia.fr/fr/actualites/reussir-limplantation-des-pois-et-feveroles-de-printemps
* Dry bean: Bio Bourgogne / Chambers 21, 89, 71 (2021), late spring sowing,
  reproductive heat at 30-35 C, irrigation and harvesting damage:
  https://www.produire-bio.fr/articles-pratiques/a-la-decouverte-du-phasealus-vulgaris/

Heat is sum(max(TMAX - threshold, 0)), in degree-days, in the reproductive
window. Cold is a count of days below a threshold in the stated cold window.
For chickpea only, (TMAX+TMIN)/2 approximates daily mean temperature because the
cache contains no T2M mean: this approximation is an additional hypothesis.
Rain sums are NOT a water balance; soil storage, irrigation and ET are absent.
Wheat retains the six original features in the shared comparison model.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SPEC_VERSION = "calendar-proxies-v1-2026-10-31"
LEGACY_WEATHER = ("pluie_mj", "pluie_avj", "j30_jj", "gel_tardif", "pluie_recolte", "tmax_mj")
PARAMETERS = ("T2M_MAX", "T2M_MIN", "PRECTOTCORR")
SUFFIXES = ("rain_vegetative_mm", "rain_reproductive_mm", "rain_harvest_mm",
            "heat_excess_cdays", "cold_days")

# Calendar ranges are inclusive and deliberately fixed across departments/years.
# The 30 C pea threshold and all cold/frost thresholds except chickpea <15 C
# are scenario choices, not claimed damage thresholds established by a source.
# No winter/spring classification is inferred from the crop name or weather.
FEATURE_SPECS = {
    "lentille": {
        "vegetative": ("03-01", "04-30"), "reproductive": ("05-01", "06-30"),
        "harvest": ("07-01", "08-15"), "heat_threshold_c": 30.0,
        "cold_window": ("03-01", "05-15"), "cold_variable": "T2M_MIN", "cold_threshold_c": 0.0,
    },
    "pois_chiche": {
        "vegetative": ("03-01", "05-31"), "reproductive": ("06-01", "07-31"),
        "harvest": ("08-01", "08-31"), "heat_threshold_c": 35.0,
        "cold_window": ("06-01", "07-31"), "cold_variable": "MEAN_APPROX", "cold_threshold_c": 15.0,
    },
    "haricot": {
        "vegetative": ("05-15", "06-30"), "reproductive": ("07-01", "08-15"),
        "harvest": ("08-16", "09-30"), "heat_threshold_c": 30.0,
        "cold_window": ("05-15", "06-15"), "cold_variable": "T2M_MIN", "cold_threshold_c": 0.0,
    },
    "pois": {
        "vegetative": ("02-01", "04-30"), "reproductive": ("05-01", "06-30"),
        "harvest": ("07-01", "08-15"), "heat_threshold_c": 30.0,
        "cold_window": ("02-01", "04-30"), "cold_variable": "T2M_MIN", "cold_threshold_c": -2.0,
    },
    "feverole": {
        "vegetative": ("02-01", "04-30"), "reproductive": ("05-01", "07-15"),
        "harvest": ("07-16", "08-31"), "heat_threshold_c": 25.0,
        "cold_window": ("02-01", "04-30"), "cold_variable": "T2M_MIN", "cold_threshold_c": -2.0,
    },
}


def seasonal_columns(culture: str) -> tuple[str, ...]:
    """Five weather proxies for a legume; unchanged legacy weather for wheat."""
    if culture == "ble":
        return LEGACY_WEATHER
    if culture not in FEATURE_SPECS:
        raise ValueError(f"Unknown culture: {culture}")
    return tuple(f"{culture}_{suffix}" for suffix in SUFFIXES)


def read_daily(path: Path) -> pd.DataFrame:
    """Read recorded temperatures/rainfall and preserve missing values as NaN."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    values = raw["properties"]["parameter"]
    missing = set(PARAMETERS) - set(values)
    if missing:
        raise ValueError(f"{path}: missing NASA parameters {sorted(missing)}")
    daily = pd.DataFrame({name: values[name] for name in PARAMETERS})
    daily.index = pd.to_datetime(daily.index, format="%Y%m%d")
    if not daily.index.is_unique:
        raise ValueError(f"{path}: duplicate daily dates")
    fill = raw.get("header", {}).get("fill_value", -999.0)
    return daily.replace(fill, np.nan).astype(float).sort_index()


def aggregate_year(daily: pd.DataFrame, year: int) -> dict[str, float | int]:
    """Aggregate one complete calendar year; refuse silent missing-day sums."""
    expected = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    if not daily.index.is_unique:
        raise ValueError("Duplicate daily dates")
    g = daily.reindex(expected)[list(PARAMETERS)]
    if not np.isfinite(g.to_numpy(dtype=float)).all():
        raise ValueError(f"Incomplete or non-finite NASA daily weather for {year}")
    if (g.T2M_MIN > g.T2M_MAX).any() or (g.PRECTOTCORR < 0).any():
        raise ValueError(f"Invalid temperature ordering or negative precipitation for {year}")

    def window(bounds):
        return g.loc[f"{year}-{bounds[0]}":f"{year}-{bounds[1]}"]

    result = {}
    for crop, spec in FEATURE_SPECS.items():
        for phase in ("vegetative", "reproductive", "harvest"):
            result[f"{crop}_rain_{phase}_mm"] = round(float(window(spec[phase]).PRECTOTCORR.sum()), 6)
        reproductive = window(spec["reproductive"])
        result[f"{crop}_heat_excess_cdays"] = round(float(
            (reproductive.T2M_MAX - spec["heat_threshold_c"]).clip(lower=0).sum()), 6)
        cold = window(spec["cold_window"])
        temperature = ((cold.T2M_MAX + cold.T2M_MIN) / 2 if spec["cold_variable"] == "MEAN_APPROX"
                       else cold[spec["cold_variable"]])
        result[f"{crop}_cold_days"] = int((temperature < spec["cold_threshold_c"]).sum())
    return result


def build_features(cache_dir=ROOT / "data_raw" / "nasa_power",
                   base_file=ROOT / "data" / "meteo_dept_cultures.csv") -> pd.DataFrame:
    """Follow exactly the department/year universe of the existing weather file."""
    base = pd.read_csv(base_file, dtype={"dep": str})[["dep", "annee"]]
    if base.duplicated(["dep", "annee"]).any():
        raise ValueError("Duplicate department/year in the baseline weather file")
    rows = []
    for dep, keys in base.sort_values(["dep", "annee"]).groupby("dep", sort=True):
        daily = read_daily(Path(cache_dir) / f"{dep}.json")
        for year in keys.annee.astype(int):
            rows.append({"dep": dep, "annee": year, **aggregate_year(daily, year)})
    columns = ["dep", "annee"] + [name for crop in FEATURE_SPECS for name in seasonal_columns(crop)]
    return pd.DataFrame(rows, columns=columns)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "data_raw" / "nasa_power")
    parser.add_argument("--base-file", type=Path, default=ROOT / "data" / "meteo_dept_cultures.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "meteo_saisonnier_cultures.csv")
    args = parser.parse_args()
    data = build_features(args.cache_dir, args.base_file)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.output, index=False)
    print(f"{args.output}: {len(data)} rows, {data.dep.nunique()} departments, "
          f"{data.annee.min()}-{data.annee.max()}, {len(data.columns) - 2} weather proxies ({SPEC_VERSION})")


if __name__ == "__main__":
    main()
