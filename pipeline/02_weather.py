"""Variables météo par département et par année, depuis l'API NASA POWER.

Un point par département : le centroïde du contour départemental (version 1).
Les réponses sont mises en cache dans data_raw/nasa_power/ ; une pause sépare
chaque requête. Sortie : data/meteo_dept.csv.
"""
import json
import time

import pandas as pd
import requests
from shapely.geometry import shape

from common import DATA, DEPTS_URL, IDF_AGRI, RAW, download

API = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMS = "T2M_MAX,T2M_MIN,PRECTOTCORR"
CACHE = RAW / "nasa_power"


def centroids() -> dict:
    gj = json.loads(download(DEPTS_URL, RAW / "geo" / "departements.geojson").read_text())
    out = {}
    for f in gj["features"]:
        c = shape(f["geometry"]).representative_point()
        out[f["properties"]["code"]] = (round(c.x, 3), round(c.y, 3))
    return out


def fetch(dep: str, lon: float, lat: float) -> pd.DataFrame:
    path = CACHE / f"{dep}.json"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        q = dict(parameters=PARAMS, community="AG", longitude=lon, latitude=lat,
                 start="20100101", end="20251231", format="JSON")
        for attempt in range(4):
            try:
                r = requests.get(API, params=q, timeout=180)
                r.raise_for_status()
                path.write_text(r.text)
                break
            except requests.RequestException:
                if attempt == 3:
                    raise
                time.sleep(2 ** (attempt + 2))
        time.sleep(1.5)
    p = json.loads(path.read_text())["properties"]["parameter"]
    df = pd.DataFrame(p)
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    return df.replace(-999.0, float("nan"))


def features(d: pd.DataFrame) -> pd.DataFrame:
    """Agrège la météo journalière en variables annuelles (docs/MODELE.md §1)."""
    rows = []
    for y, g in d.groupby(d.index.year):
        m, day = g.index.month, g.index.day
        between = lambda m1, d1, m2, d2: ((m > m1) | ((m == m1) & (day >= d1))) & \
                                         ((m < m2) | ((m == m2) & (day <= d2)))
        rows.append({
            "annee": y,
            "pluie_mj": g.PRECTOTCORR[(m >= 3) & (m <= 7)].sum(),
            "pluie_avj": g.PRECTOTCORR[(m >= 4) & (m <= 6)].sum(),
            "j30_jj": int((g.T2M_MAX[(m >= 6) & (m <= 7)] > 30).sum()),
            "gel_tardif": int((g.T2M_MIN[between(4, 1, 5, 15)] < -2).sum()),
            "pluie_recolte": g.PRECTOTCORR[between(7, 15, 8, 15)].sum(),
            "tmax_mj": g.T2M_MAX[(m >= 5) & (m <= 7)].mean(),
        })
    return pd.DataFrame(rows)


def main():
    panel = pd.read_csv(DATA / "panel_rendements.csv", dtype={"dep": str, "serie_groupe": str})
    # Acquisition covers every usable lentil territory. The legacy global
    # duplicate flags must never decide which weather histories are available
    # to a chronological fold; model.fit learns grouping on proper training only.
    u = panel[panel.utilisable]
    lent = set(u[u.culture == "lentille"].dep)
    deps = sorted(lent | set(IDF_AGRI))
    cents = centroids()
    out = []
    for i, dep in enumerate(deps, 1):
        lon, lat = cents[dep]
        f = features(fetch(dep, lon, lat))
        f.insert(0, "dep", dep)
        f["lon"], f["lat"] = lon, lat
        out.append(f)
        print(f"[{i}/{len(deps)}] {dep} ok", flush=True)
    df = pd.concat(out)
    df.to_csv(DATA / "meteo_dept.csv", index=False)
    print(df.groupby("annee")[["pluie_mj", "j30_jj", "gel_tardif"]].mean().round(1))


if __name__ == "__main__":
    main()
