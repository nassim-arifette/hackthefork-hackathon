"""Retrieve real Météo-France SIM decadal soil-water/weather data, 2010–2025.

The open SIM (Safran–Isba) product is used, NOT the uniform CatNat SWI.
The 8-km cells are weighted by their intersection with each department. This
is an area-weighted department summary, not a crop-area/RPG weighted summary.
Decadal flux sums are apportioned by days overlapping fixed crop windows;
soil-water means are day weighted. Thus a partial-decade approximation is
explicit, and drought-day counts are proxies based on decadal mean SWI.

These are retrospective model/reanalysis features. Contract simulations may
replay past years only; observations from the future contract year are not
available at signature. Source snapshots and all transformations are recorded.

Dependencies: numpy, pandas, shapely>=2, pyproj. No API key is required.
Source: https://www.data.gouv.fr/datasets/donnees-changement-climatique-sim-decadaire
"""
from __future__ import annotations

import argparse
import calendar
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
from pathlib import Path
import time
import urllib.request

import numpy as np
import pandas as pd

from crop_weather import FEATURE_SPECS

ROOT = Path(__file__).resolve().parents[1]
CATALOG = "https://www.data.gouv.fr/api/1/datasets/donnees-changement-climatique-sim-decadaire/"
PREFIX = "https://meteofrance.s3.sbg.io.cloud.ovh.net/data/REF_CC/SIM_DECAD/"
DEPARTMENT_URL = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson"
RAW_COLUMNS = ("PRETOTD", "EVAP", "ETP", "SWI")
SUFFIXES = ("swi_vegetative", "swi_reproductive", "swi_reproductive_min_decade",
            "low_swi_reproductive_days_proxy", "climatic_deficit_reproductive_mm",
            "evap_etp_reproductive_ratio", "rain_harvest_mm", "swi_january_february")
SPECS = dict(FEATURE_SPECS, ble={"vegetative": ("03-01", "04-30"),
    "reproductive": ("05-01", "06-30"), "harvest": ("07-01", "08-15")})


def sim_columns(culture, tag="sim"):
    if culture not in SPECS:
        raise ValueError(f"Unknown crop {culture}")
    return tuple(f"{culture}_{tag}_{name}" for name in SUFFIXES)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def retrieve(url, path, attempts=5):
    path = Path(path)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                if response.status != 200:
                    raise ValueError(f"Partial response {response.status}: {url}")
                content = response.read()
            if path.suffix == ".gz":
                gzip.decompress(content)  # Detect a truncated cache before saving it.
            temporary = path.with_suffix(path.suffix + ".part")
            temporary.write_bytes(content)
            temporary.replace(path)
            return path
        except Exception:
            if attempt + 1 == attempts:
                raise
            time.sleep(min(2 ** attempt, 8))


def read_year(path, year):
    columns = ["LAMBX", "LAMBY", "DATE", "DECADE", *RAW_COLUMNS]
    data = pd.read_csv(path, sep=";", usecols=columns)
    if data.duplicated(["LAMBX", "LAMBY", "DATE", "DECADE"]).any():
        raise ValueError("Duplicate SIM cell/decade")
    if not np.isfinite(data[columns].to_numpy(dtype=float)).all():
        raise ValueError("Missing/nonfinite SIM measurement")
    if not ((data.DATE // 100 == year).all() and data.DECADE.isin([1, 2, 3]).all()):
        raise ValueError("Unexpected SIM year or decade")
    if (data.groupby(["LAMBX", "LAMBY"]).size() != 36).any():
        raise ValueError("Each SIM grid cell must contain all 36 decades")
    # Actual evaporation may be negative (net condensation), and SWI can leave
    # [0, 1]; retain those physically meaningful model outputs unchanged.
    if (data[["PRETOTD", "ETP"]] < 0).any().any():
        raise ValueError("Negative SIM precipitation/potential evaporation")
    return data


def department_weights(grid, geojson, departments):
    """Exact polygon-intersection weights in the native equal-sized SIM grid.

    SIM LAMBX/LAMBY are hectometres in Lambert II extended, EPSG:27572.
    Cell centres are expanded to 8,000-m squares before intersection.
    """
    from pyproj import Transformer
    from shapely.geometry import box, shape
    from shapely.ops import transform
    from shapely.strtree import STRtree
    from shapely import make_valid

    project = Transformer.from_crs(4326, 27572, always_xy=True).transform
    grid = grid[["LAMBX", "LAMBY"]].drop_duplicates().sort_values(["LAMBX", "LAMBY"])
    cells = [box(x * 100 - 4000, y * 100 - 4000, x * 100 + 4000, y * 100 + 4000)
             for x, y in grid.to_numpy()]
    tree = STRtree(cells)
    coordinates = grid.to_numpy()
    rows, coverage = [], {}
    features = json.loads(Path(geojson).read_text())["features"]
    by_dep = {f["properties"]["code"]: f for f in features}
    for dep in departments:
        polygon = make_valid(transform(project, shape(by_dep[dep]["geometry"])))
        matches = []
        for i in tree.query(polygon):
            area = polygon.intersection(cells[i]).area
            if area > 1:
                matches.append((int(i), area))
        total = sum(area for _, area in matches)
        if total <= 0:
            raise ValueError(f"No intersecting SIM cell for {dep}")
        coverage[dep] = {"cells": len(matches), "grid_covered_area_fraction": total / polygon.area}
        for i, area in matches:
            x, y = coordinates[i]
            rows.append({"dep": dep, "LAMBX": x, "LAMBY": y, "weight": area / total})
    return pd.DataFrame(rows), coverage


def spatial_average(data, weights):
    merged = weights.merge(data, on=["LAMBX", "LAMBY"], validate="many_to_many")
    sums = merged.groupby(["dep", "DATE", "DECADE"]).weight.sum()
    if not np.allclose(sums, 1, rtol=0, atol=1e-10):
        raise ValueError("SIM cell coverage changed or a decade is incomplete")
    for column in RAW_COLUMNS:
        merged[column] *= merged.weight
    result = merged.groupby(["dep", "DATE", "DECADE"], as_index=False)[list(RAW_COLUMNS)].sum()
    if set(result.dep) != set(weights.dep) or (result.groupby("dep").size() != 36).any():
        raise ValueError("Incomplete department calendar")
    return result


def agriculture_weights(weights, fractions, allow_unmapped=False):
    """Multiply geometric weights by observed fixed agricultural fractions.

    The fraction table must have one row for every intersecting native grid
    cell, including explicit zeros. Missing cells cannot silently become zeros;
    explicit allow_unmapped excludes them and renormalizes on mapped cells.
    Fractions describe the supplied land-cover vintage, not annual crop areas.
    """
    required = ["LAMBX", "LAMBY", "agri_fraction"]
    if not set(required).issubset(fractions.columns):
        raise ValueError(f"Agricultural input requires {required}")
    if fractions.duplicated(["LAMBX", "LAMBY"]).any():
        raise ValueError("Duplicate agricultural cell")
    fraction = fractions.agri_fraction
    if not np.isfinite(fraction).all() or not fraction.between(0, 1).all():
        raise ValueError("Agricultural fractions must lie in [0, 1]")
    merged = weights.merge(fractions[required], on=["LAMBX", "LAMBY"], how="left", validate="many_to_one")
    if merged.agri_fraction.isna().any() and not allow_unmapped:
        missing = merged.loc[merged.agri_fraction.isna(), ["LAMBX", "LAMBY"]].drop_duplicates()
        raise ValueError(f"Missing agricultural fractions for {len(missing)} intersecting cells")
    merged = merged.dropna(subset=["agri_fraction"])
    if set(merged.dep) != set(weights.dep):
        raise ValueError("Department without mapped agricultural fractions")
    merged["weight"] *= merged.agri_fraction
    totals = merged.groupby("dep").weight.transform("sum")
    if (totals <= 0).any():
        raise ValueError("Department without positive agricultural area")
    merged["weight"] /= totals
    return merged.loc[merged.weight > 0, ["dep", "LAMBX", "LAMBY", "weight"]]


def overlap_days(year, month, decade, bounds):
    first = (decade - 1) * 10 + 1
    last = min(decade * 10, calendar.monthrange(year, month)[1]) if decade < 3 else calendar.monthrange(year, month)[1]
    start = pd.Timestamp(year, month, first)
    stop = pd.Timestamp(year, month, last)
    lower, upper = (pd.Timestamp(f"{year}-{part}") for part in bounds)
    overlap = max(0, (min(stop, upper) - max(start, lower)).days + 1)
    return overlap, last - first + 1


def phase_values(frame, year, bounds):
    periods = [overlap_days(year, int(d) % 100, int(k), bounds)
               for d, k in zip(frame.DATE, frame.DECADE)]
    days, lengths = np.array(periods, dtype=float).T
    expected = (pd.Timestamp(f"{year}-{bounds[1]}") - pd.Timestamp(f"{year}-{bounds[0]}")).days + 1
    if days.sum() != expected:
        raise ValueError("Phase calendar coverage mismatch")
    fraction = days / lengths
    active = days > 0
    evap, etp = float(frame.EVAP @ fraction), float(frame.ETP @ fraction)
    if etp <= 0:
        raise ValueError("Nonpositive reference evapotranspiration in phase")
    return {"swi_mean": float(frame.SWI @ days / days.sum()),
        "swi_min": float(frame.loc[active, "SWI"].min()),
        "low_swi_days": float((frame.SWI < .4) @ days),
        "deficit_mm": float(np.maximum(frame.ETP - frame.PRETOTD, 0) @ fraction),
        "evap_etp": evap / etp, "rain_mm": float(frame.PRETOTD @ fraction)}


def annual_features(frame, year, tag="sim"):
    rows = []
    for dep, local in frame.groupby("dep", sort=True):
        row = {"dep": dep, "annee": year}
        winter = phase_values(local, year, ("01-01", "02-29" if calendar.isleap(year) else "02-28"))
        for crop, spec in SPECS.items():
            veg = phase_values(local, year, spec["vegetative"])
            repro = phase_values(local, year, spec["reproductive"])
            harvest = phase_values(local, year, spec["harvest"])
            values = [veg["swi_mean"], repro["swi_mean"], repro["swi_min"],
                      repro["low_swi_days"], repro["deficit_mm"], repro["evap_etp"],
                      harvest["rain_mm"], winter["swi_mean"]]
            row.update(zip(sim_columns(crop, tag), values))
        rows.append(row)
    return pd.DataFrame(rows)


def run(args):
    base = pd.read_csv(args.base_file, dtype={"dep": str})[["dep", "annee"]]
    if base.duplicated().any():
        raise ValueError("Duplicate target department/year")
    years, departments = sorted(base.annee.unique()), sorted(base.dep.unique())
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    if not args.departments_geojson.exists():
        retrieve(DEPARTMENT_URL, args.departments_geojson)
    catalog_path = retrieve(CATALOG, args.cache_dir / "catalog.json")
    catalog = json.loads(catalog_path.read_text())
    resources = {r["title"]: r for r in catalog["resources"]}
    for year in years:
        title = f"DECAD_SIM2_{year}"
        if resources.get(title, {}).get("url") != f"{PREFIX}{title}.csv.gz":
            raise ValueError(f"Source URL not verified against official catalogue: {title}")

    def get(year):
        url = resources[f"DECAD_SIM2_{year}"]["url"]
        path = retrieve(url, args.cache_dir / f"DECAD_SIM2_{year}.csv.gz")
        print(f"SIM {year}: downloaded {path.stat().st_size:,} bytes", flush=True)
        return year, path

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        files = dict(pool.map(get, years))
    first = read_year(files[years[0]], years[0])
    weights, coverage = department_weights(first, args.departments_geojson, departments)
    weights.to_csv(args.cache_dir / "department_weights.csv", index=False)
    if args.agricultural_fractions:
        fractions = pd.read_csv(args.agricultural_fractions)
        known = weights.merge(fractions[["LAMBX", "LAMBY"]], on=["LAMBX", "LAMBY"], validate="many_to_one")
        mapped = known.groupby("dep").weight.sum()
        for dep in departments:
            coverage[dep]["agricultural_map_covered_area_fraction"] = float(mapped.get(dep, 0))
        weights = agriculture_weights(weights, fractions, args.allow_unmapped_agriculture)
    all_features, sources = [], []
    for year in years:
        data = first if year == years[0] else read_year(files[year], year)
        all_features.append(annual_features(spatial_average(data, weights), year, args.column_tag))
        sources.append({"year": int(year), "url": resources[f"DECAD_SIM2_{year}"]["url"],
            "sha256": sha256(files[year]), "compressed_bytes": files[year].stat().st_size,
            "rows": len(data), "cells": len(data[["LAMBX", "LAMBY"]].drop_duplicates())})
        print(f"SIM {year}: {len(departments)} departments processed", flush=True)
    features = pd.concat(all_features, ignore_index=True)
    output = base.merge(features, on=["dep", "annee"], validate="one_to_one").sort_values(["dep", "annee"])
    if len(output) != len(base) or not np.isfinite(output.drop(columns="dep")).all().all():
        raise ValueError("Output coverage or finiteness check failed")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False, float_format="%.8f")
    manifest = {"source": "Météo-France SIM decadal (Safran–Isba), not CatNat uniform SWI",
        "catalog": CATALOG, "catalog_sha256": sha256(catalog_path),
        "license": "Licence Ouverte Etalab 2.0", "spec_version": "sim-decadal-zonal-v1",
        "years": list(map(int, years)), "departments": departments, "rows": len(output),
        "columns": {crop: list(sim_columns(crop, args.column_tag)) for crop in SPECS}, "sources": sources,
        "department_geometry_sha256": sha256(args.departments_geojson),
        "default_department_geometry_url": DEPARTMENT_URL,
        "geometry": "8 km squares centered on native Lambert II extended grid (EPSG:27572), polygon intersection area weights, normalized over available cells",
        "spatial_weighting": "department intersection area times supplied fixed agricultural fraction" if args.agricultural_fractions else "department area; NOT crop/RPG area",
        "agricultural_fractions_sha256": sha256(args.agricultural_fractions) if args.agricultural_fractions else None,
        "unmapped_agricultural_cells": "explicitly excluded, weights renormalized over mapped cells; no zero-agriculture imputation" if args.agricultural_fractions and args.allow_unmapped_agriculture else "none permitted",
        "coverage": coverage,
        "window_specifications": SPECS,
        "window_source_code_sha256": sha256(ROOT / "pipeline/crop_weather.py"),
        "parameters_documentation": "https://static.data.gouv.fr/resources/donnees-changement-climatique-sim-decadaire/20260415-135515/sim-decadaires-parametres-20260415.pdf",
        "temporal_aggregation": "decadal means day-weighted; flux sums prorated by overlap days; partial-decade approximation",
        "swi_low_threshold": .4, "swi_low_threshold_status": "feature engineering hypothesis, not a universal crop damage threshold",
        "deficit_definition": "sum of positive (ETP minus total precipitation) per decade, prorated by overlap; NOT a full crop water balance",
        "usage": "historical reanalysis scenarios only for pre-season contract; target-year realized features only for after-harvest diagnostics",
        "availability_note": "current reanalysis vintage replayed retrospectively; not an archive of data releases available at each historical signature date",
        "source_code_sha256": sha256(__file__), "output_sha256": sha256(args.output)}
    args.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"Saved {args.output}: {len(output)} rows, {len(output.columns)-2} features", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-file", type=Path, default=ROOT / "data/meteo_dept_cultures.csv")
    parser.add_argument("--departments-geojson", type=Path, default=ROOT / "data_raw/geo/departements.geojson")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "data_raw/sim_decadaire")
    parser.add_argument("--output", type=Path, default=ROOT / "data/sim_features.csv")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/sim_manifest.json")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--agricultural-fractions", type=Path)
    parser.add_argument("--allow-unmapped-agriculture", action="store_true")
    parser.add_argument("--column-tag", default="sim", help="Use sim_agri for a separate agricultural-weight ablation")
    run(parser.parse_args())
