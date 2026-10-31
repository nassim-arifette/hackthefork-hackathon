"""Prototype de suivi en saison : NDVI Sentinel-2 de parcelles de lentille déclarées en 2025.

Replay de la saison 2025 (1er mars - 15 août) sur des parcelles réelles du RPG 2025 (code LEC),
les plus proches du site de collecte du scénario. Images Sentinel-2 L2A (Copernicus), catalogue
Earth Search d'Element 84, fichiers COG en accès libre, lus par fenêtres.

Pour chaque image et chaque parcelle : pixels de 10 m à l'intérieur de la parcelle réduite de
10 m (pour écarter les bordures), classés végétation ou sol nu par la couche SCL. La date est
retenue si au moins 60 % des pixels sont valides ; le NDVI de la parcelle est leur médiane.
Les seuils de statut sont des choix de l'équipe (supposé).

Réflectances : les métadonnées annoncent un décalage de +1 000 (bases de traitement ≥ 04.00)
et un indicateur `earthsearch:boa_offset_applied`. Dans toutes les images vérifiées, y compris
celles marquées « non corrigées », les valeurs sont déjà sans décalage : le rouge descend sous
1 000 sur la végétation (292 en médiane sur une lentille en juin), ce qui serait impossible
avec le décalage. Le NDVI se calcule donc sur les valeurs brutes, où l'échelle s'annule. Une
image marquée « non corrigée » dont tous les rouges dépassent 1 000 est écartée, faute de
pouvoir trancher.

Sortie : data/sentinel_lentilles_2025.json et app/src/data/sentinel.json.
"""
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import pyogrio
from pyproj import Transformer
import shapely
from shapely.geometry import mapping, shape

from common import APP_DATA, DATA, RAW, hypotheses

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif")
os.environ.setdefault("GDAL_HTTP_MULTIRANGE", "YES")
os.environ.setdefault("GDAL_HTTP_MERGE_CONSECUTIVE_RANGES", "YES")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "4")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")

import rasterio  # noqa: E402  (après la configuration GDAL)
from rasterio.enums import Resampling  # noqa: E402
from rasterio.features import geometry_mask  # noqa: E402
from rasterio.windows import bounds as win_bounds, from_bounds  # noqa: E402
from pystac_client import Client  # noqa: E402

STAC = "https://earth-search.aws.element84.com/v1"
SAISON = ("2025-03-01", "2025-08-15")
N_PARCELLES = 8
SURFACE_MIN_HA = 4.0
TAMPON_M = 10.0
PART_VALIDE_MIN = 0.6
SCL_VALIDE = (4, 5)  # végétation, sol nu
FENETRE_ECART = ("2025-05-01", "2025-06-30")  # floraison et remplissage
SEUILS = {"surveiller": -0.05, "retard": -0.10}  # écart de NDVI au groupe (supposé)


def haversine_km(lon1, lat1, lon2, lat2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def choisir_parcelles():
    """Les parcelles LEC du RPG 2025 affichées sur la carte, d'au moins 4 ha, les plus proches du site."""
    site = hypotheses()["site_acheteur"]["valeur"]
    carte = json.loads((APP_DATA / "parcels.json").read_text())
    lec = {p[0]: p[1] for p in carte if p[2] == "lentille"}
    gpkg = next((RAW / "rpg" / "x").glob("**/RPG_Parcelles.gpkg"))
    g = pyogrio.read_dataframe(gpkg, columns=["id_parcel", "surf_parc", "code_cultu"], where="code_cultu = 'LEC'")
    g = g[g.id_parcel.isin(lec) & (g.surf_parc >= SURFACE_MIN_HA)].copy()
    g["dep"] = g.id_parcel.map(lec)
    wgs = g.to_crs(4326)
    pts = wgs.geometry.representative_point()
    g["dist_km"] = haversine_km(pts.x.to_numpy(), pts.y.to_numpy(), site[0], site[1])
    g["geom_wgs"] = wgs.geometry
    return g.sort_values("dist_km").head(N_PARCELLES).reset_index(drop=True)


def lire_item(item, parcelles):
    """NDVI médian et part de pixels valides de chaque parcelle contenue dans l'image."""
    foot = shape(item.geometry)
    dedans = [i for i, r in parcelles.iterrows() if foot.contains(r.geom_wgs)]
    if not dedans:
        return []
    epsg = item.properties.get("proj:epsg") or int(str(item.properties.get("proj:code")).split(":")[1])
    tf = Transformer.from_crs(2154, epsg, always_xy=True)
    to_utm = lambda c: np.column_stack(tf.transform(c[:, 0], c[:, 1]))
    bands = {k: item.assets[k] for k in ("red", "nir", "scl")}
    base = float(item.properties.get("s2:processing_baseline", "0") or 0)
    a_verifier = base >= 4.0 and not item.properties.get("earthsearch:boa_offset_applied", False)
    out, rouges = [], []
    with rasterio.open(bands["red"].href) as red, rasterio.open(bands["nir"].href) as nir, \
            rasterio.open(bands["scl"].href) as scl:
        for i in dedans:
            r = parcelles.loc[i]
            geom = shapely.transform(r.geometry, to_utm).buffer(-TAMPON_M)
            if geom.is_empty:
                continue
            win = from_bounds(*geom.bounds, transform=red.transform).round_offsets().round_lengths()
            h, w = int(win.height), int(win.width)
            if h < 2 or w < 2:
                continue
            tr = red.window_transform(win)
            inside = geometry_mask([mapping(geom)], out_shape=(h, w), transform=tr, invert=True)
            n_in = int(inside.sum())
            if n_in < 20:
                continue
            b4 = red.read(1, window=win).astype("float32")
            b8 = nir.read(1, window=win).astype("float32")
            win_s = from_bounds(*win_bounds(win, red.transform), transform=scl.transform)
            s = scl.read(1, window=win_s, out_shape=(h, w), resampling=Resampling.nearest)
            ok = inside & np.isin(s, SCL_VALIDE) & ((b4 + b8) > 0)
            if ok.any():
                rouges.append(float(np.percentile(b4[ok], 2)))
            part = float(ok.sum()) / n_in
            ndvi = float(np.median(((b8 - b4) / (b8 + b4))[ok])) if ok.any() else None
            out.append({"id": r.id_parcel, "date": item.datetime.date().isoformat(), "tuile": item.id.split("_")[1],
                        "ndvi": None if ndvi is None else round(ndvi, 3), "part_valide": round(part, 3), "pixels": n_in})
    if a_verifier and rouges and min(rouges) >= 1000:
        print("  image écartée, décalage impossible à trancher :", item.id)
        return []
    return out


def statuts(series: dict[str, pd.Series]):
    """Écart de chaque parcelle au NDVI médian du groupe pendant la floraison et le remplissage."""
    jours = pd.date_range(*SAISON, freq="D")
    daily = pd.DataFrame({k: s.reindex(s.index.union(jours)).interpolate("time", limit_area="inside").reindex(jours)
                          for k, s in series.items()})
    ref = daily.median(axis=1, skipna=True)
    fen = (jours >= FENETRE_ECART[0]) & (jours <= FENETRE_ECART[1])
    out = {}
    for k in series:
        ecart = float((daily[k][fen] - ref[fen]).mean())
        statut = "en_retard" if ecart < SEUILS["retard"] else "a_surveiller" if ecart < SEUILS["surveiller"] else "conforme"
        pic = daily[k].idxmax()
        out[k] = {"ecart_floraison": round(ecart, 3), "statut": statut,
                  "ndvi_pic": round(float(daily[k].max()), 3), "date_pic": pic.date().isoformat()}
    ref_points = [[d.date().isoformat(), round(float(v), 3)] for d, v in ref.dropna().iloc[::3].items()]
    return out, ref_points


def main():
    parcelles = choisir_parcelles()
    print("Parcelles retenues :", parcelles[["id_parcel", "dep", "surf_parc", "dist_km"]].round(2).to_dict("records"))
    wgs_bounds = np.array([g.bounds for g in parcelles.geom_wgs])
    bbox = [wgs_bounds[:, 0].min(), wgs_bounds[:, 1].min(), wgs_bounds[:, 2].max(), wgs_bounds[:, 3].max()]
    items = list(Client.open(STAC).search(collections=["sentinel-2-l2a"], bbox=bbox, datetime="/".join(SAISON),
                                          query={"eo:cloud_cover": {"lt": 85}}).items())
    print(len(items), "images Sentinel-2 L2A sur la saison")
    mesures = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(lire_item, it, parcelles): it.id for it in items}
        for n, f in enumerate(as_completed(futs), 1):
            try:
                mesures += f.result()
            except Exception as e:  # une image illisible ne bloque pas le replay
                print("  image ignorée :", futs[f], type(e).__name__, str(e)[:120])
            if n % 20 == 0:
                print(f"  {n}/{len(items)} images lues")
    m = pd.DataFrame(mesures)
    # Une parcelle vue par deux tuiles le même jour : on garde la mesure la plus complète.
    m = m.sort_values("part_valide").drop_duplicates(["id", "date"], keep="last").sort_values(["id", "date"])
    valides = m[(m.part_valide >= PART_VALIDE_MIN) & m.ndvi.notna()]
    series = {k: g.set_index(pd.to_datetime(g.date)).ndvi for k, g in valides.groupby("id")}
    st, ref = statuts(series)

    out = {
        "saison": 2025, "periode": list(SAISON),
        "source": "Sentinel-2 L2A (Copernicus), catalogue Earth Search (Element 84)",
        "seuil_part_valide": PART_VALIDE_MIN, "tampon_m": TAMPON_M,
        "fenetre_ecart": list(FENETRE_ECART), "seuils_statut": SEUILS,
        "n_images": len(items), "reference": ref,
        "parcelles": [],
    }
    for _, r in parcelles.iterrows():
        mm = m[m.id == r.id_parcel]
        v = valides[valides.id == r.id_parcel]
        out["parcelles"].append({
            "id": r.id_parcel, "dep": r.dep, "surface_ha": round(float(r.surf_parc), 2),
            "dist_km": round(float(r.dist_km), 1), "pixels": int(mm.pixels.max()) if len(mm) else 0,
            "dates_vues": int(len(mm)), "dates_valides": int(len(v)),
            "serie": [[d, x] for d, x in zip(v.date, v.ndvi)],
        } | st.get(r.id_parcel, {}))
        print(r.id_parcel, out["parcelles"][-1].get("statut"), "dates valides", len(v), "/", len(mm))
    (DATA / "sentinel_lentilles_2025.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    (APP_DATA / "sentinel.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
