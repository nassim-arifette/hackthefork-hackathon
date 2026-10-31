"""Le Maillon vu du ciel, prototype : repérer les légumineuses à graines d'une saison sans attendre le RPG.

Le RPG d'une campagne n'est publié que l'année suivante. Peut-on savoir avant la récolte où
poussent les légumineuses du bassin ? Zone de 24 × 24 km autour du site de collecte du scénario,
tuile Sentinel-2 31UDP. Pour 2024 et 2025 : images L2A du 1er avril au 31 juillet (catalogue
Earth Search, nuages < 95 % sur la tuile), NDVI et NDMI médians de chaque parcelle sur ses pixels
valides (SCL 4-5) après un tampon de 10 m. Une image ne compte pour une parcelle que si 60 % de
ses pixels sont valides. Médiane par période de 10 jours, interpolée dans le temps.
Étiquettes : RPG de la même campagne, groupes 8 (protéagineux : pois, féverole, lupin) et 15
(légumineuses à grains : lentille, pois chiche...). Modèle : LightGBM, classes pondérées,
variables spectrales seulement (la surface d'une parcelle l'identifierait d'une année à l'autre).

Validations, chacune en saison complète (images jusqu'au 31 juillet) et avant récolte (images
jusqu'au 10 juin seulement), toujours jugées sur des parcelles jamais vues à l'apprentissage :
- même campagne 2025, le collecteur connaît un bloc de 4 km sur cinq (les parcelles de ses
  adhérents, par exemple) : apprentissage sur ce bloc, test sur les quatre autres, pour chacun des
  cinq tirages. La carte montre le premier tirage ;
- même campagne, quatre blocs sur cinq connus (validation croisée par blocs classique) ;
- d'une année à l'autre, protocole prévu : appris sur 2024 avec le RPG 2024, appliqué aux images
  2025, jugé avec le RPG 2025 publié ensuite ;
- même transfert avec des valeurs relatives à la zone le même jour (écart à la médiane, en
  écarts interquartiles). Essai choisi après avoir vu l'échec du protocole prévu : à confirmer
  sur une autre paire d'années.
Les médianes par parcelle et par image sont gardées dans data_raw/sentinel/ ; supprimer ces
fichiers pour relire les images. Sortie : data/maillon_2025.json et app/src/data/maillon.json.
"""
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import py7zr
import pyogrio
from pyproj import Transformer

from common import APP_DATA, DATA, RAW, RPG_URL, download, hypotheses

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif")
os.environ.setdefault("GDAL_HTTP_MULTIRANGE", "YES")
os.environ.setdefault("GDAL_HTTP_MERGE_CONSECUTIVE_RANGES", "YES")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "4")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")

import lightgbm as lgb  # noqa: E402
import rasterio  # noqa: E402
from rasterio.enums import Resampling  # noqa: E402
from rasterio.features import rasterize  # noqa: E402
from rasterio.transform import from_origin  # noqa: E402
from rasterio.windows import from_bounds  # noqa: E402
from pystac_client import Client  # noqa: E402
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score  # noqa: E402
from sklearn.model_selection import GroupKFold  # noqa: E402

STAC = "https://earth-search.aws.element84.com/v1"
APPRENTISSAGE, TEST = 2024, 2025
DEBUT, FIN, COUPURE = "04-01", "07-31", "06-10"  # mois-jour : saison et coupure avant récolte
VERSIONS = (("saison", FIN), ("avant_recolte", COUPURE))
NUAGES_MAX = 95
TUILE, EPSG = "31UDP", 32631
DEMI_COTE_M, RES = 12000, 10
TAMPON_M, PIXELS_MIN, PART_VALIDE_MIN, DATES_MIN = 10.0, 20, 0.6, 3
SURFACE_MIN_HA = 1.0
GROUPES_LEGUMINEUSES = {"8", "15"}
BLOC_M = 4000
PERIODE_J = 10
SEUIL = 0.5
DATE_PARCELLES_MIN = 200  # pour l'essai relatif : une date vue sur moins de parcelles ne représente pas la zone


def zone():
    site = hypotheses()["site_acheteur"]["valeur"]
    x, y = Transformer.from_crs(4326, EPSG, always_xy=True).transform(*site)
    x0, y0 = round(x / RES) * RES - DEMI_COTE_M, round(y / RES) * RES - DEMI_COTE_M
    return x0, y0, x0 + 2 * DEMI_COTE_M, y0 + 2 * DEMI_COTE_M


def gpkg(annee):
    """RPG Île-de-France d'une campagne, téléchargé et extrait au besoin (même édition 4.0)."""
    out = RAW / "rpg" / ("x" if annee == 2025 else f"x{annee}")
    found = list(out.glob("**/RPG_Parcelles.gpkg"))
    if not found:
        url = RPG_URL.replace("2025-01-01", f"{annee}-01-01")
        with py7zr.SevenZipFile(download(url, RAW / "rpg" / f"rpg_idf_{annee}.7z", timeout=900)) as z:
            z.extractall(out)
        found = list(out.glob("**/RPG_Parcelles.gpkg"))
    return found[0]


def parcelles(b, annee):
    bbox = Transformer.from_crs(EPSG, 2154, always_xy=True).transform_bounds(*b, densify_pts=21)
    g = pyogrio.read_dataframe(gpkg(annee), bbox=bbox, columns=["id_parcel", "surf_parc", "code_cultu", "code_group"])
    g = g[g.surf_parc >= SURFACE_MIN_HA].to_crs(EPSG)
    c = g.geometry.representative_point()
    inside = ((c.x > b[0]) & (c.x < b[2]) & (c.y > b[1]) & (c.y < b[3])).to_numpy()
    g, c = g[inside].reset_index(drop=True), c[inside].reset_index(drop=True)
    g["id_parcel"] = g.id_parcel.astype(str)
    g["legumineuse"] = g.code_group.astype(str).isin(GROUPES_LEGUMINEUSES).astype(int)
    g["bloc"] = ((c.x - b[0]) // BLOC_M).astype(int) * 100 + ((c.y - b[1]) // BLOC_M).astype(int)
    return g


def raster_parcelles(g, b):
    """Numéro de parcelle de chaque pixel de 10 m (−1 hors parcelle), parcelles réduites de 10 m."""
    n = int((b[2] - b[0]) / RES)
    shapes = [(s, i) for i, s in enumerate(g.geometry.buffer(-TAMPON_M)) if not s.is_empty]
    lab = rasterize(shapes, out_shape=(n, n), transform=from_origin(b[0], b[3], RES, RES), fill=-1, dtype="int32")
    return lab, np.bincount(lab[lab >= 0], minlength=len(g))


def images(annee, b):
    bbox = Transformer.from_crs(EPSG, 4326, always_xy=True).transform_bounds(*b)
    its = Client.open(STAC).search(collections=["sentinel-2-l2a"], bbox=bbox, datetime=f"{annee}-{DEBUT}/{annee}-{FIN}",
                                   query={"eo:cloud_cover": {"lt": NUAGES_MAX}}).items()
    par_prise = {}
    for it in its:
        sat, tuile, jour, num = it.id.split("_")[:4]
        if tuile == TUILE and int(num) >= int(par_prise.get((sat, jour), ("", "-1"))[1]):
            par_prise[(sat, jour)] = (it, num)  # un retraitement remplace la version précédente
    return sorted((v[0] for v in par_prise.values()), key=lambda it: it.datetime)


def lire_image(item, b, lab, n_pix, ids):
    """Médianes de NDVI et NDMI des parcelles dont au moins 60 % des pixels sont valides."""
    n = lab.shape[0]
    arr = {}
    for k in ("red", "nir", "swir16", "scl"):
        with rasterio.open(item.assets[k].href) as src:
            win = from_bounds(*b, transform=src.transform)
            rs = Resampling.nearest if k == "scl" else Resampling.bilinear
            arr[k] = src.read(1, window=win, out_shape=(n, n), resampling=rs, boundless=True, fill_value=0)
    red, nir, sw = (arr[k].astype("float32") for k in ("red", "nir", "swir16"))
    ok = (lab >= 0) & np.isin(arr["scl"], (4, 5)) & (red > 0) & (nir > 0) & (sw > 0)
    vide = pd.DataFrame(columns=["id_parcel", "date", "ndvi", "ndmi"])
    if not ok.any():
        return vide
    # Même règle que 08_sentinel.py : sans décalage +1000 appliqué, le rouge des couverts denses
    # descend sous 1000 ; s'il ne descend jamais sous ce seuil, l'image est écartée.
    base = float(item.properties.get("s2:processing_baseline", "0") or 0)
    if base >= 4.0 and not item.properties.get("earthsearch:boa_offset_applied", False) \
            and np.percentile(red[ok], 2) >= 1000:
        print("  image écartée, décalage radiométrique impossible à trancher :", item.id)
        return vide
    idx = lab[ok]
    df = pd.DataFrame({"p": idx, "ndvi": ((nir - red) / (nir + red))[ok], "ndmi": ((nir - sw) / (nir + sw))[ok]})
    med = df.groupby("p").median()
    part = np.bincount(idx, minlength=len(n_pix)) / np.maximum(n_pix, 1)
    med = med[part[med.index] >= PART_VALIDE_MIN]
    med.insert(0, "id_parcel", ids[med.index])
    med.insert(1, "date", item.datetime.date().isoformat())
    return med.reset_index(drop=True)


def observations(annee, g, b, lab, n_pix):
    cache = RAW / "sentinel" / f"maillon_{annee}.csv.gz"
    if cache.exists():
        return pd.read_csv(cache, dtype={"id_parcel": str})
    its = images(annee, b)
    print(f"{annee} : {len(its)} images de la tuile {TUILE} à lire")
    obs, ids = [], g.id_parcel.to_numpy()
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(lire_image, it, b, lab, n_pix, ids): it.id for it in its}
        for k, f in enumerate(as_completed(futs), 1):
            try:
                obs.append(f.result())
            except Exception as e:  # une image illisible ne bloque pas la saison
                print("  image ignorée :", futs[f], type(e).__name__, str(e)[:100])
            if k % 5 == 0:
                print(f"  {k}/{len(its)} images")
    obs = pd.concat(obs).sort_values(["date", "id_parcel"]).reset_index(drop=True)
    cache.parent.mkdir(parents=True, exist_ok=True)
    obs.to_csv(cache, index=False, float_format="%.4f")
    return obs


def caracteristiques(obs, ids, annee, fin):
    """Séries par période de 10 jours, interpolées dans le temps, quelques résumés, dates utiles."""
    debut, fin = pd.Timestamp(f"{annee}-{DEBUT}"), pd.Timestamp(f"{annee}-{fin}")
    o = obs[pd.to_datetime(obs.date) <= fin].copy()
    o["periode"] = ((pd.to_datetime(o.date) - debut).dt.days // PERIODE_J).astype(int)
    feats = []
    for v in ("ndvi", "ndmi"):
        piv = o.pivot_table(index="id_parcel", columns="periode", values=v, aggfunc="median")
        piv = piv.reindex(index=ids, columns=range((fin - debut).days // PERIODE_J + 1)).astype(float)
        piv = piv.interpolate(axis=1, method="index", limit_direction="both")  # périodes sans image
        piv.columns = [f"{v}_{c:02d}" for c in piv.columns]
        feats.append(piv)
    f = pd.concat(feats, axis=1).reset_index(drop=True)
    ndvi = f[[c for c in f.columns if c.startswith("ndvi_")]].fillna(-1).to_numpy()
    f["ndvi_max"] = ndvi.max(axis=1)
    f["ndvi_periode_max"] = ndvi.argmax(axis=1)
    f["ndvi_amplitude"] = ndvi.max(axis=1) - ndvi.min(axis=1)
    n_dates = o.groupby("id_parcel").date.nunique().reindex(ids).fillna(0).astype(int).to_numpy()
    return f, n_dates


def relatives(obs):
    """Essai : chaque valeur rapportée à la zone le même jour, (x − médiane) / écart interquartile."""
    o = obs[obs.groupby("date").id_parcel.transform("size") >= DATE_PARCELLES_MIN].copy()
    for v in ("ndvi", "ndmi"):
        q = o.groupby("date")[v]
        iqr = q.transform(lambda x: x.quantile(0.75) - x.quantile(0.25)).clip(lower=0.05)
        o[v] = (o[v] - q.transform("median")) / iqr
    return o


def modele():
    return lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=15, min_child_samples=10,
                              subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                              class_weight="balanced", random_state=0, verbose=-1)


def metriques(y, proba, surf):
    pred = (proba >= SEUIL).astype(int)
    return {
        "n_parcelles": len(y), "n_legumineuses": int(y.sum()),
        "precision": round(float(precision_score(y, pred)), 3),
        "rappel": round(float(recall_score(y, pred)), 3),
        "f1": round(float(f1_score(y, pred)), 3),
        "precision_moyenne": round(float(average_precision_score(y, proba)), 3),
        "vrais_positifs": int(((pred == 1) & (y == 1)).sum()), "faux_positifs": int(((pred == 1) & (y == 0)).sum()),
        "faux_negatifs": int(((pred == 0) & (y == 1)).sum()),
        "surface_rpg_ha": round(float(surf[y == 1].sum()), 1),
        "surface_detectee_ha": round(float(surf[pred == 1].sum()), 1),
        "surface_bien_detectee_ha": round(float(surf[(pred == 1) & (y == 1)].sum()), 1),
    }


def maturite(obs, g, code, seuil=0.5, vues_min=10):
    """Date où le NDVI médian d'une culture repasse sous `seuil` après son pic (interpolée entre deux dates)."""
    o = obs.merge(g[["id_parcel", "code_cultu"]], on="id_parcel")
    m = o[o.code_cultu == code].groupby("date").ndvi.agg(["median", "size"])
    m = m[m["size"] >= vues_min]["median"]
    m.index = pd.to_datetime(m.index)
    apres = m[m.index >= m.idxmax()]
    sous = apres[apres < seuil]
    if sous.empty:
        return None
    d1, v1 = sous.index[0], sous.iloc[0]
    d0 = apres.index[apres.index.get_loc(d1) - 1]
    v0 = apres[d0]
    return (d0 + (d1 - d0) * float((v0 - seuil) / (v0 - v1))).date().isoformat()


def arrondi(p):
    """Probabilité arrondie au centième sans franchir le seuil : la carte reste fidèle aux métriques."""
    if np.isnan(p):
        return None
    r = round(float(p), 2)
    return min(r, round(SEUIL - 0.01, 2)) if p < SEUIL else max(r, SEUIL)


def campagne(annee, b):
    g = parcelles(b, annee)
    lab, n_pix = raster_parcelles(g, b)
    obs = observations(annee, g, b, lab, n_pix)
    ids, leg = g.id_parcel.to_numpy(), g.legumineuse.to_numpy()
    X, ok, dates_med = {}, {}, {}
    for variante, o in (("brut", obs), ("relatif", relatives(obs))):
        for nom, fin in VERSIONS:
            X[variante, nom], n_dates = caracteristiques(o, ids, annee, fin)
            # Sinon : parcelle non classée (trop petite, ou trop peu de dates sans nuages).
            ok[variante, nom] = (n_pix >= PIXELS_MIN) & (n_dates >= DATES_MIN)
            if variante == "brut":
                dates_med[nom] = float(np.median(n_dates[n_pix >= PIXELS_MIN]))
    resume = {
        "n_parcelles_zone": len(g), "n_legumineuses_zone": int(leg.sum()),
        "surface_legumineuses_ha": round(float(g.surf_parc[leg == 1].sum()), 1),
        "n_images": int(obs.date.nunique()),
        "versions": {nom: {"n_dates": int(obs[obs.date <= f"{annee}-{fin}"].date.nunique()),
                           "n_parcelles": int(ok["brut", nom].sum()), "n_legumineuses": int(leg[ok["brut", nom]].sum()),
                           "dates_par_parcelle_mediane": dates_med[nom]}
                     for nom, fin in VERSIONS},
        "maturite_ndvi_05": {c: maturite(obs, g, c) for c in ("BTH", "FVL")},
        "legumineuses_par_code": {k: {"n": int(v.n), "ha": round(float(v.ha), 1)} for k, v in
                                  g[leg == 1].groupby("code_cultu").agg(n=("id_parcel", "size"),
                                                                        ha=("surf_parc", "sum")).iterrows()},
    }
    print(annee, resume)
    return {"g": g, "ok": ok, "X": X, "resume": resume}


def main():
    b = zone()
    a, t = campagne(APPRENTISSAGE, b), campagne(TEST, b)
    gt = t["g"]
    yt, st, ct = gt.legumineuse.to_numpy(), gt.surf_parc.to_numpy(), gt.code_cultu.to_numpy()
    ya = a["g"].legumineuse.to_numpy()
    res, probas, confusions, blocs_connus = {}, {}, {}, None
    for nom, fin in VERSIONS:
        r = {"coupure": f"{TEST}-{fin}"}
        ok = t["ok"]["brut", nom]
        Xt, y, grp = t["X"]["brut", nom][ok].reset_index(drop=True), yt[ok], gt.bloc.to_numpy()[ok]
        # Quatre blocs sur cinq connus : validation croisée par blocs classique.
        p = np.zeros(len(y))
        for tr, te in GroupKFold(n_splits=5).split(Xt, y, grp):
            p[te] = modele().fit(Xt.iloc[tr], y[tr]).predict_proba(Xt.iloc[te])[:, 1]
        r["blocs"] = metriques(y, p, st[ok])
        # Un bloc sur cinq connu : on apprend sur le cinquième, on juge sur le reste.
        tirages = []
        for k, (reste, connus) in enumerate(GroupKFold(n_splits=5).split(Xt, y, grp)):
            p = modele().fit(Xt.iloc[connus], y[connus]).predict_proba(Xt.iloc[reste])[:, 1]
            tirages.append(metriques(y[reste], p, st[ok][reste]) | {"n_legumineuses_apprentissage": int(y[connus].sum())})
            if k == 0 and blocs_connus is None:
                blocs_connus = np.unique(grp[connus])
        # Carte : le premier tirage, avec les mêmes blocs connus pour les deux versions.
        connus = ok & np.isin(gt.bloc.to_numpy(), blocs_connus)
        reste = ok & ~connus
        p = modele().fit(t["X"]["brut", nom][connus], yt[connus]).predict_proba(t["X"]["brut", nom][reste])[:, 1]
        probas[nom] = np.full(len(gt), np.nan)
        probas[nom][reste] = p
        r["un_sur_cinq"] = {
            "moyenne": {k: round(float(np.mean([x[k] for x in tirages])), 3) for k in ("precision", "rappel", "precision_moyenne")},
            "min": {k: round(float(min(x[k] for x in tirages)), 3) for k in ("precision", "rappel")},
            "max": {k: round(float(max(x[k] for x in tirages)), 3) for k in ("precision", "rappel")},
            "surface_detectee_sur_rpg": round(float(np.mean([x["surface_detectee_ha"] / x["surface_rpg_ha"] for x in tirages])), 3),
            "tirages": tirages, "carte": metriques(yt[reste], p, st[reste]),
        }
        pred, codes, yr = p >= SEUIL, ct[reste], yt[reste]
        confusions[nom] = {
            "faux_positifs_par_code": pd.Series(codes[pred & (yr == 0)]).value_counts().head(6).to_dict(),
            "rappel_par_code": {c: {"n": int(((codes == c) & (yr == 1)).sum()), "vus": int(((codes == c) & (yr == 1) & pred).sum())}
                                for c in sorted(set(codes[yr == 1]))},
        }
        # D'une année à l'autre : appris sur 2024, appliqué à 2025.
        for variante, cle in (("brut", "transfert"), ("relatif", "transfert_relatif")):
            ok, oka = t["ok"][variante, nom], a["ok"][variante, nom]
            mod = modele().fit(a["X"][variante, nom][oka].reset_index(drop=True), ya[oka])
            p = mod.predict_proba(t["X"][variante, nom][ok].reset_index(drop=True))[:, 1]
            r[cle] = metriques(yt[ok], p, st[ok]) | {"n_apprentissage": int(oka.sum()),
                                                     "n_legumineuses_apprentissage": int(ya[oka].sum())}
        for cle in ("blocs", "transfert", "transfert_relatif"):
            # Rappel sur toutes les légumineuses de la zone : une parcelle non classée compte comme manquée.
            r[cle]["rappel_zone"] = round(r[cle]["vrais_positifs"] / int(yt.sum()), 3)
            print(nom, f"{cle:18s}", r[cle])
        print(nom, "un_sur_cinq       ", {k: v for k, v in r["un_sur_cinq"].items() if k != "tirages"})
        res[nom] = r

    # Carte 2025 : géométries simplifiées en WGS 84 ; [code, légumineuse, bloc connu, p au 10 juin, p au 31 juillet, ha, contour].
    gw = gt.copy()
    gw["geometry"] = gw.geometry.simplify(8, preserve_topology=True)
    gw = gw.to_crs(4326)
    carte = []
    for i, r in enumerate(gw.itertuples()):
        geom = r.geometry if r.geometry.geom_type == "Polygon" else max(r.geometry.geoms, key=lambda q: q.area)
        ring = [round(v, 5) for xy in geom.exterior.coords for v in xy]
        pa, ps = probas["avant_recolte"][i], probas["saison"][i]
        carte.append([r.code_cultu, int(r.legumineuse), int(r.bloc in blocs_connus), arrondi(pa), arrondi(ps),
                      round(float(r.surf_parc), 2), ring])

    out = {
        "campagne_test": TEST, "campagne_apprentissage": APPRENTISSAGE, "periode": [DEBUT, FIN], "coupure": COUPURE,
        "tuile": TUILE, "zone_km": 2 * DEMI_COTE_M / 1000,
        "zone_wgs84": [round(v, 5) for v in Transformer.from_crs(EPSG, 4326, always_xy=True).transform_bounds(*b)],
        "nuages_max_tuile": NUAGES_MAX, "bloc_km": BLOC_M / 1000, "groupes_rpg": sorted(GROUPES_LEGUMINEUSES),
        "seuil": SEUIL, "campagnes": {str(APPRENTISSAGE): a["resume"], str(TEST): t["resume"]},
        "resultats": res, "blocs_connus_carte": [int(v) for v in blocs_connus], "confusions_carte": confusions,
    }
    (DATA / "maillon_2025.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    (APP_DATA / "maillon.json").write_text(json.dumps(out | {"parcelles": carte}, ensure_ascii=False, separators=(",", ":")))
    print(json.dumps(confusions, ensure_ascii=False))


if __name__ == "__main__":
    main()
