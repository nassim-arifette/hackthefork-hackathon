"""Parcelles candidates d'Île-de-France depuis le RPG 2025 (IGN).

Parcelles retenues : blé tendre d'hiver (code BTH), candidates à la bascule, et
lentilles déjà déclarées (code LEC) pour référence. Les géométries sont simplifiées
en Lambert-93 puis converties en WGS84. Sortie : data/parcelles.json (compact).
"""
import json
import math

import numpy as np
import py7zr
import pyogrio
from shapely.geometry import shape
from shapely import STRtree

from common import DATA, DEPTS_URL, IDF_AGRI, RAW, RPG_URL, download

SIMPLIFY_M = 8
MIN_SURF_HA = 1.0
CODES = {"BTH": "ble", "LEC": "lentille"}


def gpkg_path():
    archive = download(RPG_URL, RAW / "rpg" / "rpg_idf_2025.7z", timeout=900)
    out = RAW / "rpg" / "x"
    found = list(out.glob("**/RPG_Parcelles.gpkg"))
    if not found:
        with py7zr.SevenZipFile(archive) as z:
            z.extractall(out)
        found = list(out.glob("**/RPG_Parcelles.gpkg"))
    return found[0]


def haversine_km(lon1, lat1, lon2, lat2):
    r = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dl = p2 - p1, np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def main():
    gdf = pyogrio.read_dataframe(gpkg_path(), columns=["id_parcel", "surf_parc", "code_cultu"],
                                 where="code_cultu IN ('BTH','LEC')")
    print("Parcelles RPG retenues :", gdf.code_cultu.value_counts().to_dict())
    gdf = gdf[gdf.surf_parc >= MIN_SURF_HA]
    gdf["geometry"] = gdf.geometry.simplify(SIMPLIFY_M, preserve_topology=True)
    gdf = gdf.to_crs(4326)

    deps = json.loads(download(DEPTS_URL, RAW / "geo" / "departements.geojson").read_text())
    feats = [f for f in deps["features"] if f["properties"]["code"] in IDF_AGRI]
    polys = [shape(f["geometry"]) for f in feats]
    tree = STRtree(polys)
    pts = gdf.geometry.representative_point()
    dep_of = []
    for p in pts:
        idx = [i for i in tree.query(p) if polys[i].contains(p)]
        dep_of.append(feats[idx[0]]["properties"]["code"] if idx else None)
    gdf["dep"] = dep_of
    gdf = gdf[gdf.dep.notna()]
    gdf["lon"], gdf["lat"] = pts.loc[gdf.index].x, pts.loc[gdf.index].y

    out = []
    for r in gdf.itertuples():
        g = r.geometry
        poly = max(g.geoms, key=lambda x: x.area) if g.geom_type == "MultiPolygon" else g
        ring = [round(v, 5) for xy in poly.exterior.coords for v in xy]
        out.append([r.id_parcel, r.dep, CODES[r.code_cultu], round(r.surf_parc, 2),
                    round(r.lon, 5), round(r.lat, 5), ring])
    (DATA / "parcelles.json").write_text(json.dumps(out, separators=(",", ":")))
    contours = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"code": f["properties"]["code"], "nom": f["properties"]["nom"]},
         "geometry": f["geometry"]} for f in feats]}
    (DATA / "contours_idf.json").write_text(json.dumps(contours, separators=(",", ":")))
    print(f"{len(out)} parcelles exportées, "
          f"{(DATA / 'parcelles.json').stat().st_size / 1e6:.1f} Mo")


if __name__ == "__main__":
    main()
