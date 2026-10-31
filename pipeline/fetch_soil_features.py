"""Retrieve real INRAE soil data and aggregate agricultural-area soil features.

The soil map is a static environmental covariate, not a measured annual yield.
Its first public release was October 2021: a 2019--2021 evaluation using it is a
retrospective static-map experiment, not a claim of data availability then.

The default small GeoPackage supplies BDGSF soil properties on SAFRAN cells and
CLC 2012 agricultural fractions. Aggregation weights exact department/grid
intersection area by CLC classes 211 + 241 + 242 (arable/annual/mixed cropping).
This is an agricultural mask, not a crop-specific or irrigation mask. The
GeoPackage was first published in 2022; its soil and CLC covariates are static,
so using it for earlier test years is an explicitly retrospective experiment.

The optional high-resolution raster uses every valid pixel centre within each
department, without agricultural weighting. ``soil_ru_sd_spatial_mm`` describes
spatial heterogeneity, not map prediction uncertainty. Missing cells are never
replaced with invented soil values. The model must keep these static
columns separate from weather anomalies (department centring would erase them).

Default source: Bertuzzi, P. and Clastre, P. (2022), "Information sur les mailles
SAFRAN", doi:10.57745/1PDFNL (BDGSF soil properties and CLC2012 land cover).
Optional raster: Roman Dobarco et al. (2021), doi:10.15454/9IRARJ, which considers
coarse fragments and estimated soil depth up to 2 m; related methods paper:
Román Dobarco et al. (2019), doi:10.1016/j.geoderma.2018.08.022.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import urllib.request
import urllib.parse

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOIL_URL = "https://entrepot.recherche.data.gouv.fr/api/access/datafile/121589"
SOIL_MD5 = "d3c9ef312fb66a208a63f275c1623900"
SOIL_BYTES = 644097138
GPKG_URL = "https://entrepot.recherche.data.gouv.fr/api/access/datafile/557079?format=original"
GPKG_MD5 = "591c0669f8d23b371db93ad14db9c33b"
GPKG_BYTES = 3358720
RU_COLUMNS = ("soil_ru_mean_mm", "soil_ru_sd_spatial_mm", "soil_ru_q10_mm", "soil_ru_q90_mm")
STATIC_COLUMNS = RU_COLUMNS + ("soil_depth_mean_cm", "soil_field_capacity_pct", "soil_wilting_point_pct")
RPG_CODES = {"LEC": "lentille", "PCH": "pois_chiche", "PHI": "pois", "PPR": "pois",
             "FVL": "feverole", "FVP": "feverole", "FVT": "feverole", "FEV": "feverole",
             "PHS": "haricot"}


def file_hash(path: Path, algorithm="sha256") -> str:
    digest = hashlib.new(algorithm)
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch_raster(path: Path) -> Path:
    """Download public bytes atomically, verifying the publisher's MD5."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.stat().st_size != SOIL_BYTES or file_hash(path, "md5") != SOIL_MD5:
            raise ValueError("Existing soil raster does not match the published checksum")
        return path
    temporary = path.with_suffix(".download")
    started, size = time.monotonic(), 0
    with urllib.request.urlopen(SOIL_URL, timeout=180) as response, temporary.open("wb") as out:
        for block in iter(lambda: response.read(8 * 1024 * 1024), b""):
            out.write(block)
            size += len(block)
            if size % (100 * 1024 * 1024) < len(block):
                print(json.dumps({"soil_download_bytes": size, "elapsed_s": round(time.monotonic() - started, 1)}), flush=True)
    if size != SOIL_BYTES or file_hash(temporary, "md5") != SOIL_MD5:
        raise ValueError("Downloaded soil raster does not match the published checksum")
    temporary.replace(path)
    return path


def summarize_values(values):
    """Population statistics in mm, preserving zero capacities if present."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values) & (values >= 0)]
    if not values.size:
        raise ValueError("No finite nonnegative soil values inside geometry")
    q10, q90 = np.quantile(values, [.1, .9])
    return dict(zip(RU_COLUMNS, map(float, [values.mean(), values.std(), q10, q90])))


def weighted_soil_statistics(values, weights):
    values, weights = np.asarray(values, float), np.asarray(weights, float)
    if values.shape != weights.shape or np.any(weights < 0) or not np.isfinite(weights).all():
        raise ValueError("Invalid soil weights")
    keep = np.isfinite(values) & (values >= 0) & (weights > 0)
    values, weights = values[keep], weights[keep]
    if not len(values):
        raise ValueError("No usable soil values with positive area")
    weights = weights / weights.sum()
    order = np.argsort(values, kind="stable")
    qs = values[order][np.searchsorted(np.cumsum(weights[order]), [.1, .9], side="left").clip(max=len(values) - 1)]
    mean = np.dot(values, weights)
    sd = np.sqrt(np.dot((values - mean) ** 2, weights))
    return dict(zip(RU_COLUMNS, map(float, [mean, sd, *qs])))


def fetch_geopackage(path):
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(GPKG_URL, timeout=180) as response:
            payload = response.read()
        if len(payload) != GPKG_BYTES or hashlib.md5(payload).hexdigest() != GPKG_MD5:
            raise ValueError("Soil GeoPackage download failed its published checksum")
        temporary = path.with_suffix(".download")
        temporary.write_bytes(payload)
        temporary.replace(path)
    if path.stat().st_size != GPKG_BYTES or file_hash(path, "md5") != GPKG_MD5:
        raise ValueError("Existing soil GeoPackage failed its published checksum")
    return path


def gpkg_geometry(blob):
    """Decode the standard GeoPackage binary envelope before its WKB geometry."""
    import shapely
    if blob[:2] != b"GP":
        raise ValueError("Invalid GeoPackage geometry header")
    envelope = (blob[3] >> 1) & 7
    sizes = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}
    if envelope not in sizes:
        raise ValueError("Invalid GeoPackage envelope")
    return shapely.from_wkb(blob[8 + sizes[envelope]:])


def load_soil_cells(gpkg_path, grid_path):
    """Match the 8602 source polygons to native SIM grid centres within 10 m."""
    from pyproj import Transformer
    from scipy.spatial import cKDTree
    import shapely

    with sqlite3.connect(gpkg_path) as connection:
        cells = pd.read_sql_query("SELECT * FROM safran", connection)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:27572", always_xy=True)
    geometries = [gpkg_geometry(blob) for blob in cells.location]
    projected = shapely.transform(np.asarray(geometries, dtype=object), transformer.transform, interleaved=False)
    centres = shapely.centroid(projected)
    points = np.c_[shapely.get_x(centres), shapely.get_y(centres)]
    grid = pd.read_csv(grid_path)
    distances, indexes = cKDTree(grid[["LAMBX", "LAMBY"]].to_numpy() * 100).query(points)
    if distances.max() > 10 or len(set(indexes)) != len(indexes):
        raise ValueError("Soil and native SIM grids do not align one-to-one within 10 metres")
    cells[["LAMBX", "LAMBY"]] = grid.iloc[indexes][["LAMBX", "LAMBY"]].to_numpy()
    cells["agri_fraction"] = cells[["clc_211", "clc_241", "clc_242"]].sum(axis=1, min_count=3) / 100
    if not cells.agri_fraction.dropna().between(0, 1).all():
        raise ValueError("Invalid Corine agricultural fractions")
    return cells, {"cells": len(cells), "native_grid_distance_max_m": float(distances.max()),
                   "missing_agricultural_fraction_cells": int(cells.agri_fraction.isna().sum())}


def aggregate_soil_cells(cells, department_weights):
    """Agricultural weights are computed without any crop yield or test score."""
    weights = department_weights.copy()
    if not np.isfinite(weights.weight).all() or (weights.weight < 0).any():
        raise ValueError("Invalid department intersection weights")
    merged = weights.merge(cells.drop(columns=["location", "dep"], errors="ignore"),
                           on=["LAMBX", "LAMBY"], how="left", validate="many_to_one")
    rows, coverage = [], []
    required = ["rupro", "pro", "hcc", "hpf", "agri_fraction"]
    for dep, g in merged.groupby("dep", sort=True):
        valid = np.isfinite(g[required].to_numpy(dtype=float)).all(axis=1)
        known = g[valid].copy()
        covered = float(known.weight.sum() / g.weight.sum())
        known["agri_weight"] = known.weight * known.agri_fraction
        known = known[known.agri_weight > 0]
        if known.empty:
            raise ValueError(f"No agricultural soil coverage for department {dep}")
        aw = known.agri_weight.to_numpy()
        stats = weighted_soil_statistics(known.rupro, aw)
        stats.update({out: float(np.average(known[col], weights=aw)) for col, out in
                      [("pro", "soil_depth_mean_cm"), ("hcc", "soil_field_capacity_pct"),
                       ("hpf", "soil_wilting_point_pct")]})
        rows.append({"dep": dep, **stats})
        coverage.append({"dep": dep, "known_soil_land_weight": covered,
                         "agricultural_weight_before_normalizing": float(aw.sum()),
                         "positive_agricultural_cells": len(known)})
    return pd.DataFrame(rows), coverage


def fetch_rpg_2015(cache_dir):
    """Complete deterministic pagination of selected 2015 RPG crop codes.

    PHS is a mixed dry-pea/dry-bean category: its use for haricot is an explicit
    proxy, never a claim that individual dry-bean fields have been identified.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cql = "code_cultu IN ('LEC','PCH','PHI','PPR','FVL','FVP','FVT','FEV','PHS')"
    start, matched, features, files = 0, None, [], []
    while matched is None or start < matched:
        path = cache_dir / f"rpg2015_legumes_{start}.json"
        if not path.exists():
            query = {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature",
                     "TYPENAMES": "RPG.2015:parcelles_graphiques", "OUTPUTFORMAT": "application/json",
                     "COUNT": "5000", "STARTINDEX": str(start), "SRSNAME": "EPSG:4326",
                     "CQL_FILTER": cql, "SORTBY": "id_parcel",
                     "PROPERTYNAME": "id_parcel,surf_parc,code_cultu,geom"}
            url = "https://data.geopf.fr/wfs/ows?" + urllib.parse.urlencode(query)
            with urllib.request.urlopen(url, timeout=180) as response:
                payload = response.read()
            record = json.loads(payload)
            if not record.get("features"):
                raise ValueError("RPG page unexpectedly empty")
            temporary = path.with_suffix(".download")
            temporary.write_bytes(payload)
            temporary.replace(path)
        record = json.loads(path.read_text())
        if matched is not None and record["numberMatched"] != matched:
            raise ValueError("RPG source changed while paginating")
        matched = int(record["numberMatched"])
        page = record["features"]
        if not page or len(page) > 5000:
            raise ValueError("Invalid RPG pagination")
        features.extend(page)
        files.append({"filename": path.name, "sha256": file_hash(path), "rows": len(page)})
        start += len(page)
    ids = [item["properties"]["id_parcel"] for item in features]
    if len(ids) != matched or len(set(ids)) != len(ids):
        raise ValueError("RPG pagination contains duplicates or omissions")
    code_counts = pd.Series([item["properties"]["code_cultu"] for item in features]).value_counts().sort_index().to_dict()
    return features, {"url": "https://data.geopf.fr/wfs/ows", "layer": "RPG.2015:parcelles_graphiques",
                      "land_cover_year": 2015, "matched_parcels": matched, "cql_filter": cql,
                      "files": files, "license": "Etalab Open License",
                      "crop_codes": RPG_CODES,
                      "observed_crop_code_counts": {k: int(v) for k, v in code_counts.items()},
                      "haricot_mask": "No PHS parcels were returned in the executed 2015 extraction; haricot uses general agricultural soil features. PHS, if present in another extraction, groups dry peas and dry beans and would only be a proxy."}


def aggregate_rpg_soil(features, cells, grid_path, geojson_path, departments):
    """Area-weight soil cells under representative points of historic parcels.

    A parcel is assigned to its containing department and nearest 8-km grid
    centre. The point-on-surface approximation is explicit; this does not claim
    subparcel precision for the 1:1,000,000 BDGSF soil input.
    """
    import shapely
    from shapely.geometry import shape
    from scipy.spatial import cKDTree
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:27572", always_xy=True)
    polygons = np.asarray([shape(f["geometry"]) for f in features], dtype=object)
    polygons = shapely.transform(polygons, transformer.transform, interleaved=False)
    points = shapely.point_on_surface(polygons)
    coords = np.c_[shapely.get_x(points), shapely.get_y(points)]
    boundaries = [f for f in json.loads(Path(geojson_path).read_text())["features"]
                  if str(f["properties"]["code"]) in set(departments)]
    boundary_geoms = shapely.transform(np.asarray([shape(f["geometry"]) for f in boundaries], dtype=object),
                                         transformer.transform, interleaved=False)
    dep_codes = [str(f["properties"]["code"]) for f in boundaries]
    hits = shapely.STRtree(boundary_geoms).query(points, predicate="within")
    dep_for_point = {}
    for point_index, dep_index in zip(*hits):
        code = dep_codes[dep_index]
        dep_for_point[int(point_index)] = min(code, dep_for_point.get(int(point_index), code))
    grid = pd.read_csv(grid_path)
    distance, index = cKDTree(grid[["LAMBX", "LAMBY"]].to_numpy() * 100).query(coords)
    parcels = pd.DataFrame({
        "dep": [dep_for_point.get(i) for i in range(len(features))],
        "culture": [RPG_CODES[f["properties"]["code_cultu"]] for f in features],
        "surface_ha": [float(f["properties"]["surf_parc"]) for f in features],
        "LAMBX": grid.iloc[index].LAMBX.to_numpy(), "LAMBY": grid.iloc[index].LAMBY.to_numpy(),
        "grid_distance_m": distance,
    })
    if not np.isfinite(parcels.surface_ha).all() or (parcels.surface_ha < 0).any():
        raise ValueError("Invalid RPG parcel areas")
    parcels = parcels[parcels.dep.notna() & (parcels.surface_ha > 0)].copy()
    if parcels.grid_distance_m.max() > 5700:
        raise ValueError("RPG points lie outside native SIM grid coverage")
    joined = parcels.merge(cells[["LAMBX", "LAMBY", "rupro", "pro", "hcc", "hpf"]],
                           on=["LAMBX", "LAMBY"], how="left", validate="many_to_one")
    rows, coverage, grid_rows = [], [], []
    for (dep, culture), group in joined.groupby(["dep", "culture"], sort=True):
        valid = np.isfinite(group[["rupro", "pro", "hcc", "hpf"]].to_numpy()).all(axis=1)
        used = group[valid]
        covered = float(used.surface_ha.sum() / group.surface_ha.sum())
        coverage.append({"dep": dep, "culture": culture, "source_parcels": len(group),
                         "soil_parcels": len(used), "source_surface_ha": float(group.surface_ha.sum()),
                         "known_soil_area_fraction": covered})
        if used.empty:
            continue
        aw = used.surface_ha.to_numpy()
        stats = weighted_soil_statistics(used.rupro, aw)
        stats.update({out: float(np.average(used[col], weights=aw)) for col, out in
                      [("pro", "soil_depth_mean_cm"), ("hcc", "soil_field_capacity_pct"),
                       ("hpf", "soil_wilting_point_pct")]})
        rows.append({"dep": dep, "culture": culture, **stats})
        weights = used.groupby(["LAMBX", "LAMBY"]).surface_ha.sum()
        for (x, y), area in weights.items():
            grid_rows.append({"dep": dep, "culture": culture, "LAMBX": x, "LAMBY": y,
                              "weight": float(area / weights.sum())})
    return pd.DataFrame(rows), pd.DataFrame(grid_rows), coverage


def aggregate_departments(raster_path: Path, geojson_path: Path, departments):
    """Exact pixel-centre zonal statistics in the raster's projected CRS."""
    import rasterio
    from rasterio.features import geometry_mask, geometry_window
    from rasterio.warp import transform_geom

    features = json.loads(Path(geojson_path).read_text())["features"]
    polygons = {str(f["properties"]["code"]): f["geometry"] for f in features}
    rows = []
    with rasterio.open(raster_path) as raster:
        if not raster.crs or not raster.crs.is_projected:
            raise ValueError("Equal-area pixel aggregation expects a projected soil raster")
        for dep in sorted(map(str, departments)):
            geometry = transform_geom("EPSG:4326", raster.crs, polygons[dep])
            window = geometry_window(raster, [geometry])
            data = raster.read(1, window=window, masked=True)
            inside = geometry_mask([geometry], out_shape=data.shape,
                transform=raster.window_transform(window), invert=True, all_touched=False)
            valid = inside & ~np.ma.getmaskarray(data) & np.isfinite(data.data) & (data.data >= 0)
            stats = summarize_values(data.data[valid])
            rows.append({"dep": dep, **stats,
                         "soil_valid_pixels": int(valid.sum()),
                         "soil_inside_pixels": int(inside.sum()),
                         "soil_valid_fraction": float(valid.sum() / inside.sum())})
            print(f"soil {dep}: {valid.sum()} pixels, mean {stats['soil_ru_mean_mm']:.1f} mm", flush=True)
        metadata = {"crs": str(raster.crs), "resolution": list(raster.res),
                    "width": raster.width, "height": raster.height, "nodata": raster.nodata}
    return pd.DataFrame(rows), metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["geopackage", "raster"], default="geopackage")
    parser.add_argument("--geopackage", type=Path, default=ROOT / "data_raw/soil/safran.gpkg")
    parser.add_argument("--grid", type=Path, default=ROOT / "data_raw/sim_decadaire/sim_grid.csv")
    parser.add_argument("--department-weights", type=Path, default=ROOT / "data_raw/sim_decadaire/department_weights.csv")
    parser.add_argument("--agricultural-fractions", type=Path, default=ROOT / "data/soil_agricultural_fractions.csv")
    parser.add_argument("--rpg", action="store_true", help="Also build optional crop-weighted 2015 RPG soil features")
    parser.add_argument("--rpg-cache", type=Path, default=ROOT / "data_raw/soil")
    parser.add_argument("--crop-output", type=Path, default=ROOT / "data/soil_features_crop.csv")
    parser.add_argument("--rpg-grid-output", type=Path, default=ROOT / "data/soil_rpg_grid_weights.csv")
    parser.add_argument("--raster", type=Path, default=ROOT / "data_raw/soil/AWCr_mm_0_200.tif")
    parser.add_argument("--geojson", type=Path, default=ROOT / "data_raw/geo/departements.geojson")
    parser.add_argument("--weather", type=Path, default=ROOT / "data/meteo_dept_cultures.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data/soil_features.csv")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/soil_manifest.json")
    args = parser.parse_args()
    if args.source == "geopackage":
        fetch_geopackage(args.geopackage)
        cells, mapping = load_soil_cells(args.geopackage, args.grid)
        fractions = cells[cells.agri_fraction.notna()][["LAMBX", "LAMBY", "agri_fraction", "cell"]].rename(columns={"cell": "soil_cell"})
        fractions.to_csv(args.agricultural_fractions, index=False, float_format="%.8f")
        weights = pd.read_csv(args.department_weights, dtype={"dep": str})
        result, coverage = aggregate_soil_cells(cells, weights)
        expected = set(pd.read_csv(args.weather, dtype={"dep": str}).dep)
        if set(result.dep) != expected:
            raise ValueError("Soil output and benchmark departments differ")
        result.to_csv(args.output, index=False, float_format="%.8f")
        manifest = {
            "source": {"doi": "10.57745/1PDFNL", "url": GPKG_URL,
                       "filename": args.geopackage.name, "published_year": 2022,
                       "md5": GPKG_MD5, "sha256": file_hash(args.geopackage),
                       "bytes": GPKG_BYTES, "license": "Etalab Open License 2.0"},
            "source_description": "INRAE BDGSF soil properties and Corine Land Cover 2012 fractions on SAFRAN cells",
            "aggregation": "department-grid exact intersection weight times CLC2012 fractions 211+241+242; normalize within department",
            "not_crop_specific": True,
            "static_columns": list(STATIC_COLUMNS),
            "spatial_sd_is_not_map_uncertainty": True,
            "availability": "Retrospective static environmental map for 2019-2025; GeoPackage published in 2022, CLC land cover vintage 2012; no yield target enters extraction",
            "mapping": mapping, "department_count": len(result), "coverage": coverage,
            "department_weights_sha256": file_hash(args.department_weights),
            "grid_sha256": file_hash(args.grid), "output_sha256": file_hash(args.output),
            "source_code_sha256": file_hash(Path(__file__)),
            "agricultural_fractions_sha256": file_hash(args.agricultural_fractions),
            "high_resolution_alternative": {"doi": "10.15454/9IRARJ", "url": SOIL_URL,
                "status": "public and reachable, full transfer deferred after measured 1 MiB range took 37 seconds; not used"},
        }
        if args.rpg:
            features, rpg_manifest = fetch_rpg_2015(args.rpg_cache)
            crop_result, grid_weights, crop_coverage = aggregate_rpg_soil(
                features, cells, args.grid, args.geojson, expected)
            crop_result.to_csv(args.crop_output, index=False, float_format="%.8f")
            grid_weights.to_csv(args.rpg_grid_output, index=False, float_format="%.10f")
            rpg_manifest.update({"aggregation": "parcel reported hectares, point-on-surface assignment to containing department and nearest native 8-km grid centre",
                "coverage": crop_coverage, "dep_crop_rows": len(crop_result),
                "missing_groups": "Groups absent from this file have no usable 2015 parcel mask; model must explicitly fall back to general agricultural soil features",
                "output_sha256": file_hash(args.crop_output), "grid_output_sha256": file_hash(args.rpg_grid_output)})
            manifest["rpg_2015"] = rpg_manifest
        args.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({"output": str(args.output), "departments": len(result), "mapping": mapping}))
        return
    fetch_raster(args.raster)
    departments = pd.read_csv(args.weather, dtype={"dep": str}).dep.unique()
    result, raster_metadata = aggregate_departments(args.raster, args.geojson, departments)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False, float_format="%.8f")
    manifest = {
        "source": {"doi": "10.15454/9IRARJ", "url": SOIL_URL,
                   "filename": args.raster.name, "published": "2021-10-04",
                   "md5": SOIL_MD5, "sha256": file_hash(args.raster),
                   "bytes": SOIL_BYTES, "license": "Etalab Open License 2.0"},
        "raster": raster_metadata,
        "aggregation": "all valid raster pixel centres in department; no crop-area weighting",
        "static_columns": list(RU_COLUMNS),
        "spatial_sd_is_not_map_uncertainty": True,
        "availability": "Static-map retrospective experiment before October 2021; available for decisions from 2022",
        "department_count": len(result),
        "coverage_min": float(result.soil_valid_fraction.min()),
        "geojson_sha256": file_hash(args.geojson),
        "output_sha256": file_hash(args.output),
        "dependencies": {name: __import__(name).__version__ for name in ("numpy", "pandas", "rasterio")},
    }
    args.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"output": str(args.output), "departments": len(result)}))


if __name__ == "__main__":
    main()
