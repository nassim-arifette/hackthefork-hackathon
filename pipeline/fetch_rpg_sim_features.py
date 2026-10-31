"""SIM features weighted by the real fixed RPG 2015 crop footprints.

This is a separate ablation; existing SIM and CLC outputs are never modified.
Observed RPG department/crop weights take precedence. Uncovered groups retain
the exact existing CLC-2012 agricultural SIM features, including all wheat and
haricot groups. No annual RPG or rotations are inferred from the fixed mask.
The historical climate is reanalysed with a 2015 spatial footprint: this is
explicitly a retrospective spatial ablation, not an archived real-time product.
"""
from __future__ import annotations

import argparse
import calendar
import json
from pathlib import Path

import numpy as np
import pandas as pd

from fetch_sim_features import (ROOT, SPECS, phase_values, read_year, sha256,
                                sim_columns, spatial_average)


def validate_rpg_weights(weights, allowed_departments):
    required = ["dep", "culture", "LAMBX", "LAMBY", "weight"]
    if not set(required).issubset(weights):
        raise ValueError(f"RPG weights require columns {required}")
    weights = weights[required].copy()
    if weights.duplicated(required[:-1]).any():
        raise ValueError("Duplicate RPG department/crop/cell")
    if not set(weights.dep).issubset(set(allowed_departments)):
        raise ValueError("RPG weights reference an unknown target department")
    if not set(weights.culture).issubset(SPECS):
        raise ValueError("RPG weights reference an unknown crop")
    if not np.isfinite(weights[["LAMBX", "LAMBY", "weight"]]).all().all() or (weights.weight <= 0).any():
        raise ValueError("RPG weights must be finite and positive")
    totals = weights.groupby(["dep", "culture"]).weight.transform("sum")
    if not np.allclose(totals, 1, atol=1e-7, rtol=0):
        raise ValueError("RPG area weights must sum to one before rounding correction")
    weights.weight /= totals  # CSV source rounds weights to ten decimals.
    return weights


def crop_features(frame, year, crop):
    rows = []
    spec = SPECS[crop]
    for dep, local in frame.groupby("dep", sort=True):
        winter = phase_values(local, year, ("01-01", "02-29" if calendar.isleap(year) else "02-28"))
        veg = phase_values(local, year, spec["vegetative"])
        repro = phase_values(local, year, spec["reproductive"])
        harvest = phase_values(local, year, spec["harvest"])
        values = [veg["swi_mean"], repro["swi_mean"], repro["swi_min"],
                  repro["low_swi_days"], repro["deficit_mm"], repro["evap_etp"],
                  harvest["rain_mm"], winter["swi_mean"]]
        rows.append({"dep": dep, "annee": year, **dict(zip(sim_columns(crop, "sim_rpg"), values))})
    return pd.DataFrame(rows)


def start_from_fallback(fallback):
    required = ["dep", "annee", *(c for crop in SPECS for c in sim_columns(crop, "sim_agri"))]
    if not set(required).issubset(fallback):
        raise ValueError("Incomplete CLC fallback feature schema")
    if fallback.duplicated(["dep", "annee"]).any():
        raise ValueError("Duplicate CLC department/year")
    if not np.isfinite(fallback.drop(columns="dep").to_numpy(dtype=float)).all():
        raise ValueError("Missing/nonfinite CLC fallback feature")
    return fallback[required].rename(columns={c: c.replace("_sim_agri_", "_sim_rpg_")
                                              for c in required}).set_index(["dep", "annee"])


def run(args):
    frozen = {str(p): sha256(p) for p in [args.fallback_file, args.fallback_manifest,
               args.rpg_weights, args.soil_manifest, ROOT / "pipeline/fetch_sim_features.py"]}
    fallback = pd.read_csv(args.fallback_file, dtype={"dep": str})
    fallback_manifest = json.loads(args.fallback_manifest.read_text())
    if fallback_manifest["output_sha256"] != sha256(args.fallback_file):
        raise ValueError("CLC fallback does not match its source manifest")
    weights = validate_rpg_weights(pd.read_csv(args.rpg_weights, dtype={"dep": str}), fallback.dep.unique())
    output = start_from_fallback(fallback)
    years = sorted(fallback.annee.unique())
    crops = sorted(weights.culture.unique())
    known_sources = {int(s["year"]): s for s in fallback_manifest["sources"]}
    for year in years:
        path = args.cache_dir / f"DECAD_SIM2_{year}.csv.gz"
        if not path.exists() or sha256(path) != known_sources[int(year)]["sha256"]:
            raise ValueError(f"SIM {year} cache is absent or differs from frozen source")
        data = read_year(path, int(year))
        for crop in crops:
            local_weights = weights[weights.culture == crop].drop(columns="culture")
            values = crop_features(spatial_average(data, local_weights), int(year), crop).set_index(["dep", "annee"])
            if not values.index.isin(output.index).all():
                raise ValueError("RPG feature rows fall outside the frozen target cohort")
            output.loc[values.index, values.columns] = values
        print(f"RPG-weighted SIM {year}: {len(crops)} observed crop masks, remaining groups retain CLC", flush=True)
    if not np.isfinite(output.to_numpy(dtype=float)).all():
        raise ValueError("RPG output contains missing or nonfinite values")
    output = output.reset_index().sort_values(["dep", "annee"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False, float_format="%.8f")
    rpg_meta = json.loads(args.soil_manifest.read_text())["rpg_2015"]
    source_coverage = {(r["dep"], r["culture"]): r for r in rpg_meta.get("coverage", [])}
    counts = weights.groupby(["dep", "culture"]).size()
    coverage = []
    for crop in SPECS:
        for dep in sorted(fallback.dep.unique()):
            key = (dep, crop)
            row = {"dep": dep, "culture": crop,
                "weather_weight_source": "RPG 2015 crop-specific parcel area" if key in counts else "CLC 2012 general agricultural fallback",
                "rpg_grid_cells": int(counts.get(key, 0)),
                "fallback": key not in counts}
            if key in source_coverage:
                row["parcel_mapping_coverage"] = source_coverage[key]
            coverage.append(row)
    manifest = {"spec_version": "sim-rpg2015-spatial-ablation-v1", "source": "Météo-France SIM decadal plus IGN/ASP RPG 2015 parcel areas",
        "rows": len(output), "departments": sorted(fallback.dep.unique()), "years": list(map(int, years)),
        "columns": {crop: list(sim_columns(crop, "sim_rpg")) for crop in SPECS},
        "crop_groups_using_rpg": int(len(counts)), "all_crop_groups": len(coverage),
        "coverage": coverage, "rpg_metadata": rpg_meta,
        "spatial_method": "fixed RPG 2015 reported parcel area, point-on-surface assigned to containing department and nearest 8-km SIM centre; weights normalized per department/crop",
        "fallback": "exact existing CLC 2012 agricultural SIM values where crop-specific RPG weights are absent; all wheat and haricot groups are fallback in this extraction",
        "temporal_method": fallback_manifest["temporal_aggregation"],
        "availability_note": "2015 footprint is fixed across historical weather years. No annual crop-mask or rotation claim. Current reanalysis and source vintage are retrospective; pre-season decisions replay only past weather years.",
        "sim_sources": list(known_sources.values()), "frozen_inputs_sha256": frozen,
        "source_code_sha256": sha256(__file__), "output_sha256": sha256(args.output)}
    args.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    if any(sha256(p) != digest for p, digest in frozen.items()):
        raise ValueError("A frozen input changed during RPG feature generation")
    # Explicit fallback integrity: no unobserved crop/department is changed.
    indexed = output.set_index(["dep", "annee"])
    old = start_from_fallback(fallback)
    for row in coverage:
        if row["fallback"]:
            columns = list(sim_columns(row["culture"], "sim_rpg"))
            if not np.array_equal(indexed.loc[row["dep"], columns].to_numpy(), old.loc[row["dep"], columns].to_numpy()):
                raise AssertionError("Fallback group changed")
    print(f"Saved {args.output}: {len(output)} rows, {len(counts)} RPG crop/department groups", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fallback-file", type=Path, default=ROOT / "data/sim_agri_features.csv")
    parser.add_argument("--fallback-manifest", type=Path, default=ROOT / "data/sim_agri_manifest.json")
    parser.add_argument("--rpg-weights", type=Path, default=ROOT / "data/soil_rpg_grid_weights.csv")
    parser.add_argument("--soil-manifest", type=Path, default=ROOT / "data/soil_manifest.json")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "data_raw/sim_decadaire")
    parser.add_argument("--output", type=Path, default=ROOT / "data/sim_rpg_features.csv")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/sim_rpg_manifest.json")
    run(parser.parse_args())
